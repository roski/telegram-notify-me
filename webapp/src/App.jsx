import { useEffect } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { initTelegram, getColorScheme, getThemeParams } from './lib/telegram'
import { TimelinePage } from './pages/TimelinePage'
import { CreatePage } from './pages/CreatePage'
import { SettingsPage } from './pages/SettingsPage'

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
  }, [])

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<TimelinePage />} />
        <Route path="/create" element={<CreatePage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
