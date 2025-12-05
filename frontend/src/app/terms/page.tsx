'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'

export default function TermsPage() {
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
    updateDate: {
      fontSize: '14px',
      color: theme === 'light' ? '#718096' : '#a0aec0',
      textAlign: 'center' as const,
      marginBottom: '32px',
    },
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
      borderBottom: theme === 'light' ? '2px solid #667eea' : '2px solid #667eea',
      paddingBottom: '8px',
    },
    paragraph: {
      marginBottom: '12px',
      textAlign: 'justify' as const,
    },
    list: {
      paddingRight: '24px',
      marginBottom: '16px',
    },
    listItem: {
      marginBottom: '8px',
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
        <h1 style={styles.title}>شرایط استفاده و سیاست حریم خصوصی</h1>
        <p style={styles.updateDate}>به‌روز‌رسانی: ۱۴۰۴/۰۹/۱۴</p>
        
        <div style={styles.content}>
          {/* بخش ۱ */}
          <h2 style={styles.sectionTitle}>۱) تعریف اصطلاحات</h2>
          <p style={styles.paragraph}>
            <strong>سامانه مشاور هوشمند حقوقی (سامانه):</strong> پلتفرم به نشانی tejarat.chat که با استفاده از مدل‌های هوش مصنوعی از جمله OpenAI، Anthropic، Google و سایر ارائه‌دهندگان، خدمات مشاوره اولیه، تحلیل متون و توضیح مسائل حقوقی را ارائه می‌دهد.
          </p>
          <p style={styles.paragraph}>
            <strong>کاربر:</strong> هر شخص حقیقی یا حقوقی که از سامانه استفاده می‌کند یا حساب کاربری ایجاد می‌نماید.
          </p>
          <p style={styles.paragraph}>
            <strong>اعتبار حساب:</strong> مبلغ پرداختی کاربر که امکان استفاده از خدمات سامانه را فراهم می‌کند.
          </p>
          <p style={styles.paragraph}>
            <strong>داده ورودی (Input):</strong> هرگونه متن، سؤال، سند یا اطلاعاتی که توسط کاربر وارد می‌شود.
          </p>
          <p style={styles.paragraph}>
            <strong>داده خروجی (Output):</strong> هر متن، پاسخ یا تحلیل تولیدشده توسط سامانه بر اساس داده ورودی.
          </p>
          <p style={styles.paragraph}>
            <strong>بازخورد:</strong> اعلام رضایت یا عدم‌رضایت کاربر نسبت به نتایج تولیدشده.
          </p>

          {/* بخش ۲ */}
          <h2 style={styles.sectionTitle}>۲) ماهیت خدمات سامانه</h2>
          <p style={styles.paragraph}>
            سامانه از فناوری هوش مصنوعی برای ارائه تحلیل‌ها، توضیحات، تفسیرهای عمومی حقوقی، پردازش متون، شبیه‌سازی استدلال‌ها و ارائه پیشنهادهای اولیه استفاده می‌کند.
          </p>
          <p style={styles.paragraph}><strong>مهم:</strong></p>
          <ul style={styles.list}>
            <li style={styles.listItem}>سامانه «وکیل» نیست، اما «مشاور هوشمند حقوقی» است که به کاربر در فهم بهتر موضوعات و انتخاب مسیر مناسب کمک می‌کند.</li>
            <li style={styles.listItem}>خروجی‌ها می‌توانند دید حقوقی، تحلیل متن، پیشنهاد مسیر اقدام یا فهم قوانین را تسهیل کنند.</li>
            <li style={styles.listItem}>خروجی‌ها «نظر تخصصی کمکی» هستند و نه «تعهد یا تضمین نتیجه».</li>
            <li style={styles.listItem}>کاربر مسئول ارزیابی نهایی و تصمیم‌گیری است.</li>
          </ul>
          <p style={styles.paragraph}>
            سامانه متعهد است تا حد توان، اطلاعات دقیق و تحلیل‌های معتبر ارائه دهد، اما هیچ‌گونه تضمین قطعی در خصوص نتایج یا صحت کامل خروجی‌ها ارائه نمی‌دهد.
          </p>

          {/* بخش ۳ */}
          <h2 style={styles.sectionTitle}>۳) الزامات عمومی کاربران</h2>
          <ul style={styles.list}>
            <li style={styles.listItem}>استفاده از سامانه به معنای پذیرش کامل این شرایط است.</li>
            <li style={styles.listItem}>کاربر باید اطلاعات صحیح ارائه دهد و در صورت تغییر، آن را به‌روزرسانی کند.</li>
            <li style={styles.listItem}>انتقال حساب کاربری بدون اجازه ممنوع است.</li>
            <li style={styles.listItem}>کاربر متعهد است از سامانه به شکل قانونی استفاده کند و حقوق اشخاص ثالث را نقض ننماید.</li>
            <li style={styles.listItem}>حداقل سن برای استفاده مستقل ۱۸ سال است. زیر ۱۸ سال با رضایت و نظارت ولی/قیم مجاز است.</li>
          </ul>
          <p style={styles.paragraph}><strong>کاربران مجاز به انجام موارد زیر نیستند:</strong></p>
          <ul style={styles.list}>
            <li style={styles.listItem}>فعالیت غیرقانونی یا تسهیل آن</li>
            <li style={styles.listItem}>انتشار محتوای مضر، توهین‌آمیز، مستهجن یا نفرت‌پراکن</li>
            <li style={styles.listItem}>نقض حقوق مالکیت فکری دیگران</li>
            <li style={styles.listItem}>تولید محتوای جعلی برای فریب یا جعل سند</li>
            <li style={styles.listItem}>استخراج داده‌های سامانه، Scraping، یا مهندسی معکوس</li>
            <li style={styles.listItem}>تلاش برای دور‌زدن محدودیت‌ها یا حمله به سرویس</li>
            <li style={styles.listItem}>استفاده از سامانه برای تصمیم‌گیری‌های بسیار حساس بدون بررسی و ارزیابی مستقل</li>
            <li style={styles.listItem}>بارگذاری محتوای محرمانه‌ای که کاربر اجازه قانونی افشای آن را ندارد</li>
          </ul>

          {/* بخش ۴ */}
          <h2 style={styles.sectionTitle}>۴) الزامات مربوط به داده ورودی</h2>
          <p style={styles.paragraph}><strong>کاربر تأیید می‌کند که:</strong></p>
          <ul style={styles.list}>
            <li style={styles.listItem}>مالک، صاحب اختیار یا دارای اجازه استفاده از داده‌های ورودی است.</li>
            <li style={styles.listItem}>داده ورودی ناقض حریم خصوصی، اسرار تجاری، اطلاعات محرمانه سازمان‌ها یا مفاد قراردادهای عدم افشا نیست.</li>
            <li style={styles.listItem}>هیچ‌گونه داده غیرقانونی، مستهجن، خشونت‌آمیز، یا حاوی تهدید ارائه نمی‌کند.</li>
            <li style={styles.listItem}>هیچ سند یا اطلاعاتی که افشای آن ممنوع است (مثلاً اطلاعات طبقه‌بندی‌شده، اطلاعات حساس سازمانی و…) وارد نمی‌کند.</li>
          </ul>
          <p style={styles.paragraph}>
            سامانه هیچ مسئولیتی در قبال عواقب ناشی از ارائه داده ورودی غیرمجاز توسط کاربر ندارد.
          </p>

          {/* بخش ۵ */}
          <h2 style={styles.sectionTitle}>۵) الزامات مربوط به داده خروجی</h2>
          <p style={styles.paragraph}>
            داده خروجی توسط سیستم تولید می‌شود و انسان آن را ننوشته است. کاربر باید بداند:
          </p>
          <ul style={styles.list}>
            <li style={styles.listItem}>خروجی‌ها تحلیل خودکار هستند و ممکن است شامل خطا، ابهام یا برداشت ناقص باشند.</li>
            <li style={styles.listItem}>خروجی‌ها قطعی، الزام‌آور یا جایگزین بررسی انسانی نیستند، بلکه «ابزار کمک‌تحلیلی» محسوب می‌شوند.</li>
            <li style={styles.listItem}>کاربر باید قبل از استفاده عملی، موارد مهم را ارزیابی کند.</li>
            <li style={styles.listItem}>در صورت انتشار خروجی، ذکر «تولید‌شده توسط هوش مصنوعی» الزامی است.</li>
            <li style={styles.listItem}>انتساب نادرست خروجی به اشخاص ممنوع است.</li>
            <li style={styles.listItem}>کاربر مسئول استفاده از داده خروجی است.</li>
          </ul>

          {/* بخش ۶ */}
          <h2 style={styles.sectionTitle}>۶) سیاست حریم خصوصی و مدیریت داده‌ها</h2>
          <p style={styles.paragraph}>
            <strong>اطلاعات شخصی:</strong> سامانه اطلاعاتی مانند نام، شماره تماس، ایمیل و اطلاعات ثبت‌نام را ذخیره می‌کند و فقط برای ارائه خدمات، امنیت، احراز هویت و پشتیبانی استفاده می‌شود.
          </p>
          <p style={styles.paragraph}><strong>سامانه همچنین مجاز است:</strong></p>
          <ul style={styles.list}>
            <li style={styles.listItem}>داده‌های فنی شامل لاگ سرور، نوع دستگاه، زمان استفاده و کوکی‌ها را نگهداری کند.</li>
            <li style={styles.listItem}>داده‌های ورودی، خروجی و بازخوردها را صرفاً برای بهبود کیفیت، توسعه خدمات و تحلیل عملکرد استفاده کند.</li>
            <li style={styles.listItem}>هیچ‌یک از داده‌ها را بدون حکم قانونی یا ضرورت عملیاتی افشا نکند.</li>
          </ul>
          <p style={styles.paragraph}>
            اطلاعات شخصی به‌محض درخواست حذف حساب، پاک می‌شود، مگر در موارد الزامی قانونی.
          </p>

          {/* بخش ۷ */}
          <h2 style={styles.sectionTitle}>۷) مالکیت فکری</h2>
          <ul style={styles.list}>
            <li style={styles.listItem}>کاربر مالک داده ورودی خود است.</li>
            <li style={styles.listItem}>کاربر مسئول کامل محتوای ورودی است.</li>
            <li style={styles.listItem}>سامانه حقوق مالکیت فکری خود را بر وب‌سایت، کدها، طراحی، برند، مدل‌ها، مستندات و سایر اجزای سیستم محفوظ می‌دارد.</li>
            <li style={styles.listItem}>کاربران بدون اجازه کتبی حق کپی، استخراج، فروش، انتشار یا ساخت سرویس مشابه بر اساس ساختار سامانه را ندارند.</li>
          </ul>
          <p style={styles.paragraph}>
            <strong>مالکیت داده خروجی:</strong> سامانه حقوق خود را در داده خروجی به کاربر واگذار می‌کند؛ اما سامانه حق استفاده از خروجی‌ها برای آموزش و بهبود سیستم را حفظ می‌کند (بدون افشای هویت کاربر).
          </p>
          <p style={styles.paragraph}>
            خروجی‌ها ممکن است برای کاربران مختلف مشابه باشد و سامانه انحصار یا یکتایی آن‌ها را تضمین نمی‌کند.
          </p>

          {/* بخش ۸ */}
          <h2 style={styles.sectionTitle}>۸) محدودیت مسئولیت</h2>
          <p style={styles.paragraph}>
            حداکثر مسئولیت سامانه در قبال هر ادعا، برابر با مبلغ پرداخت‌شده توسط کاربر در ماه گذشته است.
          </p>
          <p style={styles.paragraph}>
            سامانه تحت هیچ شرایطی مسئول خسارات غیرمستقیم، تبعی، از‌دست‌رفتن داده یا خسارات ناشی از برداشت اشتباه کاربر نیست.
          </p>

          {/* بخش ۹ */}
          <h2 style={styles.sectionTitle}>۹) شرایط بازپرداخت</h2>
          <ul style={styles.list}>
            <li style={styles.listItem}>کاربر می‌تواند درخواست بازپرداخت ارائه کند.</li>
            <li style={styles.listItem}>در صورت تأیید وجود نقص واقعی در سرویس، بازپرداخت بر اساس میزان اعتبار مصرف‌نشده محاسبه می‌شود.</li>
            <li style={styles.listItem}>سامانه حق دارد درخواست‌هایی را که فاقد دلیل معتبر باشند رد کند.</li>
            <li style={styles.listItem}>در صورت تخلف کاربر و مسدودی حساب، هیچ مبلغی عودت داده نخواهد شد.</li>
          </ul>

          {/* بخش ۱۰ */}
          <h2 style={styles.sectionTitle}>۱۰) قوه قاهره (Force Majeure)</h2>
          <p style={styles.paragraph}>در صورت وقوع اختلالات زیر، سامانه مسئولیتی در قبال توقف سرویس ندارد:</p>
          <ul style={styles.list}>
            <li style={styles.listItem}>قطعی اینترنت</li>
            <li style={styles.listItem}>مشکلات دیتاسنتر یا ارائه‌دهندگان API</li>
            <li style={styles.listItem}>حملات سایبری</li>
            <li style={styles.listItem}>تغییرات قانونی</li>
            <li style={styles.listItem}>بلایای طبیعی یا شرایط اضطراری</li>
          </ul>
          <p style={styles.paragraph}>
            در صورت قطع طولانی‌مدت (بیش از ۶۰ روز)، سامانه می‌تواند ارائه خدمات را خاتمه دهد و نسبت به بسته‌های استفاده‌نشده مطابق شرایط خود تصمیم‌گیری کند.
          </p>

          {/* بخش ۱۱ */}
          <h2 style={styles.sectionTitle}>۱۱) شرایط استفاده از API</h2>
          <ul style={styles.list}>
            <li style={styles.listItem}>توسعه‌دهندگان باید کلید API را محرمانه نگه دارند.</li>
            <li style={styles.listItem}>استفاده بیش از حد یا سوءاستفاده موجب محدودیت یا قطع دسترسی می‌شود.</li>
            <li style={styles.listItem}>توسعه‌دهندگان نمی‌توانند سرویس مشابه یا رقیب مستقیم ایجاد کنند.</li>
            <li style={styles.listItem}>باید کاربران نهایی را از استفاده سامانه به‌عنوان ارائه‌دهنده خدمات هوش مصنوعی مطلع کنند.</li>
          </ul>

          {/* بخش ۱۲ */}
          <h2 style={styles.sectionTitle}>۱۲) تغییرات در شرایط</h2>
          <p style={styles.paragraph}>
            سامانه می‌تواند شرایط را در هر زمان تغییر دهد. ادامه استفاده به معنای پذیرش نسخه جدید است.
          </p>
          <p style={styles.paragraph}>
            در صورت عدم موافقت، کاربر می‌تواند از سرویس خارج شود.
          </p>

          {/* بخش ۱۳ */}
          <h2 style={styles.sectionTitle}>۱۳) حل اختلاف</h2>
          <p style={styles.paragraph}>
            در صورت اختلاف، ابتدا موضوع از طریق پشتیبانی سامانه بررسی می‌شود.
          </p>
          <p style={styles.paragraph}>
            اگر موضوع حل نشود، اختلاف مطابق قوانین ایران و توسط مرجع صالح قضایی یا مرکز داوری مورد توافق طرفین حل‌وفصل خواهد شد.
          </p>

          {/* بخش ۱۴ */}
          <h2 style={styles.sectionTitle}>۱۴) ارزش اثباتی</h2>
          <p style={styles.paragraph}>
            «تأیید و پذیرش این شرایط توسط کاربر، اعم از ثبت‌نام، ورود یا استفاده از سامانه، طبق مواد ۶، ۷ و ۱۲ قانون تجارت الکترونیکی، به منزله «رضایت صریح» و «امضای الکترونیکی معتبر» بوده و از حیث اعتبار و آثار حقوقی، معادل اسناد و قراردادهای کتبی و قابل استناد در مراجع قضایی و داوری است.»
          </p>
        </div>
        
        <Link href="/auth/login" style={styles.backLink}>
          بازگشت به صفحه ورود
        </Link>
      </div>
    </div>
  )
}
