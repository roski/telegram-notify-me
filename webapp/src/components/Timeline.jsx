import { Trash2 } from 'lucide-react'
import { cn } from '@/lib/utils'

/**
 * A single notification card in the timeline.
 *
 * @param {{ notification: object, onDelete: (id: number) => void }} props
 */
function NotificationCard({ notification, onDelete }) {
  const isPast = new Date(notification.scheduled_at) < new Date()

  return (
    <div
      className={cn(
        'flex-1 rounded-2xl p-4 shadow-sm transition-all',
        isPast ? 'bg-white opacity-60' : 'bg-white'
      )}
    >
      <div className="flex justify-between items-start gap-2">
        <span className={cn('font-bold text-sm leading-snug', isPast ? 'text-gray-500' : 'text-gray-900')}>
          {notification.title}
        </span>
        <div className="flex items-center gap-2 shrink-0">
          <span className="text-xs text-gray-400 whitespace-nowrap">{notification.local_time}</span>
          <button
            onClick={() => onDelete(notification.id)}
            className="text-gray-300 hover:text-red-400 transition-colors"
            aria-label="Delete notification"
          >
            <Trash2 size={14} />
          </button>
        </div>
      </div>
      {notification.description && (
        <p className="text-xs text-gray-400 mt-1 leading-relaxed">{notification.description}</p>
      )}
      {notification.recurrence_type && notification.recurrence_type !== 'once' && (
        <span className="mt-2 inline-block text-xs text-blue-400 bg-blue-50 px-2 py-0.5 rounded-full capitalize">
          🔁 {notification.recurrence_type}
        </span>
      )}
    </div>
  )
}

/**
 * Vertical timeline of notifications for the selected day.
 *
 * @param {{ notifications: object[], onDelete: (id: number) => void, loading: boolean }} props
 */
export function Timeline({ notifications, onDelete, loading }) {
  if (loading) {
    return (
      <div className="flex flex-col gap-3 px-4 py-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="flex gap-3">
            <div className="flex flex-col items-center">
              <div className="w-3 h-3 rounded-full bg-gray-200 animate-pulse" />
              <div className="w-0.5 flex-1 bg-gray-200 animate-pulse mt-1" />
            </div>
            <div className="flex-1 mb-3 h-16 rounded-2xl bg-gray-200 animate-pulse" />
          </div>
        ))}
      </div>
    )
  }

  if (notifications.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-gray-400">
        <span className="text-4xl mb-3">🔔</span>
        <p className="text-base font-medium">No notifications</p>
        <p className="text-sm mt-1">Tap + to add one</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col px-4 py-2">
      {notifications.map((notif, index) => {
        const isPast = new Date(notif.scheduled_at) < new Date()
        const isLast = index === notifications.length - 1

        return (
          <div key={notif.id} className="flex gap-3">
            {/* Timeline spine */}
            <div className="flex flex-col items-center">
              <div
                className={cn(
                  'w-3 h-3 rounded-full border-2 mt-4 z-10 bg-white shrink-0',
                  isPast ? 'border-gray-300' : 'border-blue-500'
                )}
              />
              {!isLast && <div className="w-0.5 flex-1 bg-blue-100 my-0.5" />}
            </div>

            {/* Card */}
            <div className="flex-1 mb-3">
              <NotificationCard notification={notif} onDelete={onDelete} />
            </div>
          </div>
        )
      })}
    </div>
  )
}
