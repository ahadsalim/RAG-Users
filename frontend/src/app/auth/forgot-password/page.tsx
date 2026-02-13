'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import toast from 'react-hot-toast'
import { SiteSubtitle } from '@/components/SiteName'

const API_URL = process.env.NEXT_PUBLIC_API_URL || ''

export default function ForgotPasswordPage() {
  const router = useRouter()
  const [theme, setTheme] = useState<'light' | 'dark'>('light')
  const [isLoading, setIsLoading] = useState(false)
  const [emailSent, setEmailSent] = useState(false)
  
  // Load theme from localStorage
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') as 'light' | 'dark' | null
    if (savedTheme) {
      setTheme(savedTheme)
    }
  }, [])
  
  const handleThemeToggle = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light'
    setTheme(newTheme)
    localStorage.setItem('theme', newTheme)
  }
  
  const [cacheVersion] = useState(() => Date.now())
  const [email, setEmail] = useState('')

  const handleSubmit = async (e: any) => {
    e.preventDefault()
    
    if (!email) {
      toast.error('لطفا ایمیل خود را وارد کنید')
      return
    }
    
    setIsLoading(true)
    
    try {
      const response = await fetch(`${API_URL}/api/v1/auth/forgot-password/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email })
      })
      
      
      if (response.ok) {
        const data = await response.json()
        setEmailSent(true)
        toast.success('لینک بازیابی رمز عبور به ایمیل شما ارسال شد')
      } else {
        const data = await response.json()
        console.error('Error response:', data)
        toast.error(data.message || 'خطا در ارسال ایمیل')
      }
    } catch (err) {
      console.error('Fetch error:', err)
      toast.error('خطا در ارتباط با سرور')
    } finally {
      setIsLoading(false)
    }
  }

  const styles = {
    container: {
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: theme === 'light' 
        ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
        : 'linear-gradient(135deg, #1a202c 0%, #2d3748 100%)',
      padding: '20px',
      direction: 'rtl' as const,
      transition: 'all 0.5s ease'
    },
    card: {
      width: '100%',
      maxWidth: '420px',
      borderRadius: '16px',
      boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
      padding: '30px',
      background: theme === 'light'
        ? 'rgba(255, 255, 255, 0.2)'
        : 'rgba(45, 55, 72, 0.4)',
      backdropFilter: 'blur(20px)',
      border: theme === 'light'
        ? '1px solid rgba(255, 255, 255, 0.3)'
        : '1px solid rgba(113, 128, 150, 0.3)',
      transition: 'all 0.5s ease'
    },
    header: {
      display: 'flex',
      flexDirection: 'column' as const,
      alignItems: 'center',
      marginBottom: '20px',
      gap: '12px'
    },
    headerTop: {
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      width: '100%',
      position: 'relative' as const
    },
    logoContainer: {
      display: 'flex',
      flexDirection: 'column' as const,
      justifyContent: 'center',
      alignItems: 'center',
      marginBottom: '8px',
      gap: '8px'
    },
    subtitle: {
      fontSize: '16px',
      fontWeight: '600',
      color: theme === 'light' ? '#fff' : '#e2e8f0',
      margin: 0,
      fontFamily: 'IRANSans, Vazirmatn, sans-serif',
      textShadow: '0 2px 4px rgba(0,0,0,0.2)',
      letterSpacing: '0.5px'
    },
    title: {
      fontSize: '24px',
      fontWeight: 'bold',
      color: theme === 'light' ? '#fff' : '#e2e8f0',
      margin: 0,
      textShadow: '0 2px 4px rgba(0,0,0,0.1)'
    },
    themeBtn: {
      position: 'absolute' as const,
      top: '-10px',
      left: '0',
      padding: '8px',
      borderRadius: '50%',
      border: theme === 'light' 
        ? '1px solid rgba(255, 255, 255, 0.4)'
        : '1px solid #4a5568',
      background: theme === 'light'
        ? 'rgba(255, 255, 255, 0.3)'
        : '#2d3748',
      color: theme === 'light' ? '#fff' : '#e2e8f0',
      cursor: 'pointer',
      fontSize: '20px',
      transition: 'all 0.3s ease',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      width: '40px',
      height: '40px'
    },
    form: {
      display: 'flex',
      flexDirection: 'column' as const,
      gap: '16px'
    },
    inputGroup: {
      display: 'flex',
      flexDirection: 'column' as const,
      gap: '6px'
    },
    inputGroupRow: {
      display: 'flex',
      alignItems: 'center',
      gap: '12px'
    },
    labelInline: {
      fontSize: '14px',
      fontWeight: '500',
      color: theme === 'light' ? '#fff' : '#cbd5e0',
      minWidth: '75px',
      whiteSpace: 'nowrap' as const
    },
    input: {
      width: '100%',
      padding: '10px 14px',
      borderRadius: '8px',
      border: theme === 'light'
        ? '1px solid rgba(255, 255, 255, 0.3)'
        : '1px solid rgba(113, 128, 150, 0.3)',
      background: theme === 'light'
        ? 'rgba(255, 255, 255, 0.2)'
        : 'rgba(45, 55, 72, 0.5)',
      color: theme === 'light' ? '#fff' : '#e2e8f0',
      fontSize: '14px',
      outline: 'none',
      transition: 'all 0.3s ease',
      boxSizing: 'border-box' as const,
      backdropFilter: 'blur(10px)'
    },
    submitBtn: {
      width: '100%',
      padding: '12px',
      borderRadius: '8px',
      border: 'none',
      background: theme === 'light'
        ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
        : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      color: '#fff',
      fontSize: '15px',
      fontWeight: '600',
      cursor: isLoading ? 'not-allowed' : 'pointer',
      opacity: isLoading ? 0.5 : 1,
      boxShadow: '0 4px 15px rgba(102, 126, 234, 0.4)',
      transition: 'all 0.3s ease'
    },
    successBox: {
      padding: '16px',
      borderRadius: '8px',
      background: 'rgba(72, 187, 120, 0.2)',
      border: '1px solid rgba(72, 187, 120, 0.3)',
      color: theme === 'light' ? '#fff' : '#e2e8f0',
      fontSize: '14px',
      textAlign: 'center' as const,
      lineHeight: '1.6'
    },
    link: {
      color: theme === 'light' ? 'rgba(255, 255, 255, 0.9)' : '#a0aec0',
      textDecoration: 'none',
      fontSize: '14px',
      textAlign: 'center' as const,
      marginTop: '16px',
      display: 'block'
    }
  }

  return (
    <>
      <style>{`
        input::placeholder {
          color: ${theme === 'light' ? 'rgba(255, 255, 255, 0.6)' : '#a0aec0'} !important;
          opacity: 1;
        }
        body::before {
          content: '${cacheVersion}';
          display: none;
        }
      `}</style>
      <div style={styles.container}>
        <div style={styles.card}>
          <div style={styles.header}>
            <div style={styles.logoContainer}>
              <img 
                src={`/logo-small.png?v=${cacheVersion}`}
                alt="Logo" 
                width={70} 
                height={70}
                style={{ objectFit: 'contain' }}
              />
              <SiteSubtitle style={styles.subtitle} />
            </div>
            
            <div style={styles.headerTop}>
              <h2 style={styles.title}>بازیابی رمز عبور</h2>
              <button
                type="button"
                style={styles.themeBtn}
                onClick={handleThemeToggle}
                title={theme === 'light' ? 'حالت تاریک' : 'حالت روشن'}
              >
                {theme === 'light' ? '🌙' : '☀️'}
              </button>
            </div>
          </div>

          {!emailSent ? (
            <form style={styles.form} onSubmit={handleSubmit}>
              <div style={styles.inputGroup}>
                <div style={styles.inputGroupRow}>
                  <label style={styles.labelInline}>ایمیل</label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="ایمیل خود را وارد کنید"
                    style={{...styles.input, flex: 1}}
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                style={styles.submitBtn}
              >
                {isLoading ? 'در حال ارسال...' : 'ارسال لینک بازیابی'}
              </button>
            </form>
          ) : (
            <div style={styles.successBox}>
              ✅ لینک بازیابی رمز عبور به ایمیل شما ارسال شد.
              <br />
              لطفا ایمیل خود را بررسی کنید.
            </div>
          )}

          <Link href="/auth/login" style={styles.link}>
            بازگشت به صفحه ورود
          </Link>
        </div>
      </div>
    </>
  )
}
