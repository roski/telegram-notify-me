from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.i18n import get_text


def main_menu_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=get_text("main_menu.create_notification", lang), callback_data="create_notification")],
            [InlineKeyboardButton(text=get_text("main_menu.scheduled_notifications", lang), callback_data="scheduled_notifications")],
        ]
    )


def recurrence_keyboard(lang: str) -> InlineKeyboardMarkup:
    recurrence_types = ["once", "daily", "weekly", "monthly", "yearly"]
    rows = [
        [InlineKeyboardButton(text=get_text(f"recurrence.{r}", lang), callback_data=f"recurrence:{r}")]
        for r in recurrence_types
    ]
    rows.append([InlineKeyboardButton(text=get_text("cancel", lang), callback_data="cancel_create")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def scheduled_period_keyboard(lang: str, period: str = "week") -> InlineKeyboardMarkup:
    buttons = []
    if period != "week":
        buttons.append([InlineKeyboardButton(text=get_text("scheduled.week", lang), callback_data="scheduled:week")])
    if period != "month":
        buttons.append([InlineKeyboardButton(text=get_text("scheduled.view_month", lang), callback_data="scheduled:month")])
    if period != "year":
        buttons.append([InlineKeyboardButton(text=get_text("scheduled.view_year", lang), callback_data="scheduled:year")])
    buttons.append([InlineKeyboardButton(text=get_text("scheduled.back", lang), callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def notification_list_keyboard(notifications: list, lang: str, period: str = "week") -> InlineKeyboardMarkup:
    from bot.database.models import RecurrenceType

    rows = []
    for notif in notifications:
        icon = "🔁 " if notif.recurrence_type != RecurrenceType.once else ""
        label = f"{icon}{notif.title}"
        rows.append(
            [InlineKeyboardButton(text=label, callback_data=f"notif_detail:{notif.id}:{period}")]
        )
    if period != "week":
        rows.append([InlineKeyboardButton(text=get_text("scheduled.week", lang), callback_data="scheduled:week")])
    if period != "month":
        rows.append([InlineKeyboardButton(text=get_text("scheduled.view_month", lang), callback_data="scheduled:month")])
    if period != "year":
        rows.append([InlineKeyboardButton(text=get_text("scheduled.view_year", lang), callback_data="scheduled:year")])
    rows.append([InlineKeyboardButton(text=get_text("scheduled.back", lang), callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def notification_detail_keyboard(notification_id: int, lang: str, period: str = "week") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=get_text("notification.edit", lang), callback_data=f"notif_edit:{notification_id}:{period}"),
                InlineKeyboardButton(text=get_text("notification.delete", lang), callback_data=f"notif_delete:{notification_id}:{period}"),
            ],
            [InlineKeyboardButton(text=get_text("notification.back", lang), callback_data=f"scheduled:{period}")],
        ]
    )


def edit_field_keyboard(notification_id: int, lang: str, period: str = "week") -> InlineKeyboardMarkup:
    fields = ["title", "description", "date", "time", "recurrence"]
    rows = [
        [InlineKeyboardButton(text=get_text(f"edit_fields.{f}", lang), callback_data=f"edit_field:{notification_id}:{f}:{period}")]
        for f in fields
    ]
    rows.append([InlineKeyboardButton(text=get_text("notification.back", lang), callback_data=f"notif_detail:{notification_id}:{period}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def edit_recurrence_keyboard(notification_id: int, lang: str, period: str = "week") -> InlineKeyboardMarkup:
    recurrence_types = ["once", "daily", "weekly", "monthly", "yearly"]
    rows = [
        [InlineKeyboardButton(text=get_text(f"recurrence.{r}", lang), callback_data=f"edit_recurrence:{notification_id}:{r}:{period}")]
        for r in recurrence_types
    ]
    rows.append([InlineKeyboardButton(text=get_text("notification.back", lang), callback_data=f"notif_edit:{notification_id}:{period}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
