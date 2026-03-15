import logging
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from sqlalchemy import select

from bot.database.models import DeliveryStatus, Notification, NotificationHistory, RecurrenceType

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None
_bot = None
_session_factory = None


def init_scheduler(bot, session_factory) -> AsyncIOScheduler:
    global _scheduler, _bot, _session_factory
    _bot = bot
    _session_factory = session_factory
    _scheduler = AsyncIOScheduler(timezone="UTC")
    _scheduler.start()
    return _scheduler


def _compute_next_run(current: datetime, recurrence: RecurrenceType) -> datetime | None:
    if recurrence == RecurrenceType.once:
        return None
    elif recurrence == RecurrenceType.daily:
        return current + timedelta(days=1)
    elif recurrence == RecurrenceType.weekly:
        return current + timedelta(weeks=1)
    elif recurrence == RecurrenceType.monthly:
        # Add roughly one month
        month = current.month + 1
        year = current.year + (month - 1) // 12
        month = ((month - 1) % 12) + 1
        try:
            return current.replace(year=year, month=month)
        except ValueError:
            # Handle edge cases like Jan 31 + 1 month
            import calendar
            last_day = calendar.monthrange(year, month)[1]
            return current.replace(year=year, month=month, day=min(current.day, last_day))
    elif recurrence == RecurrenceType.yearly:
        try:
            return current.replace(year=current.year + 1)
        except ValueError:
            # Feb 29 edge case
            return current.replace(year=current.year + 1, day=28)
    return None


async def _send_notification(notification_id: int, telegram_id: int) -> None:
    from bot.i18n import get_text

    async with _session_factory() as session:
        result = await session.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        notif = result.scalar_one_or_none()
        if not notif or not notif.is_active:
            return

        # Determine user language
        from bot.database.models import User
        user_result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = user_result.scalar_one_or_none()
        lang = user.language_code if user else "en"

        delivery_status = DeliveryStatus.sent
        try:
            # Display time in user's local timezone
            from bot.utils.timezone import utc_to_user
            user_tz = user.timezone if user and user.timezone else "UTC"
            local_time = utc_to_user(notif.next_run_at, user_tz) if notif.next_run_at else None
            await _bot.send_message(
                chat_id=telegram_id,
                text=get_text("send.message", lang).format(
                    title=notif.title,
                    description=notif.description,
                    time=local_time.strftime("%H:%M") if local_time else "",
                ),
                parse_mode="HTML",
            )
        except Exception as e:
            logger.error("Failed to send notification %d to user %d: %s", notification_id, telegram_id, e)
            delivery_status = DeliveryStatus.failed

        # Record history
        history = NotificationHistory(
            notification_id=notif.id,
            user_id=notif.user_id,
            sent_at=datetime.now(timezone.utc),
            delivery_status=delivery_status,
        )
        session.add(history)

        # Update execution count and schedule next run
        notif.execution_count += 1
        current_run = notif.next_run_at or datetime.now(timezone.utc)
        next_run = _compute_next_run(current_run, notif.recurrence_type)

        if next_run:
            notif.next_run_at = next_run
            await session.commit()
            # Reschedule
            _scheduler.add_job(
                _send_notification,
                trigger=DateTrigger(run_date=next_run),
                args=[notification_id, telegram_id],
                id=f"notif_{notification_id}",
                replace_existing=True,
                misfire_grace_time=300,
            )
        else:
            notif.is_active = False
            notif.next_run_at = None
            await session.commit()


async def schedule_notification(notification: Notification, telegram_id: int) -> None:
    if not _scheduler or not notification.is_active:
        return
    run_at = notification.next_run_at or notification.scheduled_at
    if run_at is None or run_at <= datetime.now(timezone.utc):
        return
    _scheduler.add_job(
        _send_notification,
        trigger=DateTrigger(run_date=run_at),
        args=[notification.id, telegram_id],
        id=f"notif_{notification.id}",
        replace_existing=True,
        misfire_grace_time=300,
    )
    logger.info("Scheduled notification %d for %s", notification.id, run_at)


def remove_notification_job(notification_id: int) -> None:
    if not _scheduler:
        return
    job_id = f"notif_{notification_id}"
    try:
        _scheduler.remove_job(job_id)
    except Exception:
        pass


async def load_pending_notifications(session_factory) -> None:
    """Load all pending active notifications from DB and schedule them on startup."""
    from bot.database.models import User

    async with session_factory() as session:
        result = await session.execute(
            select(Notification, User.telegram_id)
            .join(User, User.id == Notification.user_id)
            .where(
                Notification.is_active,
                Notification.next_run_at > datetime.now(timezone.utc),
            )
        )
        rows = result.all()

    for notif, telegram_id in rows:
        await schedule_notification(notif, telegram_id)
    logger.info("Loaded %d pending notification(s) from database", len(rows))
