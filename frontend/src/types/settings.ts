export interface Currency {
  id: number
  code: string
  name: string
  symbol: string
  has_decimals: boolean
  decimal_places: number
  exchange_rate: string
  is_active: boolean
  display_order: number
}

export interface PaymentGateway {
  id: number
  name: string
  gateway_type: string
  is_active: boolean
  is_sandbox: boolean
  supported_currencies: Currency[]
  commission_percentage: string
  display_order: number
}

export interface SiteSettings {
  site_name: string
  site_url: string
  site_description: string
  base_currency: Currency | null
  default_payment_gateway: PaymentGateway | null
  support_email: string
  support_phone: string
  telegram_url: string
  instagram_url: string
  twitter_url: string
  maintenance_mode: boolean
  maintenance_message: string
  allow_registration: boolean
  require_email_verification: boolean
  enable_two_factor: boolean
}

export interface CurrencyConversionRequest {
  from_currency: string
  to_currency: string
  amount: number
}

export interface CurrencyConversionResponse {
  from_currency: string
  to_currency: string
  amount: number
  converted_amount: number
  formatted: string
}
