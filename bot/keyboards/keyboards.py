from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

from bot.i18n import get_text
from bot.utils.timezone import REGION_ORDER, TIMEZONE_REGIONS, tz_display_name


def main_menu_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=get_text("main_menu.create_notification", lang), callback_data="create_notification")],
            [InlineKeyboardButton(text=get_text("main_menu.scheduled_notifications", lang), callback_data="scheduled_notifications")],
            [InlineKeyboardButton(text=get_text("main_menu.configuration", lang), callback_data="configuration")],
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


# ---------------------------------------------------------------------------
# Timezone setup keyboards
# ---------------------------------------------------------------------------

def timezone_setup_keyboard(lang: str) -> ReplyKeyboardMarkup:
    """Reply keyboard that offers to share location or select timezone manually."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text=get_text("timezone.share_location_button", lang),
                    request_location=True,
                )
            ],
            [KeyboardButton(text=get_text("timezone.select_manually_button", lang))],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def timezone_region_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Inline keyboard listing all supported regions."""
    rows = [
        [InlineKeyboardButton(text=region, callback_data=f"tz_region:{region}")]
        for region in REGION_ORDER
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def timezone_city_keyboard(region: str, lang: str) -> InlineKeyboardMarkup:
    """Inline keyboard listing cities for a given region."""
    cities = TIMEZONE_REGIONS.get(region, [])
    rows = [
        [InlineKeyboardButton(text=tz_display_name(tz), callback_data=f"tz_city:{tz}")]
        for tz in cities
    ]
    rows.append(
        [InlineKeyboardButton(text=get_text("timezone.back_to_regions", lang), callback_data="tz_back_regions")]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def remove_reply_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()


# ---------------------------------------------------------------------------
# Configuration menu keyboards
# ---------------------------------------------------------------------------

def config_menu_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Inline keyboard for the Configuration menu."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=get_text("config.change_timezone", lang), callback_data="config_change_timezone")],
            [InlineKeyboardButton(text=get_text("config.change_language", lang), callback_data="config_change_language")],
            [InlineKeyboardButton(text=get_text("config.back", lang), callback_data="main_menu")],
        ]
    )


# Human-readable names for all 16 supported languages displayed in the language picker.
_LANGUAGE_NAMES: dict[str, str] = {
    "en": "🇬🇧 English",
    "zh": "🇨🇳 中文 (Chinese)",
    "hi": "🇮🇳 हिन्दी (Hindi)",
    "es": "🇪🇸 Español (Spanish)",
    "fr": "🇫🇷 Français (French)",
    "ar": "🇸🇦 العربية (Arabic)",
    "bn": "🇧🇩 বাংলা (Bengali)",
    "ru": "🇷🇺 Русский (Russian)",
    "pt": "🇧🇷 Português (Portuguese)",
    "id": "🇮🇩 Bahasa Indonesia",
    "de": "🇩🇪 Deutsch (German)",
    "ja": "🇯🇵 日本語 (Japanese)",
    "pa": "🇮🇳 ਪੰਜਾਬੀ (Punjabi)",
    "jv": "🇮🇩 Basa Jawa (Javanese)",
    "ko": "🇰🇷 한국어 (Korean)",
    "uk": "🇺🇦 Українська (Ukrainian)",
}

_LANGUAGE_ORDER = ["en", "zh", "hi", "es", "fr", "ar", "bn", "ru", "pt", "id", "de", "ja", "pa", "jv", "ko", "uk"]


def language_select_keyboard(current_lang: str) -> InlineKeyboardMarkup:
    """Inline keyboard listing all 16 supported languages (2 per row)."""
    rows = []
    langs = _LANGUAGE_ORDER
    for i in range(0, len(langs), 2):
        row = []
        for code in langs[i : i + 2]:
            label = _LANGUAGE_NAMES.get(code, code)
            if code == current_lang:
                label = "✅ " + label
            row.append(InlineKeyboardButton(text=label, callback_data=f"set_language:{code}"))
        rows.append(row)
    rows.append([InlineKeyboardButton(text=get_text("config.back", current_lang), callback_data="configuration")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_language_name(lang_code: str) -> str:
    """Return the human-readable name for a language code."""
    return _LANGUAGE_NAMES.get(lang_code, lang_code)
