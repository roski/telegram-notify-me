/** @returns {import('@twa-dev/types').WebApp | null} */
function getTg() {
  return window.Telegram?.WebApp ?? null
}

/** Initialise the Telegram WebApp SDK (call once on app mount). */
export function initTelegram() {
  const tg = getTg()
  if (!tg) return
  tg.ready()
  tg.expand()
}

/** Raw initData string sent by Telegram (used for server-side validation). */
export function getInitData() {
  return getTg()?.initData ?? ''
}

/** Telegram user object from initDataUnsafe. */
export function getTelegramUser() {
  return getTg()?.initDataUnsafe?.user ?? null
}

/** Telegram colour scheme: "light" | "dark". */
export function getColorScheme() {
  return getTg()?.colorScheme ?? 'light'
}

/** Telegram theme params (bg_color, text_color, …). */
export function getThemeParams() {
  return getTg()?.themeParams ?? {}
}

/** Close the Mini App. */
export function closeTelegram() {
  getTg()?.close()
}
