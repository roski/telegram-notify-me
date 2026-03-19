import { format, startOfWeek, addDays, isToday, isSameDay } from 'date-fns'
import { useTranslation } from 'react-i18next'
import { cn } from '@/lib/utils'
import { getDateFnsLocale } from '@/lib/locale'

/**
 * Horizontal 7-day calendar showing the current week (Mon–Sun).
 *
 * @param {{ selectedDate: Date, onSelectDate: (d: Date) => void }} props
 */
export function WeeklyCalendar({ selectedDate, onSelectDate }) {
  const { i18n } = useTranslation()
  const locale = getDateFnsLocale(i18n.language)
  const weekStart = startOfWeek(new Date(), { weekStartsOn: 1 })
  const days = Array.from({ length: 7 }, (_, i) => addDays(weekStart, i))

  return (
    <div className="flex justify-between px-2">
      {days.map((day) => {
        const selected = isSameDay(day, selectedDate)
        const today = isToday(day)

        return (
          <button
            key={day.toISOString()}
            onClick={() => onSelectDate(day)}
            className={cn(
              'flex flex-col items-center py-2 px-2.5 rounded-2xl transition-all min-w-[40px]',
              selected && 'bg-blue-500 shadow-md',
              !selected && today && 'text-blue-500',
              !selected && !today && 'text-gray-500'
            )}
          >
            <span className={cn('text-xs font-medium', selected && 'text-white')}>
              {format(day, 'EEE', { locale })}
            </span>
            <span
              className={cn(
                'text-base font-bold mt-0.5',
                selected && 'text-white',
                !selected && today && 'text-blue-500',
                !selected && !today && 'text-gray-800'
              )}
            >
              {format(day, 'd')}
            </span>
            {today && (
              <span
                className={cn(
                  'w-1.5 h-1.5 rounded-full mt-0.5',
                  selected ? 'bg-white' : 'bg-blue-500'
                )}
              />
            )}
          </button>
        )
      })}
    </div>
  )
}
