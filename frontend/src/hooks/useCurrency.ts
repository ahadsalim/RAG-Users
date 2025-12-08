import { useSettings } from '@/contexts/SettingsContext'
import { formatPrice as formatPriceUtil } from '@/utils/currency'
import type { Currency } from '@/types/settings'

/**
 * Hook for currency-related utilities
 */
export function useCurrency() {
  const { baseCurrency } = useSettings()

  /**
   * Format a price using the base currency or a specific currency
   */
  const formatPrice = (amount: number, currency?: Currency | null): string => {
    return formatPriceUtil(amount, currency || baseCurrency)
  }

  /**
   * Get currency symbol
   */
  const getCurrencySymbol = (currency?: Currency | null): string => {
    const curr = currency || baseCurrency
    return curr?.symbol || ''
  }

  /**
   * Check if currency has decimals
   */
  const hasDecimals = (currency?: Currency | null): boolean => {
    const curr = currency || baseCurrency
    return curr?.has_decimals || false
  }

  return {
    baseCurrency,
    formatPrice,
    getCurrencySymbol,
    hasDecimals,
  }
}
