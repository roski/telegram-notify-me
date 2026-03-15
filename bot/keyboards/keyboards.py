import calendar as _cal
from datetime import date

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


# ---------------------------------------------------------------------------
# Date calendar keyboard
# ---------------------------------------------------------------------------

def calendar_keyboard(year: int, month: int, lang: str) -> InlineKeyboardMarkup:
    """Inline calendar for the given year/month.

    Past days are shown as disabled dots; today is highlighted with brackets.
    The bottom row always offers a manual-entry shortcut and a cancel button.
    Users cannot navigate to months before the current month.
    """
    today = date.today()

    # Navigation targets
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1

    # Disable "previous" button when already at the current month
    at_min_month = (year, month) <= (today.year, today.month)
    prev_cb = "cal_ignore" if at_min_month else f"cal_nav:{prev_year}-{prev_month:02d}"

    month_names = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    ]
    month_label = f"{month_names[month - 1]} {year}"

    nav_row = [
        InlineKeyboardButton(text="◀️" if not at_min_month else " ", callback_data=prev_cb),
        InlineKeyboardButton(text=month_label, callback_data="cal_ignore"),
        InlineKeyboardButton(text="▶️", callback_data=f"cal_nav:{next_year}-{next_month:02d}"),
    ]

    # Day-of-week headers (Mon … Sun)
    dow_row = [
        InlineKeyboardButton(text=d, callback_data="cal_ignore")
        for d in ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
    ]

    # Build day rows
    day_rows = []
    for week in _cal.monthcalendar(year, month):
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(text=" ", callback_data="cal_ignore"))
            else:
                d = date(year, month, day)
                if d < today:
                    # Past – shown as disabled
                    row.append(InlineKeyboardButton(text=f"·{day}·", callback_data="cal_ignore"))
                elif d == today:
                    row.append(InlineKeyboardButton(text=f"[{day}]", callback_data=f"cal_day:{d.isoformat()}"))
                else:
                    row.append(InlineKeyboardButton(text=str(day), callback_data=f"cal_day:{d.isoformat()}"))
        day_rows.append(row)

    bottom_row = [
        InlineKeyboardButton(text=get_text("create.enter_manually", lang), callback_data="cal_manual"),
        InlineKeyboardButton(text=get_text("cancel", lang), callback_data="cancel_create"),
    ]

    return InlineKeyboardMarkup(inline_keyboard=[nav_row, dow_row] + day_rows + [bottom_row])


# ---------------------------------------------------------------------------
# Time-picker keyboards (12-hour and 24-hour)
# ---------------------------------------------------------------------------

def time_ampm_keyboard(lang: str) -> InlineKeyboardMarkup:
    """First step for 12-hour format: choose AM or PM."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🌅 AM", callback_data="tp_ampm:AM"),
                InlineKeyboardButton(text="🌆 PM", callback_data="tp_ampm:PM"),
            ],
            [
                InlineKeyboardButton(text=get_text("create.back", lang), callback_data="tp_back"),
                InlineKeyboardButton(text=get_text("cancel", lang), callback_data="cancel_create"),
            ],
        ]
    )


def time_hour_keyboard_12(lang: str) -> InlineKeyboardMarkup:
    """Hour grid 1–12 for the 12-hour picker (4 columns)."""
    hours = list(range(1, 13))
    rows = [
        [InlineKeyboardButton(text=str(h), callback_data=f"tp_hour:{h}") for h in hours[i: i + 4]]
        for i in range(0, 12, 4)
    ]
    rows.append([
        InlineKeyboardButton(text=get_text("create.back", lang), callback_data="tp_back"),
        InlineKeyboardButton(text=get_text("cancel", lang), callback_data="cancel_create"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def time_hour_keyboard_24(lang: str) -> InlineKeyboardMarkup:
    """Hour grid 0–23 for the 24-hour picker (4 columns)."""
    rows = [
        [InlineKeyboardButton(text=str(h), callback_data=f"tp_hour:{h}") for h in range(i, min(i + 4, 24))]
        for i in range(0, 24, 4)
    ]
    rows.append([
        InlineKeyboardButton(text=get_text("create.back", lang), callback_data="tp_back"),
        InlineKeyboardButton(text=get_text("cancel", lang), callback_data="cancel_create"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def time_minute_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Minute grid 00, 05, …, 55 (4 columns)."""
    minutes = [f"{m:02d}" for m in range(0, 60, 5)]
    rows = [
        [InlineKeyboardButton(text=m, callback_data=f"tp_min:{m}") for m in minutes[i: i + 4]]
        for i in range(0, 12, 4)
    ]
    rows.append([
        InlineKeyboardButton(text=get_text("create.back", lang), callback_data="tp_back"),
        InlineKeyboardButton(text=get_text("cancel", lang), callback_data="cancel_create"),
    ])
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
