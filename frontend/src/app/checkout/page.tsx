'use client'

import { useState, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { ArrowRight, CreditCard, CheckCircle, AlertCircle, Loader2 } from 'lucide-react'
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || ''

interface Plan {
  id: string
  name: string
  description: string
  price: number
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

export default function CheckoutPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const planId = searchParams.get('plan')
  
  const [plan, setPlan] = useState<Plan | null>(null)
  const [gateways, setGateways] = useState<PaymentGateway[]>([])
  const [selectedGateway, setSelectedGateway] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [processing, setProcessing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchData = async () => {
      if (!planId) {
        setError('پلن انتخاب نشده است')
        setLoading(false)
        return
      }

      try {
        // Get token from zustand persist storage
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

        // Fetch payment gateways
        const gatewaysResponse = await axios.get(`${API_URL}/api/v1/payments/gateways/`, { headers })
        const activeGateways = gatewaysResponse.data.filter((g: PaymentGateway) => g.is_active)
        setGateways(activeGateways)
        
        // Auto-select first gateway
        if (activeGateways.length > 0) {
          setSelectedGateway(activeGateways[0].id)
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
  }, [planId, router])

  const handlePayment = async () => {
    if (!selectedGateway || !plan) return

    setProcessing(true)
    setError(null)

    try {
      // Get token from zustand persist storage
      let token = null
      const authStorage = localStorage.getItem('auth-storage')
      if (authStorage) {
        try {
          const parsed = JSON.parse(authStorage)
          token = parsed?.state?.accessToken
        } catch (e) {}
      }
      const headers = { Authorization: `Bearer ${token}` }

      // Create payment request
      const response = await axios.post(
        `${API_URL}/api/v1/payments/create/`,
        {
          plan_id: plan.id,
          gateway_id: selectedGateway,
        },
        { headers }
      )

      // Redirect to payment gateway
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

  const formatPrice = (price: number) => {
    return price.toLocaleString('fa-IR')
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    )
  }

  if (error && !plan) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400 mb-4">{error}</p>
          <button
            onClick={() => router.push('/chat')}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
          >
            بازگشت
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8 px-4" dir="rtl">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          <button
            onClick={() => router.back()}
            className="p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            <ArrowRight className="w-6 h-6 text-gray-600 dark:text-gray-400" />
          </button>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">پیش‌فاکتور</h1>
        </div>

        {/* Plan Details Card */}
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">جزئیات پلن</h2>
          
          {plan && (
            <div className="space-y-4">
              <div className="flex justify-between items-center py-3 border-b border-gray-200 dark:border-gray-700">
                <span className="text-gray-600 dark:text-gray-400">نام پلن</span>
                <span className="font-semibold text-gray-900 dark:text-white">{plan.name}</span>
              </div>
              
              <div className="flex justify-between items-center py-3 border-b border-gray-200 dark:border-gray-700">
                <span className="text-gray-600 dark:text-gray-400">مدت اعتبار</span>
                <span className="font-semibold text-gray-900 dark:text-white">{plan.duration_days} روز</span>
              </div>
              
              <div className="flex justify-between items-center py-3 border-b border-gray-200 dark:border-gray-700">
                <span className="text-gray-600 dark:text-gray-400">سوال در روز</span>
                <span className="font-semibold text-gray-900 dark:text-white">{plan.max_queries_per_day}</span>
              </div>
              
              <div className="flex justify-between items-center py-3 border-b border-gray-200 dark:border-gray-700">
                <span className="text-gray-600 dark:text-gray-400">سوال در ماه</span>
                <span className="font-semibold text-gray-900 dark:text-white">{plan.max_queries_per_month}</span>
              </div>
              
              <div className="flex justify-between items-center py-4 bg-blue-50 dark:bg-blue-900/20 rounded-xl px-4 -mx-2">
                <span className="text-lg font-semibold text-gray-900 dark:text-white">مبلغ قابل پرداخت</span>
                <span className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                  {plan.formatted_price || `${formatPrice(plan.price)} ${plan.currency_symbol || 'تومان'}`}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Payment Gateway Selection */}
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">انتخاب درگاه پرداخت</h2>
          
          {gateways.length > 0 ? (
            <div className="space-y-3">
              {gateways.map((gateway) => (
                <label
                  key={gateway.id}
                  className={`flex items-center gap-4 p-4 border-2 rounded-xl cursor-pointer transition-all ${
                    selectedGateway === gateway.id
                      ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                      : 'border-gray-200 dark:border-gray-700 hover:border-blue-300'
                  }`}
                >
                  <input
                    type="radio"
                    name="gateway"
                    value={gateway.id}
                    checked={selectedGateway === gateway.id}
                    onChange={() => setSelectedGateway(gateway.id)}
                    className="w-5 h-5 text-blue-500"
                  />
                  <CreditCard className="w-6 h-6 text-gray-500" />
                  <span className="font-medium text-gray-900 dark:text-white">{gateway.name}</span>
                </label>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <AlertCircle className="w-12 h-12 mx-auto mb-2 text-yellow-500" />
              <p>درگاه پرداختی فعال نیست</p>
            </div>
          )}
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-4 mb-6">
            <div className="flex items-center gap-2 text-red-600 dark:text-red-400">
              <AlertCircle className="w-5 h-5" />
              <span>{error}</span>
            </div>
          </div>
        )}

        {/* Payment Button */}
        <button
          onClick={handlePayment}
          disabled={!selectedGateway || processing || gateways.length === 0}
          className={`w-full py-4 rounded-xl font-semibold text-lg transition-all flex items-center justify-center gap-2 ${
            selectedGateway && !processing && gateways.length > 0
              ? 'bg-green-500 hover:bg-green-600 text-white'
              : 'bg-gray-300 dark:bg-gray-700 text-gray-500 cursor-not-allowed'
          }`}
        >
          {processing ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              در حال پردازش...
            </>
          ) : (
            <>
              <CheckCircle className="w-5 h-5" />
              پرداخت و فعال‌سازی
            </>
          )}
        </button>

        {/* Security Note */}
        <p className="text-center text-sm text-gray-500 dark:text-gray-400 mt-4">
          پرداخت شما از طریق درگاه امن بانکی انجام می‌شود
        </p>
      </div>
    </div>
  )
}
