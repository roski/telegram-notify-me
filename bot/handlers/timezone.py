"""Timezone setup handlers.

Flow:
  1.  User receives a ReplyKeyboard with:
        • "📍 Share Location" (Telegram location request)
        • "🗺 Select manually" (plain text button)
  2a. If location is shared → timezone is detected automatically.
  2b. If "Select manually" → inline region list → inline city list → timezone saved.
"""
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import User
from bot.i18n import get_text
from bot.keyboards.keyboards import (
    main_menu_keyboard,
    remove_reply_keyboard,
    timezone_city_keyboard,
    timezone_region_keyboard,
    timezone_setup_keyboard,
)
from bot.utils.timezone import timezone_from_location, tz_display_name

router = Router()


class TimezoneStates(StatesGroup):
    waiting_setup = State()


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

async def _get_user(session: AsyncSession, telegram_id: int) -> User | None:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one_or_none()


async def _save_timezone(session: AsyncSession, user: User, tz_str: str) -> None:
    user.timezone = tz_str
    await session.commit()


async def _finish_timezone_setup(
    message: Message,
    state: FSMContext,
    lang: str,
    tz_str: str,
) -> None:
    """Remove the reply keyboard, confirm the timezone and show the main menu."""
    await state.clear()
    name = message.from_user.first_name or message.from_user.username or "there"
    await message.answer(
        get_text("timezone.saved", lang).format(timezone=tz_str),
        reply_markup=remove_reply_keyboard(),
        parse_mode="HTML",
    )
    await message.answer(
        get_text("welcome", lang).format(name=name),
        reply_markup=main_menu_keyboard(lang),
        parse_mode="HTML",
    )


# ---------------------------------------------------------------------------
# Public helper — called by start handler to prompt timezone setup
# ---------------------------------------------------------------------------

async def prompt_timezone_setup(message: Message, state: FSMContext, lang: str) -> None:
    """Send the timezone setup prompt to the user and enter the FSM state."""
    await state.set_state(TimezoneStates.waiting_setup)
    await state.update_data(lang=lang)
    await message.answer(
        get_text("timezone.setup_prompt", lang),
        reply_markup=timezone_setup_keyboard(lang),
        parse_mode="HTML",
    )


# ---------------------------------------------------------------------------
# Option 1 — Location shared
# ---------------------------------------------------------------------------

@router.message(TimezoneStates.waiting_setup, F.location)
async def handle_location(message: Message, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    lang = data.get("lang", "en")

    lat = message.location.latitude
    lng = message.location.longitude
    tz_str = timezone_from_location(lat, lng)

    user = await _get_user(session, message.from_user.id)
    if not user:
        await state.clear()
        return

    if not tz_str:
        # Detection failed — fall back to manual selection
        await message.answer(
            get_text("timezone.detection_failed", lang),
            reply_markup=remove_reply_keyboard(),
            parse_mode="HTML",
        )
        await message.answer(
            get_text("timezone.select_region", lang),
            reply_markup=timezone_region_keyboard(lang),
            parse_mode="HTML",
        )
        return

    await _save_timezone(session, user, tz_str)

    await message.answer(
        get_text("timezone.detected", lang).format(timezone=tz_str),
        reply_markup=remove_reply_keyboard(),
        parse_mode="HTML",
    )
    name = message.from_user.first_name or message.from_user.username or "there"
    await message.answer(
        get_text("welcome", lang).format(name=name),
        reply_markup=main_menu_keyboard(lang),
        parse_mode="HTML",
    )
    await state.clear()


# ---------------------------------------------------------------------------
# Option 2 — Manual selection: "Select manually" button (any non-location text)
# ---------------------------------------------------------------------------

@router.message(TimezoneStates.waiting_setup, F.text)
async def handle_manual_text(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "en")
    await message.answer(
        get_text("timezone.select_region", lang),
        reply_markup=timezone_region_keyboard(lang),
        parse_mode="HTML",
    )


# ---------------------------------------------------------------------------
# Region selected (inline callback)
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("tz_region:"))
async def handle_region_select(callback: CallbackQuery, state: FSMContext) -> None:
    region = callback.data.split(":", 1)[1]
    data = await state.get_data()
    lang = data.get("lang", "en")

    await state.update_data(tz_region=region)
    await callback.message.edit_text(
        get_text("timezone.select_city", lang).format(region=region),
        reply_markup=timezone_city_keyboard(region, lang),
        parse_mode="HTML",
    )
    await callback.answer()


# ---------------------------------------------------------------------------
# City selected (inline callback) — timezone confirmed
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("tz_city:"))
async def handle_city_select(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    tz_str = callback.data.split(":", 1)[1]
    data = await state.get_data()
    lang = data.get("lang", "en")

    user = await _get_user(session, callback.from_user.id)
    if not user:
        await callback.answer()
        await state.clear()
        return

    await _save_timezone(session, user, tz_str)

    name = callback.from_user.first_name or callback.from_user.username or "there"
    await callback.message.edit_text(
        get_text("timezone.saved", lang).format(timezone=tz_str),
        parse_mode="HTML",
    )
    await callback.message.answer(
        get_text("welcome", lang).format(name=name),
        reply_markup=main_menu_keyboard(lang),
        parse_mode="HTML",
    )
    await state.clear()
    await callback.answer()


# ---------------------------------------------------------------------------
# "Back to regions" button
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "tz_back_regions")
async def handle_back_to_regions(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "en")
    await callback.message.edit_text(
        get_text("timezone.select_region", lang),
        reply_markup=timezone_region_keyboard(lang),
        parse_mode="HTML",
    )
    await callback.answer()
