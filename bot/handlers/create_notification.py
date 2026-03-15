from datetime import datetime, timezone

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import Notification, RecurrenceType, User
from bot.i18n import get_text
from bot.keyboards.keyboards import main_menu_keyboard, recurrence_keyboard
from bot.scheduler.scheduler import schedule_notification
from bot.utils.timezone import user_to_utc

router = Router()


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


@router.message(CreateNotificationStates.waiting_title)
async def process_title(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "en")
    await state.update_data(title=message.text.strip())
    await state.set_state(CreateNotificationStates.waiting_description)
    await message.answer(get_text("create.description", lang), parse_mode="HTML")


@router.message(CreateNotificationStates.waiting_description)
async def process_description(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "en")
    await state.update_data(description=message.text.strip())
    await state.set_state(CreateNotificationStates.waiting_date)
    await message.answer(get_text("create.date", lang), parse_mode="HTML")


@router.message(CreateNotificationStates.waiting_date)
async def process_date(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "en")
    text = message.text.strip()
    try:
        datetime.strptime(text, "%Y-%m-%d")
    except ValueError:
        await message.answer(get_text("create.invalid_date", lang), parse_mode="HTML")
        return
    await state.update_data(date=text)
    await state.set_state(CreateNotificationStates.waiting_time)
    await message.answer(get_text("create.time", lang), parse_mode="HTML")


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
