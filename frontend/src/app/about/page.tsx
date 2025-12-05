'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'

export default function AboutPage() {
  const [theme, setTheme] = useState<'light' | 'dark'>('light')

  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') as 'light' | 'dark' | null
    if (savedTheme) {
      setTheme(savedTheme)
    }
  }, [])

  const styles = {
    container: {
      minHeight: '100vh',
      background: theme === 'light' 
        ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
        : 'linear-gradient(135deg, #1a202c 0%, #2d3748 100%)',
      padding: '40px 20px',
      direction: 'rtl' as const,
    },
    card: {
      maxWidth: '800px',
      margin: '0 auto',
      borderRadius: '16px',
      boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
      padding: '40px',
      background: theme === 'light'
        ? 'rgba(255, 255, 255, 0.95)'
        : 'rgba(45, 55, 72, 0.95)',
      backdropFilter: 'blur(20px)',
    },
    title: {
      fontSize: '28px',
      fontWeight: 'bold',
      color: theme === 'light' ? '#667eea' : '#e2e8f0',
      marginBottom: '24px',
      textAlign: 'center' as const,
    },
    content: {
      fontSize: '16px',
      lineHeight: '2',
      color: theme === 'light' ? '#4a5568' : '#cbd5e0',
    },
    backLink: {
      display: 'inline-block',
      marginTop: '24px',
      padding: '12px 24px',
      borderRadius: '8px',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      color: '#fff',
      textDecoration: 'none',
      fontWeight: '600',
    }
  }

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h1 style={styles.title}>درباره ما</h1>
        <div style={styles.content}>
          <p>
            سامانه مشاور هوشمند کسب و کار، یک پلتفرم پیشرفته مبتنی بر هوش مصنوعی است که به کسب‌وکارها در تصمیم‌گیری‌های استراتژیک کمک می‌کند.
          </p>
          <p>
            محتوای این صفحه به زودی تکمیل خواهد شد.
          </p>
        </div>
        <Link href="/auth/login" style={styles.backLink}>
          بازگشت به صفحه ورود
        </Link>
      </div>
    </div>
  )
}
