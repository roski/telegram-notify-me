import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { api } from '@/lib/api'

const RECURRENCE_VALUES = ['once', 'daily', 'weekly', 'monthly', 'yearly']

/** Return the current local datetime formatted for datetime-local input. */
function defaultDatetimeLocal() {
  const now = new Date()
  now.setMinutes(now.getMinutes() + 5)
  // Format: "YYYY-MM-DDTHH:MM"
  const pad = (n) => String(n).padStart(2, '0')
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}T${pad(now.getHours())}:${pad(now.getMinutes())}`
}

export function CreatePage() {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const [form, setForm] = useState({
    title: '',
    description: '',
    datetimeLocal: defaultDatetimeLocal(),
    recurrence_type: 'once',
  })
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  const handleChange = (field) => (e) => {
    setForm((prev) => ({ ...prev, [field]: e.target.value }))
  }

  const handleRecurrence = (value) => {
    setForm((prev) => ({ ...prev, recurrence_type: value }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)

    if (!form.title.trim()) {
      setError(t('web.create.error_title_required'))
      return
    }
    if (!form.datetimeLocal) {
      setError(t('web.create.error_datetime_required'))
      return
    }

    // Convert the local datetime string to a UTC ISO string.
    const localDate = new Date(form.datetimeLocal)
    if (isNaN(localDate.getTime())) {
      setError(t('web.create.error_invalid_datetime'))
      return
    }
    if (localDate <= new Date()) {
      setError(t('web.create.error_future_required'))
      return
    }

    setSubmitting(true)
    try {
      await api.createNotification({
        title: form.title.trim(),
        description: form.description.trim(),
        scheduled_at: localDate.toISOString(),
        recurrence_type: form.recurrence_type,
      })
      navigate('/')
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="flex flex-col min-h-full bg-gray-50">
      {/* Top bar */}
      <div className="bg-white px-4 py-4 flex items-center gap-3 shadow-sm">
        <button
          onClick={() => navigate(-1)}
          className="w-9 h-9 flex items-center justify-center rounded-xl hover:bg-gray-100 transition-colors"
          aria-label={t('web.create.back')}
        >
          <ArrowLeft size={20} className="text-gray-600" />
        </button>
        <h2 className="text-lg font-bold text-gray-900">{t('web.create.page_title')}</h2>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="flex flex-col gap-5 px-5 py-6 flex-1">
        {/* Title */}
        <div className="flex flex-col gap-2">
          <Label htmlFor="title">{t('web.create.title_label')} *</Label>
          <Input
            id="title"
            placeholder={t('web.create.title_placeholder')}
            value={form.title}
            onChange={handleChange('title')}
            maxLength={255}
            required
          />
        </div>

        {/* Description */}
        <div className="flex flex-col gap-2">
          <Label htmlFor="description">{t('web.create.description_label')}</Label>
          <textarea
            id="description"
            placeholder={t('web.create.description_placeholder')}
            value={form.description}
            onChange={handleChange('description')}
            rows={3}
            className="w-full rounded-2xl border border-gray-200 bg-white px-4 py-3 text-sm placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
          />
        </div>

        {/* Date & Time */}
        <div className="flex flex-col gap-2">
          <Label htmlFor="datetimeLocal">{t('web.create.datetime_label')} *</Label>
          <Input
            id="datetimeLocal"
            type="datetime-local"
            value={form.datetimeLocal}
            onChange={handleChange('datetimeLocal')}
            required
          />
        </div>

        {/* Repeat */}
        <div className="flex flex-col gap-2">
          <Label htmlFor="recurrence">{t('web.create.repeat_label')}</Label>
          <Select value={form.recurrence_type} onValueChange={handleRecurrence}>
            <SelectTrigger id="recurrence">
              <SelectValue placeholder={t('web.create.repeat_label')} />
            </SelectTrigger>
            <SelectContent>
              {RECURRENCE_VALUES.map((value) => (
                <SelectItem key={value} value={value}>
                  {t(`recurrence.${value}`)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {error && (
          <p className="text-sm text-red-500 bg-red-50 px-4 py-3 rounded-2xl">{error}</p>
        )}

        <div className="mt-auto pt-4">
          <Button type="submit" className="w-full" size="lg" disabled={submitting}>
            {submitting ? t('web.create.submitting') : t('web.create.submit')}
          </Button>
        </div>
      </form>
    </div>
  )
}
