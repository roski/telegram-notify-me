import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { format, isToday } from 'date-fns'
import { Plus } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { WeeklyCalendar } from '@/components/WeeklyCalendar'
import { Timeline } from '@/components/Timeline'
import { BottomNav } from '@/components/BottomNav'
import { api } from '@/lib/api'

export function TimelinePage() {
  const [selectedDate, setSelectedDate] = useState(new Date())
  const [notifications, setNotifications] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const navigate = useNavigate()
  const { t } = useTranslation()

  const fetchNotifications = useCallback(async (date) => {
    setLoading(true)
    setError(null)
    try {
      const dateStr = format(date, 'yyyy-MM-dd')
      const data = await api.getNotifications(dateStr)
      setNotifications(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchNotifications(selectedDate)
  }, [selectedDate, fetchNotifications])

  const handleSelectDate = (date) => {
    setSelectedDate(date)
  }

  const handleDelete = async (id) => {
    try {
      await api.deleteNotification(id)
      setNotifications((prev) => prev.filter((n) => n.id !== id))
    } catch (err) {
      console.error('Failed to delete notification:', err)
    }
  }

  const dateLabel = isToday(selectedDate) ? t('web.timeline.today') : format(selectedDate, 'EEEE')
  const formattedDate = format(selectedDate, 'MMMM d, yyyy')

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* Header */}
      <div className="bg-white px-5 pt-5 pb-3 shadow-sm">
        <p className="text-xs text-gray-400 font-medium">{formattedDate}</p>
        <h1 className="text-3xl font-bold text-gray-900 mt-0.5">{dateLabel}</h1>

        {/* Weekly calendar strip */}
        <div className="mt-4">
          <WeeklyCalendar selectedDate={selectedDate} onSelectDate={handleSelectDate} />
        </div>
      </div>

      {/* Timeline area */}
      <div className="flex-1 overflow-y-auto pb-32 mt-2">
        {error ? (
          <div className="flex flex-col items-center justify-center py-16 px-6 text-center">
            <span className="text-3xl mb-3">⚠️</span>
            <p className="text-gray-500 text-sm">{error}</p>
            <button
              onClick={() => fetchNotifications(selectedDate)}
              className="mt-4 text-blue-500 text-sm font-medium"
            >
              {t('web.timeline.retry')}
            </button>
          </div>
        ) : (
          <Timeline
            notifications={notifications}
            onDelete={handleDelete}
            loading={loading}
          />
        )}
      </div>

      {/* FAB – Add notification */}
      <button
        onClick={() => navigate('/create')}
        className="fixed bottom-20 left-1/2 -translate-x-1/2 z-30 w-14 h-14 bg-blue-500 rounded-2xl shadow-lg flex items-center justify-center active:scale-95 transition-transform hover:bg-blue-600"
        aria-label={t('web.create.submit')}
      >
        <Plus size={28} className="text-white" strokeWidth={2.5} />
      </button>

      <BottomNav />
    </div>
  )
}
