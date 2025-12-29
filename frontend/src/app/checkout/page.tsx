'use client'

import { useState, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { ArrowRight, CreditCard, CheckCircle, AlertCircle, Loader2, Shield, Building2 } from 'lucide-react'
import axios from 'axios'
import Image from 'next/image'
import { useSettings } from '@/contexts/SettingsContext'

const API_URL = process.env.NEXT_PUBLIC_API_URL || ''

interface Plan {
  id: string
  name: string
  description: string
  price: number
  display_price: number
  formatted_price: string
  currency_symbol: string
  duration_days: number
  max_queries_per_day: number
  max_queries_per_month: number
}

interface PaymentGateway {
  id: number
  name: string
  gateway_type: string
  is_active: boolean
}

interface FinancialSettings {
  company_name: string
  company_address: string
  tax_rate: number
  economic_code: string
  national_id: string
  phone: string
  postal_code: string
}

interface SiteSettings {
  frontend_site_name: string
  admin_site_name: string
  support_email: string
  support_phone: string
}

export default function CheckoutPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const planId = searchParams.get('plan')
  const { userPreferredCurrency } = useSettings()
  
  const [plan, setPlan] = useState<Plan | null>(null)
  const [gateways, setGateways] = useState<PaymentGateway[]>([])
  const [selectedGateway, setSelectedGateway] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [processing, setProcessing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [financialSettings, setFinancialSettings] = useState<FinancialSettings | null>(null)
  const [siteSettings, setSiteSettings] = useState<SiteSettings | null>(null)
  const [invoiceNumber, setInvoiceNumber] = useState<string>('')

  // تولید شماره پیش‌فاکتور موقت
  useEffect(() => {
    const generateTempInvoiceNumber = () => {
      const now = new Date()
      const year = now.getFullYear()
      const month = String(now.getMonth() + 1).padStart(2, '0')
      const day = String(now.getDate()).padStart(2, '0')
      const random = Math.floor(Math.random() * 10000).toString().padStart(4, '0')
      return `PRE-${year}${month}${day}-${random}`
    }
    setInvoiceNumber(generateTempInvoiceNumber())
  }, [])

  useEffect(() => {
    const fetchData = async () => {
      if (!planId) {
        setError('پلن انتخاب نشده است')
        setLoading(false)
        return
      }

      try {
        let token = null
        const authStorage = localStorage.getItem('auth-storage')
        if (authStorage) {
          try {
            const parsed = JSON.parse(authStorage)
            token = parsed?.state?.accessToken
          } catch (e) {}
        }
        
        if (!token) {
          router.push('/auth/login?redirect=/checkout?plan=' + planId)
          return
        }

        const headers = { Authorization: `Bearer ${token}` }

        // Fetch plan details
        const planResponse = await axios.get(`${API_URL}/api/v1/subscriptions/plans/${planId}/`, { headers })
        setPlan(planResponse.data)

        // Fetch payment gateways with user's preferred currency
        const currencyParam = userPreferredCurrency?.code || 'USD'
        const gatewaysResponse = await axios.get(
          `${API_URL}/api/v1/payments/gateways/?currency=${currencyParam}`,
          { headers }
        )
        const activeGateways = gatewaysResponse.data.filter((g: PaymentGateway) => g.is_active)
        setGateways(activeGateways)
        
        if (activeGateways.length > 0) {
          setSelectedGateway(activeGateways[0].id)
        }

        // Fetch financial settings
        try {
          const finResponse = await axios.get(`${API_URL}/api/v1/finance/settings/public/`)
          setFinancialSettings(finResponse.data)
        } catch (e) {
          // Use defaults if not available
          setFinancialSettings({
            company_name: 'تجارت چت',
            company_address: '',
            tax_rate: 10,
            economic_code: '',
            national_id: '',
            phone: '',
            postal_code: ''
          })
        }

        // Fetch site settings
        try {
          const siteResponse = await axios.get(`${API_URL}/api/v1/settings/`)
          setSiteSettings(siteResponse.data)
        } catch (e) {
          setSiteSettings({
            frontend_site_name: 'تجارت چت',
            admin_site_name: 'پنل مدیریت',
            support_email: '',
            support_phone: ''
          })
        }
      } catch (err: any) {
        console.error('Error fetching checkout data:', err)
        if (err.response?.status === 401) {
          router.push('/auth/login?redirect=/checkout?plan=' + planId)
        } else {
          setError('خطا در بارگذاری اطلاعات')
        }
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [planId, router, userPreferredCurrency])

  const handlePayment = async () => {
    if (!selectedGateway || !plan) return

    setProcessing(true)
    setError(null)

    try {
      let token = null
      const authStorage = localStorage.getItem('auth-storage')
      if (authStorage) {
        try {
          const parsed = JSON.parse(authStorage)
          token = parsed?.state?.accessToken
        } catch (e) {}
      }
      const headers = { Authorization: `Bearer ${token}` }

      const response = await axios.post(
        `${API_URL}/api/v1/payments/create/`,
        {
          plan_id: plan.id,
          gateway_id: selectedGateway,
          currency: userPreferredCurrency?.code || 'USD',
        },
        { headers }
      )

      // ذخیره شماره پیش‌فاکتور
      if (response.data.reference_id) {
        setInvoiceNumber(response.data.reference_id)
      }

      if (response.data.payment_url) {
        window.location.href = response.data.payment_url
      } else {
        setError('خطا در ایجاد لینک پرداخت')
      }
    } catch (err: any) {
      console.error('Payment error:', err)
      setError(err.response?.data?.error || 'خطا در پردازش پرداخت')
    } finally {
      setProcessing(false)
    }
  }

  // تبدیل اعداد به فارسی
  const toPersianNumber = (num: number | string) => {
    const persianDigits = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹']
    return String(num).replace(/\d/g, (d) => persianDigits[parseInt(d)])
  }
  
  const formatPrice = (price: number) => toPersianNumber(price.toLocaleString('en-US'))
  
  const taxRate = financialSettings?.tax_rate || 10
  const basePrice = Number(plan?.display_price ?? plan?.price) || 0
  const taxAmount = Math.round(basePrice * taxRate / 100)
  const totalPrice = basePrice + taxAmount

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 dark:bg-gray-900 flex items-center justify-center">
        <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
      </div>
    )
  }

  if (error && !plan) {
    return (
      <div className="min-h-screen bg-gray-100 dark:bg-gray-900 flex items-center justify-center p-4">
        <div className="text-center bg-white dark:bg-gray-800 rounded-lg p-6 shadow max-w-sm">
          <AlertCircle className="w-10 h-10 text-red-500 mx-auto mb-3" />
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">{error}</p>
          <button
            onClick={() => router.push('/chat')}
            className="px-4 py-2 text-sm bg-blue-500 text-white rounded-lg hover:bg-blue-600"
          >
            بازگشت
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900 py-6 px-4" dir="rtl">
      <div className="max-w-md mx-auto">
        
        {/* Header with Logo */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-4 mb-4">
          <div className="flex items-center justify-between">
            <button
              onClick={() => router.back()}
              className="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
            >
              <ArrowRight className="w-5 h-5 text-gray-500" />
            </button>
            <div className="flex items-center gap-2">
              <Image 
                src="/logo.png" 
                alt={siteSettings?.frontend_site_name || 'تجارت چت'} 
                width={28} 
                height={28}
                onError={(e) => { e.currentTarget.style.display = 'none' }}
              />
              <span className="font-bold text-gray-900 dark:text-white">{siteSettings?.frontend_site_name || 'تجارت چت'}</span>
            </div>
            <div className="w-8" />
          </div>
        </div>

        {/* Invoice Card */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm overflow-hidden mb-4">
          {/* Invoice Header */}
          <div className="bg-gradient-to-l from-blue-500 to-blue-600 px-4 py-3">
            <div className="flex items-center justify-between">
              <h1 className="text-white font-medium text-sm">پیش‌فاکتور خرید اشتراک</h1>
              {invoiceNumber && (
                <span className="text-white/90 text-xs font-mono">#{invoiceNumber}</span>
              )}
            </div>
          </div>
          
          {/* Seller Info */}
          <div className="px-4 py-3 border-b border-gray-100 dark:border-gray-700">
            <div className="flex items-start gap-2">
              <Building2 className="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
              <div className="text-xs text-gray-600 dark:text-gray-400">
                <p className="font-medium text-gray-900 dark:text-white mb-1">
                  {financialSettings?.company_name || 'تجارت چت'}
                </p>
                {financialSettings?.company_address && (
                  <p className="leading-relaxed">{financialSettings.company_address}</p>
                )}
                {financialSettings?.economic_code && (
                  <p className="mt-1">کد اقتصادی: {financialSettings.economic_code}</p>
                )}
              </div>
            </div>
          </div>

          {/* Plan Details */}
          {plan && (
            <div className="px-4 py-3">
              <table className="w-full text-xs">
                <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                  <tr>
                    <td className="py-2 text-gray-500">شرح</td>
                    <td className="py-2 text-left font-medium text-gray-900 dark:text-white">{plan.name}</td>
                  </tr>
                  <tr>
                    <td className="py-2 text-gray-500">مدت</td>
                    <td className="py-2 text-left text-gray-700 dark:text-gray-300">{toPersianNumber(plan.duration_days)} روز</td>
                  </tr>
                  <tr>
                    <td className="py-2 text-gray-500">سهمیه روزانه</td>
                    <td className="py-2 text-left text-gray-700 dark:text-gray-300">{toPersianNumber(plan.max_queries_per_day)} سوال</td>
                  </tr>
                  <tr>
                    <td className="py-2 text-gray-500">سهمیه ماهانه</td>
                    <td className="py-2 text-left text-gray-700 dark:text-gray-300">{toPersianNumber(plan.max_queries_per_month)} سوال</td>
                  </tr>
                </tbody>
              </table>
              
              {/* Price Breakdown */}
              <div className="mt-3 pt-3 border-t border-gray-100 dark:border-gray-700 space-y-2">
                <div className="flex justify-between text-xs">
                  <span className="text-gray-500">مبلغ پایه</span>
                  <span className="text-gray-700 dark:text-gray-300">{formatPrice(basePrice)} تومان</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-gray-500">مالیات ارزش افزوده ({toPersianNumber(taxRate)}٪)</span>
                  <span className="text-gray-700 dark:text-gray-300">{formatPrice(taxAmount)} تومان</span>
                </div>
                <div className="flex justify-between pt-2 border-t border-gray-200 dark:border-gray-600">
                  <span className="text-sm font-medium text-gray-900 dark:text-white">جمع کل</span>
                  <span className="text-sm font-bold text-blue-600 dark:text-blue-400">{formatPrice(totalPrice)} تومان</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Payment Gateway */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-4 mb-4">
          <h2 className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-3">درگاه پرداخت</h2>
          
          {gateways.length > 0 ? (
            <div className="space-y-2">
              {gateways.map((gateway) => (
                <label
                  key={gateway.id}
                  className={`flex items-center gap-3 p-3 border rounded-lg cursor-pointer transition-all text-sm ${
                    selectedGateway === gateway.id
                      ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                  }`}
                >
                  <input
                    type="radio"
                    name="gateway"
                    checked={selectedGateway === gateway.id}
                    onChange={() => setSelectedGateway(gateway.id)}
                    className="w-4 h-4 text-blue-500"
                  />
                  <CreditCard className="w-4 h-4 text-gray-400" />
                  <span className="text-gray-900 dark:text-white">{gateway.name}</span>
                </label>
              ))}
            </div>
          ) : (
            <div className="text-center py-4 text-xs text-gray-500">
              <AlertCircle className="w-8 h-8 mx-auto mb-2 text-yellow-500" />
              درگاه پرداختی فعال نیست
            </div>
          )}
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3 mb-4">
            <div className="flex items-center gap-2 text-xs text-red-600 dark:text-red-400">
              <AlertCircle className="w-4 h-4" />
              <span>{error}</span>
            </div>
          </div>
        )}

        {/* Pay Button */}
        <button
          onClick={handlePayment}
          disabled={!selectedGateway || processing || gateways.length === 0}
          className={`w-full py-3 rounded-lg font-medium text-sm transition-all flex items-center justify-center gap-2 ${
            selectedGateway && !processing && gateways.length > 0
              ? 'bg-green-500 hover:bg-green-600 text-white'
              : 'bg-gray-200 dark:bg-gray-700 text-gray-400 cursor-not-allowed'
          }`}
        >
          {processing ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              در حال پردازش...
            </>
          ) : (
            <>
              <CheckCircle className="w-4 h-4" />
              پرداخت {formatPrice(totalPrice)} تومان
            </>
          )}
        </button>

        {/* Security Note */}
        <div className="flex items-center justify-center gap-1.5 mt-3 text-xs text-gray-400">
          <Shield className="w-3.5 h-3.5" />
          <span>پرداخت امن از طریق درگاه بانکی</span>
        </div>
      </div>
    </div>
  )
}
