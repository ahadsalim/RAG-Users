import React, { useState, useEffect } from 'react';
import { X, User, Bell, Shield, CreditCard, Palette, Globe, Monitor, Brain, Building2, Smartphone, Laptop, Trash2 } from 'lucide-react';
import axios from 'axios';
import { useTheme } from 'next-themes';
import { useAuthStore } from '@/store/auth';
import MemorySection from '@/components/settings/MemorySection';
import OrganizationSection from '@/components/settings/OrganizationSection';
import CurrencySelector from '@/components/settings/CurrencySelector';
import { useCurrency } from '@/hooks/useCurrency';

const API_URL = process.env.NEXT_PUBLIC_API_URL || '';

interface SettingsPageProps {
  isOpen: boolean;
  onClose: () => void;
}

type SettingsTab = 'profile' | 'subscription' | 'memory' | 'organization' | 'preferences' | 'notifications' | 'security' | 'sessions';

interface UserSettings {
  // Profile
  full_name: string;
  company_name: string;
  email: string;
  phone: string;
  national_id: string;
  
  // Preferences
  theme: 'light' | 'dark';
  enable_web_search: boolean | null;
}

interface SubscriptionInfo {
  plan_name: string;
  status: string;
  end_date: string;
  queries_used_today: number;
  queries_used_month: number;
  max_queries_per_day: number;
  max_queries_per_month: number;
}

const SettingsPage: React.FC<SettingsPageProps> = ({ isOpen, onClose }) => {
  const [activeTab, setActiveTab] = useState<SettingsTab>('profile');
  const { user } = useAuthStore();
  
  // بارگذاری اولیه از localStorage با توجه به user فعلی
  const getInitialSettings = (): UserSettings => {
    if (typeof window !== 'undefined') {
      const savedSettings = localStorage.getItem('userSettings');
      if (savedSettings) {
        try {
          const parsed = JSON.parse(savedSettings);
          // بررسی اینکه آیا شماره تلفن در localStorage با user فعلی مطابقت دارد
          if (user?.phone_number && parsed.phone !== user.phone_number) {
            // اگر شماره تلفن متفاوت است، localStorage قدیمی است - پاک کن
            localStorage.removeItem('userSettings');
            return {
              full_name: user?.first_name && user?.last_name ? `${user.first_name} ${user.last_name}` : '',
              company_name: user?.company_name || '',
              email: user?.email || '',
              phone: user?.phone_number || '',
              national_id: user?.national_id || '',
              theme: 'light',
              enable_web_search: null,
            };
          }
          return parsed;
        } catch (e) {
          console.error('Error loading settings:', e);
        }
      }
    }
    // اگر localStorage خالی است، از user فعلی استفاده کن
    return {
      full_name: user?.first_name && user?.last_name ? `${user.first_name} ${user.last_name}` : '',
      company_name: user?.company_name || '',
      email: user?.email || '',
      phone: user?.phone_number || '',
      national_id: user?.national_id || '',
      theme: 'light',
      enable_web_search: null,
    };
  };
  
  const [settings, setSettings] = useState<UserSettings>(getInitialSettings());
  const [subscription, setSubscription] = useState<SubscriptionInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState('');

  // بارگذاری اطلاعات اشتراک
  useEffect(() => {
    if (isOpen && activeTab === 'subscription') {
      loadSubscriptionInfo();
    }
  }, [isOpen, activeTab]);

  const loadSubscriptionInfo = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/v1/subscriptions/current/');
      setSubscription(response.data);
    } catch (error) {
      console.error('Error loading subscription:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setSaveMessage('');
      
      // ذخیره تنظیمات عمومی در localStorage
      localStorage.setItem('userSettings', JSON.stringify(settings));
      
      // اعمال تم
      if (settings.theme === 'dark') {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }
      
      // ذخیره تنظیمات اعلان‌ها (اگر تغییر کرده باشد)
      const notificationPrefs = localStorage.getItem('notificationPreferences');
      if (notificationPrefs) {
        try {
          await axios.put('/api/v1/notifications/preferences/', JSON.parse(notificationPrefs));
          localStorage.removeItem('notificationPreferences'); // پاک کردن بعد از ذخیره موفق
        } catch (error) {
          console.error('Error saving notification preferences:', error);
        }
      }
      
      // TODO: ارسال سایر تنظیمات به سرور
      // await axios.post('/api/v1/users/settings/', settings);
      
      setSaveMessage('✓ تنظیمات با موفقیت ذخیره شد');
      setTimeout(() => setSaveMessage(''), 3000);
    } catch (error) {
      console.error('Error saving settings:', error);
      setSaveMessage('✗ خطا در ذخیره تنظیمات');
    } finally {
      setSaving(false);
    }
  };

  if (!isOpen) return null;

  // Show organization tab only for business users
  const isBusinessUser = user?.user_type === 'business';
  
  const tabs = [
    { id: 'profile' as SettingsTab, label: 'پروفایل', icon: User },
    { id: 'subscription' as SettingsTab, label: 'اشتراک', icon: CreditCard },
    { id: 'memory' as SettingsTab, label: 'حافظه من', icon: Brain },
    ...(isBusinessUser ? [{ id: 'organization' as SettingsTab, label: 'مدیریت سازمان', icon: Building2 }] : []),
    { id: 'preferences' as SettingsTab, label: 'تنظیمات', icon: Palette },
    { id: 'notifications' as SettingsTab, label: 'تنظیمات اطلاع رسانی', icon: Bell },
    { id: 'security' as SettingsTab, label: 'امنیت', icon: Shield },
    { id: 'sessions' as SettingsTab, label: 'جلسات فعال', icon: Monitor },
  ];

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div 
        className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl w-full max-w-4xl h-[80vh] flex overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Sidebar */}
        <div className="w-64 bg-gray-50 dark:bg-gray-800 border-l border-gray-200 dark:border-gray-700 flex flex-col">
          {/* Header */}
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">اطلاعات کاربری</h2>
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all ${
                    activeTab === tab.id
                      ? 'bg-blue-500 text-white shadow-lg shadow-blue-500/30'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </nav>

          {/* Footer */}
          <div className="p-4 border-t border-gray-200 dark:border-gray-700 space-y-2">
            {/* Save Message */}
            {saveMessage && (
              <div className={`text-center text-sm py-2 rounded-lg ${
                saveMessage.includes('✓') 
                  ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300' 
                  : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'
              }`}>
                {saveMessage}
              </div>
            )}
            
            {/* Buttons */}
            <div className="flex gap-2">
              <button
                onClick={handleSave}
                disabled={saving}
                className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm font-medium"
              >
                {saving ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    <span>در حال ذخیره...</span>
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    <span>ذخیره</span>
                  </>
                )}
              </button>
              <button
                onClick={onClose}
                className="px-3 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors text-sm"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Content Area */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Content Header */}
          <div className="p-6 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
            <h3 className="text-2xl font-bold text-gray-900 dark:text-white">
              {tabs.find(t => t.id === activeTab)?.label}
            </h3>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
            >
              <X className="w-5 h-5 text-gray-500" />
            </button>
          </div>

          {/* Content Body */}
          <div className="flex-1 overflow-y-auto p-6">
            {activeTab === 'profile' && <ProfileTab settings={settings} setSettings={setSettings} userPhone={user?.phone_number} userType={user?.user_type} />}
            {activeTab === 'subscription' && <SubscriptionTab subscription={subscription} loading={loading} />}
            {activeTab === 'memory' && <MemorySection />}
            {activeTab === 'organization' && <OrganizationSection />}
            {activeTab === 'preferences' && <PreferencesTab settings={settings} setSettings={setSettings} />}
            {activeTab === 'notifications' && <NotificationsTab />}
            {activeTab === 'security' && <SecurityTab />}
            {activeTab === 'sessions' && <SessionsTab />}
          </div>
        </div>
      </div>
    </div>
  );
};

// Profile Tab
const ProfileTab: React.FC<{ settings: UserSettings; setSettings: React.Dispatch<React.SetStateAction<UserSettings>>; userPhone?: string; userType?: string }> = ({ settings, setSettings, userPhone, userType }) => {
  const isBusiness = userType === 'business';
  
  return (
    <div className="bg-gray-50 dark:bg-gray-800 rounded-xl p-5">
      <div className="space-y-5">
        {/* نام شرکت/سازمان - فقط برای کاربران حقوقی */}
        {isBusiness && (
          <>
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                نام شرکت/سازمان
              </span>
              <input
                type="text"
                value={settings.company_name}
                onChange={(e) => setSettings({ ...settings, company_name: e.target.value })}
                className="w-64 px-3 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white text-sm"
              />
            </div>
            <div className="border-t border-gray-200 dark:border-gray-700" />
          </>
        )}

        {/* نام و نام خانوادگی - برای همه */}
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            نام و نام خانوادگی
          </span>
          <input
            type="text"
            value={settings.full_name}
            onChange={(e) => setSettings({ ...settings, full_name: e.target.value })}
            className="w-64 px-3 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white text-sm"
          />
        </div>

        <div className="border-t border-gray-200 dark:border-gray-700" />

        {/* ایمیل */}
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">ایمیل</span>
          <input
            type="email"
            value={settings.email}
            onChange={(e) => setSettings({ ...settings, email: e.target.value })}
            className="w-64 px-3 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white text-sm"
          />
        </div>

        <div className="border-t border-gray-200 dark:border-gray-700" />

        {/* کدملی / شناسه ملی */}
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            {isBusiness ? 'شناسه ملی' : 'کدملی'}
          </span>
          <input
            type="text"
            value={settings.national_id}
            onChange={(e) => setSettings({ ...settings, national_id: e.target.value })}
            maxLength={isBusiness ? 11 : 10}
            placeholder={isBusiness ? '11 رقم' : '10 رقم'}
            className="w-64 px-3 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white text-sm"
          />
        </div>

        <div className="border-t border-gray-200 dark:border-gray-700" />

        {/* شماره تلفن */}
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            شماره تلفن
            {!isBusiness && <span className="text-xs text-gray-500 mr-1">(غیرقابل تغییر)</span>}
          </span>
          <input
            type="tel"
            value={userPhone || ''}
            disabled={!isBusiness}
            onChange={(e) => isBusiness && setSettings({ ...settings, phone: e.target.value })}
            className={`w-64 px-3 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg text-sm ${
              isBusiness 
                ? 'bg-white dark:bg-gray-900 text-gray-900 dark:text-white' 
                : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 cursor-not-allowed'
            }`}
          />
        </div>
      </div>
    </div>
  );
};

// Subscription Tab
interface Plan {
  id: string;
  name: string;
  price: number;
  duration_days: number;
  max_queries_per_day?: number;
  max_queries_per_month?: number;
  features?: {
    max_queries_per_day?: number;
    max_queries_per_month?: number;
    [key: string]: any;
  };
  is_active: boolean;
}

const SubscriptionTab: React.FC<{ subscription: SubscriptionInfo | null; loading: boolean }> = ({ subscription, loading: initialLoading }) => {
  const [plans, setPlans] = React.useState<Plan[]>([]);
  const [usageStats, setUsageStats] = React.useState<any>(null);
  const [loading, setLoading] = React.useState(initialLoading);
  const { formatPrice, activeCurrency } = useCurrency();

  // بارگذاری پلن‌ها و آمار مصرف
  React.useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      try {
        // بارگذاری پلن‌ها - URL صحیح
        const plansResponse = await axios.get(`${API_URL}/api/v1/subscriptions/plans/`);
        if (plansResponse.data?.results) {
          setPlans(plansResponse.data.results);
        } else if (Array.isArray(plansResponse.data)) {
          setPlans(plansResponse.data);
        }
      } catch (error) {
        console.error('Error loading plans:', error);
      }

      try {
        // بارگذاری آمار مصرف
        const usageResponse = await axios.get(`${API_URL}/api/v1/subscriptions/usage/stats/`);
        setUsageStats(usageResponse.data);
      } catch (error) {
        console.error('Error loading usage:', error);
      }
      
      setLoading(false);
    };

    loadData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
        <span className="mr-3 text-gray-600 dark:text-gray-400">در حال بارگذاری...</span>
      </div>
    );
  }

  const usage = usageStats?.usage || {};
  const stats = usageStats?.stats || {};

  // فرمت تاریخ
  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('fa-IR');
  };

  return (
    <div className="space-y-6">
      {/* Current Plan - Compact & Beautiful */}
      <div className="bg-gradient-to-l from-blue-600 via-purple-600 to-indigo-600 rounded-xl p-4 text-white shadow-lg">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center">
              <span className="text-xl">👑</span>
            </div>
            <div>
              <p className="text-xs opacity-80">پلن فعلی</p>
              <p className="text-xl font-bold">{usageStats?.subscription?.plan || subscription?.plan_name || 'رایگان'}</p>
            </div>
          </div>
          {usageStats?.subscription?.status === 'active' && (
            <div className="px-3 py-1 rounded-full text-xs font-medium bg-green-400/20 text-green-100">
              ✓ فعال
            </div>
          )}
        </div>
        
        <div className="grid grid-cols-4 gap-2 text-xs">
          <div className="bg-white/10 rounded-lg p-2 text-center">
            <p className="opacity-70">عضویت</p>
            <p className="font-medium">{formatDate(usageStats?.user?.date_joined)}</p>
          </div>
          {usageStats?.subscription?.status === 'active' ? (
            <>
              <div className="bg-white/10 rounded-lg p-2 text-center">
                <p className="opacity-70">شروع پلن</p>
                <p className="font-medium">{formatDate(usageStats?.subscription?.start_date)}</p>
              </div>
              <div className="bg-white/10 rounded-lg p-2 text-center">
                <p className="opacity-70">انقضا</p>
                <p className="font-medium">{formatDate(usageStats?.subscription?.end_date)}</p>
              </div>
              <div className="bg-white/10 rounded-lg p-2 text-center">
                <p className="opacity-70">باقیمانده</p>
                <p className="font-medium">{usageStats?.subscription?.days_remaining || 0} روز</p>
              </div>
            </>
          ) : (
            <>
              <div className="bg-white/10 rounded-lg p-2 text-center col-span-2">
                <p className="opacity-70">وضعیت</p>
                <p className="font-medium">نامحدود</p>
              </div>
              <div className="bg-white/10 rounded-lg p-2 text-center">
                <p className="opacity-70">نوع</p>
                <p className="font-medium">آزاد</p>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Usage Stats */}
      <div className="bg-gray-50 dark:bg-gray-800 rounded-xl p-6">
        <h4 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">میزان استفاده</h4>
        <div className="space-y-4">
          <div>
            <div className="flex justify-between text-sm mb-2">
              <span className="text-gray-600 dark:text-gray-400">استفاده امروز</span>
              <span className="font-semibold text-gray-900 dark:text-white">
                {usage.daily_used || 0} / {usage.daily_limit || 10}
              </span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div 
                className={`h-2 rounded-full transition-all ${
                  (usage.daily_used / usage.daily_limit) > 0.8 ? 'bg-red-500' : 'bg-blue-500'
                }`}
                style={{ width: `${Math.min(100, ((usage.daily_used || 0) / (usage.daily_limit || 10)) * 100)}%` }}
              />
            </div>
            <p className="text-xs text-gray-500 mt-1">
              {usage.daily_remaining || 0} سوال باقیمانده امروز
            </p>
          </div>
          <div>
            <div className="flex justify-between text-sm mb-2">
              <span className="text-gray-600 dark:text-gray-400">استفاده ماهانه</span>
              <span className="font-semibold text-gray-900 dark:text-white">
                {usage.monthly_used || 0} / {usage.monthly_limit || 300}
              </span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div 
                className={`h-2 rounded-full transition-all ${
                  (usage.monthly_used / usage.monthly_limit) > 0.8 ? 'bg-red-500' : 'bg-purple-500'
                }`}
                style={{ width: `${Math.min(100, ((usage.monthly_used || 0) / (usage.monthly_limit || 300)) * 100)}%` }}
              />
            </div>
            <p className="text-xs text-gray-500 mt-1">
              {usage.monthly_remaining || 0} سوال باقیمانده این ماه
            </p>
          </div>
        </div>

        {/* Stats Summary */}
        {stats.total_queries !== undefined && (
          <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-gray-600 dark:text-gray-400">کل سوالات (30 روز)</p>
                <p className="font-semibold text-gray-900 dark:text-white">{stats.total_queries || 0}</p>
              </div>
              <div>
                <p className="text-gray-600 dark:text-gray-400">کل توکن مصرفی</p>
                <p className="font-semibold text-gray-900 dark:text-white">{stats.total_tokens?.toLocaleString() || 0}</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Available Plans */}
      {/* Available Plans - فقط پلن‌های پولی */}
      <div>
        <h4 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">پلن‌های موجود</h4>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {plans.filter((plan) => {
            // پلن رایگان را نمایش نده (چون خودکار به همه تعلق می‌گیرد)
            // بررسی قیمت و نام برای اطمینان
            if (plan.price === 0 || plan.price <= 0) return false;
            if (plan.name?.toLowerCase().includes('free') || plan.name?.toLowerCase().includes('رایگان')) return false;
            return true;
          }).length > 0 ? plans.filter((plan) => {
            if (plan.price === 0 || plan.price <= 0) return false;
            if (plan.name?.toLowerCase().includes('free') || plan.name?.toLowerCase().includes('رایگان')) return false;
            return true;
          }).map((plan) => {
            const isCurrentPlan = usageStats?.subscription?.plan === plan.name;
            const currentPlanPrice = plans.find(p => p.name === usageStats?.subscription?.plan)?.price || 0;
            const isUpgrade = plan.price > currentPlanPrice;
            
            const handlePurchase = () => {
              // Navigate to checkout page with plan info
              window.location.href = `/checkout?plan=${plan.id}`;
            };
            
            return (
              <div 
                key={plan.id} 
                className={`border rounded-xl p-4 transition-all ${
                  isCurrentPlan 
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' 
                    : 'border-gray-200 dark:border-gray-700 hover:border-blue-500'
                }`}
              >
                {isCurrentPlan && (
                  <span className="inline-block px-2 py-1 text-xs bg-blue-500 text-white rounded-full mb-2">
                    پلن فعلی
                  </span>
                )}
                <h5 className="font-semibold text-gray-900 dark:text-white mb-2">{plan.name}</h5>
                <p className="text-2xl font-bold text-blue-500 mb-2">
                  {formatPrice(plan.price)}
                </p>
                <div className="text-sm text-gray-600 dark:text-gray-400 mb-4 space-y-1">
                  <p>📅 {plan.duration_days} روز</p>
                  <p>📊 {plan.max_queries_per_day || 10} سوال/روز</p>
                  <p>📈 {plan.max_queries_per_month || 300} سوال/ماه</p>
                </div>
                <button 
                  onClick={handlePurchase}
                  className="w-full py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
                >
                  {isCurrentPlan ? 'تمدید' : (isUpgrade ? 'ارتقا' : 'خرید')}
                </button>
              </div>
            );
          }) : (
            <div className="col-span-3 text-center py-8 text-gray-500">
              پلنی یافت نشد
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Preferences Tab
const PreferencesTab: React.FC<{ settings: UserSettings; setSettings: React.Dispatch<React.SetStateAction<UserSettings>> }> = ({ settings, setSettings }) => {
  const { theme, setTheme } = useTheme();
  const { activeCurrency, setUserPreferredCurrency } = useCurrency();
  const [currencies, setCurrencies] = React.useState<any[]>([]);
  
  React.useEffect(() => {
    const loadCurrencies = async () => {
      try {
        const { getCurrencies } = await import('@/services/settingsService');
        const data = await getCurrencies();
        setCurrencies(data);
      } catch (error) {
        console.error('Failed to load currencies:', error);
      }
    };
    loadCurrencies();
  }, []);
  
  const handleThemeChange = (newTheme: 'light' | 'dark') => {
    setTheme(newTheme);
    setSettings({ ...settings, theme: newTheme });
  };

  const handleCurrencyChange = (currencyCode: string) => {
    const selected = currencies.find((c: any) => c.code === currencyCode);
    if (selected) {
      setUserPreferredCurrency(selected);
    }
  };
  
  return (
    <div className="bg-gray-50 dark:bg-gray-800 rounded-xl p-5">
      {/* همه تنظیمات در یک کارت */}
      <div className="space-y-5">
        {/* تم */}
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">تم برنامه</span>
          <div className="flex gap-2">
            <button
              onClick={() => handleThemeChange('light')}
              className={`px-3 py-1.5 rounded-lg text-sm transition-all flex items-center gap-1.5 ${
                theme === 'light'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
              }`}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
              روشن
            </button>
            <button
              onClick={() => handleThemeChange('dark')}
              className={`px-3 py-1.5 rounded-lg text-sm transition-all flex items-center gap-1.5 ${
                theme === 'dark'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
              }`}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
              </svg>
              تاریک
            </button>
          </div>
        </div>

        <div className="border-t border-gray-200 dark:border-gray-700" />

        {/* واحد پولی */}
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">واحد پولی</span>
          <select
            value={activeCurrency?.code || 'IRT'}
            onChange={(e) => handleCurrencyChange(e.target.value)}
            className="min-w-[160px] px-3 py-1.5 pl-7 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white text-sm cursor-pointer text-right appearance-none"
            dir="rtl"
            style={{
              backgroundImage: "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%236b7280'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E\")",
              backgroundRepeat: "no-repeat",
              backgroundPosition: "left 0.4rem center",
              backgroundSize: "1rem"
            }}
          >
            {currencies.map((currency: any) => (
              <option key={currency.id} value={currency.code}>
                {currency.name} ({currency.symbol})
              </option>
            ))}
          </select>
        </div>

        <div className="border-t border-gray-200 dark:border-gray-700" />

        {/* ابزار جستجوی وب */}
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">ابزار جستجوی وب</span>
          <select
            value={settings.enable_web_search === null ? 'default' : settings.enable_web_search ? 'enabled' : 'disabled'}
            onChange={(e) => {
              const value = e.target.value;
              setSettings({ 
                ...settings, 
                enable_web_search: value === 'default' ? null : value === 'enabled' 
              });
            }}
            className="min-w-[120px] px-3 py-1.5 pl-7 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white text-sm cursor-pointer text-right appearance-none"
            dir="rtl"
            style={{
              backgroundImage: "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%236b7280'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E\")",
              backgroundRepeat: "no-repeat",
              backgroundPosition: "left 0.4rem center",
              backgroundSize: "1rem"
            }}
          >
            <option value="default">پیش‌فرض</option>
            <option value="enabled">فعال</option>
            <option value="disabled">غیرفعال</option>
          </select>
        </div>
      </div>
    </div>
  );
};

// Notifications Tab
interface NotificationPreferences {
  email_enabled: boolean;
  sms_enabled: boolean;
  push_enabled: boolean;
  in_app_enabled: boolean;
  system_notifications: boolean;
  payment_notifications: boolean;
  subscription_notifications: boolean;
  chat_notifications: boolean;
  account_notifications: boolean;
  security_notifications: boolean;
  marketing_notifications: boolean;
  support_notifications: boolean;
}

const NotificationsTab: React.FC = () => {
  const [preferences, setPreferences] = React.useState<NotificationPreferences>({
    email_enabled: true,
    sms_enabled: true,
    push_enabled: true,
    in_app_enabled: true,
    system_notifications: true,
    payment_notifications: true,
    subscription_notifications: true,
    chat_notifications: true,
    account_notifications: true,
    security_notifications: true,
    marketing_notifications: false,
    support_notifications: true,
  });
  const [loading, setLoading] = React.useState(true);
  const [saving, setSaving] = React.useState(false);
  const [message, setMessage] = React.useState('');

  // بارگذاری تنظیمات
  React.useEffect(() => {
    const loadPreferences = async () => {
      try {
        const response = await axios.get('/api/v1/notifications/preferences/');
        setPreferences(response.data);
      } catch (error) {
        console.error('Error loading notification preferences:', error);
      } finally {
        setLoading(false);
      }
    };

    loadPreferences();
  }, []);

  // ذخیره تنظیمات
  const savePreferences = async () => {
    try {
      setSaving(true);
      await axios.put('/api/v1/notifications/preferences/', preferences);
      setMessage('✓ تنظیمات ذخیره شد');
      setTimeout(() => setMessage(''), 3000);
    } catch (error) {
      console.error('Error saving notification preferences:', error);
      setMessage('✗ خطا در ذخیره تنظیمات');
    } finally {
      setSaving(false);
    }
  };

  const handleToggle = (key: keyof NotificationPreferences) => {
    const newPreferences = { ...preferences, [key]: !preferences[key] };
    setPreferences(newPreferences);
    
    // ذخیره در localStorage برای ذخیره با دکمه اصلی
    localStorage.setItem('notificationPreferences', JSON.stringify(newPreferences));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  const channels = [
    { key: 'email_enabled' as const, label: 'ایمیل', icon: '📧' },
    { key: 'sms_enabled' as const, label: 'پیامک', icon: '📱' },
    { key: 'push_enabled' as const, label: 'Push', icon: '🔔' },
    { key: 'in_app_enabled' as const, label: 'داخل برنامه', icon: '💬' },
  ];

  const categories = [
    { key: 'system_notifications' as const, label: 'سیستمی' },
    { key: 'payment_notifications' as const, label: 'پرداخت' },
    { key: 'subscription_notifications' as const, label: 'اشتراک' },
    { key: 'chat_notifications' as const, label: 'چت' },
    { key: 'account_notifications' as const, label: 'حساب کاربری' },
    { key: 'security_notifications' as const, label: 'امنیت' },
    { key: 'marketing_notifications' as const, label: 'بازاریابی' },
    { key: 'support_notifications' as const, label: 'پشتیبانی' },
  ];

  // Toggle Switch Component
  const ToggleSwitch = ({ checked, onChange }: { checked: boolean; onChange: () => void }) => (
    <button
      type="button"
      onClick={(e) => { e.stopPropagation(); onChange(); }}
      className={`relative w-10 h-5 rounded-full transition-colors flex-shrink-0 ${
        checked ? 'bg-blue-500' : 'bg-gray-300 dark:bg-gray-600'
      }`}
    >
      <span className={`absolute top-0.5 w-4 h-4 rounded-full bg-white shadow-md transition-transform duration-200 ${
        checked ? 'translate-x-5' : 'translate-x-0.5'
      }`} />
    </button>
  );

  return (
    <div className="space-y-4">
      {/* کانال‌های اعلان */}
      <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
        <h4 className="text-sm font-semibold mb-3 text-gray-900 dark:text-white">روش‌های اطلاع‌رسانی</h4>
        <div className="grid grid-cols-2 gap-2">
          {channels.map((channel) => (
            <div 
              key={channel.key}
              className={`flex items-center justify-between p-2 rounded-lg border transition-all cursor-pointer ${
                preferences[channel.key]
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                  : 'border-gray-200 dark:border-gray-700'
              }`}
              onClick={() => handleToggle(channel.key)}
            >
              <div className="flex items-center gap-2">
                <span className="text-base">{channel.icon}</span>
                <span className="text-xs font-medium text-gray-900 dark:text-white">{channel.label}</span>
              </div>
              <ToggleSwitch checked={preferences[channel.key]} onChange={() => handleToggle(channel.key)} />
            </div>
          ))}
        </div>
      </div>

      {/* دسته‌بندی اعلان‌ها */}
      <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
        <h4 className="text-sm font-semibold mb-3 text-gray-900 dark:text-white">دسته‌بندی اعلان‌ها</h4>
        <div className="grid grid-cols-2 gap-2">
          {categories.map((category) => (
            <div 
              key={category.key}
              className="flex items-center justify-between p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            >
              <span className="text-xs font-medium text-gray-900 dark:text-white">{category.label}</span>
              <ToggleSwitch checked={preferences[category.key]} onChange={() => handleToggle(category.key)} />
            </div>
          ))}
        </div>
      </div>

    </div>
  );
};

// Security Tab
const SecurityTab: React.FC = () => {
  const [oldPassword, setOldPassword] = React.useState('');
  const [newPassword, setNewPassword] = React.useState('');
  const [confirmPassword, setConfirmPassword] = React.useState('');
  const [changing, setChanging] = React.useState(false);
  const [message, setMessage] = React.useState('');

  const handleChangePassword = async () => {
    if (!oldPassword || !newPassword || !confirmPassword) {
      setMessage('✗ لطفا تمام فیلدها را پر کنید');
      return;
    }

    if (newPassword !== confirmPassword) {
      setMessage('✗ رمز عبور جدید و تکرار آن یکسان نیستند');
      return;
    }

    if (newPassword.length < 8) {
      setMessage('✗ رمز عبور باید حداقل 8 کاراکتر باشد');
      return;
    }

    try {
      setChanging(true);
      setMessage('');
      
      // TODO: ارسال به سرور
      // await axios.post('/api/v1/auth/change-password/', {
      //   old_password: oldPassword,
      //   new_password: newPassword
      // });
      
      setMessage('✓ رمز عبور با موفقیت تغییر کرد');
      setOldPassword('');
      setNewPassword('');
      setConfirmPassword('');
      
      setTimeout(() => setMessage(''), 3000);
    } catch (error) {
      console.error('Error changing password:', error);
      setMessage('✗ خطا در تغییر رمز عبور');
    } finally {
      setChanging(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-gray-50 dark:bg-gray-800 rounded-xl p-6">
        <h4 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">تغییر رمز عبور</h4>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">رمز عبور فعلی</label>
            <input
              type="password"
              value={oldPassword}
              onChange={(e) => setOldPassword(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
              placeholder="رمز عبور فعلی خود را وارد کنید"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">رمز عبور جدید</label>
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
              placeholder="رمز عبور جدید (حداقل 8 کاراکتر)"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">تکرار رمز عبور جدید</label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
              placeholder="رمز عبور جدید را دوباره وارد کنید"
            />
          </div>

          {message && (
            <div className={`text-sm py-2 px-4 rounded-lg ${
              message.includes('✓') 
                ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300' 
                : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'
            }`}>
              {message}
            </div>
          )}

          <button
            onClick={handleChangePassword}
            disabled={changing}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
          >
            {changing ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                <span>در حال تغییر...</span>
              </>
            ) : (
              <span>تغییر رمز عبور</span>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

// Sessions Tab - Active Sessions Management
interface Session {
  id: string;
  device_type: string;
  device_name: string;
  browser: string;
  os: string;
  ip_address: string;
  location: string;
  created_at: string;
  last_activity: string;
  is_active: boolean;
  is_current: boolean;
}

interface SessionsData {
  sessions: Session[];
  max_sessions: number;
  current_sessions_count: number;
  can_create_new_session: boolean;
}

const SessionsTab: React.FC = () => {
  const [sessionsData, setSessionsData] = React.useState<SessionsData | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [revoking, setRevoking] = React.useState<string | null>(null);
  const [message, setMessage] = React.useState('');

  const loadSessions = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_URL}/api/v1/auth/sessions/with_limit/`);
      setSessionsData(response.data);
    } catch (error) {
      console.error('Error loading sessions:', error);
      setMessage('✗ خطا در بارگذاری جلسات');
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    loadSessions();
  }, []);

  const handleRevokeSession = async (sessionId: string) => {
    try {
      setRevoking(sessionId);
      await axios.post(`${API_URL}/api/v1/auth/sessions/${sessionId}/revoke/`);
      setMessage('✓ جلسه با موفقیت حذف شد');
      loadSessions();
      setTimeout(() => setMessage(''), 3000);
    } catch (error: any) {
      console.error('Error revoking session:', error);
      if (error.response?.data?.error) {
        setMessage(`✗ ${error.response.data.error}`);
      } else {
        setMessage('✗ خطا در حذف جلسه');
      }
    } finally {
      setRevoking(null);
    }
  };

  const handleRevokeAll = async () => {
    try {
      setRevoking('all');
      await axios.post(`${API_URL}/api/v1/auth/sessions/revoke_all/`);
      setMessage('✓ تمام جلسات دیگر حذف شدند');
      loadSessions();
      setTimeout(() => setMessage(''), 3000);
    } catch (error) {
      console.error('Error revoking all sessions:', error);
      setMessage('✗ خطا در حذف جلسات');
    } finally {
      setRevoking(null);
    }
  };

  const getDeviceIcon = (deviceType: string) => {
    switch (deviceType?.toLowerCase()) {
      case 'mobile':
      case 'phone':
        return <Smartphone className="w-5 h-5" />;
      case 'tablet':
        return <Smartphone className="w-5 h-5" />;
      default:
        return <Laptop className="w-5 h-5" />;
    }
  };

  const formatDate = (dateStr: string) => {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleDateString('fa-IR') + ' ' + date.toLocaleTimeString('fa-IR', { hour: '2-digit', minute: '2-digit' });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
        <span className="mr-3 text-gray-600 dark:text-gray-400">در حال بارگذاری...</span>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Session Limit Info - Compact */}
      <div className="bg-gradient-to-l from-blue-600 via-purple-600 to-indigo-600 rounded-lg p-3 text-white">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Monitor className="w-5 h-5" />
            <span className="text-sm font-medium">
              {sessionsData?.current_sessions_count || 0} از {sessionsData?.max_sessions || 3} جلسه فعال
            </span>
          </div>
          {sessionsData && !sessionsData.can_create_new_session && (
            <span className="text-xs bg-red-400/30 px-2 py-0.5 rounded">⚠️ حداکثر</span>
          )}
        </div>
      </div>

      {/* Message */}
      {message && (
        <div className={`text-xs py-1.5 px-3 rounded ${
          message.includes('✓') 
            ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300' 
            : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'
        }`}>
          {message}
        </div>
      )}

      {/* Sessions List - Compact */}
      <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
        <div className="flex items-center justify-between mb-2">
          <h4 className="text-sm font-semibold text-gray-900 dark:text-white">دستگاه‌های متصل</h4>
          {sessionsData && sessionsData.sessions.length > 1 && (
            <button
              onClick={handleRevokeAll}
              disabled={revoking === 'all'}
              className="text-xs text-red-500 hover:text-red-600 disabled:opacity-50"
            >
              {revoking === 'all' ? 'حذف...' : 'حذف همه'}
            </button>
          )}
        </div>

        <div className="space-y-2">
          {sessionsData?.sessions.map((session) => (
            <div 
              key={session.id}
              className={`flex items-center justify-between p-2 rounded border text-xs ${
                session.is_current
                  ? 'border-green-500 bg-green-50 dark:bg-green-900/20'
                  : 'border-gray-200 dark:border-gray-700'
              }`}
            >
              <div className="flex items-center gap-2">
                <div className={`w-7 h-7 rounded flex items-center justify-center ${
                  session.is_current
                    ? 'bg-green-500 text-white'
                    : 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
                }`}>
                  {getDeviceIcon(session.device_type)}
                </div>
                <div>
                  <div className="flex items-center gap-1">
                    <span className="font-medium text-gray-900 dark:text-white">
                      {session.browser || 'ناشناس'}
                    </span>
                    {session.is_current && (
                      <span className="px-1 py-0.5 text-[10px] bg-green-500 text-white rounded">فعلی</span>
                    )}
                  </div>
                  <div className="text-gray-500 dark:text-gray-400">
                    {session.os} • {session.ip_address} • {formatDate(session.last_activity)}
                  </div>
                </div>
              </div>
              
              {!session.is_current && (
                <button
                  onClick={() => handleRevokeSession(session.id)}
                  disabled={revoking === session.id}
                  className="p-1 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded disabled:opacity-50"
                  title="حذف"
                >
                  {revoking === session.id ? (
                    <div className="w-4 h-4 border-2 border-red-500 border-t-transparent rounded-full animate-spin"></div>
                  ) : (
                    <Trash2 className="w-4 h-4" />
                  )}
                </button>
              )}
            </div>
          ))}

          {(!sessionsData?.sessions || sessionsData.sessions.length === 0) && (
            <div className="text-center py-4 text-xs text-gray-500 dark:text-gray-400">
              هیچ جلسه فعالی یافت نشد
            </div>
          )}
        </div>
      </div>

      {/* Info Box - Compact */}
      <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-2 border border-blue-200 dark:border-blue-800 text-xs">
        <span className="text-blue-700 dark:text-blue-400">
          💡 دستگاه ناشناس را حذف کنید. برای افزایش سقف، پلن را ارتقا دهید.
        </span>
      </div>
    </div>
  );
};

export default SettingsPage;
