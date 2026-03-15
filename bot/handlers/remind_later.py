import calendar
import logging
from datetime import datetime, timedelta, timezone

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import Notification, User
from bot.i18n import get_text
from bot.scheduler.scheduler import remove_notification_job, schedule_notification
from bot.utils.timezone import utc_to_user

logger = logging.getLogger(__name__)

router = Router()

# Supported delay keys and their human-readable labels (used only for logging)
_VALID_DELAYS = {"5min", "10min", "1day", "1month", "1year"}


def _apply_delay(base: datetime, delay: str) -> datetime:
    """Return a new UTC datetime shifted by the requested delay."""
    if delay == "5min":
        return base + timedelta(minutes=5)
    if delay == "10min":
        return base + timedelta(minutes=10)
    if delay == "1day":
        return base + timedelta(days=1)
    if delay == "1month":
        month = base.month + 1
        year = base.year + (month - 1) // 12
        month = ((month - 1) % 12) + 1
        try:
            return base.replace(year=year, month=month)
        except ValueError:
            last_day = calendar.monthrange(year, month)[1]
            return base.replace(year=year, month=month, day=min(base.day, last_day))
    if delay == "1year":
        try:
            return base.replace(year=base.year + 1)
        except ValueError:
            # Feb 29 edge case
            return base.replace(year=base.year + 1, day=28)
    raise ValueError(f"Unknown delay: {delay!r}")


@router.callback_query(F.data.startswith("remind_later:"))
async def cb_remind_later(callback: CallbackQuery, session: AsyncSession) -> None:
    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer()
        return

    try:
        notification_id = int(parts[1])
    except ValueError:
        await callback.answer()
        return

    delay = parts[2]
    if delay not in _VALID_DELAYS:
        await callback.answer()
        return

    # Fetch user
    user_result = await session.execute(
        select(User).where(User.telegram_id == callback.from_user.id)
    )
    user = user_result.scalar_one_or_none()
    if not user:
        await callback.answer()
        return

    lang = user.language_code
    user_tz = user.timezone if user.timezone else "UTC"

    # Fetch notification (must belong to this user)
    notif_result = await session.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user.id,
        )
    )
    notif = notif_result.scalar_one_or_none()
    if not notif:
        await callback.answer(get_text("notification.not_found", lang), show_alert=True)
        return

    now_utc = datetime.now(timezone.utc)
    new_run_at = _apply_delay(now_utc, delay)

    # Reactivate and reschedule
    notif.next_run_at = new_run_at
    notif.scheduled_at = new_run_at
    notif.is_active = True
    await session.commit()

    remove_notification_job(notification_id)
    await schedule_notification(notif, callback.from_user.id)

    local_time = utc_to_user(new_run_at, user_tz)
    time_str = local_time.strftime("%Y-%m-%d %H:%M")
    confirmation = get_text("remind_later.confirmed", lang).format(time=time_str)

    await callback.answer(confirmation, show_alert=True)
    logger.info(
        "Notification %d rescheduled by user %d (delay=%s, new_run_at=%s)",
        notification_id,
        callback.from_user.id,
        delay,
        new_run_at,
    )
