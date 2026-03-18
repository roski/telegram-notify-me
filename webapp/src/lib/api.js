import { getInitData } from './telegram'

const API_BASE = import.meta.env.VITE_API_URL ?? ''

async function apiFetch(path, options = {}) {
  const initData = getInitData()
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'X-Init-Data': initData,
      ...(options.headers ?? {}),
    },
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.error ?? `HTTP ${res.status}`)
  }
  return res.json()
}

export const api = {
  /** Fetch all notifications, optionally filtered by local date (YYYY-MM-DD). */
  getNotifications: (date) =>
    apiFetch(`/api/notifications${date ? `?date=${encodeURIComponent(date)}` : ''}`),

  /** Create a new notification. */
  createNotification: (data) =>
    apiFetch('/api/notifications', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  /** Delete a notification by id. */
  deleteNotification: (id) =>
    apiFetch(`/api/notifications/${id}`, { method: 'DELETE' }),

  /** Fetch the current user's profile. */
  getUser: () => apiFetch('/api/user'),

  /** Update the current user's language preference. */
  updateLanguage: (language) =>
    apiFetch('/api/user/language', {
      method: 'PUT',
      body: JSON.stringify({ language }),
    }),
}
