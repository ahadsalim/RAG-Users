'use client'

import { useState, useEffect } from 'react'
import { useCurrency } from '@/hooks/useCurrency'
import { getCurrencies } from '@/services/settingsService'
import type { Currency } from '@/types/settings'

export default function CurrencySelector() {
  const { activeCurrency, setUserPreferredCurrency } = useCurrency()
  const [currencies, setCurrencies] = useState<Currency[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadCurrencies()
  }, [])

  const loadCurrencies = async () => {
    try {
      const data = await getCurrencies()
      setCurrencies(data)
    } catch (error) {
      console.error('Failed to load currencies:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCurrencyChange = (currencyCode: string) => {
    const selected = currencies.find(c => c.code === currencyCode)
    if (selected) {
      setUserPreferredCurrency(selected)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-gray-500">
        <div className="w-4 h-4 border-2 border-gray-300 border-t-transparent rounded-full animate-spin"></div>
        <span className="text-sm">در حال بارگذاری...</span>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          واحد پولی نمایش قیمت‌ها
        </label>
        <select
          value={activeCurrency?.code || ''}
          onChange={(e) => handleCurrencyChange(e.target.value)}
          className="w-full px-4 py-2 pr-10 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent text-right appearance-none"
          dir="rtl"
          style={{ backgroundImage: "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%236b7280'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E\")", backgroundRepeat: "no-repeat", backgroundPosition: "left 0.75rem center", backgroundSize: "1.25rem" }}
        >
          {currencies.map((currency) => (
            <option key={currency.id} value={currency.code}>
              {currency.name} ({currency.symbol})
            </option>
          ))}
        </select>
        <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
          تمام قیمت‌ها با واحد انتخابی شما نمایش داده می‌شوند
        </p>
      </div>

      {activeCurrency && (
        <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
          <div className="flex items-center gap-2 text-sm">
            <span className="text-blue-700 dark:text-blue-300 font-medium">ارز فعلی:</span>
            <span className="text-blue-900 dark:text-blue-100">
              {activeCurrency.name} ({activeCurrency.symbol})
            </span>
          </div>
          {activeCurrency.has_decimals ? (
            <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">
              ✓ با {activeCurrency.decimal_places} رقم اعشار
            </p>
          ) : (
            <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">
              ✓ بدون اعشار
            </p>
          )}
        </div>
      )}
    </div>
  )
}
