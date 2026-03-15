"""Configuration menu handlers.

Flow:
  ⚙️ Configuration
  ├── 🕐 Change Timezone  → reuses the existing timezone setup flow
  └── 🌐 Change Language  → shows 16-language picker → saves language → confirms
"""
from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import User
from bot.i18n import get_text
from bot.keyboards.keyboards import (
    config_menu_keyboard,
    get_language_name,
    language_select_keyboard,
    main_menu_keyboard,
)

router = Router()


async def _get_user(session: AsyncSession, telegram_id: int) -> User | None:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# Configuration main menu
# ---------------------------------------------------------------------------

@router.callback_query(lambda c: c.data == "configuration")
async def cb_config_menu(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await _get_user(session, callback.from_user.id)
    lang = user.language_code if user else "en"
    await callback.message.edit_text(
        get_text("config.menu", lang),
        reply_markup=config_menu_keyboard(lang),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(Command("settings"))
async def cmd_settings(message: Message, session: AsyncSession) -> None:
    user = await _get_user(session, message.from_user.id)
    if not user:
        return
    await message.answer(
        get_text("config.menu", user.language_code),
        reply_markup=config_menu_keyboard(user.language_code),
        parse_mode="HTML",
    )


# ---------------------------------------------------------------------------
# Change Timezone — delegates to the existing timezone setup flow
# ---------------------------------------------------------------------------

@router.callback_query(lambda c: c.data == "config_change_timezone")
async def cb_config_change_timezone(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    user = await _get_user(session, callback.from_user.id)
    lang = user.language_code if user else "en"

    # Remove the inline keyboard from the config menu message
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer()

    from bot.handlers.timezone import prompt_timezone_setup
    await prompt_timezone_setup(callback.message, state, lang)


# ---------------------------------------------------------------------------
# Change Language — show the language picker
# ---------------------------------------------------------------------------

@router.callback_query(lambda c: c.data == "config_change_language")
async def cb_config_change_language(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await _get_user(session, callback.from_user.id)
    lang = user.language_code if user else "en"
    await callback.message.edit_text(
        get_text("config.language_menu", lang),
        reply_markup=language_select_keyboard(lang),
        parse_mode="HTML",
    )
    await callback.answer()


# ---------------------------------------------------------------------------
# Language selected
# ---------------------------------------------------------------------------

@router.callback_query(lambda c: c.data.startswith("set_language:"))
async def cb_set_language(callback: CallbackQuery, session: AsyncSession) -> None:
    new_lang = callback.data.split(":", 1)[1]

    user = await _get_user(session, callback.from_user.id)
    if not user:
        await callback.answer()
        return

    user.language_code = new_lang
    await session.commit()

    lang_name = get_language_name(new_lang)
    confirmation = get_text("config.language_set", new_lang).format(language=lang_name)
    name = callback.from_user.first_name or callback.from_user.username or "there"

    await callback.message.edit_text(
        confirmation,
        parse_mode="HTML",
    )
    await callback.message.answer(
        get_text("welcome", new_lang).format(name=name),
        reply_markup=main_menu_keyboard(new_lang),
        parse_mode="HTML",
    )
    await callback.answer()
