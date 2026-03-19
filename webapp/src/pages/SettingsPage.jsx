import { useState, useEffect } from 'react'
import { Check } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { BottomNav } from '@/components/BottomNav'
import { api } from '@/lib/api'
import { cn } from '@/lib/utils'

const LANGUAGES = [
  { code: 'en', label: '🇬🇧 English' },
  { code: 'zh', label: '🇨🇳 中文 (Chinese)' },
  { code: 'hi', label: '🇮🇳 हिन्दी (Hindi)' },
  { code: 'es', label: '🇪🇸 Español (Spanish)' },
  { code: 'fr', label: '🇫🇷 Français (French)' },
  { code: 'ar', label: '🇸🇦 العربية (Arabic)' },
  { code: 'bn', label: '🇧🇩 বাংলা (Bengali)' },
  { code: 'ru', label: '🇷🇺 Русский (Russian)' },
  { code: 'pt', label: '🇧🇷 Português (Portuguese)' },
  { code: 'id', label: '🇮🇩 Bahasa Indonesia' },
  { code: 'de', label: '🇩🇪 Deutsch (German)' },
  { code: 'ja', label: '🇯🇵 日本語 (Japanese)' },
  { code: 'pa', label: '🇮🇳 ਪੰਜਾਬੀ (Punjabi)' },
  { code: 'jv', label: '🇮🇩 Basa Jawa (Javanese)' },
  { code: 'ko', label: '🇰🇷 한국어 (Korean)' },
  { code: 'uk', label: '🇺🇦 Українська (Ukrainian)' },
]

export function SettingsPage() {
  const { t, i18n } = useTranslation()
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState(null)

  useEffect(() => {
    api
      .getUser()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setLoading(false))
  }, [])

  const handleLanguageChange = async (code) => {
    if (!user || saving) return
    setSaving(true)
    setMessage(null)
    try {
      const updated = await api.updateLanguage(code)
      setUser((prev) => ({ ...prev, language_code: updated.language_code }))
      // Apply the new language to the UI immediately.
      await i18n.changeLanguage(updated.language_code)
      setMessage(t('web.settings.language_updated'))
      setTimeout(() => setMessage(null), 2000)
    } catch {
      setMessage(t('web.settings.language_update_failed'))
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="flex flex-col min-h-full bg-gray-50 pb-20">
      {/* Header */}
      <div className="bg-white px-5 py-5 shadow-sm">
        <h1 className="text-2xl font-bold text-gray-900">{t('web.settings.page_title')}</h1>
        {user && (
          <p className="text-sm text-gray-400 mt-0.5">
            {user.first_name ? t('web.settings.greeting', { name: user.first_name }) : ''}
            {user.timezone ? ` · ${user.timezone}` : ''}
          </p>
        )}
      </div>

      <div className="px-5 py-5 flex flex-col gap-5">
        {/* Language section */}
        <div className="bg-white rounded-2xl shadow-sm overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-50">
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
              {t('web.settings.language_section')}
            </p>
          </div>
          {loading ? (
            <div className="px-4 py-6 flex justify-center">
              <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : (
            <ul>
              {LANGUAGES.map(({ code, label }) => {
                const active = user?.language_code === code
                return (
                  <li key={code}>
                    <button
                      onClick={() => handleLanguageChange(code)}
                      disabled={saving}
                      className={cn(
                        'w-full flex items-center justify-between px-4 py-3 text-sm transition-colors',
                        active ? 'text-blue-600 font-semibold bg-blue-50' : 'text-gray-700 hover:bg-gray-50'
                      )}
                    >
                      <span>{label}</span>
                      {active && <Check size={16} className="text-blue-500" />}
                    </button>
                  </li>
                )
              })}
            </ul>
          )}
        </div>

        {/* Timezone (read-only) */}
        {user?.timezone && (
          <div className="bg-white rounded-2xl shadow-sm px-4 py-4">
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
              {t('web.settings.timezone_section')}
            </p>
            <p className="text-sm text-gray-700">{user.timezone}</p>
            <p className="text-xs text-gray-400 mt-1">
              {t('web.settings.timezone_hint')}
            </p>
          </div>
        )}
      </div>

      {/* Toast */}
      {message && (
        <div className="fixed bottom-20 left-1/2 -translate-x-1/2 bg-gray-900 text-white text-sm px-5 py-2.5 rounded-2xl shadow-lg z-50">
          {message}
        </div>
      )}

      <BottomNav />
    </div>
  )
}
