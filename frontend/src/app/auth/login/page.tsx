'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import toast from 'react-hot-toast'
import { useAuthStore } from '@/store/auth'
import { SiteSubtitle } from '@/components/SiteName'

const API_URL = typeof window !== 'undefined' ? (process.env.NEXT_PUBLIC_API_URL || 'https://admin.tejarat.chat') : 'https://admin.tejarat.chat'

export default function LoginPage() {
  const router = useRouter()
  const { login, isLoading, error, clearError } = useAuthStore()
  const [userType, setUserType] = useState<'real' | 'legal'>('real')
  const [theme, setTheme] = useState<'light' | 'dark'>('light')
  
  // Load theme from localStorage on mount
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') as 'light' | 'dark' | null
    if (savedTheme) {
      setTheme(savedTheme)
    }
  }, [])
  
  // Save theme to localStorage when it changes
  const handleThemeToggle = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light'
    setTheme(newTheme)
    localStorage.setItem('theme', newTheme)
  }
  
  // Cache buster - force reload on every page load
  const [cacheVersion] = useState(() => Date.now())
  
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
      
      
      if (response.ok) {
        const data = await response.json()
        
        // Get the actual method used (backend may fallback to SMS)
        const methodUsed = data.method || otpMethod
        const methodText = methodUsed === 'bale' ? 'پیام‌رسان (بله)' : 'پیامک'
        // Use expires_in from API response (default 120 seconds)
        const expiresIn = data.expires_in || 120
        
        setOtpSent(true)
        setOtpTimer(expiresIn)
        setCanResend(false)
        toast.success(`کد تایید از طریق ${methodText} به شماره ${phoneNumber} ارسال شد`, {
          duration: 6000,
        })
      } else {
        // If response is not ok, still allow OTP entry with default timer
        const methodText = otpMethod === 'bale' ? 'پیام‌رسان (بله)' : 'پیامک'
        setOtpSent(true)
        setOtpTimer(120) // default 2 minutes
        setCanResend(false)
        toast.success(`کد تایید از طریق ${methodText} به شماره ${phoneNumber} ارسال شد`, {
          duration: 6000,
        })
      }
      
    } catch (err: any) {
      console.error('OTP Send Error:', err)
      // Even on error, allow user to proceed with default timer
      const methodText = otpMethod === 'bale' ? 'پیام‌رسان (بله)' : 'پیامک'
      setOtpSent(true)
      setOtpTimer(120) // default 2 minutes
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
      
      
      if (response.ok) {
        const data = await response.json()
        
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
      padding: '0',
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
      fontWeight: '500',
      transition: 'all 0.3s ease',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      width: '40px',
      height: '40px',
      lineHeight: '40px',
      textAlign: 'center' as const
    },
    userTypeContainer: {
      display: 'flex',
      justifyContent: 'center',
      gap: '12px',
      marginBottom: '16px'
    },
    userTypeBtn: (active: boolean) => ({
      padding: '10px 20px',
      borderRadius: '8px',
      border: active
        ? 'none'
        : theme === 'light'
          ? '1px solid rgba(255, 255, 255, 0.4)'
          : '1px solid #718096',
      background: active
        ? theme === 'light'
          ? 'rgba(255, 255, 255, 0.95)'
          : 'rgba(226, 232, 240, 0.95)'
        : theme === 'light'
          ? 'rgba(255, 255, 255, 0.1)'
          : 'rgba(45, 55, 72, 0.3)',
      color: active
        ? theme === 'light'
          ? '#667eea'
          : '#1a202c'
        : theme === 'light'
          ? 'rgba(255, 255, 255, 0.8)'
          : '#cbd5e0',
      cursor: 'pointer',
      fontSize: '14px',
      fontWeight: '500',
      transition: 'all 0.3s ease',
      boxShadow: active ? '0 4px 12px rgba(0,0,0,0.2)' : 'none',
      backdropFilter: 'blur(10px)'
    }),
    methodSelector: {
      display: 'flex',
      gap: '12px',
      justifyContent: 'center'
    },
    methodBtn: (active: boolean) => ({
      flex: 1,
      padding: '8px 12px',
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
    label: {
      fontSize: '14px',
      fontWeight: '500',
      color: theme === 'light' ? '#fff' : '#cbd5e0'
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
    links: {
      display: 'flex',
      justifyContent: 'space-between',
      marginTop: '16px',
      fontSize: '13px',
      color: theme === 'light' ? 'rgba(255, 255, 255, 0.9)' : '#a0aec0'
    },
    supportInfo: {
      marginTop: '16px',
      padding: '10px 16px 8px',
      borderTop: theme === 'light'
        ? '1px solid rgba(255, 255, 255, 0.3)'
        : '1px solid rgba(113, 128, 150, 0.3)',
      textAlign: 'center' as const,
      fontSize: '13px',
      color: theme === 'light' ? 'rgba(255, 255, 255, 0.95)' : '#cbd5e0'
    },
    supportTitle: {
      fontWeight: '600',
      marginBottom: '4px',
      color: theme === 'light' ? '#fff' : '#e2e8f0'
    },
    phoneNumbers: {
      display: 'flex',
      flexDirection: 'column' as const,
      gap: '2px',
      alignItems: 'center'
    },
    phoneNumber: {
      fontFamily: 'monospace',
      fontSize: '14px',
      fontWeight: '600',
      color: theme === 'light' ? '#fff' : '#e2e8f0',
      direction: 'ltr' as const
    },
    link: {
      color: 'inherit',
      textDecoration: 'none',
      borderBottom: '1px solid transparent',
      transition: 'border-color 0.3s ease'
    },
    footerSection: {
      marginTop: '20px',
      paddingTop: '16px',
      borderTop: theme === 'light'
        ? '1px solid rgba(255, 255, 255, 0.3)'
        : '1px solid rgba(113, 128, 150, 0.3)',
      textAlign: 'center' as const,
      fontSize: '12px',
      color: theme === 'light' ? 'rgba(255, 255, 255, 0.9)' : '#a0aec0'
    },
    footerLinks: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginTop: '10px',
      fontSize: '13px'
    },
    footerLink: {
      color: theme === 'light' ? '#fff' : '#e2e8f0',
      textDecoration: 'none',
      fontWeight: '500',
      transition: 'opacity 0.3s ease'
    },
    supportContact: {
      display: 'flex',
      alignItems: 'center',
      gap: '8px',
      color: theme === 'light' ? '#fff' : '#e2e8f0',
      fontSize: '13px'
    }
  }

  return (
    <>
      <style>{`
        input::placeholder {
          color: ${theme === 'light' ? 'rgba(255, 255, 255, 0.6)' : '#a0aec0'} !important;
          opacity: 1;
        }
        /* Force reload styles - cache buster */
        body::before {
          content: '${cacheVersion}';
          display: none;
        }
      `}</style>
      <div style={styles.container}>
      <div style={styles.card}>
        <div style={styles.header}>
          {/* Logo */}
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
          
          {/* Title and Theme Button */}
          <div style={styles.headerTop}>
            <h2 style={styles.title}>ورود به سامانه</h2>
            <button
              type="button"
              style={styles.themeBtn}
              onClick={handleThemeToggle}
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
              title={theme === 'light' ? 'حالت تاریک' : 'حالت روشن'}
            >
              <span style={{display: 'flex', alignItems: 'center', justifyContent: 'center', width: '100%', height: '100%'}}>{theme === 'light' ? '🌙' : '☀️'}</span>
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
              <div style={styles.inputGroupRow}>
                <label style={styles.labelInline}>ایمیل</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="ایمیل خود را وارد کنید"
                  style={{...styles.input, flex: 1}}
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
            </div>

            <div style={styles.inputGroup}>
              <div style={styles.inputGroupRow}>
                <label style={styles.labelInline}>رمز عبور</label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="رمز عبور خود را وارد کنید"
                  style={{...styles.input, flex: 1}}
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
              <div style={styles.inputGroupRow}>
                <label style={styles.labelInline}>شماره موبایل</label>
                <input
                  type="tel"
                  value={phoneNumber}
                  onChange={(e) => setPhoneNumber(e.target.value)}
                  placeholder="09123456789"
                  style={{...styles.input, flex: 1}}
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
                      src={`/bale_64.png?v=${cacheVersion}`}
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
                    <span style={{fontSize: '20px', lineHeight: '1', display: 'flex', alignItems: 'center'}}>💬</span> پیامک
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
                <p style={{...styles.label, fontSize: '12px', marginTop: '8px', textAlign: 'center', lineHeight: '2'}}>
                  کد ۶ رقمی ارسال شده از طریق {otpMethod === 'bale' ? 'پیام‌رسان بله' : 'پیامک'} به {phoneNumber} را وارد کنید
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

        {/* Footer Section */}
        <div style={styles.footerSection}>
          <p style={{ margin: 0 }}>
            با ورود به سامانه، شما{' '}
            <Link href="/terms" style={{...styles.footerLink, textDecoration: 'underline'}}>قوانین</Link>
            {' '}و{' '}
            <Link href="/privacy" style={{...styles.footerLink, textDecoration: 'underline'}}>حریم خصوصی</Link>
            {' '}استفاده را می‌پذیرید.
          </p>
          
          <div style={styles.footerLinks}>
            <Link 
              href="/about" 
              style={styles.footerLink}
              onMouseOver={(e) => { e.currentTarget.style.opacity = '0.8' }}
              onMouseOut={(e) => { e.currentTarget.style.opacity = '1' }}
            >
              درباره ما
            </Link>
            
            <div style={styles.supportContact}>
              <span>تماس با پشتیبانی:</span>
              <a href="tel:02191097737" style={{...styles.footerLink, fontFamily: 'monospace', direction: 'ltr' as const}}>
                021-91097737
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
    </>
  )
}
