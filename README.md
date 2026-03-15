# telegram-notify-me

A production-ready Telegram notification bot that lets users create, manage, and receive scheduled notifications with support for recurring reminders and internationalization (English & Ukrainian).

---

## Features

- 📅 **Scheduled notifications** — one-time or recurring (daily, weekly, monthly, yearly)
- 🌍 **Internationalization** — English and Ukrainian, auto-detected from Telegram user settings
- 🔁 **Recurring notifications** — marked with 🔁 icon in lists
- 📋 **Notification management** — view, edit, and delete from within Telegram
- 👥 **Multi-user** — each user sees only their own notifications
- 🗃️ **Notification history** — every delivery is logged with status
- 🐘 **PostgreSQL** — clean schema with migrations via Alembic
- 🐳 **Docker Compose** — single command to run everything

---

## Project Structure

```
telegram-notify-me/
├── bot/
│   ├── main.py                          # Entry point
│   ├── config.py                        # Environment configuration
│   ├── i18n.py                          # Internationalization helper
│   ├── database/
│   │   ├── models.py                    # SQLAlchemy models
│   │   └── database.py                  # Async DB engine + session factory
│   ├── handlers/
│   │   ├── start.py                     # /start command + main menu
│   │   ├── create_notification.py       # FSM-based notification creation flow
│   │   └── scheduled_notifications.py  # View / edit / delete notifications
│   ├── keyboards/
│   │   └── keyboards.py                 # All inline keyboards
│   ├── scheduler/
│   │   └── scheduler.py                 # APScheduler integration
│   └── locales/
│       ├── en.json                      # English translations
│       └── uk.json                      # Ukrainian translations
├── migrations/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 001_initial.py              # Initial schema migration
├── docker-compose.yml
├── Dockerfile
├── alembic.ini
├── requirements.txt
└── .env.example
```

---

## Database Schema

### `users`
| Column          | Type        | Description                        |
|-----------------|-------------|------------------------------------|
| id              | Integer PK  | Auto-increment                     |
| telegram_id     | BigInteger  | Telegram user ID (unique, indexed) |
| username        | String      | Telegram username                  |
| first_name      | String      | Telegram first name                |
| last_name       | String      | Telegram last name                 |
| language_code   | String      | Detected language (`en` / `uk`)    |
| created_at      | Timestamp   | Row creation time                  |

### `notifications`
| Column           | Type        | Description                                  |
|------------------|-------------|----------------------------------------------|
| id               | Integer PK  | Auto-increment                               |
| user_id          | Integer FK  | References `users.id`                        |
| title            | String      | Notification title                           |
| description      | Text        | Notification body                            |
| scheduled_at     | Timestamp   | Original scheduled time                      |
| recurrence_type  | Enum        | `once / daily / weekly / monthly / yearly`  |
| execution_count  | Integer     | Number of times sent                         |
| next_run_at      | Timestamp   | Next scheduled send time (nullable)          |
| is_active        | Boolean     | Whether the notification is still active     |
| created_at       | Timestamp   | Row creation time                            |

### `notification_history`
| Column           | Type        | Description                         |
|------------------|-------------|-------------------------------------|
| id               | Integer PK  | Auto-increment                      |
| notification_id  | Integer FK  | References `notifications.id`       |
| user_id          | Integer FK  | References `users.id`               |
| sent_at          | Timestamp   | When the message was sent           |
| delivery_status  | Enum        | `sent` or `failed`                  |

---

## Setup

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/)
- A Telegram bot token from [@BotFather](https://t.me/BotFather)

### 1. Clone the repository

```bash
git clone https://github.com/roski/telegram-notify-me.git
cd telegram-notify-me
```

### 2. Create the `.env` file

```bash
cp .env.example .env
```

Edit `.env` and set your values:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=telegram_notify
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
```

### 3. Start with Docker Compose

```bash
docker compose up --build
```

This starts:
- `postgres` — PostgreSQL 16
- `bot` — the Telegram bot

The bot creates all database tables automatically on startup.

### 4. Run database migrations (optional, for production)

```bash
docker compose run --rm bot alembic upgrade head
```

---

## Running Locally (without Docker)

### Requirements

- Python 3.12+
- PostgreSQL running locally

```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your local settings (POSTGRES_HOST=localhost)
python -m bot.main
```

---

## Environment Variables

| Variable           | Description                            | Default        |
|--------------------|----------------------------------------|----------------|
| `TELEGRAM_BOT_TOKEN` | Bot token from @BotFather           | **required**   |
| `POSTGRES_USER`    | PostgreSQL username                    | `postgres`     |
| `POSTGRES_PASSWORD`| PostgreSQL password                    | `postgres`     |
| `POSTGRES_DB`      | PostgreSQL database name               | `telegram_notify` |
| `POSTGRES_HOST`    | PostgreSQL host                        | `localhost`    |
| `POSTGRES_PORT`    | PostgreSQL port                        | `5432`         |

---

## Bot Usage

1. Start the bot: `/start`
2. Choose **➕ Create Notification** to create a new notification
3. Follow the step-by-step flow (title → description → date → time → recurrence)
4. Choose **📅 Scheduled Notifications** to view upcoming notifications
5. Click any notification to view details, edit, or delete it

---

## Scaling Suggestions

For high notification volumes consider:

- **Redis + Celery / RQ** — offload notification sending to a dedicated worker pool; use Redis as the broker and result backend
- **APScheduler with Redis job store** — persist scheduled jobs in Redis so they survive restarts and can be shared across worker processes
- **Message batching** — group notifications due within the same second/minute and send them in batch API calls
- **Horizontal scaling** — run multiple bot worker containers behind a load balancer; use Redis for shared FSM state (`aiogram-redis-storage`)
- **Separate scheduler process** — extract the APScheduler into its own service so it scales independently from bot I/O handling
- **Database read replicas** — direct read-heavy queries (listing notifications) to replicas and writes to the primary