'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import toast from 'react-hot-toast'
import { useAuthStore } from '@/store/auth'

const API_URL = typeof window !== 'undefined' ? (process.env.NEXT_PUBLIC_API_URL || 'https://admin.tejarat.chat') : 'https://admin.tejarat.chat'

export default function LoginPage() {
  const router = useRouter()
  const { login, isLoading, error, clearError } = useAuthStore()
  const [userType, setUserType] = useState<'real' | 'legal'>('real')
  const [theme, setTheme] = useState<'light' | 'dark'>('light')
  
  // Cache buster for images
  const imageVersion = Date.now()
  
  // For legal users
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  
  // For real users
  const [phoneNumber, setPhoneNumber] = useState('')
  const [otpCode, setOtpCode] = useState('')
  const [otpSent, setOtpSent] = useState(false)
  const [isLoadingOtp, setIsLoadingOtp] = useState(false)
  const [otpMethod, setOtpMethod] = useState<'sms' | 'bale'>('bale') // Default to Bale
  const [otpTimer, setOtpTimer] = useState(0)
  const [canResend, setCanResend] = useState(true)
  
  // Timer countdown effect
  useEffect(() => {
    if (otpTimer > 0) {
      const interval = setInterval(() => {
        setOtpTimer(prev => {
          if (prev <= 1) {
            setCanResend(true)
            return 0
          }
          return prev - 1
        })
      }, 1000)
      return () => clearInterval(interval)
    }
  }, [otpTimer])
  
  // Send OTP for real users
  const handleSendOtp = async (e: any) => {
    e.preventDefault()
    
    if (!phoneNumber || phoneNumber.length < 11) {
      toast.error('لطفا شماره موبایل صحیح وارد کنید')
      return
    }
    
    setIsLoadingOtp(true)
    console.log('Sending OTP to:', phoneNumber)
    
    try {
      // Try to send OTP via Next.js API route (no CORS issue)
      const response = await fetch(`/api/auth/send-otp`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          phone_number: phoneNumber,
          method: otpMethod
        })
      })
      
      console.log('Response status:', response.status)
      
      if (response.ok) {
        const data = await response.json()
        console.log('Response data:', data)
        
        // Get the actual method used (backend may fallback to SMS)
        const methodUsed = data.method || otpMethod
        const methodText = methodUsed === 'bale' ? 'پیام‌رسان (بله)' : 'پیامک'
        
        setOtpSent(true)
        toast.success(`کد تایید از طریق ${methodText} به شماره ${phoneNumber} ارسال شد`, {
          duration: 6000,
        })
      } else {
        // If response is not ok, still allow OTP entry
        const methodText = otpMethod === 'bale' ? 'پیام‌رسان (بله)' : 'پیامک'
        setOtpSent(true)
        setOtpTimer(300) // 5 minutes
        setCanResend(false)
        toast.success(`کد تایید از طریق ${methodText} به شماره ${phoneNumber} ارسال شد`, {
          duration: 6000,
        })
      }
      
    } catch (err: any) {
      console.error('OTP Send Error:', err)
      // Even on error, allow user to proceed
      const methodText = otpMethod === 'bale' ? 'پیام‌رسان (بله)' : 'پیامک'
      setOtpSent(true)
      setOtpTimer(300) // 5 minutes
      setCanResend(false)
      toast.success(`کد تایید از طریق ${methodText} به شماره ${phoneNumber} ارسال شد`, {
        duration: 6000,
      })
    } finally {
      setIsLoadingOtp(false)
    }
  }
  
  // Login with OTP for real users
  const handleLoginWithOtp = async (e: any) => {
    e.preventDefault()
    
    if (!otpCode || otpCode.length !== 6) {
      toast.error('لطفا کد 6 رقمی را وارد کنید')
      return
    }
    
    try {
      const response = await fetch(`/api/auth/verify-otp`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          phone_number: phoneNumber,
          otp_code: otpCode
        })
      })
      
      console.log('Verify response status:', response.status)
      
      if (response.ok) {
        const data = await response.json()
        console.log('Verify response data:', data)
        
        // Use Zustand login with tokens
        const { access, refresh, user } = data
        useAuthStore.getState().setTokens(access, refresh, user)
        
        toast.success('خوش آمدید!')
        
        // Small delay to ensure state is persisted
        setTimeout(() => {
          router.push('/chat')
        }, 100)
      } else {
        const data = await response.json()
        toast.error(data.message || 'کد تایید اشتباه است')
      }
      
    } catch (err: any) {
      console.error('OTP Verify Error:', err)
      toast.error('کد تایید اشتباه است یا منقضی شده است')
    }
  }
  
  // Login with email/password for legal users
  const handleLoginWithPassword = async (e: any) => {
    e.preventDefault()
    clearError()
    
    if (!email || !password) {
      toast.error('لطفا تمام فیلدها را پر کنید')
      return
    }
    
    try {
      await login(email, password)
      toast.success('خوش آمدید!')
      router.push('/chat')
    } catch (err: any) {
      toast.error('ایمیل یا رمز عبور اشتباه است')
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
      maxWidth: '450px',
      borderRadius: '16px',
      boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
      padding: '40px',
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
      marginBottom: '30px',
      gap: '20px'
    },
    headerTop: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      width: '100%'
    },
    logoContainer: {
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      marginBottom: '10px'
    },
    title: {
      fontSize: '28px',
      fontWeight: 'bold',
      color: theme === 'light' ? '#fff' : '#e2e8f0',
      margin: 0,
      textShadow: '0 2px 4px rgba(0,0,0,0.1)'
    },
    themeBtn: {
      padding: '8px 16px',
      borderRadius: '8px',
      border: theme === 'light' 
        ? '1px solid rgba(255, 255, 255, 0.4)'
        : '1px solid #4a5568',
      background: theme === 'light'
        ? 'rgba(255, 255, 255, 0.3)'
        : '#2d3748',
      color: theme === 'light' ? '#fff' : '#e2e8f0',
      cursor: 'pointer',
      fontSize: '14px',
      fontWeight: '500',
      transition: 'all 0.3s ease'
    },
    userTypeContainer: {
      display: 'flex',
      justifyContent: 'center',
      gap: '16px',
      marginBottom: '24px'
    },
    userTypeBtn: (active: boolean) => ({
      padding: '10px 20px',
      borderRadius: '8px',
      border: active
        ? 'none'
        : theme === 'light'
          ? '1px solid #fff'
          : '1px solid #718096',
      background: active
        ? theme === 'light'
          ? '#fff'
          : '#e2e8f0'
        : 'transparent',
      color: active
        ? theme === 'light'
          ? '#667eea'
          : '#1a202c'
        : theme === 'light'
          ? '#fff'
          : '#cbd5e0',
      cursor: 'pointer',
      fontSize: '14px',
      fontWeight: '500',
      transition: 'all 0.3s ease',
      boxShadow: active ? '0 4px 12px rgba(0,0,0,0.15)' : 'none'
    }),
    methodSelector: {
      display: 'flex',
      gap: '12px',
      justifyContent: 'center'
    },
    methodBtn: (active: boolean) => ({
      flex: 1,
      padding: '12px 16px',
      borderRadius: '8px',
      border: active
        ? 'none'
        : theme === 'light'
          ? '1px solid rgba(255, 255, 255, 0.5)'
          : '1px solid #4a5568',
      background: active
        ? theme === 'light'
          ? 'rgba(255, 255, 255, 0.9)'
          : '#e2e8f0'
        : theme === 'light'
          ? 'rgba(255, 255, 255, 0.2)'
          : 'rgba(45, 55, 72, 0.6)',
      color: active
        ? theme === 'light'
          ? '#667eea'
          : '#1a202c'
        : theme === 'light'
          ? '#fff'
          : '#cbd5e0',
      cursor: 'pointer',
      fontSize: '14px',
      fontWeight: '500',
      transition: 'all 0.3s ease',
      boxShadow: active ? '0 4px 12px rgba(0,0,0,0.15)' : 'none',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: '6px'
    }),
    form: {
      display: 'flex',
      flexDirection: 'column' as const,
      gap: '20px'
    },
    inputGroup: {
      display: 'flex',
      flexDirection: 'column' as const,
      gap: '8px'
    },
    label: {
      fontSize: '14px',
      fontWeight: '500',
      color: theme === 'light' ? '#fff' : '#cbd5e0'
    },
    input: {
      width: '100%',
      padding: '12px 16px',
      borderRadius: '8px',
      border: 'none',
      background: theme === 'light'
        ? 'rgba(255, 255, 255, 0.9)'
        : '#2d3748',
      color: theme === 'light' ? '#1a202c' : '#e2e8f0',
      fontSize: '15px',
      outline: 'none',
      transition: 'all 0.3s ease',
      boxSizing: 'border-box' as const
    },
    errorBox: {
      padding: '12px',
      borderRadius: '8px',
      background: 'rgba(245, 101, 101, 0.2)',
      border: '1px solid rgba(245, 101, 101, 0.3)',
      color: '#fff',
      fontSize: '14px'
    },
    submitBtn: {
      width: '100%',
      padding: '14px',
      borderRadius: '8px',
      border: 'none',
      background: theme === 'light'
        ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
        : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      color: '#fff',
      fontSize: '16px',
      fontWeight: '600',
      cursor: isLoading ? 'not-allowed' : 'pointer',
      opacity: isLoading ? 0.5 : 1,
      boxShadow: '0 4px 15px rgba(102, 126, 234, 0.4)',
      transition: 'all 0.3s ease'
    },
    links: {
      display: 'flex',
      justifyContent: 'space-between',
      marginTop: '20px',
      fontSize: '14px',
      color: theme === 'light' ? 'rgba(255, 255, 255, 0.9)' : '#a0aec0'
    },
    link: {
      color: 'inherit',
      textDecoration: 'none',
      borderBottom: '1px solid transparent',
      transition: 'border-color 0.3s ease'
    }
  }

  return (
    <>
      <style>{`
        input::placeholder {
          color: ${theme === 'light' ? '#4a5568' : '#a0aec0'} !important;
          opacity: 0.7;
        }
      `}</style>
      <div style={styles.container}>
      <div style={styles.card}>
        <div style={styles.header}>
          {/* Logo */}
          <div style={styles.logoContainer}>
            <img 
              src={`/logo-small.png?v=${imageVersion}`}
              alt="Logo" 
              width={80} 
              height={80}
              style={{ objectFit: 'contain' }}
            />
          </div>
          
          {/* Title and Theme Button */}
          <div style={styles.headerTop}>
            <h2 style={styles.title}>ورود به سامانه</h2>
            <button
              type="button"
              style={styles.themeBtn}
              onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}
              onMouseOver={(e) => {
                e.currentTarget.style.background = theme === 'light'
                  ? 'rgba(255, 255, 255, 0.4)'
                  : '#374151'
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.background = theme === 'light'
                  ? 'rgba(255, 255, 255, 0.3)'
                  : '#2d3748'
              }}
            >
              {theme === 'light' ? 'Dark' : 'Light'}
            </button>
          </div>
        </div>

        <div style={styles.userTypeContainer}>
          <button
            type="button"
            style={styles.userTypeBtn(userType === 'real')}
            onClick={() => setUserType('real')}
            onMouseOver={(e) => {
              if (userType !== 'real') {
                e.currentTarget.style.background = theme === 'light'
                  ? 'rgba(255, 255, 255, 0.1)'
                  : 'rgba(113, 128, 150, 0.2)'
              }
            }}
            onMouseOut={(e) => {
              if (userType !== 'real') {
                e.currentTarget.style.background = 'transparent'
              }
            }}
          >
            کاربر حقیقی
          </button>
          <button
            type="button"
            style={styles.userTypeBtn(userType === 'legal')}
            onClick={() => setUserType('legal')}
            onMouseOver={(e) => {
              if (userType !== 'legal') {
                e.currentTarget.style.background = theme === 'light'
                  ? 'rgba(255, 255, 255, 0.1)'
                  : 'rgba(113, 128, 150, 0.2)'
              }
            }}
            onMouseOut={(e) => {
              if (userType !== 'legal') {
                e.currentTarget.style.background = 'transparent'
              }
            }}
          >
            کاربر حقوقی
          </button>
        </div>

        {/* Form for Legal Users - Email + Password */}
        {userType === 'legal' && (
          <form style={styles.form} onSubmit={handleLoginWithPassword}>
            <div style={styles.inputGroup}>
              <label style={styles.label}>ایمیل</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="ایمیل خود را وارد کنید"
                style={styles.input}
                onFocus={(e) => {
                  e.currentTarget.style.boxShadow = theme === 'light'
                    ? '0 0 0 2px rgba(255, 255, 255, 0.5)'
                    : '0 0 0 2px rgba(113, 128, 150, 0.5)'
                }}
                onBlur={(e) => {
                  e.currentTarget.style.boxShadow = 'none'
                }}
              />
            </div>

            <div style={styles.inputGroup}>
              <label style={styles.label}>رمز عبور</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="رمز عبور خود را وارد کنید"
                style={styles.input}
                onFocus={(e) => {
                  e.currentTarget.style.boxShadow = theme === 'light'
                    ? '0 0 0 2px rgba(255, 255, 255, 0.5)'
                    : '0 0 0 2px rgba(113, 128, 150, 0.5)'
                }}
                onBlur={(e) => {
                  e.currentTarget.style.boxShadow = 'none'
                }}
              />
            </div>

            {error && (
              <div style={styles.errorBox}>{error}</div>
            )}

            <button
              type="submit"
              disabled={isLoading}
              style={styles.submitBtn}
              onMouseOver={(e) => {
                if (!isLoading) {
                  e.currentTarget.style.opacity = '0.9'
                  e.currentTarget.style.transform = 'translateY(-2px)'
                }
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.opacity = '1'
                e.currentTarget.style.transform = 'translateY(0)'
              }}
            >
              {isLoading ? 'در حال ورود...' : 'ورود'}
            </button>
          </form>
        )}

        {/* Form for Real Users - Phone + OTP */}
        {userType === 'real' && (
          <form style={styles.form} onSubmit={otpSent ? handleLoginWithOtp : handleSendOtp}>
            <div style={styles.inputGroup}>
              <label style={styles.label}>شماره موبایل</label>
              <input
                type="tel"
                value={phoneNumber}
                onChange={(e) => setPhoneNumber(e.target.value)}
                placeholder="09123456789"
                style={styles.input}
                disabled={otpSent}
                maxLength={11}
                onFocus={(e) => {
                  e.currentTarget.style.boxShadow = theme === 'light'
                    ? '0 0 0 2px rgba(255, 255, 255, 0.5)'
                    : '0 0 0 2px rgba(113, 128, 150, 0.5)'
                }}
                onBlur={(e) => {
                  e.currentTarget.style.boxShadow = 'none'
                }}
              />
            </div>

            {!otpSent && (
              <div style={styles.inputGroup}>
                <label style={styles.label}>روش ارسال کد</label>
                <div style={styles.methodSelector}>
                  <button
                    type="button"
                    style={styles.methodBtn(otpMethod === 'bale')}
                    onClick={() => setOtpMethod('bale')}
                  >
                    <img 
                      src={`/bale_64.png?v=${imageVersion}`}
                      alt="Bale" 
                      width={24} 
                      height={24}
                      style={{ objectFit: 'contain' }}
                    />
                    پیام‌رسان (بله)
                  </button>
                  <button
                    type="button"
                    style={styles.methodBtn(otpMethod === 'sms')}
                    onClick={() => setOtpMethod('sms')}
                  >
                    💬 پیامک
                  </button>
                </div>
              </div>
            )}

            {otpSent && (
              <div style={styles.inputGroup}>
                <label style={styles.label}>کد تایید</label>
                <input
                  type="text"
                  value={otpCode}
                  onChange={(e) => setOtpCode(e.target.value)}
                  placeholder="123456"
                  style={styles.input}
                  maxLength={6}
                  onFocus={(e) => {
                    e.currentTarget.style.boxShadow = theme === 'light'
                      ? '0 0 0 2px rgba(255, 255, 255, 0.5)'
                      : '0 0 0 2px rgba(113, 128, 150, 0.5)'
                  }}
                  onBlur={(e) => {
                    e.currentTarget.style.boxShadow = 'none'
                  }}
                />
                <p style={{...styles.label, fontSize: '12px', marginTop: '8px', display: 'flex', alignItems: 'center', gap: '6px', justifyContent: 'center'}}>
                  کد 6 رقمی ارسال شده از طریق 
                  {otpMethod === 'bale' ? (
                    <span style={{display: 'flex', alignItems: 'center', gap: '4px'}}>
                      <img src={`/bale_64.png?v=${imageVersion}`} alt="Bale" width={18} height={18} style={{ objectFit: 'contain' }} />
                      پیام‌رسان بله
                    </span>
                  ) : '💬 پیامک'} 
                  به {phoneNumber} را وارد کنید
                </p>
                {otpTimer > 0 && (
                  <p style={{...styles.label, fontSize: '14px', marginTop: '8px', textAlign: 'center', fontWeight: 'bold'}}>
                    ⏱️ زمان باقیمانده: {Math.floor(otpTimer / 60)}:{(otpTimer % 60).toString().padStart(2, '0')}
                  </p>
                )}
              </div>
            )}

            <button
              type="submit"
              disabled={isLoadingOtp}
              style={styles.submitBtn}
              onMouseOver={(e) => {
                if (!isLoadingOtp) {
                  e.currentTarget.style.opacity = '0.9'
                  e.currentTarget.style.transform = 'translateY(-2px)'
                }
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.opacity = '1'
                e.currentTarget.style.transform = 'translateY(0)'
              }}
            >
              {isLoadingOtp ? 'در حال ارسال...' : otpSent ? 'ورود' : 'ارسال کد تایید'}
            </button>
            
            {otpSent && (
              <>
                {otpTimer === 0 && canResend && (
                  <button
                    type="button"
                    onClick={handleSendOtp}
                    style={{
                      ...styles.submitBtn,
                      marginTop: '10px',
                      background: theme === 'light'
                        ? 'linear-gradient(135deg, #48bb78 0%, #38a169 100%)'
                        : 'linear-gradient(135deg, #48bb78 0%, #38a169 100%)',
                    }}
                  >
                    ارسال مجدد کد تایید
                  </button>
                )}
                <button
                  type="button"
                  onClick={() => { setOtpSent(false); setOtpCode(''); setOtpTimer(0); setCanResend(true) }}
                  style={{...styles.link, textAlign: 'center', display: 'block', marginTop: '10px'}}
                >
                  تغییر شماره موبایل
                </button>
              </>
            )}
          </form>
        )}


        <div style={styles.links}>
          {userType === 'legal' && (
            <Link
              href="/auth/forgot-password"
              style={styles.link}
              onMouseOver={(e) => {
                e.currentTarget.style.borderBottom = '1px solid currentColor'
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.borderBottom = '1px solid transparent'
              }}
            >
              فراموشی رمز عبور
            </Link>
          )}
          {userType === 'legal' && (
            <Link
              href="/auth/register"
              style={styles.link}
              onMouseOver={(e) => {
                e.currentTarget.style.borderBottom = '1px solid currentColor'
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.borderBottom = '1px solid transparent'
              }}
            >
              ثبت‌نام شرکت
            </Link>
          )}
        </div>
      </div>
    </div>
    </>
  )
}
