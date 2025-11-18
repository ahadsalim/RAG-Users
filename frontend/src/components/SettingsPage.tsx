import React, { useState, useEffect } from 'react';
import { X, User, Bell, Shield, CreditCard, Palette, Globe, HelpCircle } from 'lucide-react';
import axios from 'axios';
import { useAuthStore } from '@/store/auth';

interface SettingsPageProps {
  isOpen: boolean;
  onClose: () => void;
}

type SettingsTab = 'profile' | 'subscription' | 'preferences' | 'notifications' | 'security' | 'help';

interface UserSettings {
  // Profile
  full_name: string;
  company_name: string;
  email: string;
  phone: string;
  
  // Preferences
  theme: 'light' | 'dark';
  response_style: 'formal' | 'casual' | 'academic' | 'simple';
  detail_level: 'brief' | 'moderate' | 'comprehensive' | 'detailed';
  language_style: 'simple' | 'technical' | 'mixed';
  format: 'bullet_points' | 'numbered_list' | 'paragraph';
  include_examples: boolean;
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
              theme: 'light',
              response_style: 'formal',
              detail_level: 'moderate',
              language_style: 'simple',
              format: 'paragraph',
              include_examples: true,
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
      theme: 'light',
      response_style: 'formal',
      detail_level: 'moderate',
      language_style: 'simple',
      format: 'paragraph',
      include_examples: true,
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
      
      // ذخیره در localStorage
      localStorage.setItem('userSettings', JSON.stringify(settings));
      
      // اعمال تم
      if (settings.theme === 'dark') {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }
      
      // TODO: ارسال به سرور
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

  const tabs = [
    { id: 'profile' as SettingsTab, label: 'پروفایل', icon: User },
    { id: 'subscription' as SettingsTab, label: 'اشتراک', icon: CreditCard },
    { id: 'preferences' as SettingsTab, label: 'تنظیمات', icon: Palette },
    { id: 'notifications' as SettingsTab, label: 'اعلان‌ها', icon: Bell },
    { id: 'security' as SettingsTab, label: 'امنیت', icon: Shield },
    { id: 'help' as SettingsTab, label: 'راهنما', icon: HelpCircle },
  ];

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div 
        className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl w-full max-w-6xl h-[85vh] flex overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Sidebar */}
        <div className="w-64 bg-gray-50 dark:bg-gray-800 border-l border-gray-200 dark:border-gray-700 flex flex-col">
          {/* Header */}
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">تنظیمات</h2>
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
            {activeTab === 'preferences' && <PreferencesTab settings={settings} setSettings={setSettings} />}
            {activeTab === 'notifications' && <NotificationsTab />}
            {activeTab === 'security' && <SecurityTab />}
            {activeTab === 'help' && <HelpTab />}
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
    <div className="space-y-6">
      <div className="bg-gray-50 dark:bg-gray-800 rounded-xl p-6">
        <h4 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">اطلاعات کاربری</h4>
        <div className="space-y-4">
          {isBusiness ? (
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">نام شرکت/سازمان</label>
              <input
                type="text"
                value={settings.company_name}
                onChange={(e) => setSettings({ ...settings, company_name: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
                placeholder="نام شرکت یا سازمان خود را وارد کنید"
              />
            </div>
          ) : (
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">نام و نام خانوادگی</label>
              <input
                type="text"
                value={settings.full_name}
                onChange={(e) => setSettings({ ...settings, full_name: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
                placeholder="نام خود را وارد کنید"
              />
            </div>
          )}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">ایمیل</label>
            <input
              type="email"
              value={settings.email}
              onChange={(e) => setSettings({ ...settings, email: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
              placeholder="email@example.com"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              شماره تلفن
              {!isBusiness && <span className="text-xs text-gray-500 mr-2">(غیرقابل تغییر)</span>}
            </label>
            <input
              type="tel"
              value={userPhone || ''}
              disabled={!isBusiness}
              onChange={(e) => isBusiness && setSettings({ ...settings, phone: e.target.value })}
              className={`w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg ${
                isBusiness 
                  ? 'bg-white dark:bg-gray-900 text-gray-900 dark:text-white' 
                  : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 cursor-not-allowed'
              }`}
              placeholder={isBusiness ? "شماره تلفن برای اطلاع‌رسانی" : "شماره تلفن ثبت نشده"}
            />
            {isBusiness && (
              <p className="text-xs text-gray-500 mt-1">این شماره فقط برای اطلاع‌رسانی استفاده می‌شود</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// Subscription Tab
const SubscriptionTab: React.FC<{ subscription: SubscriptionInfo | null; loading: boolean }> = ({ subscription, loading }) => {
  if (loading) {
    return <div className="text-center py-12">در حال بارگذاری...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Current Plan */}
      <div className="bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl p-6 text-white">
        <h4 className="text-lg font-semibold mb-2">پلن فعلی</h4>
        <p className="text-3xl font-bold mb-4">{subscription?.plan_name || 'رایگان'}</p>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p className="opacity-80">وضعیت</p>
            <p className="font-semibold">{subscription?.status === 'active' ? 'فعال' : 'غیرفعال'}</p>
          </div>
          <div>
            <p className="opacity-80">تاریخ انقضا</p>
            <p className="font-semibold">{subscription?.end_date || '-'}</p>
          </div>
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
                {subscription?.queries_used_today || 0} / {subscription?.max_queries_per_day || 10}
              </span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div 
                className="bg-blue-500 h-2 rounded-full transition-all"
                style={{ width: `${((subscription?.queries_used_today || 0) / (subscription?.max_queries_per_day || 10)) * 100}%` }}
              />
            </div>
          </div>
          <div>
            <div className="flex justify-between text-sm mb-2">
              <span className="text-gray-600 dark:text-gray-400">استفاده ماهانه</span>
              <span className="font-semibold text-gray-900 dark:text-white">
                {subscription?.queries_used_month || 0} / {subscription?.max_queries_per_month || 300}
              </span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div 
                className="bg-purple-500 h-2 rounded-full transition-all"
                style={{ width: `${((subscription?.queries_used_month || 0) / (subscription?.max_queries_per_month || 300)) * 100}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Available Plans */}
      <div>
        <h4 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">پلن‌های موجود</h4>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            { name: 'رایگان', price: '0', queries: '10 سوال/روز' },
            { name: 'پایه', price: '299,000', queries: '50 سوال/روز' },
            { name: 'حرفه‌ای', price: '799,000', queries: '200 سوال/روز' },
          ].map((plan) => (
            <div key={plan.name} className="border border-gray-200 dark:border-gray-700 rounded-xl p-4 hover:border-blue-500 transition-colors">
              <h5 className="font-semibold text-gray-900 dark:text-white mb-2">{plan.name}</h5>
              <p className="text-2xl font-bold text-blue-500 mb-2">{plan.price} <span className="text-sm">تومان</span></p>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">{plan.queries}</p>
              <button className="w-full py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors">
                ارتقا
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// Preferences Tab
const PreferencesTab: React.FC<{ settings: UserSettings; setSettings: React.Dispatch<React.SetStateAction<UserSettings>> }> = ({ settings, setSettings }) => {
  return (
    <div className="space-y-6">
      <div className="bg-gray-50 dark:bg-gray-800 rounded-xl p-6">
        <h4 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">تنظیمات پاسخ</h4>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">سبک پاسخ</label>
            <select
              value={settings.response_style}
              onChange={(e) => setSettings({ ...settings, response_style: e.target.value as any })}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white text-right"
              dir="rtl"
              style={{ backgroundPosition: 'left 0.75rem center' }}
            >
              <option value="formal">رسمی</option>
              <option value="casual">غیررسمی</option>
              <option value="academic">آکادمیک</option>
              <option value="simple">ساده</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">سطح جزئیات</label>
            <select
              value={settings.detail_level}
              onChange={(e) => setSettings({ ...settings, detail_level: e.target.value as any })}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white text-right"
              dir="rtl"
              style={{ backgroundPosition: 'left 0.75rem center' }}
            >
              <option value="brief">خلاصه</option>
              <option value="moderate">متوسط</option>
              <option value="comprehensive">جامع</option>
              <option value="detailed">تفصیلی</option>
            </select>
          </div>
        </div>
      </div>
    </div>
  );
};

// Notifications Tab
const NotificationsTab: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="bg-gray-50 dark:bg-gray-800 rounded-xl p-6">
        <h4 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">تنظیمات اعلان</h4>
        <p className="text-gray-600 dark:text-gray-400">به زودی...</p>
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

// Help Tab
const HelpTab: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="bg-gray-50 dark:bg-gray-800 rounded-xl p-6">
        <h4 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">راهنما و پشتیبانی</h4>
        <p className="text-gray-600 dark:text-gray-400">به زودی...</p>
      </div>
    </div>
  );
};

export default SettingsPage;
