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
      maxWidth: '900px',
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
      marginBottom: '8px',
      textAlign: 'center' as const,
    },
    subtitle: {
      fontSize: '16px',
      color: theme === 'light' ? '#718096' : '#a0aec0',
      textAlign: 'center' as const,
      marginBottom: '32px',
    },
    content: {
      fontSize: '15px',
      lineHeight: '2.2',
      color: theme === 'light' ? '#4a5568' : '#cbd5e0',
    },
    paragraph: {
      marginBottom: '20px',
      textAlign: 'justify' as const,
    },
    highlight: {
      background: theme === 'light' 
        ? 'linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%)'
        : 'linear-gradient(135deg, rgba(102, 126, 234, 0.2) 0%, rgba(118, 75, 162, 0.2) 100%)',
      borderRadius: '12px',
      padding: '20px 24px',
      marginBottom: '24px',
      borderRight: '4px solid #667eea',
    },
    sectionTitle: {
      fontSize: '18px',
      fontWeight: 'bold',
      color: theme === 'light' ? '#667eea' : '#e2e8f0',
      marginTop: '28px',
      marginBottom: '16px',
    },
    list: {
      paddingRight: '24px',
      marginBottom: '20px',
    },
    listItem: {
      marginBottom: '10px',
      position: 'relative' as const,
    },
    featureGrid: {
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
      gap: '16px',
      marginBottom: '24px',
    },
    featureCard: {
      background: theme === 'light' 
        ? 'rgba(102, 126, 234, 0.08)'
        : 'rgba(102, 126, 234, 0.15)',
      borderRadius: '10px',
      padding: '16px',
      textAlign: 'center' as const,
    },
    featureIcon: {
      fontSize: '28px',
      marginBottom: '8px',
    },
    featureText: {
      fontSize: '14px',
      fontWeight: '500',
      color: theme === 'light' ? '#4a5568' : '#e2e8f0',
    },
    mission: {
      background: theme === 'light' 
        ? 'rgba(72, 187, 120, 0.1)'
        : 'rgba(72, 187, 120, 0.2)',
      borderRadius: '12px',
      padding: '20px 24px',
      marginBottom: '24px',
      borderRight: '4px solid #48bb78',
    },
    goal: {
      background: theme === 'light' 
        ? 'rgba(237, 137, 54, 0.1)'
        : 'rgba(237, 137, 54, 0.2)',
      borderRadius: '12px',
      padding: '20px 24px',
      marginBottom: '24px',
      borderRight: '4px solid #ed8936',
    },
    backLink: {
      display: 'inline-block',
      marginTop: '32px',
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
        <p style={styles.subtitle}>سامانه هوشمند مشاور کسب‌وکار تجارت‌چت (Tejarat.Chat)</p>
        
        <div style={styles.content}>
          {/* معرفی */}
          <div style={styles.highlight}>
            <p style={{...styles.paragraph, marginBottom: 0}}>
              سامانه <strong>تجارت‌چت (Tejarat.Chat)</strong> در سال ۱۴۰۴ با هدف کمک به کسب‌وکارهای کوچک، اصناف، استارتاپ‌ها و اشخاص حقیقی تأسیس شد؛ گروهی که معمولاً با چالش‌های حقوقی، مالیاتی و مقرراتی متعددی روبه‌رو هستند، اما امکان استفاده مستمر از خدمات وکلاء یا مشاوران حرفه‌ای را به دلیل هزینه‌های بالا ندارند.
            </p>
          </div>

          {/* توضیح سامانه */}
          <p style={styles.paragraph}>
            تجارت‌چت یک <strong>سامانه هوشمند مشاور کسب‌وکار</strong> مبتنی بر مدل‌های پیشرفته هوش مصنوعی است که با استفاده از:
          </p>

          <div style={styles.featureGrid}>
            <div style={styles.featureCard}>
              <div style={styles.featureIcon}>📜</div>
              <div style={styles.featureText}>متن قوانین تنقیح‌شده جمهوری اسلامی ایران</div>
            </div>
            <div style={styles.featureCard}>
              <div style={styles.featureIcon}>📋</div>
              <div style={styles.featureText}>آیین‌نامه‌ها، بخشنامه‌ها و دستورالعمل‌ها</div>
            </div>
            <div style={styles.featureCard}>
              <div style={styles.featureIcon}>🗄️</div>
              <div style={styles.featureText}>پایگاه‌های معتبر مقرراتی و محتوای ساختاریافته</div>
            </div>
            <div style={styles.featureCard}>
              <div style={styles.featureIcon}>🤖</div>
              <div style={styles.featureText}>موتورهای پردازش هوشمند</div>
            </div>
          </div>

          <p style={styles.paragraph}>
            به کاربران کمک می‌کند تا درک روشن‌تر و سریع‌تری از تکالیف قانونی، مالیاتی، بیمه‌ای و مقرراتی خود داشته باشند.
          </p>

          {/* ماموریت */}
          <div style={styles.mission}>
            <h3 style={{...styles.sectionTitle, marginTop: 0, color: '#276749'}}>🎯 ماموریت ما</h3>
            <p style={{...styles.paragraph, marginBottom: 0}}>
              ارائه راهکارهای تحلیلی هوشمند برای موضوعاتی است که روزانه هزاران کسب‌وکار را درگیر می‌کند:
            </p>
          </div>

          <ul style={styles.list}>
            <li style={styles.listItem}>📊 قوانین مالیاتی و تکالیف مودیان</li>
            <li style={styles.listItem}>🏥 مقررات مرتبط با تأمین اجتماعی</li>
            <li style={styles.listItem}>👷 الزامات وزارت کار</li>
            <li style={styles.listItem}>📝 حقوق کسب‌وکارها و قراردادها</li>
            <li style={styles.listItem}>🏛️ فرایندهای اداری و مجوزها</li>
            <li style={styles.listItem}>⚖️ و دیگر موضوعات حقوقی مرتبط با فعالیت‌های اقتصادی</li>
          </ul>

          {/* هدف */}
          <div style={styles.goal}>
            <h3 style={{...styles.sectionTitle, marginTop: 0, color: '#c05621'}}>🎯 هدف ما</h3>
            <p style={{...styles.paragraph, marginBottom: 0}}>
              پیشگیری از ضررهای مالی، جریمه‌های ناخواسته و اشتباهات رایج است؛ اشتباهاتی که معمولاً به دلیل ناآگاهی از قوانین رخ می‌دهد.
            </p>
          </div>

          {/* جمع‌بندی */}
          <p style={styles.paragraph}>
            تجارت‌چت با ترکیب <strong>دانش حقوقی ساختاریافته</strong> و <strong>الگوریتم‌های تحلیل متن</strong>، تلاش می‌کند تجربه‌ای سریع، قابل‌فهم و مقرون‌به‌صرفه از مشاوره هوشمند را فراهم کند و راهنمای قابل‌اعتمادی برای کاربران در مسیر انجام صحیح امور قانونی باشد.
          </p>
        </div>
        
        <Link href="/auth/login" style={styles.backLink}>
          بازگشت به صفحه ورود
        </Link>
      </div>
    </div>
  )
}
