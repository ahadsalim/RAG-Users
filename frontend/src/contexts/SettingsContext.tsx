'use client'

import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { getSiteSettings } from '@/services/settingsService'
import type { SiteSettings, Currency } from '@/types/settings'

interface SettingsContextType {
  settings: SiteSettings | null
  baseCurrency: Currency | null
  isLoading: boolean
  error: string | null
  refreshSettings: () => Promise<void>
}

const SettingsContext = createContext<SettingsContextType | undefined>(undefined)

export function SettingsProvider({ children }: { children: ReactNode }) {
  const [settings, setSettings] = useState<SiteSettings | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadSettings = async () => {
    try {
      setIsLoading(true)
      setError(null)
      const data = await getSiteSettings()
      setSettings(data)
    } catch (err) {
      console.error('Failed to load site settings:', err)
      setError('خطا در دریافت تنظیمات سایت')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadSettings()
  }, [])

  const value: SettingsContextType = {
    settings,
    baseCurrency: settings?.base_currency || null,
    isLoading,
    error,
    refreshSettings: loadSettings,
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
