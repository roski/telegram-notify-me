import { Suspense, useEffect } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { initTelegram, getColorScheme, getThemeParams } from './lib/telegram'
import { TimelinePage } from './pages/TimelinePage'
import { CreatePage } from './pages/CreatePage'
import { SettingsPage } from './pages/SettingsPage'
import './lib/i18n'
import i18n from './lib/i18n'
import { api } from './lib/api'

function App() {
  useEffect(() => {
    initTelegram()

    // Apply Telegram theme CSS variables
    const params = getThemeParams()
    const scheme = getColorScheme()
    const root = document.documentElement

    if (scheme === 'dark') {
      root.style.setProperty('--bg-color', params.bg_color ?? '#1c1c1e')
      root.style.setProperty('--text-color', params.text_color ?? '#ffffff')
      root.style.setProperty('--hint-color', params.hint_color ?? '#8e8e93')
      root.style.setProperty('--secondary-bg', params.secondary_bg_color ?? '#2c2c2e')
      document.body.classList.add('dark')
    } else {
      root.style.setProperty('--bg-color', params.bg_color ?? '#f0f4f8')
      root.style.setProperty('--text-color', params.text_color ?? '#1a1a2e')
      root.style.setProperty('--hint-color', params.hint_color ?? '#7f8c8d')
      root.style.setProperty('--secondary-bg', params.secondary_bg_color ?? '#ffffff')
    }

    // Load the user's saved language and apply it to the UI.
    api
      .getUser()
      .then(async (user) => {
        if (user?.language_code) {
          // Load translations for the user's language before changing.
          await i18n.loadNamespaces(['translation'], { lng: user.language_code })
          await i18n.changeLanguage(user.language_code)
        }
      })
      .catch(() => {
        // Ignore auth errors (e.g. during local development outside Telegram).
      })
  }, [])

  return (
    <BrowserRouter>
      <Suspense fallback={null}>
        <Routes>
          <Route path="/" element={<TimelinePage />} />
          <Route path="/create" element={<CreatePage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  )
}

export default App
