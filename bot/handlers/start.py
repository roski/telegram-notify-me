from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import User
from bot.i18n import get_text
from bot.keyboards.keyboards import main_menu_keyboard

router = Router()


async def _get_or_create_user(session: AsyncSession, message: Message) -> User:
    tg_user = message.from_user
    result = await session.execute(select(User).where(User.telegram_id == tg_user.id))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(
            telegram_id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
            last_name=tg_user.last_name,
            language_code=tg_user.language_code or "en",
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, session: AsyncSession) -> None:
    user = await _get_or_create_user(session, message)
    lang = user.language_code

    if not user.timezone:
        # Import here to avoid circular imports
        from bot.handlers.timezone import prompt_timezone_setup
        await prompt_timezone_setup(message, state, lang)
        return

    name = message.from_user.first_name or message.from_user.username or "there"
    await message.answer(
        get_text("welcome", lang).format(name=name),
        reply_markup=main_menu_keyboard(lang),
        parse_mode="HTML",
    )


@router.callback_query(lambda c: c.data == "main_menu")
async def cb_main_menu(callback: CallbackQuery, session: AsyncSession) -> None:
    result = await session.execute(select(User).where(User.telegram_id == callback.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language_code if user else "en"
    name = callback.from_user.first_name or callback.from_user.username or "there"
    await callback.message.edit_text(
        get_text("welcome", lang).format(name=name),
        reply_markup=main_menu_keyboard(lang),
        parse_mode="HTML",
    )
    await callback.answer()
