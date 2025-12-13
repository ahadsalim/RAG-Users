import api from '@/lib/axios'
import type { SiteSettings, Currency, PaymentGateway, CurrencyConversionRequest, CurrencyConversionResponse } from '@/types/settings'

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
  const response = await api.get('/api/v1/currencies/')
  return response.data.results || response.data
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
  const response = await api.post('/api/v1/currencies/convert/', request)
  return response.data
}
