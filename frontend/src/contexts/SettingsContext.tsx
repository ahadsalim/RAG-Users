'use client'

import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { getSiteSettings } from '@/services/settingsService'
import type { SiteSettings, Currency } from '@/types/settings'

interface SettingsContextType {
  settings: SiteSettings | null
  baseCurrency: Currency | null
  userPreferredCurrency: Currency | null
  isLoading: boolean
  error: string | null
  refreshSettings: () => Promise<void>
  setUserPreferredCurrency: (currency: Currency | null) => void
}

const SettingsContext = createContext<SettingsContextType | undefined>(undefined)

export function SettingsProvider({ children }: { children: ReactNode }) {
  const [settings, setSettings] = useState<SiteSettings | null>(null)
  const [userPreferredCurrency, setUserPreferredCurrencyState] = useState<Currency | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadSettings = async () => {
    try {
      setIsLoading(true)
      setError(null)
      const data = await getSiteSettings()
      setSettings(data)
      
      // Load user preferred currency from localStorage
      const savedCurrency = localStorage.getItem('preferred_currency')
      if (savedCurrency) {
        try {
          const parsed = JSON.parse(savedCurrency)
          setUserPreferredCurrencyState(parsed)
        } catch {
          // If parsing fails, use base currency
          setUserPreferredCurrencyState(data.base_currency)
        }
      } else {
        // Default to base currency
        setUserPreferredCurrency(data.base_currency)
      }
    } catch (err) {
      console.error('Failed to load site settings:', err)
      setError('خطا در دریافت تنظیمات سایت')
    } finally {
      setIsLoading(false)
    }
  }

  const setUserPreferredCurrency = (currency: Currency | null) => {
    setUserPreferredCurrencyState(currency)
    if (currency) {
      localStorage.setItem('preferred_currency', JSON.stringify(currency))
    } else {
      localStorage.removeItem('preferred_currency')
    }
  }

  useEffect(() => {
    loadSettings()
  }, [])

  const value: SettingsContextType = {
    settings,
    baseCurrency: settings?.base_currency || null,
    userPreferredCurrency: userPreferredCurrency || settings?.base_currency || null,
    isLoading,
    error,
    refreshSettings: loadSettings,
    setUserPreferredCurrency,
  }

  return (
    <SettingsContext.Provider value={value}>
      {children}
    </SettingsContext.Provider>
  )
}

export function useSettings() {
  const context = useContext(SettingsContext)
  if (context === undefined) {
    throw new Error('useSettings must be used within a SettingsProvider')
  }
  return context
}
