'use client'

import { useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import toast, { Toaster } from 'react-hot-toast'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://admin.tejarat.chat'

export default function VerifyEmailPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [isVerifying, setIsVerifying] = useState(true)
  const [isSuccess, setIsSuccess] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')
  const [theme, setTheme] = useState<'light' | 'dark'>('dark')

  // Load theme from localStorage
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') as 'light' | 'dark' | null
    if (savedTheme) {
      setTheme(savedTheme)
    }
  }, [])

  useEffect(() => {
    const verifyEmail = async () => {
      const token = searchParams.get('token')
      const user = searchParams.get('user')

      if (!token || !user) {
        setIsVerifying(false)
        setErrorMessage('لینک تایید نامعتبر است')
        toast.error('لینک تایید نامعتبر است')
        return
      }

      try {
        const response = await fetch(
          `${API_URL}/api/v1/auth/verify-email/?token=${token}&user=${user}`
        )

        const data = await response.json()

        if (response.ok) {
          setIsSuccess(true)
          toast.success('ایمیل شما با موفقیت تایید شد!')
          setTimeout(() => {
            router.push('/auth/login')
          }, 2000)
        } else {
          setErrorMessage(data.error || 'خطا در تایید ایمیل')
          toast.error(data.error || 'خطا در تایید ایمیل')
        }
      } catch (err) {
        setErrorMessage('خطا در ارتباط با سرور')
        toast.error('خطا در ارتباط با سرور')
      } finally {
        setIsVerifying(false)
      }
    }

    verifyEmail()
  }, [searchParams, router])

  const styles = {
    container: {
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: theme === 'light'
        ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
        : 'linear-gradient(135deg, #1a202c 0%, #2d3748 100%)',
      fontFamily: 'IRANSans, Vazirmatn, -apple-system, BlinkMacSystemFont, sans-serif',
      padding: '20px'
    },
    card: {
      background: theme === 'light'
        ? 'rgba(255, 255, 255, 0.15)'
        : 'rgba(45, 55, 72, 0.6)',
      backdropFilter: 'blur(20px)',
      borderRadius: '20px',
      padding: '40px',
      width: '100%',
      maxWidth: '450px',
      boxShadow: theme === 'light'
        ? '0 20px 60px rgba(0, 0, 0, 0.3)'
        : '0 20px 60px rgba(0, 0, 0, 0.5)',
      border: theme === 'light'
        ? '1px solid rgba(255, 255, 255, 0.3)'
        : '1px solid rgba(113, 128, 150, 0.3)',
      textAlign: 'center' as const
    },
    icon: {
      fontSize: '64px',
      marginBottom: '20px'
    },
    title: {
      fontSize: '24px',
      fontWeight: '700',
      color: theme === 'light' ? '#fff' : '#e2e8f0',
      marginBottom: '12px'
    },
    message: {
      fontSize: '16px',
      color: theme === 'light' ? 'rgba(255, 255, 255, 0.9)' : '#cbd5e0',
      marginBottom: '30px',
      lineHeight: '1.6'
    },
    spinner: {
      border: '4px solid rgba(255, 255, 255, 0.3)',
      borderTop: '4px solid #fff',
      borderRadius: '50%',
      width: '50px',
      height: '50px',
      animation: 'spin 1s linear infinite',
      margin: '0 auto 20px'
    },
    button: {
      width: '100%',
      padding: '12px',
      borderRadius: '10px',
      border: 'none',
      background: theme === 'light'
        ? 'rgba(255, 255, 255, 0.95)'
        : 'rgba(226, 232, 240, 0.95)',
      color: theme === 'light' ? '#667eea' : '#1a202c',
      fontSize: '16px',
      fontWeight: '600',
      cursor: 'pointer',
      transition: 'all 0.3s ease',
      boxShadow: '0 4px 12px rgba(0,0,0,0.2)',
      textDecoration: 'none',
      display: 'inline-block'
    }
  }

  return (
    <>
      <style jsx>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
      <Toaster position="top-center" />
      <div style={styles.container}>
        <div style={styles.card}>
          {isVerifying && (
            <>
              <div style={styles.spinner}></div>
              <div style={styles.title}>در حال تایید ایمیل...</div>
              <div style={styles.message}>لطفا صبر کنید</div>
            </>
          )}

          {!isVerifying && isSuccess && (
            <>
              <div style={styles.icon}>✅</div>
              <div style={styles.title}>ایمیل تایید شد!</div>
              <div style={styles.message}>
                ایمیل شما با موفقیت تایید شد. اکنون می‌توانید وارد حساب کاربری خود شوید.
              </div>
              <Link href="/auth/login" style={styles.button}>
                ورود به حساب کاربری
              </Link>
            </>
          )}

          {!isVerifying && !isSuccess && (
            <>
              <div style={styles.icon}>❌</div>
              <div style={styles.title}>خطا در تایید ایمیل</div>
              <div style={styles.message}>{errorMessage}</div>
              <Link href="/auth/login" style={styles.button}>
                بازگشت به صفحه ورود
              </Link>
            </>
          )}
        </div>
      </div>
    </>
  )
}
