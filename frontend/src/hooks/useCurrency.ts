import { useSettings } from '@/contexts/SettingsContext'
import { formatPrice as formatPriceUtil } from '@/utils/currency'
import type { Currency } from '@/types/settings'

/**
 * Hook for currency-related utilities
 */
export function useCurrency() {
  const { baseCurrency, userPreferredCurrency, setUserPreferredCurrency } = useSettings()

  // Use user's preferred currency if set, otherwise use base currency
  const activeCurrency = userPreferredCurrency || baseCurrency

  /**
   * Format a price using the user's preferred currency or a specific currency
   */
  const formatPrice = (amount: number, currency?: Currency | null): string => {
    return formatPriceUtil(amount, currency || activeCurrency)
  }

  /**
   * Get currency symbol
   */
  const getCurrencySymbol = (currency?: Currency | null): string => {
    const curr = currency || activeCurrency
    return curr?.symbol || ''
  }

  /**
   * Check if currency has decimals
   */
  const hasDecimals = (currency?: Currency | null): boolean => {
    const curr = currency || activeCurrency
    return curr?.has_decimals || false
  }

  return {
    baseCurrency,
    userPreferredCurrency,
    activeCurrency,
    formatPrice,
    getCurrencySymbol,
    hasDecimals,
    setUserPreferredCurrency,
  }
}
