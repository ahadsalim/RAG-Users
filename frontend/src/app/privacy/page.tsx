'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'

export default function PrivacyPage() {
  const [theme, setTheme] = useState<'light' | 'dark'>('light')
  const [language, setLanguage] = useState<'fa' | 'en'>('fa')

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
      direction: language === 'fa' ? 'rtl' as const : 'ltr' as const,
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
    updateDate: {
      fontSize: '14px',
      color: theme === 'light' ? '#718096' : '#a0aec0',
      textAlign: 'center' as const,
      marginBottom: '24px',
    },
    langToggle: {
      display: 'flex',
      justifyContent: 'center',
      gap: '12px',
      marginBottom: '24px',
    },
    langBtn: (active: boolean) => ({
      padding: '8px 20px',
      borderRadius: '8px',
      border: 'none',
      background: active
        ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
        : theme === 'light'
          ? 'rgba(102, 126, 234, 0.2)'
          : 'rgba(102, 126, 234, 0.3)',
      color: active ? '#fff' : theme === 'light' ? '#667eea' : '#e2e8f0',
      cursor: 'pointer',
      fontSize: '14px',
      fontWeight: '600',
      transition: 'all 0.3s ease',
    }),
    content: {
      fontSize: '15px',
      lineHeight: '2',
      color: theme === 'light' ? '#4a5568' : '#cbd5e0',
    },
    sectionTitle: {
      fontSize: '18px',
      fontWeight: 'bold',
      color: theme === 'light' ? '#667eea' : '#e2e8f0',
      marginTop: '28px',
      marginBottom: '12px',
      borderBottom: '2px solid #667eea',
      paddingBottom: '8px',
    },
    paragraph: {
      marginBottom: '12px',
      textAlign: 'justify' as const,
    },
    list: {
      paddingRight: language === 'fa' ? '24px' : '0',
      paddingLeft: language === 'en' ? '24px' : '0',
      marginBottom: '16px',
    },
    listItem: {
      marginBottom: '8px',
    },
    warning: {
      background: theme === 'light' ? 'rgba(237, 137, 54, 0.1)' : 'rgba(237, 137, 54, 0.2)',
      border: '1px solid #ed8936',
      borderRadius: '8px',
      padding: '12px 16px',
      marginBottom: '16px',
      color: theme === 'light' ? '#c05621' : '#fbd38d',
    },
    contact: {
      background: theme === 'light' ? 'rgba(102, 126, 234, 0.1)' : 'rgba(102, 126, 234, 0.2)',
      borderRadius: '8px',
      padding: '16px',
      marginTop: '24px',
      textAlign: 'center' as const,
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
        <h1 style={styles.title}>
          {language === 'fa' ? 'سیاست حریم خصوصی' : 'Privacy Policy'}
        </h1>
        <p style={styles.updateDate}>
          {language === 'fa' ? 'به‌روزرسانی: ۱۴۰۴/۰۹/۱۴' : 'Last Updated: December 4, 2025'}
        </p>
        
        {/* Language Toggle */}
        <div style={styles.langToggle}>
          <button 
            style={styles.langBtn(language === 'fa')} 
            onClick={() => setLanguage('fa')}
          >
            فارسی
          </button>
          <button 
            style={styles.langBtn(language === 'en')} 
            onClick={() => setLanguage('en')}
          >
            English
          </button>
        </div>

        {language === 'fa' ? (
          /* Persian Content */
          <div style={styles.content}>
            <p style={styles.paragraph}>
              این «سیاست حریم خصوصی» توضیح می‌دهد که وب‌سایت و سامانه «سامانه مشاور هوشمند کسب‌وکار / مشاور حقوقی هوشمند» به نشانی tejarat.chat چگونه داده‌های کاربران را جمع‌آوری، ذخیره، استفاده و حفاظت می‌کند. استفاده از سامانه به معنای پذیرش این سیاست است.
            </p>

            <h2 style={styles.sectionTitle}>۱. تعاریف</h2>
            <ul style={styles.list}>
              <li style={styles.listItem}><strong>«ما» یا «سامانه»:</strong> پلتفرم ارائه‌دهنده خدمات هوش مصنوعی، مشاوره تحلیلی، تولید محتوا، و ابزارهای پردازشی مبتنی‌بر API.</li>
              <li style={styles.listItem}><strong>«شما» یا «کاربر»:</strong> هر فردی که از سرویس استفاده می‌کند یا حساب کاربری ایجاد می‌کند.</li>
              <li style={styles.listItem}><strong>«داده شخصی»:</strong> هر داده‌ای که برای شناسایی یک فرد قابل استفاده باشد.</li>
              <li style={styles.listItem}><strong>«داده ورودی»:</strong> کلیه اطلاعاتی که کاربر در چت، فرم‌ها یا ابزارها وارد می‌کند.</li>
              <li style={styles.listItem}><strong>«داده خروجی»:</strong> محتوایی که هوش مصنوعی بر اساس ورودی تولید می‌کند.</li>
              <li style={styles.listItem}><strong>«داده فنی و تحلیلی»:</strong> شامل IP، Device Info، Usage Data، Log Data و…</li>
            </ul>

            <h2 style={styles.sectionTitle}>۲. داده‌هایی که جمع‌آوری می‌کنیم</h2>
            <p style={styles.paragraph}><strong>۱) اطلاعات شناسایی و تماس:</strong></p>
            <ul style={styles.list}>
              <li style={styles.listItem}>نام</li>
              <li style={styles.listItem}>شماره موبایل</li>
              <li style={styles.listItem}>ایمیل</li>
              <li style={styles.listItem}>اطلاعات پروفایل (در صورت وجود)</li>
            </ul>

            <p style={styles.paragraph}><strong>۲) داده ورودی (Input):</strong></p>
            <p style={styles.paragraph}>تمام متونی که شما در سیستم وارد می‌کنید.</p>
            <div style={styles.warning}>
              <strong>تذکر:</strong> شما نباید هیچ‌گونه اطلاعات طبقه‌بندی‌شده، محرمانه سازمانی، پرونده قضایی محرمانه، یا داده‌ای که طبق قرارداد محرمانگی متعلق به شما نیست را وارد کنید.
            </div>

            <p style={styles.paragraph}><strong>۳) داده خروجی (Output):</strong></p>
            <p style={styles.paragraph}>محتوای تولیدشده توسط مدل‌های هوش مصنوعی. این داده خروجی ممکن است مشابه موارد تولیدشده برای کاربران دیگر باشد.</p>

            <p style={styles.paragraph}><strong>۴) داده فنی – Usage / Log / Device:</strong></p>
            <ul style={styles.list}>
              <li style={styles.listItem}>IP</li>
              <li style={styles.listItem}>نوع دستگاه و مرورگر</li>
              <li style={styles.listItem}>صفحات بازدیدشده</li>
              <li style={styles.listItem}>زمان‌های مراجعه</li>
              <li style={styles.listItem}>رفتار کلی کاربر در سرویس (بدون قابلیت شناسایی مستقیم)</li>
            </ul>

            <p style={styles.paragraph}><strong>۵) کوکی‌ها (Cookies):</strong></p>
            <p style={styles.paragraph}>سامانه از کوکی‌های ضروری، عملکردی و تحلیلی برای ارائه سرویس استفاده می‌کند. کاربر می‌تواند کوکی‌ها را در مرورگر خود غیرفعال کند، اما ممکن است برخی امکانات از دسترس خارج شود.</p>

            <h2 style={styles.sectionTitle}>۳. هدف استفاده از داده‌ها</h2>
            <p style={styles.paragraph}>ما از داده‌های جمع‌آوری‌شده برای اهداف زیر استفاده می‌کنیم:</p>
            <ul style={styles.list}>
              <li style={styles.listItem}>ارائه و نگهداری سرویس</li>
              <li style={styles.listItem}>احراز هویت</li>
              <li style={styles.listItem}>ارتباط با کاربر و پشتیبانی</li>
              <li style={styles.listItem}>پیشگیری از سوءاستفاده و فعالیت‌های غیرقانونی</li>
              <li style={styles.listItem}>بهبود سرویس، پژوهش، آموزش مدل‌ها و تحلیل استفاده</li>
              <li style={styles.listItem}>شخصی‌سازی تجربه کاربری</li>
              <li style={styles.listItem}>مدیریت تراکنش‌ها و امور مالی</li>
              <li style={styles.listItem}>رعایت الزامات قانونی کشور</li>
            </ul>
            <p style={styles.paragraph}>سامانه ممکن است داده‌های ورودی، خروجی و بازخوردها را به‌صورت ناشناس و بدون امکان شناسایی فرد برای بهبود مدل‌ها و توسعه سرویس استفاده کند.</p>

            <h2 style={styles.sectionTitle}>۴. اشتراک‌گذاری داده‌ها</h2>
            <p style={styles.paragraph}><strong>سامانه داده شخصی کاربران را نمی‌فروشد.</strong></p>
            <p style={styles.paragraph}>اشتراک‌گذاری داده فقط در موارد زیر انجام می‌شود:</p>
            <ul style={styles.list}>
              <li style={styles.listItem}>ارائه‌دهندگان زیرساخت (مانند OpenAI، Anthropic، Google) در چارچوب API</li>
              <li style={styles.listItem}>شرکت‌های ارائه‌دهنده سرویس‌های امنیتی، پیامکی یا پرداخت</li>
              <li style={styles.listItem}>مواردی که قانون کشور الزام کرده باشد (درخواست مراجع ذی‌صلاح)</li>
              <li style={styles.listItem}>پیشگیری از تقلب، حمله سایبری یا سوءاستفاده</li>
              <li style={styles.listItem}>انتقال اجباری داده در صورت تغییر مالکیت سرویس (در حد نیاز)</li>
            </ul>
            <p style={styles.paragraph}>هیچ‌گونه اطلاعاتی که به‌طور مستقیم فرد را شناسایی کند بدون رضایت کاربر به اشخاص ثالث ارائه نمی‌شود مگر در موارد قانونی.</p>

            <h2 style={styles.sectionTitle}>۵. نگهداری و حذف داده‌ها</h2>
            <ul style={styles.list}>
              <li style={styles.listItem}>داده‌ها تا زمانی نگهداری می‌شوند که حساب کاربر فعال باشد.</li>
              <li style={styles.listItem}>پس از درخواست حذف حساب، داده‌های قابل شناسایی ظرف حداکثر ۳۰ روز حذف می‌شوند مگر:
                <ul style={{...styles.list, marginTop: '8px'}}>
                  <li style={styles.listItem}>مراجع قانونی نگهداری را الزام کنند</li>
                  <li style={styles.listItem}>داده برای پیشگیری از سوءاستفاده یا مسائل امنیتی لازم باشد</li>
                </ul>
              </li>
            </ul>
            <p style={styles.paragraph}>داده‌های خروجی و داده‌های ناشناس‌شده می‌توانند برای پژوهش و بهبود سیستم باقی بمانند.</p>

            <h2 style={styles.sectionTitle}>۶. امنیت داده‌ها</h2>
            <p style={styles.paragraph}>ما از استانداردهای امنیتی مناسب مانند رمزگذاری، محدودسازی دسترسی و مانیتورینگ استفاده می‌کنیم.</p>
            <p style={styles.paragraph}>با این حال هیچ سیستم آنلاین امنیت ۱۰۰٪ تضمین‌شده ندارد.</p>
            <p style={styles.paragraph}><strong>مسئولیت نگهداری ایمن رمز عبور و اطلاعات حساب با کاربر است.</strong></p>

            <h2 style={styles.sectionTitle}>۷. حریم خصوصی کودکان</h2>
            <p style={styles.paragraph}>استفاده از سرویس برای افراد زیر ۱۸ سال فقط با نظارت و رضایت ولی قانونی مجاز است.</p>

            <h2 style={styles.sectionTitle}>۸. حقوق کاربران</h2>
            <p style={styles.paragraph}>کاربر می‌تواند:</p>
            <ul style={styles.list}>
              <li style={styles.listItem}>درخواست دسترسی به داده‌های خود را ثبت کند</li>
              <li style={styles.listItem}>درخواست اصلاح یا به‌روزرسانی دهد</li>
              <li style={styles.listItem}>درخواست حذف حساب و اطلاعات بدهد</li>
              <li style={styles.listItem}>از دریافت پیام‌های تبلیغاتی انصراف دهد</li>
            </ul>

            <h2 style={styles.sectionTitle}>۹. تغییرات این سیاست</h2>
            <p style={styles.paragraph}>سامانه ممکن است این سیاست را به‌روزرسانی کند.</p>
            <p style={styles.paragraph}>تاریخ آخرین تغییر در بالای صفحه درج می‌شود.</p>
            <p style={styles.paragraph}>استفاده ادامه‌دار از سرویس به منزله پذیرش نسخه جدید است.</p>

            <h2 style={styles.sectionTitle}>۱۰. راه‌های تماس</h2>
            <div style={styles.contact}>
              <p style={{margin: '0 0 8px 0'}}>برای هرگونه سؤال یا درخواست:</p>
              <p style={{margin: '0 0 4px 0', fontWeight: 'bold', fontSize: '18px', direction: 'ltr'}}>021-91097737</p>
              <p style={{margin: 0}}>ایمیل: <a href="mailto:info@tejarat.chat" style={{color: '#667eea'}}>info@tejarat.chat</a></p>
            </div>
          </div>
        ) : (
          /* English Content */
          <div style={styles.content}>
            <p style={styles.paragraph}>
              This Privacy Policy describes how the Smart Business Advisor / Smart Legal Advisor platform at tejarat.chat collects, uses, stores, and protects your personal data. By using the Service, you agree to this Policy.
            </p>

            <h2 style={styles.sectionTitle}>1. Definitions</h2>
            <ul style={styles.list}>
              <li style={styles.listItem}><strong>"We", "Platform":</strong> The AI-based platform providing legal-tech, business advisory, and AI assistant services.</li>
              <li style={styles.listItem}><strong>"User":</strong> Any individual or legal entity using the Service.</li>
              <li style={styles.listItem}><strong>"Personal Data":</strong> Any data that can identify a person.</li>
              <li style={styles.listItem}><strong>"Input Data":</strong> Information that you enter into the chat or tools.</li>
              <li style={styles.listItem}><strong>"Output Data":</strong> AI-generated responses.</li>
              <li style={styles.listItem}><strong>"Technical Data":</strong> IP, device info, logs, and analytics.</li>
            </ul>

            <h2 style={styles.sectionTitle}>2. Data We Collect</h2>
            <p style={styles.paragraph}><strong>Identification and contact information:</strong></p>
            <ul style={styles.list}>
              <li style={styles.listItem}>Name</li>
              <li style={styles.listItem}>Phone number</li>
              <li style={styles.listItem}>Email</li>
            </ul>

            <p style={styles.paragraph}><strong>Input Data:</strong></p>
            <p style={styles.paragraph}>All data you enter into the Service.</p>
            <div style={styles.warning}>
              <strong>Warning:</strong> Do not enter confidential, classified, or non-public information belonging to others.
            </div>

            <p style={styles.paragraph}><strong>Output Data:</strong></p>
            <p style={styles.paragraph}>AI-generated content based on your input.</p>

            <p style={styles.paragraph}><strong>Technical and Usage Data:</strong></p>
            <ul style={styles.list}>
              <li style={styles.listItem}>IP address</li>
              <li style={styles.listItem}>Browser/device information</li>
              <li style={styles.listItem}>Pages visited</li>
              <li style={styles.listItem}>Timestamps</li>
              <li style={styles.listItem}>Usage patterns</li>
            </ul>

            <p style={styles.paragraph}><strong>Cookies:</strong></p>
            <p style={styles.paragraph}>We use essential, functional, and analytics cookies.</p>

            <h2 style={styles.sectionTitle}>3. How We Use Your Data</h2>
            <p style={styles.paragraph}>We use data to:</p>
            <ul style={styles.list}>
              <li style={styles.listItem}>Provide and maintain the Service</li>
              <li style={styles.listItem}>Authenticate users</li>
              <li style={styles.listItem}>Communicate with you</li>
              <li style={styles.listItem}>Detect fraud or misuse</li>
              <li style={styles.listItem}>Improve features, train systems, and perform research (in anonymized form)</li>
              <li style={styles.listItem}>Personalize the user experience</li>
              <li style={styles.listItem}>Comply with legal obligations</li>
            </ul>

            <h2 style={styles.sectionTitle}>4. Sharing Your Data</h2>
            <p style={styles.paragraph}><strong>We do not sell personal data.</strong></p>
            <p style={styles.paragraph}>Data may be shared with:</p>
            <ul style={styles.list}>
              <li style={styles.listItem}>Infrastructure providers such as OpenAI, Anthropic, Google</li>
              <li style={styles.listItem}>Security, SMS, or payment service providers</li>
              <li style={styles.listItem}>Legal authorities when required by law</li>
              <li style={styles.listItem}>To prevent fraud or cyberattacks</li>
              <li style={styles.listItem}>In case of business transfer or acquisition</li>
            </ul>
            <p style={styles.paragraph}>Only the minimum necessary data is shared.</p>

            <h2 style={styles.sectionTitle}>5. Data Retention and Deletion</h2>
            <ul style={styles.list}>
              <li style={styles.listItem}>Data is retained as long as the account is active.</li>
              <li style={styles.listItem}>Upon account deletion, identifiable data is deleted within 30 days unless:
                <ul style={{...styles.list, marginTop: '8px'}}>
                  <li style={styles.listItem}>Law requires longer retention</li>
                  <li style={styles.listItem}>Security or compliance reasons require retention</li>
                </ul>
              </li>
            </ul>
            <p style={styles.paragraph}>Anonymized data may be preserved for research.</p>

            <h2 style={styles.sectionTitle}>6. Data Security</h2>
            <p style={styles.paragraph}>We use industry-standard technical and organizational measures.</p>
            <p style={styles.paragraph}>However, no system is 100% secure.</p>

            <h2 style={styles.sectionTitle}>7. Children's Privacy</h2>
            <p style={styles.paragraph}>Services are intended for users 18+. Minors may use the Service only with parental/legal guardian consent.</p>

            <h2 style={styles.sectionTitle}>8. User Rights</h2>
            <p style={styles.paragraph}>You may:</p>
            <ul style={styles.list}>
              <li style={styles.listItem}>Request access to your data</li>
              <li style={styles.listItem}>Request correction or update</li>
              <li style={styles.listItem}>Request deletion of your account</li>
              <li style={styles.listItem}>Opt out of promotional messages</li>
            </ul>

            <h2 style={styles.sectionTitle}>9. Changes to this Policy</h2>
            <p style={styles.paragraph}>We may update this Policy periodically.</p>
            <p style={styles.paragraph}>Continued use of the Service constitutes acceptance of changes.</p>

            <h2 style={styles.sectionTitle}>10. Contact</h2>
            <div style={styles.contact}>
              <p style={{margin: '0 0 8px 0'}}>For any questions or requests:</p>
              <p style={{margin: '0 0 4px 0', fontWeight: 'bold', fontSize: '18px'}}>021-91097737</p>
              <p style={{margin: 0}}>Email: <a href="mailto:info@tejarat.chat" style={{color: '#667eea'}}>info@tejarat.chat</a></p>
            </div>
          </div>
        )}
        
        <Link href="/auth/login" style={styles.backLink}>
          {language === 'fa' ? 'بازگشت به صفحه ورود' : 'Back to Login'}
        </Link>
      </div>
    </div>
  )
}
