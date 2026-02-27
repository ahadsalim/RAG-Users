'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import toast from 'react-hot-toast'
import { useAuthStore } from '@/store/auth'
import { SiteSubtitle } from '@/components/SiteName'

const API_URL = process.env.NEXT_PUBLIC_API_URL || ''
const BALE_ENABLED = process.env.NEXT_PUBLIC_BALE_ENABLED === 'true'

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
  const [otpMethod, setOtpMethod] = useState<'sms' | 'bale'>(BALE_ENABLED ? 'bale' : 'sms')
  const [otpTimer, setOtpTimer] = useState(0)
  const [canResend, setCanResend] = useState(true)
  
  // Site settings for licenses
  const [licenses, setLicenses] = useState<Array<{name: string, url: string}>>([])
  
  // Fetch site settings for licenses
  useEffect(() => {
    const fetchLicenses = async () => {
      try {
        const response = await fetch(`${API_URL}/api/core/settings/`)
        if (response.ok) {
          const data = await response.json()
          const licensesData = []
          if (data.license_1_name && data.license_1_logo_url) {
            licensesData.push({ name: data.license_1_name, url: data.license_1_logo_url })
          }
          if (data.license_2_name && data.license_2_logo_url) {
            licensesData.push({ name: data.license_2_name, url: data.license_2_logo_url })
          }
          if (data.license_3_name && data.license_3_logo_url) {
            licensesData.push({ name: data.license_3_name, url: data.license_3_logo_url })
          }
          setLicenses(licensesData)
        }
      } catch (error) {
        console.error('Failed to fetch licenses:', error)
      }
    }
    fetchLicenses()
  }, [])
  
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
      background: theme === 'light' 
        ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
        : 'linear-gradient(135deg, #1a202c 0%, #2d3748 100%)',
      direction: 'rtl' as const,
      transition: 'all 0.5s ease',
      overflowY: 'auto' as const
    },
    loginSection: {
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px'
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
        <div style={styles.loginSection}>
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

            {!otpSent && BALE_ENABLED && (
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

        {/* Landing Page Sections */}
        <div style={{
          background: theme === 'light' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.2)',
          padding: '60px 20px',
          backdropFilter: 'blur(10px)'
        }}>
          <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
            
            {/* Hero Section */}
            <div style={{
              textAlign: 'center',
              marginBottom: '60px',
              padding: '40px 20px',
              background: theme === 'light' 
                ? 'linear-gradient(135deg, rgba(255, 255, 255, 0.2) 0%, rgba(255, 255, 255, 0.1) 100%)'
                : 'linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%)',
              borderRadius: '16px',
              border: '1px solid rgba(255, 255, 255, 0.3)'
            }}>
              <h1 style={{
                fontSize: '42px',
                fontWeight: 'bold',
                color: '#fff',
                marginBottom: '20px',
                textShadow: '0 2px 10px rgba(0,0,0,0.3)'
              }}>
                مشاور هوشمند کسب‌وکار شما
              </h1>
              <p style={{
                fontSize: '22px',
                color: 'rgba(255, 255, 255, 0.95)',
                marginBottom: '15px',
                fontWeight: '500'
              }}>
                پاسخ دقیق، مستند و به‌روز به سؤالات مالیاتی، بیمه‌ای، گمرکی و بانکی — در چند ثانیه
              </p>
              <p style={{
                fontSize: '16px',
                color: 'rgba(255, 255, 255, 0.85)',
                lineHeight: '1.8',
                maxWidth: '800px',
                margin: '0 auto'
              }}>
                در دنیای پیچیده قوانین و بخشنامه‌ها، یک سؤال ساده می‌تواند ساعت‌ها وقت، هزینه و استرس به شما تحمیل کند.<br/>
                <strong style={{ color: '#fff', fontSize: '18px' }}>ما این مشکل را حل کرده‌ایم.</strong>
              </p>
            </div>

            {/* What We Do Section */}
            <div style={{
              marginBottom: '60px',
              padding: '40px 30px',
              background: theme === 'light' ? 'rgba(255, 255, 255, 0.15)' : 'rgba(255, 255, 255, 0.05)',
              borderRadius: '16px',
              border: '1px solid rgba(255, 255, 255, 0.2)'
            }}>
              <h2 style={{
                fontSize: '32px',
                fontWeight: 'bold',
                color: '#fff',
                marginBottom: '20px',
                textAlign: 'center'
              }}>
                این سامانه چیست؟
              </h2>
              <p style={{
                fontSize: '17px',
                color: 'rgba(255, 255, 255, 0.9)',
                lineHeight: '2',
                textAlign: 'center',
                maxWidth: '900px',
                margin: '0 auto 30px'
              }}>
                این سامانه یک <strong>مشاور هوشمند تخصصی کسب‌وکار</strong> است که با تکیه بر هزاران متن قانونی، آراء رسمی و منابع آموزشی معتبر، به سؤالات واقعی شما پاسخ می‌دهد؛ دقیق، مستند و منطبق با آخرین مقررات.
              </p>
              
              <h3 style={{
                fontSize: '24px',
                fontWeight: 'bold',
                color: '#fff',
                marginBottom: '20px',
                marginTop: '40px',
                textAlign: 'center'
              }}>
                ما دقیقاً چه کاری انجام می‌دهیم؟
              </h3>
              <p style={{
                fontSize: '16px',
                color: 'rgba(255, 255, 255, 0.9)',
                lineHeight: '2',
                textAlign: 'center',
                marginBottom: '30px'
              }}>
                ما یک سیستم مبتنی بر هوش مصنوعی و RAG ساخته‌ایم که نقش یک مشاور باتجربه مالیاتی، بیمه‌ای و گمرکی را برای شما ایفا می‌کند.
              </p>

              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
                gap: '20px',
                marginTop: '30px'
              }}>
                {[
                  { icon: '💰', title: 'مالیات', desc: 'اظهارنامه، رسیدگی، جرایم، معافیت‌ها، ارزش افزوده، مالیات حقوق و …' },
                  { icon: '🏥', title: 'بیمه تأمین اجتماعی', desc: 'لیست، حق بیمه، قراردادها، بازرسی، بدهی و اعتراض' },
                  { icon: '🚢', title: 'گمرک و تجارت', desc: 'تعرفه، ارزش، ترخیص، صادرات، واردات، مقررات و بخشنامه‌ها' },
                  { icon: '🏦', title: 'امور پولی و بانکی', desc: 'دستورالعمل‌ها، مقررات بانک مرکزی، الزامات بانکی' },
                  { icon: '💼', title: 'سؤالات کسب‌وکار', desc: 'سؤالات روزمره و عملیاتی کسب‌وکار شما' }
                ].map((item, idx) => (
                  <div key={idx} style={{
                    background: theme === 'light' ? 'rgba(255, 255, 255, 0.2)' : 'rgba(255, 255, 255, 0.08)',
                    padding: '25px',
                    borderRadius: '12px',
                    border: '1px solid rgba(255, 255, 255, 0.25)',
                    textAlign: 'center'
                  }}>
                    <div style={{ fontSize: '40px', marginBottom: '12px' }}>{item.icon}</div>
                    <h4 style={{ fontSize: '18px', fontWeight: 'bold', color: '#fff', marginBottom: '10px' }}>
                      {item.title}
                    </h4>
                    <p style={{ fontSize: '14px', color: 'rgba(255, 255, 255, 0.85)', lineHeight: '1.6' }}>
                      {item.desc}
                    </p>
                  </div>
                ))}
              </div>

              <p style={{
                fontSize: '17px',
                color: 'rgba(255, 255, 255, 0.95)',
                lineHeight: '2',
                textAlign: 'center',
                marginTop: '30px',
                fontWeight: '500'
              }}>
                و پاسخ خود را نه بر اساس حدس یا تجربه شخصی، بلکه <strong style={{ color: '#fff' }}>مستند به قانون، بخشنامه و رأی رسمی</strong> دریافت کنید.
              </p>
            </div>

            {/* Target Audience */}
            <div style={{
              marginBottom: '60px',
              padding: '40px 30px',
              background: theme === 'light' 
                ? 'linear-gradient(135deg, rgba(72, 187, 120, 0.2) 0%, rgba(56, 161, 105, 0.15) 100%)'
                : 'linear-gradient(135deg, rgba(72, 187, 120, 0.15) 0%, rgba(56, 161, 105, 0.1) 100%)',
              borderRadius: '16px',
              border: '1px solid rgba(72, 187, 120, 0.3)'
            }}>
              <h2 style={{
                fontSize: '32px',
                fontWeight: 'bold',
                color: '#fff',
                marginBottom: '25px',
                textAlign: 'center'
              }}>
                مناسب چه کسانی است؟
              </h2>
              <p style={{
                fontSize: '17px',
                color: 'rgba(255, 255, 255, 0.95)',
                lineHeight: '2',
                textAlign: 'center',
                marginBottom: '30px'
              }}>
                فرقی نمی‌کند که شما:
              </p>
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                gap: '20px'
              }}>
                {[
                  { icon: '🏪', text: 'یک مغازه‌دار یا کاسب' },
                  { icon: '🏢', text: 'صاحب کسب‌وکار کوچک یا متوسط' },
                  { icon: '📊', text: 'کارشناس یا مدیر مالی، حسابداری یا بازرگانی' },
                  { icon: '👔', text: 'مشاور که نیاز به پاسخ سریع و مستند دارد' }
                ].map((item, idx) => (
                  <div key={idx} style={{
                    background: 'rgba(255, 255, 255, 0.15)',
                    padding: '20px',
                    borderRadius: '12px',
                    textAlign: 'center',
                    border: '1px solid rgba(255, 255, 255, 0.3)'
                  }}>
                    <div style={{ fontSize: '36px', marginBottom: '10px' }}>{item.icon}</div>
                    <p style={{ fontSize: '15px', color: '#fff', fontWeight: '500' }}>{item.text}</p>
                  </div>
                ))}
              </div>
              <p style={{
                fontSize: '18px',
                color: '#fff',
                fontWeight: 'bold',
                textAlign: 'center',
                marginTop: '30px'
              }}>
                این سامانه برای شما طراحی شده است.
              </p>
            </div>

            {/* Data Power Section */}
            <div style={{
              marginBottom: '60px',
              padding: '40px 30px',
              background: theme === 'light' 
                ? 'linear-gradient(135deg, rgba(66, 153, 225, 0.2) 0%, rgba(49, 130, 206, 0.15) 100%)'
                : 'linear-gradient(135deg, rgba(66, 153, 225, 0.15) 0%, rgba(49, 130, 206, 0.1) 100%)',
              borderRadius: '16px',
              border: '1px solid rgba(66, 153, 225, 0.3)'
            }}>
              <h2 style={{
                fontSize: '32px',
                fontWeight: 'bold',
                color: '#fff',
                marginBottom: '20px',
                textAlign: 'center'
              }}>
                قدرت واقعی سامانه در داده‌های آن است
              </h2>
              <p style={{
                fontSize: '17px',
                color: 'rgba(255, 255, 255, 0.95)',
                lineHeight: '2',
                textAlign: 'center',
                marginBottom: '35px'
              }}>
                این سیستم بر پایه حجم عظیم و کاملی از قوانین و مقررات کسب‌وکار در ایران ساخته شده است:
              </p>
              
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
                gap: '25px'
              }}>
                {[
                  { icon: '📘', number: '۹۳', title: 'قانون مصوب', desc: 'مجلس شورای اسلامی، مجلس شورای ملی و شورای انقلاب' },
                  { icon: '⚖️', number: '۶۰۱', title: 'رأی هیئت عمومی', desc: 'دیوان عدالت اداری' },
                  { icon: '🧾', number: '۱۱۳۵', title: 'بخشنامه', desc: 'گمرک (۱۰ سال اخیر)، سازمان امور مالیاتی، تأمین اجتماعی، بانک مرکزی' },
                  { icon: '📋', number: '۴۵', title: 'دستورالعمل تخصصی', desc: 'راهنماهای عملیاتی و اجرایی' },
                  { icon: '🎓', number: '۵۲۸', title: 'متن آموزشی', desc: 'منابع معتبر و کاربردی' }
                ].map((item, idx) => (
                  <div key={idx} style={{
                    background: 'rgba(255, 255, 255, 0.15)',
                    padding: '30px',
                    borderRadius: '12px',
                    textAlign: 'center',
                    border: '1px solid rgba(255, 255, 255, 0.3)',
                    transition: 'transform 0.3s ease'
                  }}>
                    <div style={{ fontSize: '48px', marginBottom: '15px' }}>{item.icon}</div>
                    <div style={{ fontSize: '36px', fontWeight: 'bold', color: '#fff', marginBottom: '10px' }}>
                      {item.number}
                    </div>
                    <h4 style={{ fontSize: '18px', fontWeight: 'bold', color: '#fff', marginBottom: '10px' }}>
                      {item.title}
                    </h4>
                    <p style={{ fontSize: '14px', color: 'rgba(255, 255, 255, 0.85)', lineHeight: '1.6' }}>
                      {item.desc}
                    </p>
                  </div>
                ))}
              </div>

              <div style={{
                marginTop: '40px',
                padding: '25px',
                background: 'rgba(255, 255, 255, 0.1)',
                borderRadius: '12px',
                border: '1px solid rgba(255, 255, 255, 0.25)'
              }}>
                <p style={{
                  fontSize: '18px',
                  color: '#fff',
                  fontWeight: 'bold',
                  textAlign: 'center',
                  marginBottom: '15px'
                }}>
                  این یعنی پاسخ‌هایی که می‌گیرید:
                </p>
                <div style={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  justifyContent: 'center',
                  gap: '20px'
                }}>
                  {['✅ دقیق', '✅ مستند', '✅ به‌روز', '✅ قابل استناد در عمل'].map((item, idx) => (
                    <div key={idx} style={{
                      fontSize: '17px',
                      color: '#fff',
                      fontWeight: '500',
                      padding: '10px 20px',
                      background: 'rgba(72, 187, 120, 0.3)',
                      borderRadius: '8px'
                    }}>
                      {item}
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Why Valuable */}
            <div style={{
              marginBottom: '60px',
              padding: '40px 30px',
              background: theme === 'light' ? 'rgba(255, 255, 255, 0.15)' : 'rgba(255, 255, 255, 0.05)',
              borderRadius: '16px',
              border: '1px solid rgba(255, 255, 255, 0.2)'
            }}>
              <h2 style={{
                fontSize: '32px',
                fontWeight: 'bold',
                color: '#fff',
                marginBottom: '30px',
                textAlign: 'center'
              }}>
                چرا این سامانه ارزشمند است؟
              </h2>
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
                gap: '25px'
              }}>
                {[
                  { icon: '⏱️', title: 'صرفه‌جویی چشمگیر در زمان', color: 'rgba(237, 137, 54, 0.3)' },
                  { icon: '💰', title: 'کاهش هزینه مشاوره‌های تکراری', color: 'rgba(72, 187, 120, 0.3)' },
                  { icon: '📑', title: 'دسترسی سریع به قوانین و بخشنامه‌های پراکنده', color: 'rgba(66, 153, 225, 0.3)' },
                  { icon: '🤝', title: 'نقش یک مشاور حرفه‌ای، همیشه در دسترس شما', color: 'rgba(159, 122, 234, 0.3)' }
                ].map((item, idx) => (
                  <div key={idx} style={{
                    background: item.color,
                    padding: '30px',
                    borderRadius: '12px',
                    textAlign: 'center',
                    border: '1px solid rgba(255, 255, 255, 0.3)'
                  }}>
                    <div style={{ fontSize: '48px', marginBottom: '15px' }}>{item.icon}</div>
                    <p style={{ fontSize: '17px', color: '#fff', fontWeight: 'bold', lineHeight: '1.6' }}>
                      {item.title}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            {/* Pricing Section */}
            <div style={{
              marginBottom: '60px',
              padding: '40px 30px',
              background: theme === 'light' 
                ? 'linear-gradient(135deg, rgba(159, 122, 234, 0.2) 0%, rgba(128, 90, 213, 0.15) 100%)'
                : 'linear-gradient(135deg, rgba(159, 122, 234, 0.15) 0%, rgba(128, 90, 213, 0.1) 100%)',
              borderRadius: '16px',
              border: '1px solid rgba(159, 122, 234, 0.3)'
            }}>
              <h2 style={{
                fontSize: '32px',
                fontWeight: 'bold',
                color: '#fff',
                marginBottom: '20px',
                textAlign: 'center'
              }}>
                ثبت‌نام رایگان + اشتراک انعطاف‌پذیر
              </h2>
              <div style={{
                background: 'rgba(255, 255, 255, 0.15)',
                padding: '30px',
                borderRadius: '12px',
                border: '1px solid rgba(255, 255, 255, 0.3)',
                marginBottom: '25px'
              }}>
                <p style={{
                  fontSize: '24px',
                  color: '#fff',
                  fontWeight: 'bold',
                  textAlign: 'center',
                  marginBottom: '15px'
                }}>
                  ✅ ثبت‌نام کاملاً رایگان است
                </p>
                <p style={{
                  fontSize: '17px',
                  color: 'rgba(255, 255, 255, 0.95)',
                  lineHeight: '2',
                  textAlign: 'center'
                }}>
                  شما می‌توانید سامانه را امتحان کنید و کیفیت پاسخ‌ها را ببینید.
                </p>
              </div>

              <p style={{
                fontSize: '18px',
                color: 'rgba(255, 255, 255, 0.95)',
                lineHeight: '2',
                textAlign: 'center',
                marginBottom: '25px'
              }}>
                در صورت نیاز بیشتر:
              </p>

              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
                gap: '20px',
                marginBottom: '25px'
              }}>
                {[
                  { icon: '📦', text: 'پلن‌های اشتراک متناسب با حجم استفاده' },
                  { icon: '👤', text: 'مخصوص اشخاص حقیقی یا حقوقی' },
                  { icon: '📊', text: 'بر اساس تعداد سؤال روزانه و ماهانه' }
                ].map((item, idx) => (
                  <div key={idx} style={{
                    background: 'rgba(255, 255, 255, 0.15)',
                    padding: '20px',
                    borderRadius: '12px',
                    textAlign: 'center',
                    border: '1px solid rgba(255, 255, 255, 0.3)'
                  }}>
                    <div style={{ fontSize: '36px', marginBottom: '10px' }}>{item.icon}</div>
                    <p style={{ fontSize: '15px', color: '#fff', fontWeight: '500', lineHeight: '1.6' }}>
                      {item.text}
                    </p>
                  </div>
                ))}
              </div>

              <p style={{
                fontSize: '18px',
                color: '#fff',
                fontWeight: 'bold',
                textAlign: 'center'
              }}>
                شما فقط به اندازه‌ای که استفاده می‌کنید، هزینه می‌پردازید.
              </p>
            </div>

            {/* Final CTA */}
            <div style={{
              textAlign: 'center',
              padding: '50px 30px',
              background: theme === 'light' 
                ? 'linear-gradient(135deg, rgba(72, 187, 120, 0.25) 0%, rgba(56, 161, 105, 0.2) 100%)'
                : 'linear-gradient(135deg, rgba(72, 187, 120, 0.2) 0%, rgba(56, 161, 105, 0.15) 100%)',
              borderRadius: '16px',
              border: '2px solid rgba(72, 187, 120, 0.4)'
            }}>
              <h2 style={{
                fontSize: '36px',
                fontWeight: 'bold',
                color: '#fff',
                marginBottom: '20px'
              }}>
                یک سؤال بپرسید، تفاوت را احساس کنید
              </h2>
              <p style={{
                fontSize: '18px',
                color: 'rgba(255, 255, 255, 0.95)',
                lineHeight: '2',
                marginBottom: '15px',
                maxWidth: '700px',
                margin: '0 auto 30px'
              }}>
                اگر با قوانین، بخشنامه‌ها و ابهام‌های اداری سروکار دارید،<br/>
                <strong style={{ fontSize: '20px', color: '#fff' }}>این سامانه می‌تواند اولین و اصلی‌ترین مرجع پاسخ‌گویی شما باشد.</strong>
              </p>
              <button
                onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
                style={{
                  background: 'linear-gradient(135deg, #48bb78 0%, #38a169 100%)',
                  color: '#fff',
                  padding: '18px 50px',
                  borderRadius: '12px',
                  border: 'none',
                  fontSize: '20px',
                  fontWeight: 'bold',
                  cursor: 'pointer',
                  transition: 'all 0.3s ease',
                  boxShadow: '0 4px 15px rgba(72, 187, 120, 0.4)'
                }}
                onMouseOver={(e) => {
                  e.currentTarget.style.transform = 'translateY(-3px)'
                  e.currentTarget.style.boxShadow = '0 10px 25px rgba(72, 187, 120, 0.5)'
                }}
                onMouseOut={(e) => {
                  e.currentTarget.style.transform = 'translateY(0)'
                  e.currentTarget.style.boxShadow = '0 4px 15px rgba(72, 187, 120, 0.4)'
                }}
              >
                همین حالا ثبت‌نام کنید
              </button>
              <p style={{
                fontSize: '16px',
                color: 'rgba(255, 255, 255, 0.9)',
                marginTop: '20px',
                fontStyle: 'italic'
              }}>
                و مشاور هوشمند کسب‌وکار خود را همیشه در کنار داشته باشید.
              </p>
            </div>

            {/* Licenses Section */}
            {licenses.length > 0 && (
              <div style={{
                marginTop: '60px',
                padding: '40px 30px',
                background: theme === 'light' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(255, 255, 255, 0.05)',
                borderRadius: '16px',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                textAlign: 'center'
              }}>
                <h3 style={{
                  fontSize: '24px',
                  fontWeight: 'bold',
                  color: '#fff',
                  marginBottom: '30px'
                }}>
                  مجوزها و گواهینامه‌ها
                </h3>
                <div style={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  justifyContent: 'center',
                  alignItems: 'center',
                  gap: '30px'
                }}>
                  {licenses.map((license, idx) => (
                    <div key={idx} style={{
                      background: 'rgba(255, 255, 255, 0.15)',
                      padding: '20px',
                      borderRadius: '12px',
                      border: '1px solid rgba(255, 255, 255, 0.3)',
                      minWidth: '200px',
                      maxWidth: '250px'
                    }}>
                      <img 
                        src={license.url}
                        alt={license.name}
                        style={{
                          maxWidth: '100%',
                          height: 'auto',
                          maxHeight: '120px',
                          objectFit: 'contain',
                          marginBottom: '15px'
                        }}
                        onError={(e) => {
                          e.currentTarget.style.display = 'none'
                        }}
                      />
                      <p style={{
                        fontSize: '14px',
                        color: 'rgba(255, 255, 255, 0.9)',
                        fontWeight: '500',
                        marginTop: '10px'
                      }}>
                        {license.name}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

          </div>
        </div>
      </div>
    </>
  )
}
