'use client'

import { useRouter, useSearchParams } from 'next/navigation'
import { XCircle, ArrowRight, RefreshCw } from 'lucide-react'

export default function PaymentErrorPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  
  const message = searchParams.get('message') || 'خطای نامشخص در پردازش پرداخت'

  const handleRetry = () => {
    router.push('/checkout')
  }

  const handleGoHome = () => {
    router.push('/chat')
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-red-50 to-orange-50 flex items-center justify-center p-4" dir="rtl">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8 text-center">
        <div className="mb-6">
          <XCircle className="w-20 h-20 text-red-500 mx-auto" />
        </div>
        
        <h1 className="text-2xl font-bold text-gray-800 mb-2">
          خطا در پرداخت
        </h1>
        
        <p className="text-gray-600 mb-6">
          متأسفانه پرداخت شما با خطا مواجه شد.
        </p>

        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <p className="text-sm text-red-700">
            {decodeURIComponent(message)}
          </p>
        </div>

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

        <p className="text-xs text-gray-500 mt-6">
          در صورت کسر وجه از حساب شما، مبلغ ظرف 72 ساعت به حساب شما بازگردانده خواهد شد.
        </p>
      </div>
    </div>
  )
}
