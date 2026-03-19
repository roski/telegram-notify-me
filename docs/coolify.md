# Deploying to Coolify

[Coolify](https://coolify.io) is a self-hosted PaaS that can deploy this project directly from GitHub with zero manual Docker commands.

---

## Prerequisites

- A running Coolify instance (v4 or later)
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- The repository forked or accessible from your Coolify server

---

## Step 1 — Add a new resource

1. Open your Coolify dashboard and select (or create) a **Project**.
2. Click **+ New Resource → Docker Compose**.
3. Choose **GitHub** (or **Public Repository**) as the source.
4. Enter the repository URL — your fork or the upstream project:  
   `https://github.com/YOUR_USERNAME/telegram-notify-me`  
   Select the branch you want to deploy (e.g. `main`).

---

## Step 2 — Configure environment variables

Coolify shows an **Environment Variables** panel after the source is connected.

Set the **required** variable:

| Variable | Value |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Your bot token from @BotFather |

The remaining variables have sensible defaults and are **optional**:

| Variable | Default | Notes |
|---|---|---|
| `POSTGRES_DB` | `notifications` | |
| `POSTGRES_USER` | `postgres` | |
| `POSTGRES_PASSWORD` | `postgres` | Change for production |
| `POSTGRES_HOST` | `db` | Keep as `db` — matches the compose service name |
| `POSTGRES_PORT` | `5432` | |
| `WEBAPP_URL` | *(auto)* | See [WEBAPP_URL section](#webapp_url-auto-population) below |

> **Tip:** You can change the PostgreSQL password by setting `POSTGRES_PASSWORD` in the Coolify UI before the first deploy.

---

## Step 3 — Assign domains

Coolify can expose the `webapp` and `api` services on your custom domains.

1. In the resource view, open the **Domains** tab (or the individual service settings).
2. Assign a public domain to the **webapp** service (e.g. `notify.example.com`).
3. Optionally assign a domain to the **api** service if you need direct API access.
4. Coolify will provision TLS certificates automatically via Let's Encrypt.

> **Important:** The webapp domain must use **HTTPS** because Telegram Mini Apps require a secure origin.

---

## Step 4 — Deploy

Click **Deploy**. Coolify will:

1. Clone the repository
2. Build all three services (`bot`, `api`, `webapp`) in parallel
3. Start the containers and attach them to an internal network
4. Expose the `webapp` container on the domain you configured

Watch the **Deployment Logs** panel for progress. A successful deploy shows all three services in a **Running** state.

---

## WEBAPP_URL auto-population

`WEBAPP_URL` is the public HTTPS URL that the bot uses to show the **Open Web App** button in the Telegram menu. On Coolify, **you do not need to set this manually**.

Coolify automatically provides a `SERVICE_URL_WEBAPP` environment variable that contains the full URL of your webapp service. The bot reads `WEBAPP_URL` first; if it is empty, it falls back to `SERVICE_URL_WEBAPP`.

This means the "Open Web App" button appears automatically as soon as you assign a domain to the `webapp` service in Coolify — no extra configuration required.

If you need to override the URL (e.g., to use a custom domain not managed by Coolify), set `WEBAPP_URL` explicitly in the Coolify environment variables panel.

---

## Step 5 — Run database migrations (first deploy only)

On the very first deployment the bot creates all tables automatically. If you prefer to manage the schema with Alembic:

```bash
# From the Coolify server, exec into the bot container
docker exec -it <bot-container-name> alembic upgrade head
```

Or add a one-off job in Coolify's **Scheduled Tasks** / **One-off Commands** panel.

---

## Redeployment

Push a commit to the tracked branch and Coolify will pick it up automatically (if webhooks are configured) or click **Redeploy** in the dashboard.

All persistent data (PostgreSQL) is stored in a named Docker volume and survives redeployments.

---

## Troubleshooting

### `npm ci` fails during webapp build

If you see an error like:
```
process "/bin/sh -c npm ci" did not complete successfully: exit code: 1
```

This is usually caused by a transient npm registry connectivity issue in the build environment. Try the following:

1. **Redeploy** — click **Redeploy** in Coolify. Transient network failures resolve themselves.
2. **Check disk space** — ensure the Coolify server has sufficient disk space (`df -h`).
3. **Clear build cache** — in Coolify's resource settings, enable **Force rebuild** (clears the Docker layer cache) and redeploy.

### "Open Web App" button does not appear

- Confirm you have assigned a public HTTPS domain to the `webapp` service in Coolify.
- Check that `SERVICE_URL_WEBAPP` is visible in the **Environment Variables** panel (Coolify sets it automatically after a domain is assigned).
- If it still doesn't appear, set `WEBAPP_URL` manually to the webapp's HTTPS URL.

### Services cannot reach each other

All services defined in the same `docker-compose.yml` share a Coolify-managed Docker network and resolve each other by service name (`db`, `api`, `webapp`). If you split services across multiple Coolify resources, you will need to update `POSTGRES_HOST` and the nginx proxy accordingly.

### Webhook not triggering redeployment

1. Go to **Settings → Git** in the resource view.
2. Click **Regenerate Webhook** and update the webhook URL in your GitHub repository settings (**Settings → Webhooks**).
