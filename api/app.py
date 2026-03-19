import hashlib
import hmac
import json
import logging
import os
import sys
from datetime import datetime, timezone
from urllib.parse import parse_qsl

import pytz
from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

# Make the top-level package importable from the API container.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.database.models import Notification, RecurrenceType, User  # noqa: E402
from bot.i18n import _LOCALES_DIR, _SUPPORTED_LANGS, normalize_language_code  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

BOT_TOKEN: str = os.environ.get("TELEGRAM_BOT_TOKEN", "")


def _db_url() -> str:
    user = os.environ.get("POSTGRES_USER", "postgres")
    password = os.environ.get("POSTGRES_PASSWORD", "postgres")
    host = os.environ.get("POSTGRES_HOST", "db")
    port = os.environ.get("POSTGRES_PORT", "5432")
    db = os.environ.get("POSTGRES_DB", "notifications")
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"


engine = create_engine(_db_url(), pool_pre_ping=True)


# ---------------------------------------------------------------------------
# Telegram initData validation
# ---------------------------------------------------------------------------

def validate_init_data(init_data: str) -> dict | None:
    """Validate Telegram WebApp initData using HMAC-SHA256.

    Returns the parsed parameter dict (without *hash*) on success, or *None*
    when validation fails.
    """
    if not init_data or not BOT_TOKEN:
        return None
    try:
        params = dict(parse_qsl(init_data, keep_blank_values=True))
        hash_value = params.pop("hash", "")
        if not hash_value:
            return None

        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(params.items()))

        # secret_key = HMAC-SHA256(key="WebAppData", msg=bot_token)
        secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
        # expected = HMAC-SHA256(key=secret_key, msg=data_check_string)
        expected = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

        if not hmac.compare_digest(expected, hash_value):
            return None
        return params
    except Exception:
        logger.exception("Error validating initData")
        return None


def _get_current_user(session: Session) -> User | None:
    """Extract and validate the Telegram user from the request headers."""
    init_data = request.headers.get("X-Init-Data", "")
    if not init_data:
        return None
    params = validate_init_data(init_data)
    if params is None:
        return None
    try:
        user_data = json.loads(params.get("user", "{}"))
    except (json.JSONDecodeError, TypeError):
        return None
    telegram_id = user_data.get("id")
    if not telegram_id:
        return None
    result = session.execute(select(User).where(User.telegram_id == int(telegram_id)))
    return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# i18n – serve translation JSON for the Web App
# ---------------------------------------------------------------------------

@app.route("/api/i18n/<string:lang>", methods=["GET"])
def get_translations(lang: str):
    """Return the translation JSON for the requested language.

    Falls back to English when the requested language is not supported.
    The response is intentionally unauthenticated so the Web App can fetch
    translations before (or without) a valid Telegram session.
    """
    safe_lang = lang if lang in _SUPPORTED_LANGS else "en"
    path = _LOCALES_DIR / f"{safe_lang}.json"
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except OSError:
        return jsonify({"error": "Translations not found"}), 404
    return jsonify(data)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------

@app.route("/api/notifications", methods=["GET"])
def get_notifications():
    with Session(engine) as session:
        user = _get_current_user(session)
        if user is None:
            return jsonify({"error": "Unauthorized"}), 401

        date_filter: str | None = request.args.get("date")
        stmt = (
            select(Notification)
            .where(Notification.user_id == user.id)
            .order_by(Notification.scheduled_at)
        )
        notifications = session.execute(stmt).scalars().all()

        user_tz = pytz.timezone(user.timezone or "UTC")
        data = []
        for n in notifications:
            local_dt = n.scheduled_at.astimezone(user_tz)
            local_date_str = local_dt.strftime("%Y-%m-%d")
            if date_filter and local_date_str != date_filter:
                continue
            data.append(
                {
                    "id": n.id,
                    "title": n.title,
                    "description": n.description,
                    "scheduled_at": n.scheduled_at.isoformat(),
                    "local_date": local_date_str,
                    "local_time": local_dt.strftime("%H:%M"),
                    "recurrence_type": n.recurrence_type.value,
                    "is_active": n.is_active,
                    "created_at": n.created_at.isoformat(),
                }
            )
        return jsonify(data)


@app.route("/api/notifications", methods=["POST"])
def create_notification():
    with Session(engine) as session:
        user = _get_current_user(session)
        if user is None:
            return jsonify({"error": "Unauthorized"}), 401

        body = request.get_json(silent=True)
        if not body:
            return jsonify({"error": "Invalid JSON body"}), 400

        title = (body.get("title") or "").strip()
        description = (body.get("description") or "").strip()
        scheduled_at_str: str = body.get("scheduled_at", "")
        recurrence_str: str = body.get("recurrence_type", "once")

        if not title or not scheduled_at_str:
            return jsonify({"error": "title and scheduled_at are required"}), 400

        try:
            recurrence_type = RecurrenceType(recurrence_str)
        except ValueError:
            return jsonify({"error": f"Invalid recurrence_type: {recurrence_str}"}), 400

        try:
            scheduled_at = datetime.fromisoformat(scheduled_at_str)
            if scheduled_at.tzinfo is None:
                scheduled_at = scheduled_at.replace(tzinfo=timezone.utc)
            else:
                scheduled_at = scheduled_at.astimezone(timezone.utc)
        except ValueError:
            return jsonify({"error": "Invalid scheduled_at; use ISO 8601 format"}), 400

        if scheduled_at <= datetime.now(timezone.utc):
            return jsonify({"error": "scheduled_at must be in the future"}), 400

        notification = Notification(
            user_id=user.id,
            title=title,
            description=description,
            scheduled_at=scheduled_at,
            recurrence_type=recurrence_type,
            next_run_at=scheduled_at,
            is_active=True,
        )
        session.add(notification)
        session.commit()
        session.refresh(notification)

        return (
            jsonify(
                {
                    "id": notification.id,
                    "title": notification.title,
                    "description": notification.description,
                    "scheduled_at": notification.scheduled_at.isoformat(),
                    "recurrence_type": notification.recurrence_type.value,
                    "is_active": notification.is_active,
                }
            ),
            201,
        )


@app.route("/api/notifications/<int:notification_id>", methods=["DELETE"])
def delete_notification(notification_id: int):
    with Session(engine) as session:
        user = _get_current_user(session)
        if user is None:
            return jsonify({"error": "Unauthorized"}), 401

        result = session.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user.id,
            )
        )
        notification = result.scalar_one_or_none()
        if notification is None:
            return jsonify({"error": "Not found"}), 404

        session.delete(notification)
        session.commit()
        return jsonify({"success": True})


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------

@app.route("/api/user", methods=["GET"])
def get_user():
    with Session(engine) as session:
        user = _get_current_user(session)
        if user is None:
            return jsonify({"error": "Unauthorized"}), 401

        return jsonify(
            {
                "telegram_id": user.telegram_id,
                "username": user.username,
                "first_name": user.first_name,
                "language_code": user.language_code,
                "timezone": user.timezone,
            }
        )


@app.route("/api/user/language", methods=["PUT"])
def update_language():
    with Session(engine) as session:
        user = _get_current_user(session)
        if user is None:
            return jsonify({"error": "Unauthorized"}), 401

        body = request.get_json(silent=True)
        if not body:
            return jsonify({"error": "Invalid JSON body"}), 400

        lang = (body.get("language") or "en").strip()
        normalized = normalize_language_code(lang)
        user.language_code = normalized
        session.commit()
        return jsonify({"language_code": user.language_code})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
