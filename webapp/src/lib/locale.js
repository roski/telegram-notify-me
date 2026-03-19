import { enUS, ar, bn, de, es, fr, hi, id, ja, ko, pt, ru, uk, zhCN } from 'date-fns/locale'

/**
 * Maps i18n language codes to date-fns locales.
 * This ensures weekday names and dates are properly localized when using date-fns format().
 * 
 * Supported languages: en, ar, bn, de, es, fr, hi, id, ja, jv, ko, pa, pt, ru, uk, zh
 * Note: jv (Javanese) and pa (Punjabi) fall back to enUS as date-fns doesn't have these locales.
 */
const localeMap = {
  en: enUS,
  ar: ar,
  bn: bn,
  de: de,
  es: es,
  fr: fr,
  hi: hi,
  id: id,
  ja: ja,
  jv: enUS, // Javanese not available in date-fns, fallback to English
  ko: ko,
  pa: enUS, // Punjabi not available in date-fns, fallback to English
  pt: pt,
  ru: ru,
  uk: uk,
  zh: zhCN,
}

/**
 * Gets the date-fns locale object for the given language code.
 * Falls back to English (enUS) if the language is not found.
 * 
 * @param {string} langCode - The i18n language code (e.g., 'en', 'ru', 'es')
 * @returns {Locale} The date-fns locale object
 */
export function getDateFnsLocale(langCode) {
  return localeMap[langCode] || enUS
}
