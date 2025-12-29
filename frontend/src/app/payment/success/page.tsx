'use client'

import { useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { CheckCircle, ArrowRight } from 'lucide-react'

export default function PaymentSuccessPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [countdown, setCountdown] = useState(5)

  const refId = searchParams.get('ref_id')
  const transactionId = searchParams.get('transaction_id')

  useEffect(() => {
    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(timer)
          router.push('/chat')
          return 0
        }
        return prev - 1
      })
    }, 1000)

    return () => clearInterval(timer)
  }, [router])

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 flex items-center justify-center p-4" dir="rtl">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8 text-center">
        <div className="mb-6">
          <CheckCircle className="w-20 h-20 text-green-500 mx-auto animate-bounce" />
        </div>
        
        <h1 className="text-2xl font-bold text-gray-800 mb-2">
          پرداخت موفق
        </h1>
        
        <p className="text-gray-600 mb-6">
          پرداخت شما با موفقیت انجام شد و اشتراک شما فعال گردید.
        </p>

        {refId && (
          <div className="bg-gray-50 rounded-lg p-4 mb-6">
            <p className="text-sm text-gray-500 mb-1">کد پیگیری</p>
            <p className="text-lg font-mono font-semibold text-gray-800">{refId}</p>
          </div>
        )}

        {transactionId && (
          <div className="bg-gray-50 rounded-lg p-4 mb-6">
            <p className="text-sm text-gray-500 mb-1">شناسه تراکنش</p>
            <p className="text-xs font-mono text-gray-600">{transactionId}</p>
          </div>
        )}

        <div className="mb-6">
          <p className="text-sm text-gray-500">
            انتقال به صفحه چت در {countdown} ثانیه...
          </p>
        </div>

        <button
          onClick={() => router.push('/chat')}
          className="w-full bg-green-500 hover:bg-green-600 text-white font-semibold py-3 px-6 rounded-lg transition-colors flex items-center justify-center gap-2"
        >
          <span>رفتن به چت</span>
          <ArrowRight className="w-5 h-5" />
        </button>
      </div>
    </div>
  )
}
