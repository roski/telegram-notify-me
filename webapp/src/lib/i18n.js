import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import HttpBackend from 'i18next-http-backend'

/**
 * Shared i18n configuration.
 *
 * Translations are served by the Flask API at /api/i18n/{lang} and loaded on
 * demand via the HTTP backend.  Both the Telegram bot and the Web App consume
 * the same JSON files located in /shared/i18n/.
 *
 * Interpolation uses the same single-brace syntax ({variable}) that the bot
 * translations already use, so all shared keys work identically in both
 * environments.
 */
i18n
  .use(HttpBackend)
  .use(initReactI18next)
  .init({
    lng: 'en',
    fallbackLng: 'en',
    ns: ['translation'],
    defaultNS: 'translation',
    backend: {
      // Use single-brace syntax to match the custom interpolation prefix/suffix
      // configured below.  The HTTP backend processes this path through the same
      // i18next interpolator, so {lng} (not {{lng}}) is correctly substituted.
      loadPath: '/api/i18n/{lng}',
    },
    interpolation: {
      // Match the {variable} syntax used in the bot translation files.
      prefix: '{',
      suffix: '}',
      escapeValue: false,
    },
    react: {
      useSuspense: true,
    },
  })

export default i18n
