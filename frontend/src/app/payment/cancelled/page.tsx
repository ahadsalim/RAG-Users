'use client'

import { useRouter } from 'next/navigation'
import { AlertCircle, ArrowRight, RefreshCw } from 'lucide-react'

export default function PaymentCancelledPage() {
  const router = useRouter()

  const handleRetry = () => {
    router.push('/checkout')
  }

  const handleGoHome = () => {
    router.push('/chat')
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-yellow-50 to-orange-50 flex items-center justify-center p-4" dir="rtl">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8 text-center">
        <div className="mb-6">
          <AlertCircle className="w-20 h-20 text-yellow-500 mx-auto" />
        </div>
        
        <h1 className="text-2xl font-bold text-gray-800 mb-2">
          پرداخت لغو شد
        </h1>
        
        <p className="text-gray-600 mb-6">
          شما پرداخت را لغو کردید. هیچ مبلغی از حساب شما کسر نشده است.
        </p>

        <div className="space-y-3">
          <button
            onClick={handleRetry}
            className="w-full bg-blue-500 hover:bg-blue-600 text-white font-semibold py-3 px-6 rounded-lg transition-colors flex items-center justify-center gap-2"
          >
            <RefreshCw className="w-5 h-5" />
            <span>تلاش مجدد</span>
          </button>

          <button
            onClick={handleGoHome}
            className="w-full bg-gray-200 hover:bg-gray-300 text-gray-700 font-semibold py-3 px-6 rounded-lg transition-colors flex items-center justify-center gap-2"
          >
            <span>بازگشت به صفحه اصلی</span>
            <ArrowRight className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  )
}
