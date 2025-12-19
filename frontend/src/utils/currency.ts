import type { Currency } from '@/types/settings'

/**
 * Format price according to currency settings
 * قیمت‌ها به ریال (ارز پایه) ذخیره شده‌اند و باید به ارز مقصد تبدیل شوند
 * exchange_rate نشان می‌دهد چند واحد ریال برابر 1 واحد از این ارز است
 * مثال: تومان exchange_rate = 10 یعنی 10 ریال = 1 تومان
 */
export function formatPrice(amount: number, currency?: Currency | null): string {
  if (!currency) {
    // Fallback: فرض می‌کنیم تومان است (تقسیم بر 10)
    const convertedAmount = amount / 10
    return `${Math.floor(convertedAmount).toLocaleString('fa-IR')} تومان`
  }

  // تبدیل از ریال به ارز مقصد
  const exchangeRate = parseFloat(currency.exchange_rate) || 1
  const convertedAmount = amount / exchangeRate

  // Check if currency should show decimals
  const showDecimals = currency.has_decimals && currency.decimal_places > 0
  
  const formattedNumber = showDecimals
    ? convertedAmount.toLocaleString('fa-IR', {
        minimumFractionDigits: currency.decimal_places,
        maximumFractionDigits: currency.decimal_places,
      })
    : Math.floor(convertedAmount).toLocaleString('fa-IR')

  return `${formattedNumber} ${currency.symbol}`
}

/**
 * Convert amount from base currency to target currency
 */
export function convertCurrency(
  amount: number,
  fromCurrency: Currency,
  toCurrency: Currency
): number {
  // Convert to base first
  const baseAmount = amount / parseFloat(fromCurrency.exchange_rate)
  // Then convert to target
  return baseAmount * parseFloat(toCurrency.exchange_rate)
}

/**
 * Format a number with thousands separators (Persian format)
 */
export function formatNumber(num: number, decimals: number = 0): string {
  return num.toLocaleString('fa-IR', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })
}

/**
 * Parse price string to number
 */
export function parsePrice(priceString: string): number {
  // Remove all non-digit characters except decimal point
  const cleaned = priceString.replace(/[^\d.]/g, '')
  return parseFloat(cleaned) || 0
}
