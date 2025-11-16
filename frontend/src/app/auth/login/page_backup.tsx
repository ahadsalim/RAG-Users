'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import toast from 'react-hot-toast'
import { useAuthStore } from '@/store/auth'

export default function LoginPage() {
  const router = useRouter()
  const { login, isLoading, error, clearError } = useAuthStore()
  const [userType, setUserType] = useState<'real' | 'legal'>('real')
  const [theme, setTheme] = useState<'light' | 'dark'>('light')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  
  const handleSubmit = async (e: React.FormEvent) => {
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
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: '30px'
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
        ? 'rgba(255, 255, 255, 0.3)'
        : '#2d3748',
      color: theme === 'light' ? '#fff' : '#e2e8f0',
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
    <div style={styles.container}>
      <div style={styles.card}>
        <div style={styles.header}>
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

        <form style={styles.form} onSubmit={handleSubmit}>
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

        <div style={styles.links}>
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
            ثبت‌نام
          </Link>
        </div>
      </div>
    </div>
  )
}
