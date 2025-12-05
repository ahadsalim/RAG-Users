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
        <p style={styles.updateDate}>به‌روز‌رسانی: ۱۴۰۳/۰۹/۱۵</p>
        
        <div style={styles.content}>
          {/* بخش ۱ */}
          <h2 style={styles.sectionTitle}>۱- تعریف اصطلاحات</h2>
          <p style={styles.paragraph}>
            <strong>سامانه مشاور هوشمند کسب و کار:</strong> به معنای پلتفرم و وبسایت به نشانی tejarat.chat است که با استفاده از API های ارائه‌دهندگان مختلف هوش مصنوعی شامل OpenAI، Anthropic، Google و سایر ارائه‌دهندگان، زمینه استفاده از سرویس‌های چت هوشمند و مشاوره کسب و کار را در اختیار کاربران قرار می‌دهد.
          </p>
          <p style={styles.paragraph}>
            <strong>کاربر:</strong> به معنای هر شخص حقیقی یا حقوقی است که اقدام به ایجاد حساب کاربری در سامانه می‌نماید و طرف دوم این قرارداد محسوب می‌شود.
          </p>
          <p style={styles.paragraph}>
            <strong>اعتبار حساب:</strong> به معنای معادل ریالی ظرفیت استفاده از سامانه است که کاربر متناسب با پلن انتخابی خود از آن بهره‌مند است.
          </p>
          <p style={styles.paragraph}>
            <strong>داده ورودی (Input):</strong> به معنای مجموع داده‌ای است که کاربر در قسمت چت وارد می‌کند و سپس به مدل هوش مصنوعی داده می‌شود.
          </p>
          <p style={styles.paragraph}>
            <strong>داده خروجی (Output):</strong> به معنای داده‌ای است که به صورت هوشمند و متناظر با داده ورودی، توسط هوش مصنوعی تولید و در معرض نمایش کاربر قرار می‌گیرد.
          </p>

          {/* بخش ۲ */}
          <h2 style={styles.sectionTitle}>۲- الزامات عمومی استفاده از سامانه</h2>
          <ul style={styles.list}>
            <li style={styles.listItem}>ثبت‌نام در سامانه، ورود به حساب کاربری و یا هر استفاده بعدی، به منزله پذیرش مفاد قرارداد حاضر است.</li>
            <li style={styles.listItem}>کاربر تأیید می‌کند که در زمان پذیرش این مقررات دارای حداقل سن قانونی و اهلیت لازم جهت انعقاد قرارداد است.</li>
            <li style={styles.listItem}>کاربر متعهد است در زمان ثبت‌نام، اطلاعات صحیح، کامل، دقیق و متعلق به خود را وارد نماید.</li>
            <li style={styles.listItem}>کاربر نمی‌تواند حساب کاربری خود را بدون اجازه به دیگران منتقل نماید.</li>
            <li style={styles.listItem}>کاربر تعهد می‌نماید که از سامانه به نحوی که به منزله سوء استفاده، نقض حقوق دیگران و نقض قوانین و مقررات کشور باشد استفاده نکند.</li>
            <li style={styles.listItem}>کاربران برای استفاده از سرویس باید حداقل ۱۸ سال داشته باشند. برای کاربران زیر این سن، استفاده با رضایت و نظارت والدین مجاز است.</li>
          </ul>
          
          <p style={styles.paragraph}>کاربران نمی‌توانند از سرویس‌های سامانه برای موارد زیر استفاده کنند:</p>
          <ul style={styles.list}>
            <li style={styles.listItem}>فعالیت‌های غیرقانونی یا تسهیل آن</li>
            <li style={styles.listItem}>تولید یا انتشار محتوای مضر، توهین‌آمیز یا نفرت‌پراکنانه</li>
            <li style={styles.listItem}>نقض حقوق مالکیت فکری دیگران</li>
            <li style={styles.listItem}>ایجاد محتوای جعلی برای فریب</li>
            <li style={styles.listItem}>استخراج خودکار داده‌ها یا مهندسی معکوس</li>
            <li style={styles.listItem}>دور زدن محدودیت‌های فنی یا امنیتی</li>
            <li style={styles.listItem}>ایجاد اختلال در ارائه سرویس یا حملات سایبری</li>
            <li style={styles.listItem}>استفاده در حوزه‌های حساس بدون نظارت انسانی (پزشکی، حقوقی، مالی)</li>
          </ul>

          {/* بخش ۳ */}
          <h2 style={styles.sectionTitle}>۳- شرایط مرجوعی و بازپرداخت</h2>
          <p style={styles.paragraph}>
            <strong>درخواست بازپرداخت:</strong> کاربران می‌توانند درخواست مرجوعی سرویس خریداری‌شده را در هر زمانی پس از خرید و با ارائه‌ی توضیح دقیق درباره مشکل یا نقص ایجاد شده ثبت کنند. پس از دریافت درخواست، وضعیت و صحت مشکل بررسی می‌شود و در صورت تایید وجود نقص، فرایند بازپرداخت آغاز خواهد شد.
          </p>
          <p style={styles.paragraph}>
            <strong>میزان بازپرداخت:</strong> در صورتی که درخواست مرجوعی پذیرفته شود، مبلغ بازپرداخت بر اساس مدت زمان استفاده نشده از سرویس محاسبه می‌شود.
          </p>
          <p style={styles.paragraph}>
            <strong>حق رد درخواست:</strong> تیم سامانه این حق را برای خود محفوظ می‌دارد که در شرایط خاص و بنا بر صلاحدید، درخواست مرجوعی را نپذیرد.
          </p>

          {/* بخش ۴ */}
          <h2 style={styles.sectionTitle}>۴- الزامات راجع به داده ورودی</h2>
          <p style={styles.paragraph}>کاربران نمی‌توانند داده‌هایی را به عنوان ورودی وارد کنند که متضمن موارد زیر باشد:</p>
          <ul style={styles.list}>
            <li style={styles.listItem}>هرگونه هتک حرمت و حیثیت از قبیل توهین، تحقیر و استعمال الفاظ رکیک</li>
            <li style={styles.listItem}>هرگونه افترا یا نشر اکاذیب و نفرت‌پراکنی نسبت به اشخاص، دولت‌ها، ملیت‌ها، ادیان و مذاهب</li>
            <li style={styles.listItem}>هرگونه محتوای ضد عفت و اخلاق عمومی از قبیل محتویات مستهجن و مبتذل</li>
            <li style={styles.listItem}>هرگونه محتوای متضمن ترویج یا تشویق خشونت</li>
            <li style={styles.listItem}>هرگونه محتوای محرمانه از قبیل اسرار و اطلاعات محرمانه طبقه‌بندی‌شده</li>
            <li style={styles.listItem}>هرگونه اطلاعات ناظر به حریم خصوصی و حقوق مالکیت فکری مربوط به اشخاص ثالث</li>
          </ul>

          {/* بخش ۵ */}
          <h2 style={styles.sectionTitle}>۵- الزامات راجع به داده خروجی</h2>
          <p style={styles.paragraph}>
            داده‌های خروجی به وسیله سیستم هوشمند غیرانسانی تولید می‌شود و درنتیجه کاربران نباید داده‌های خروجی را منتسب به انسان بدانند. کاربران مجازند هرگونه استفاده‌ای اعم از تجاری و غیرتجاری از داده‌های خروجی نمایند، مشروط بر آنکه:
          </p>
          <ul style={styles.list}>
            <li style={styles.listItem}>داده‌های خروجی را به عنوان محتوای تولیدشده توسط هوش مصنوعی مشخص کنند (در صورت انتشار عمومی)</li>
            <li style={styles.listItem}>از انتساب نادرست داده‌های خروجی به افراد واقعی یا منابع معتبر خودداری کنند</li>
            <li style={styles.listItem}>مسئولیت صحت و دقت داده‌های خروجی را قبل از استفاده در موارد مهم بررسی کنند</li>
          </ul>
          <p style={styles.paragraph}>
            <strong>هشدار مهم:</strong> هوش مصنوعی مولد در معرض خطاهای بسیار است و ممکن است داده خروجی به لحاظ علمی دچار ایراداتی باشد. کاربر باید دقت هر کدام از داده‌های خروجی را متناسب با نیازمندی خود صحت‌سنجی کند. توصیه می‌شود کاربران در مورد مسائل حساسی از قبیل پیشنهاد دارو برای درمان بیماری، مشاوره حقوقی، پیش‌بینی وقایع و موارد مشابه، حتماً با متخصصین واجد شرایط مشورت نمایند.
          </p>

          {/* بخش ۶ */}
          <h2 style={styles.sectionTitle}>۶- سیاست حریم خصوصی و مدیریت داده‌ها</h2>
          <p style={styles.paragraph}>
            <strong>اطلاعات شخصی:</strong> سامانه اطلاعات شخصی از قبیل نام، شماره تماس و سایر اطلاعاتی که هنگام ثبت‌نام جمع‌آوری می‌شود را به منظور ارائه سرویس، احراز هویت، ارتباط با کاربر و پشتیبانی فنی در سیستم ذخیره می‌کند. سامانه متعهد است از این اطلاعات با رعایت استانداردهای امنیتی مناسب محافظت کرده و بدون رضایت کاربر آن را با اشخاص ثالث به اشتراک نگذارد، مگر در موارد قانونی.
          </p>
          <p style={styles.paragraph}>
            سامانه مجاز است اطلاعات ناشی از استفاده از سرویس را بدون آنکه انتساب آن به کاربر را افشا نماید، صرفاً به منظور مقاصد پژوهشی و توسعه‌ای مانند بهبود سرویس‌ها و تجربه کاربری استفاده نماید.
          </p>
          <p style={styles.paragraph}>
            <strong>محدودیت مسؤولیت مالی:</strong> در حداکثر مجاز قانونی، مسؤولیت سامانه در قبال هر ادعا یا خسارت ناشی از استفاده از سرویس، محدود به مبلغ پرداختی کاربر برای سرویس در ماه گذشته خواهد بود.
          </p>

          {/* بخش ۷ */}
          <h2 style={styles.sectionTitle}>۷- مالکیت فکری و حقوق مربوط به داده‌ها</h2>
          <p style={styles.paragraph}>
            <strong>مالکیت داده‌های ورودی:</strong> کاربران مالک داده‌های ورودی خود هستند و مسئولیت کامل محتوای آن‌ها را بر عهده دارند.
          </p>
          <p style={styles.paragraph}>
            <strong>مالکیت داده‌های خروجی:</strong> با رعایت این قرارداد، سامانه تمام حقوق خود در داده‌های خروجی را به کاربر واگذار می‌کند. کاربر می‌تواند از داده‌های خروجی برای هر منظور قانونی استفاده کند.
          </p>
          <p style={styles.paragraph}>
            <strong>توجه:</strong> داده‌های خروجی ممکن است برای کاربران مختلف مشابه یا یکسان باشد، بنابراین سامانه نمی‌تواند انحصار یا یکتایی داده‌های خروجی را تضمین کند.
          </p>

          {/* بخش ۸ */}
          <h2 style={styles.sectionTitle}>۸- ضمانت اجرا</h2>
          <p style={styles.paragraph}>
            در صورتیکه تخلف از هر یک از موارد مندرج در این قرارداد محرز شود، ضمن اطلاع‌رسانی برای کاربر، دسترسی‌ها یا حساب کاربری وی مسدود خواهد شد. چنانچه کاربر با این تصمیم مخالف باشد، می‌تواند مراتب اعتراض و توضیحات خود را ارائه نماید.
          </p>

          {/* بخش ۹ */}
          <h2 style={styles.sectionTitle}>۹- عوامل خارج از اراده (قوه قاهره)</h2>
          <p style={styles.paragraph}>در صورت بروز عوامل خارج از اراده و کنترل سامانه از جمله موارد زیر، سامانه مسؤولیتی در قبال عدم ارائه یا اختلال در سرویس نخواهد داشت:</p>
          <ul style={styles.list}>
            <li style={styles.listItem}>قطعی اینترنت، اختلالات شبکه یا زیرساخت ارتباطی</li>
            <li style={styles.listItem}>اختلالات و قطعی سرویس API از سوی ارائه‌دهندگان هوش مصنوعی</li>
            <li style={styles.listItem}>دستور قطعی سرویس از سوی مراجع ذیصلاح یا دستورهای قضایی</li>
            <li style={styles.listItem}>تحریم‌های بین‌المللی، تغییرات قوانین و مقررات</li>
            <li style={styles.listItem}>حملات سایبری و مسائل امنیتی</li>
            <li style={styles.listItem}>بلایای طبیعی، جنگ و سایر حوادث غیرمترقبه</li>
          </ul>

          {/* بخش ۱۰ */}
          <h2 style={styles.sectionTitle}>۱۰- تغییرات در شرایط و خاتمه قرارداد</h2>
          <ul style={styles.list}>
            <li style={styles.listItem}>سامانه این حق را برای خود محفوظ می‌دارد که این شرایط استفاده را در هر زمان تغییر دهد.</li>
            <li style={styles.listItem}>ادامه استفاده از سرویس پس از اعمال تغییرات، به منزله پذیرش شرایط جدید است.</li>
            <li style={styles.listItem}>کاربران می‌توانند در هر زمان حساب کاربری خود را حذف کنند.</li>
            <li style={styles.listItem}>سامانه می‌تواند در صورت نقض شرایط استفاده، حساب کاربری را معلق یا حذف کند.</li>
          </ul>

          {/* بخش ۱۱ */}
          <h2 style={styles.sectionTitle}>۱۱- سازوکار حل اختلاف</h2>
          <p style={styles.paragraph}>
            در صورت بروز هرگونه اختلاف میان سامانه و کاربر، کاربر موظف است ابتدا از طریق راه‌های ارتباطی پیش‌بینی‌شده، با پشتیبانی سامانه ارتباط برقرار نموده و موضوع مربوطه را جهت بررسی گزارش نماید.
          </p>

          {/* بخش ۱۲ */}
          <h2 style={styles.sectionTitle}>۱۲- ارزش اثباتی قرارداد</h2>
          <p style={styles.paragraph}>
            این قرارداد در ۱۲ بخش تنظیم شده و تأیید آن از سوی کاربر بر اساس قانون تجارت الکترونیکی به‌منزله‌ی تأیید و انعقاد قرارداد بوده و دارای ارزش اثباتی معادل اسناد کاغذی است.
          </p>
        </div>
        
        <Link href="/auth/login" style={styles.backLink}>
          بازگشت به صفحه ورود
        </Link>
      </div>
    </div>
  )
}
