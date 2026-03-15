from datetime import datetime, timedelta, timezone

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import Notification, RecurrenceType, User
from bot.i18n import get_text
from bot.keyboards.keyboards import (
    edit_field_keyboard,
    edit_recurrence_keyboard,
    main_menu_keyboard,
    notification_detail_keyboard,
    notification_list_keyboard,
)
from bot.scheduler.scheduler import remove_notification_job, schedule_notification
from bot.utils.timezone import user_to_utc, utc_to_user

router = Router()

PERIOD_DAYS = {"week": 7, "month": 30, "year": 365}


class EditNotificationStates(StatesGroup):
    waiting_title = State()
    waiting_description = State()
    waiting_date = State()
    waiting_time = State()


async def _get_user(session: AsyncSession, telegram_id: int) -> User | None:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one_or_none()


async def _get_notifications_for_period(
    session: AsyncSession, user_id: int, period: str
) -> list[Notification]:
    now = datetime.now(timezone.utc)
    end = now + timedelta(days=PERIOD_DAYS.get(period, 7))
    result = await session.execute(
        select(Notification)
        .where(
            and_(
                Notification.user_id == user_id,
                Notification.is_active,
                Notification.next_run_at >= now,
                Notification.next_run_at <= end,
            )
        )
        .order_by(Notification.next_run_at)
    )
    return list(result.scalars().all())


def _format_notification_list(notifications: list[Notification], lang: str, period: str, user_tz: str = "UTC") -> str:
    period_key = f"scheduled.{'week' if period == 'week' else ('month' if period == 'month' else 'year')}"
    header = get_text("scheduled.title", lang) + f"\n{get_text(period_key, lang)}\n\n"
    if not notifications:
        return header + get_text("scheduled.empty", lang)
    return header + "\n".join(
        f"{'🔁 ' if n.recurrence_type != RecurrenceType.once else ''}"
        f"<b>{n.title}</b> — {utc_to_user(n.next_run_at, user_tz).strftime('%Y-%m-%d %H:%M')}"
        for n in notifications
    )


@router.callback_query(lambda c: c.data == "scheduled_notifications")
async def cb_scheduled_notifications(callback: CallbackQuery, session: AsyncSession) -> None:
    await _show_scheduled(callback, session, "week")


@router.callback_query(F.data.startswith("scheduled:"))
async def cb_scheduled_period(callback: CallbackQuery, session: AsyncSession) -> None:
    period = callback.data.split(":")[1]
    await _show_scheduled(callback, session, period)


async def _show_scheduled(callback: CallbackQuery, session: AsyncSession, period: str) -> None:
    user = await _get_user(session, callback.from_user.id)
    if not user:
        await callback.answer()
        return
    lang = user.language_code
    user_tz = user.timezone or "UTC"
    notifications = await _get_notifications_for_period(session, user.id, period)
    text = _format_notification_list(notifications, lang, period, user_tz)
    keyboard = notification_list_keyboard(notifications, lang, period)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("notif_detail:"))
async def cb_notification_detail(callback: CallbackQuery, session: AsyncSession) -> None:
    parts = callback.data.split(":")
    notification_id = int(parts[1])
    period = parts[2] if len(parts) > 2 else "week"

    user = await _get_user(session, callback.from_user.id)
    if not user:
        await callback.answer()
        return
    lang = user.language_code
    user_tz = user.timezone or "UTC"

    result = await session.execute(
        select(Notification).where(
            and_(Notification.id == notification_id, Notification.user_id == user.id)
        )
    )
    notif = result.scalar_one_or_none()
    if not notif:
        await callback.answer(get_text("notification.not_found", lang))
        return

    local_dt = utc_to_user(notif.next_run_at, user_tz)
    recurrence_label = get_text(f"recurrence.{notif.recurrence_type.value}", lang)
    text = get_text("notification.details", lang).format(
        title=notif.title,
        description=notif.description,
        date=local_dt.strftime("%Y-%m-%d"),
        time=local_dt.strftime("%H:%M"),
        recurrence=recurrence_label,
        count=notif.execution_count,
    )
    await callback.message.edit_text(
        text,
        reply_markup=notification_detail_keyboard(notification_id, lang, period),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("notif_delete:"))
async def cb_notification_delete(callback: CallbackQuery, session: AsyncSession) -> None:
    parts = callback.data.split(":")
    notification_id = int(parts[1])
    period = parts[2] if len(parts) > 2 else "week"

    user = await _get_user(session, callback.from_user.id)
    if not user:
        await callback.answer()
        return
    lang = user.language_code
    user_tz = user.timezone or "UTC"

    result = await session.execute(
        select(Notification).where(
            and_(Notification.id == notification_id, Notification.user_id == user.id)
        )
    )
    notif = result.scalar_one_or_none()
    if not notif:
        await callback.answer(get_text("notification.not_found", lang))
        return

    remove_notification_job(notification_id)
    await session.delete(notif)
    await session.commit()

    # Show updated notification list
    notifications = await _get_notifications_for_period(session, user.id, period)
    text = _format_notification_list(notifications, lang, period, user_tz)
    keyboard = notification_list_keyboard(notifications, lang, period)
    await callback.message.edit_text(
        get_text("notification.deleted", lang) + "\n\n" + text,
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("notif_edit:"))
async def cb_notification_edit(callback: CallbackQuery, session: AsyncSession) -> None:
    parts = callback.data.split(":")
    notification_id = int(parts[1])
    period = parts[2] if len(parts) > 2 else "week"

    user = await _get_user(session, callback.from_user.id)
    if not user:
        await callback.answer()
        return
    lang = user.language_code

    await callback.message.edit_text(
        get_text("notification.edit_field", lang),
        reply_markup=edit_field_keyboard(notification_id, lang, period),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("edit_field:"))
async def cb_edit_field(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    parts = callback.data.split(":")
    notification_id = int(parts[1])
    field = parts[2]
    period = parts[3] if len(parts) > 3 else "week"

    user = await _get_user(session, callback.from_user.id)
    if not user:
        await callback.answer()
        return
    lang = user.language_code

    if field == "recurrence":
        await callback.message.edit_text(
            get_text("notification.edit_recurrence", lang),
            reply_markup=edit_recurrence_keyboard(notification_id, lang, period),
            parse_mode="HTML",
        )
        await callback.answer()
        return

    state_map = {
        "title": (EditNotificationStates.waiting_title, "notification.edit_title"),
        "description": (EditNotificationStates.waiting_description, "notification.edit_description"),
        "date": (EditNotificationStates.waiting_date, "notification.edit_date"),
        "time": (EditNotificationStates.waiting_time, "notification.edit_time"),
    }
    fsm_state, prompt_key = state_map[field]
    await state.set_state(fsm_state)
    await state.update_data(notification_id=notification_id, lang=lang, period=period, field=field)
    await callback.message.edit_text(get_text(prompt_key, lang), parse_mode="HTML")
    await callback.answer()


@router.message(EditNotificationStates.waiting_title)
async def edit_process_title(message: Message, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    lang = data.get("lang", "en")
    notification_id = data["notification_id"]
    period = data.get("period", "week")

    user = await _get_user(session, message.from_user.id)
    result = await session.execute(
        select(Notification).where(
            and_(Notification.id == notification_id, Notification.user_id == user.id)
        )
    )
    notif = result.scalar_one_or_none()
    if not notif:
        await message.answer(get_text("notification.not_found", lang))
        await state.clear()
        return

    notif.title = message.text.strip()
    await session.commit()
    await state.clear()

    await message.answer(get_text("notification.updated", lang), reply_markup=main_menu_keyboard(lang), parse_mode="HTML")


@router.message(EditNotificationStates.waiting_description)
async def edit_process_description(message: Message, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    lang = data.get("lang", "en")
    notification_id = data["notification_id"]

    user = await _get_user(session, message.from_user.id)
    result = await session.execute(
        select(Notification).where(
            and_(Notification.id == notification_id, Notification.user_id == user.id)
        )
    )
    notif = result.scalar_one_or_none()
    if not notif:
        await message.answer(get_text("notification.not_found", lang))
        await state.clear()
        return

    notif.description = message.text.strip()
    await session.commit()
    await state.clear()
    await message.answer(get_text("notification.updated", lang), reply_markup=main_menu_keyboard(lang), parse_mode="HTML")


@router.message(EditNotificationStates.waiting_date)
async def edit_process_date(message: Message, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    lang = data.get("lang", "en")
    notification_id = data["notification_id"]
    text = message.text.strip()

    try:
        datetime.strptime(text, "%Y-%m-%d")
    except ValueError:
        await message.answer(get_text("create.invalid_date", lang), parse_mode="HTML")
        return

    user = await _get_user(session, message.from_user.id)
    user_tz = user.timezone if user and user.timezone else "UTC"
    result = await session.execute(
        select(Notification).where(
            and_(Notification.id == notification_id, Notification.user_id == user.id)
        )
    )
    notif = result.scalar_one_or_none()
    if not notif:
        await message.answer(get_text("notification.not_found", lang))
        await state.clear()
        return

    # Use existing time (in user's local timezone) from the stored UTC value
    local_existing = utc_to_user(notif.next_run_at, user_tz) if notif.next_run_at else datetime.now(timezone.utc)
    existing_time = local_existing.strftime("%H:%M")
    naive_local = datetime.strptime(f"{text} {existing_time}", "%Y-%m-%d %H:%M")
    new_dt = user_to_utc(naive_local, user_tz)
    if new_dt <= datetime.now(timezone.utc):
        await message.answer(get_text("create.date_in_past", lang), parse_mode="HTML")
        return

    notif.scheduled_at = new_dt
    notif.next_run_at = new_dt
    await session.commit()

    remove_notification_job(notification_id)
    await schedule_notification(notif, user.telegram_id)

    await state.clear()
    await message.answer(get_text("notification.updated", lang), reply_markup=main_menu_keyboard(lang), parse_mode="HTML")


@router.message(EditNotificationStates.waiting_time)
async def edit_process_time(message: Message, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    lang = data.get("lang", "en")
    notification_id = data["notification_id"]
    text = message.text.strip()

    try:
        datetime.strptime(text, "%H:%M")
    except ValueError:
        await message.answer(get_text("create.invalid_time", lang), parse_mode="HTML")
        return

    user = await _get_user(session, message.from_user.id)
    user_tz = user.timezone if user and user.timezone else "UTC"
    result = await session.execute(
        select(Notification).where(
            and_(Notification.id == notification_id, Notification.user_id == user.id)
        )
    )
    notif = result.scalar_one_or_none()
    if not notif:
        await message.answer(get_text("notification.not_found", lang))
        await state.clear()
        return

    local_existing = utc_to_user(notif.next_run_at, user_tz) if notif.next_run_at else datetime.now(timezone.utc)
    existing_date = local_existing.strftime("%Y-%m-%d")
    naive_local = datetime.strptime(f"{existing_date} {text}", "%Y-%m-%d %H:%M")
    new_dt = user_to_utc(naive_local, user_tz)
    if new_dt <= datetime.now(timezone.utc):
        await message.answer(get_text("create.date_in_past", lang), parse_mode="HTML")
        return

    notif.scheduled_at = new_dt
    notif.next_run_at = new_dt
    await session.commit()

    remove_notification_job(notification_id)
    await schedule_notification(notif, user.telegram_id)

    await state.clear()
    await message.answer(get_text("notification.updated", lang), reply_markup=main_menu_keyboard(lang), parse_mode="HTML")


@router.callback_query(F.data.startswith("edit_recurrence:"))
async def cb_edit_recurrence(callback: CallbackQuery, session: AsyncSession) -> None:
    parts = callback.data.split(":")
    notification_id = int(parts[1])
    recurrence_value = parts[2]
    period = parts[3] if len(parts) > 3 else "week"

    user = await _get_user(session, callback.from_user.id)
    if not user:
        await callback.answer()
        return
    lang = user.language_code
    user_tz = user.timezone or "UTC"

    result = await session.execute(
        select(Notification).where(
            and_(Notification.id == notification_id, Notification.user_id == user.id)
        )
    )
    notif = result.scalar_one_or_none()
    if not notif:
        await callback.answer(get_text("notification.not_found", lang))
        return

    notif.recurrence_type = RecurrenceType(recurrence_value)
    await session.commit()
    await session.refresh(notif)

    remove_notification_job(notification_id)
    await schedule_notification(notif, user.telegram_id)

    local_dt = utc_to_user(notif.next_run_at, user_tz)
    recurrence_label = get_text(f"recurrence.{notif.recurrence_type.value}", lang)
    text = get_text("notification.details", lang).format(
        title=notif.title,
        description=notif.description,
        date=local_dt.strftime("%Y-%m-%d"),
        time=local_dt.strftime("%H:%M"),
        recurrence=recurrence_label,
        count=notif.execution_count,
    )
    await callback.message.edit_text(
        get_text("notification.updated", lang) + "\n\n" + text,
        reply_markup=notification_detail_keyboard(notification_id, lang, period),
        parse_mode="HTML",
    )
    await callback.answer()
