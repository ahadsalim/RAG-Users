import api from '@/lib/axios'
import type { SiteSettings, Currency, PaymentGateway, CurrencyConversionRequest, CurrencyConversionResponse } from '@/types/settings'

// Fallback currencies for when API is not available
const FALLBACK_CURRENCIES: Currency[] = [
  { id: 1, code: 'IRT', name: 'تومان', symbol: 'تومان', has_decimals: false, decimal_places: 0, exchange_rate: '10', is_active: true, display_order: 1 },
]

/**
 * Get site settings
 */
export async function getSiteSettings(): Promise<SiteSettings> {
  const response = await api.get('/api/v1/settings/')
  return response.data
}

/**
 * Get all active currencies
 */
export async function getCurrencies(): Promise<Currency[]> {
  try {
    const response = await api.get('/api/v1/finance/currencies/')
    const data = response.data.results || response.data
    return data.length > 0 ? data : FALLBACK_CURRENCIES
  } catch (error) {
    console.error('Failed to fetch currencies, using fallback:', error)
    return FALLBACK_CURRENCIES
  }
}

/**
 * Get all active payment gateways
 */
export async function getPaymentGateways(): Promise<PaymentGateway[]> {
  const response = await api.get('/api/v1/payment-gateways/')
  return response.data.results || response.data
}

/**
 * Convert currency
 */
export async function convertCurrency(request: CurrencyConversionRequest): Promise<CurrencyConversionResponse> {
  const response = await api.post('/api/v1/finance/currencies/convert/', request)
  return response.data
}
