from datetime import datetime, timezone

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import Notification, RecurrenceType, User
from bot.i18n import get_text
from bot.keyboards.keyboards import (
    calendar_keyboard,
    main_menu_keyboard,
    recurrence_keyboard,
    time_ampm_keyboard,
    time_hour_keyboard_12,
    time_hour_keyboard_24,
    time_minute_keyboard,
)
from bot.scheduler.scheduler import schedule_notification
from bot.utils.timezone import user_to_utc

router = Router()

# Languages that conventionally use a 12-hour (AM/PM) clock.
_12H_LANGS = {"en", "ar", "hi", "pa", "bn", "ko"}


def get_time_format(lang: str) -> str:
    """Return ``'12h'`` or ``'24h'`` for the given language code."""
    return "12h" if lang in _12H_LANGS else "24h"


class CreateNotificationStates(StatesGroup):
    waiting_title = State()
    waiting_description = State()
    waiting_date = State()
    waiting_time = State()
    waiting_recurrence = State()


async def _get_user_lang(session: AsyncSession, telegram_id: int) -> str:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    return user.language_code if user else "en"


async def _get_user(session: AsyncSession, telegram_id: int) -> User | None:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one_or_none()


def _show_time_picker(lang: str, time_format: str) -> tuple[str, object]:
    """Return (prompt text, keyboard) for the first time-picker step."""
    if time_format == "12h":
        return get_text("create.time_format_12", lang), time_ampm_keyboard(lang)
    return get_text("create.time_format_24", lang), time_hour_keyboard_24(lang)


# ---------------------------------------------------------------------------
# Notification creation entry point
# ---------------------------------------------------------------------------

@router.callback_query(lambda c: c.data == "create_notification")
async def cb_create_notification(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    lang = await _get_user_lang(session, callback.from_user.id)
    user = await _get_user(session, callback.from_user.id)
    user_tz = user.timezone if user and user.timezone else "UTC"
    await state.set_state(CreateNotificationStates.waiting_title)
    await state.update_data(lang=lang, user_tz=user_tz)
    await callback.message.edit_text(
        get_text("create.start", lang),
        parse_mode="HTML",
    )
    await callback.answer()


# ---------------------------------------------------------------------------
# Step 1: title
# ---------------------------------------------------------------------------

@router.message(CreateNotificationStates.waiting_title)
async def process_title(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "en")
    await state.update_data(title=message.text.strip())
    await state.set_state(CreateNotificationStates.waiting_description)
    await message.answer(get_text("create.description", lang), parse_mode="HTML")


# ---------------------------------------------------------------------------
# Step 2: description → show calendar
# ---------------------------------------------------------------------------

@router.message(CreateNotificationStates.waiting_description)
async def process_description(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "en")
    await state.update_data(description=message.text.strip())
    await state.set_state(CreateNotificationStates.waiting_date)
    today = datetime.now(timezone.utc).date()
    await message.answer(
        get_text("create.date_calendar", lang),
        reply_markup=calendar_keyboard(today.year, today.month, lang),
        parse_mode="HTML",
    )


# ---------------------------------------------------------------------------
# Step 3: date – calendar callbacks
# ---------------------------------------------------------------------------

@router.callback_query(lambda c: c.data == "cal_ignore")
async def cb_cal_ignore(callback: CallbackQuery) -> None:
    """No-op for disabled calendar cells and header buttons."""
    await callback.answer()


@router.callback_query(F.data.startswith("cal_nav:"), CreateNotificationStates.waiting_date)
async def cb_cal_nav(callback: CallbackQuery, state: FSMContext) -> None:
    """Navigate the calendar to a different month."""
    data = await state.get_data()
    lang = data.get("lang", "en")
    _, ym = callback.data.split(":", 1)
    year, month = map(int, ym.split("-"))
    today = datetime.now(timezone.utc).date()
    # Prevent navigating to months before the current one
    if (year, month) < (today.year, today.month):
        await callback.answer()
        return
    await callback.message.edit_reply_markup(reply_markup=calendar_keyboard(year, month, lang))
    await callback.answer()


@router.callback_query(F.data.startswith("cal_day:"), CreateNotificationStates.waiting_date)
async def cb_cal_day(callback: CallbackQuery, state: FSMContext) -> None:
    """User tapped a date on the calendar – proceed to the time picker."""
    data = await state.get_data()
    lang = data.get("lang", "en")
    _, date_str = callback.data.split(":", 1)

    # Guard: must not be a past date
    selected = datetime.strptime(date_str, "%Y-%m-%d").date()
    today = datetime.now(timezone.utc).date()
    if selected < today:
        await callback.answer(get_text("create.date_in_past", lang), show_alert=True)
        return

    time_format = get_time_format(lang)
    time_step = "ampm" if time_format == "12h" else "hour"
    await state.update_data(date=date_str, time_format=time_format, time_step=time_step)
    await state.set_state(CreateNotificationStates.waiting_time)

    prompt, keyboard = _show_time_picker(lang, time_format)
    await callback.message.edit_text(prompt, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(lambda c: c.data == "cal_manual", CreateNotificationStates.waiting_date)
async def cb_cal_manual(callback: CallbackQuery, state: FSMContext) -> None:
    """Switch to manual date entry."""
    data = await state.get_data()
    lang = data.get("lang", "en")
    await callback.message.edit_text(get_text("create.date_manual_prompt", lang), parse_mode="HTML")
    await callback.answer()


# Step 3: date – manual text input
@router.message(CreateNotificationStates.waiting_date)
async def process_date(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "en")
    text = message.text.strip()
    try:
        selected = datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        await message.answer(get_text("create.invalid_date", lang), parse_mode="HTML")
        return

    today = datetime.now(timezone.utc).date()
    if selected < today:
        await message.answer(get_text("create.date_in_past", lang), parse_mode="HTML")
        return

    time_format = get_time_format(lang)
    time_step = "ampm" if time_format == "12h" else "hour"
    await state.update_data(date=text, time_format=time_format, time_step=time_step)
    await state.set_state(CreateNotificationStates.waiting_time)

    prompt, keyboard = _show_time_picker(lang, time_format)
    await message.answer(prompt, reply_markup=keyboard, parse_mode="HTML")


# ---------------------------------------------------------------------------
# Step 4: time picker – inline callbacks
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("tp_ampm:"), CreateNotificationStates.waiting_time)
async def cb_tp_ampm(callback: CallbackQuery, state: FSMContext) -> None:
    """AM/PM selected (12-hour flow) – show the hour grid."""
    data = await state.get_data()
    lang = data.get("lang", "en")
    _, ampm = callback.data.split(":", 1)
    await state.update_data(time_ampm=ampm, time_step="hour")
    await callback.message.edit_text(
        get_text("create.time_select_hour", lang),
        reply_markup=time_hour_keyboard_12(lang),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("tp_hour:"), CreateNotificationStates.waiting_time)
async def cb_tp_hour(callback: CallbackQuery, state: FSMContext) -> None:
    """Hour selected – show the minute grid."""
    data = await state.get_data()
    lang = data.get("lang", "en")
    _, hour_str = callback.data.split(":", 1)
    await state.update_data(time_hour=int(hour_str), time_step="minute")
    await callback.message.edit_text(
        get_text("create.time_select_minute", lang),
        reply_markup=time_minute_keyboard(lang),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("tp_min:"), CreateNotificationStates.waiting_time)
async def cb_tp_min(callback: CallbackQuery, state: FSMContext) -> None:
    """Minute selected – validate datetime and proceed to recurrence."""
    data = await state.get_data()
    lang = data.get("lang", "en")
    user_tz = data.get("user_tz", "UTC")
    _, min_str = callback.data.split(":", 1)

    hour: int = data.get("time_hour", 0)
    ampm: str | None = data.get("time_ampm")
    time_format: str = data.get("time_format", "24h")

    # Convert 12h → 24h representation
    if time_format == "12h" and ampm is not None:
        if ampm == "PM" and hour != 12:
            hour += 12
        elif ampm == "AM" and hour == 12:
            hour = 0

    time_str = f"{hour:02d}:{min_str}"
    date_str = data.get("date")

    naive_local = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    scheduled_at_utc = user_to_utc(naive_local, user_tz)
    if scheduled_at_utc <= datetime.now(timezone.utc):
        await callback.answer(get_text("create.date_in_past", lang), show_alert=True)
        return

    await state.update_data(time=time_str)
    await state.set_state(CreateNotificationStates.waiting_recurrence)
    await callback.message.edit_text(
        get_text("create.recurrence", lang),
        reply_markup=recurrence_keyboard(lang),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "tp_back", CreateNotificationStates.waiting_time)
async def cb_tp_back(callback: CallbackQuery, state: FSMContext) -> None:
    """Navigate backwards through the time picker steps."""
    data = await state.get_data()
    lang = data.get("lang", "en")
    time_step: str = data.get("time_step", "hour")
    time_format: str = data.get("time_format", "24h")

    if time_step == "minute":
        # Go back to the hour grid
        await state.update_data(time_step="hour")
        if time_format == "12h":
            prompt = get_text("create.time_select_hour", lang)
            keyboard = time_hour_keyboard_12(lang)
        else:
            prompt = get_text("create.time_format_24", lang)
            keyboard = time_hour_keyboard_24(lang)
        await callback.message.edit_text(prompt, reply_markup=keyboard, parse_mode="HTML")

    elif time_step == "hour" and time_format == "12h":
        # Go back to AM/PM
        await state.update_data(time_step="ampm")
        await callback.message.edit_text(
            get_text("create.time_format_12", lang),
            reply_markup=time_ampm_keyboard(lang),
            parse_mode="HTML",
        )

    else:
        # Go back to date calendar (24h hour step, or 12h ampm step)
        await state.update_data(time_step=None)
        await state.set_state(CreateNotificationStates.waiting_date)
        today = datetime.now(timezone.utc).date()
        await callback.message.edit_text(
            get_text("create.date_calendar", lang),
            reply_markup=calendar_keyboard(today.year, today.month, lang),
            parse_mode="HTML",
        )

    await callback.answer()


# Step 4: time – manual text input (HH:MM, always 24-hour)
@router.message(CreateNotificationStates.waiting_time)
async def process_time(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "en")
    user_tz = data.get("user_tz", "UTC")
    text = message.text.strip()
    try:
        datetime.strptime(text, "%H:%M")
    except ValueError:
        await message.answer(get_text("create.invalid_time", lang), parse_mode="HTML")
        return
    # Validate that scheduled datetime is in the future (using user's local timezone)
    date_str = data.get("date")
    dt_str = f"{date_str} {text}"
    naive_local = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
    scheduled_at_utc = user_to_utc(naive_local, user_tz)
    if scheduled_at_utc <= datetime.now(timezone.utc):
        await message.answer(get_text("create.date_in_past", lang), parse_mode="HTML")
        return
    await state.update_data(time=text)
    await state.set_state(CreateNotificationStates.waiting_recurrence)
    await message.answer(get_text("create.recurrence", lang), reply_markup=recurrence_keyboard(lang), parse_mode="HTML")


# ---------------------------------------------------------------------------
# Step 5: recurrence
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("recurrence:"), CreateNotificationStates.waiting_recurrence)
async def process_recurrence(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    recurrence_value = callback.data.split(":")[1]
    data = await state.get_data()
    lang = data.get("lang", "en")

    date_str = data.get("date")
    time_str = data.get("time")
    title = data.get("title")
    description = data.get("description")
    user_tz = data.get("user_tz", "UTC")

    # Convert user's local time to UTC for storage
    naive_local = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    scheduled_at = user_to_utc(naive_local, user_tz)
    recurrence_type = RecurrenceType(recurrence_value)

    # Look up user
    result = await session.execute(select(User).where(User.telegram_id == callback.from_user.id))
    user = result.scalar_one_or_none()

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
    await session.commit()
    await session.refresh(notification)

    # Schedule the notification
    await schedule_notification(notification, user.telegram_id)

    recurrence_label = get_text(f"recurrence.{recurrence_value}", lang)
    await callback.message.edit_text(
        get_text("create.confirm", lang).format(
            title=title,
            description=description,
            date=date_str,
            time=time_str,
            recurrence=recurrence_label,
        ),
        parse_mode="HTML",
    )
    await callback.message.answer(
        get_text("welcome", lang).format(name=callback.from_user.first_name or "there"),
        reply_markup=main_menu_keyboard(lang),
        parse_mode="HTML",
    )
    await state.clear()
    await callback.answer()


@router.callback_query(lambda c: c.data == "cancel_create")
async def cb_cancel_create(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    lang = data.get("lang", "en")
    await state.clear()
    await callback.message.edit_text(get_text("create.cancelled", lang), parse_mode="HTML")
    await callback.message.answer(
        get_text("welcome", lang).format(name=callback.from_user.first_name or "there"),
        reply_markup=main_menu_keyboard(lang),
        parse_mode="HTML",
    )
    await callback.answer()
