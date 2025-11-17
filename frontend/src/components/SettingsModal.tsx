import React, { useState, useEffect } from 'react';
import { X, Sun, Moon, Sparkles, CreditCard } from 'lucide-react';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

interface UserSettings {
  theme: 'light' | 'dark';
  response_style: 'formal' | 'casual' | 'academic' | 'simple';
  detail_level: 'brief' | 'moderate' | 'comprehensive' | 'detailed';
  language_style: 'simple' | 'technical' | 'mixed';
  format: 'bullet_points' | 'numbered_list' | 'paragraph';
  include_examples: boolean;
  subscription: 'free' | 'basic' | 'premium' | 'enterprise';
}

const SettingsModal: React.FC<SettingsModalProps> = ({ isOpen, onClose }) => {
  const [settings, setSettings] = useState<UserSettings>({
    theme: 'light',
    response_style: 'formal',
    detail_level: 'moderate',
    language_style: 'simple',
    format: 'paragraph',
    include_examples: true,
    subscription: 'free',
  });
  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState('');

  // بارگذاری تنظیمات از localStorage
  useEffect(() => {
    const savedSettings = localStorage.getItem('userSettings');
    if (savedSettings) {
      try {
        const parsed = JSON.parse(savedSettings);
        setSettings(parsed);
        
        // اعمال تم
        if (parsed.theme === 'dark') {
          document.documentElement.classList.add('dark');
        } else {
          document.documentElement.classList.remove('dark');
        }
      } catch (e) {
        console.error('Error loading settings:', e);
      }
    }
  }, []);

  // ذخیره تنظیمات
  const handleSave = async () => {
    setIsSaving(true);
    setSaveMessage('');

    try {
      // ذخیره در localStorage
      localStorage.setItem('userSettings', JSON.stringify(settings));

      // اعمال تم
      if (settings.theme === 'dark') {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }

      // ارسال به backend
      const response = await fetch('/api/v1/accounts/settings/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify({
          preferences: {
            theme: settings.theme,
            response_style: settings.response_style,
            detail_level: settings.detail_level,
            language_style: settings.language_style,
            format: settings.format,
            include_examples: settings.include_examples,
          },
        }),
      });

      if (response.ok) {
        setSaveMessage('تنظیمات با موفقیت ذخیره شد');
        setTimeout(() => setSaveMessage(''), 3000);
      } else {
        setSaveMessage('خطا در ذخیره تنظیمات');
      }
    } catch (error) {
      console.error('Error saving settings:', error);
      setSaveMessage('خطا در ذخیره تنظیمات');
    } finally {
      setIsSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div 
        className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-lg max-h-[85vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-4 flex items-center justify-between">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">تنظیمات</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-500 dark:text-gray-400" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 space-y-4">
          {/* 1. انتخاب تم */}
          <div className="space-y-2">
            <label className="flex items-center gap-2 text-base font-semibold text-gray-900 dark:text-white">
              <Sun className="w-4 h-4" />
              تم برنامه
            </label>
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => setSettings({ ...settings, theme: 'light' })}
                className={`p-3 rounded-lg border-2 transition-all flex items-center justify-center gap-2 text-sm ${
                  settings.theme === 'light'
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                    : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                }`}
              >
                <Sun className="w-5 h-5" />
                <span className="font-medium">روشن</span>
              </button>
              <button
                onClick={() => setSettings({ ...settings, theme: 'dark' })}
                className={`p-3 rounded-lg border-2 transition-all flex items-center justify-center gap-2 text-sm ${
                  settings.theme === 'dark'
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                    : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                }`}
              >
                <Moon className="w-5 h-5" />
                <span className="font-medium">تاریک</span>
              </button>
            </div>
          </div>

          {/* 2. شخصی‌سازی پاسخ */}
          <div className="space-y-3">
            <label className="flex items-center gap-2 text-base font-semibold text-gray-900 dark:text-white">
              <Sparkles className="w-4 h-4" />
              شخصی‌سازی پاسخ
            </label>
            
            {/* سبک پاسخ */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                سبک پاسخ
              </label>
              <select
                value={settings.response_style}
                onChange={(e) => setSettings({ ...settings, response_style: e.target.value as any })}
                className="w-full p-2 text-sm border-2 border-gray-200 dark:border-gray-700 rounded-lg 
                         bg-white dark:bg-gray-900 text-gray-900 dark:text-white
                         focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 outline-none appearance-none
                         bg-[url('data:image/svg+xml;charset=UTF-8,%3csvg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 24 24\' fill=\'none\' stroke=\'currentColor\' stroke-width=\'2\' stroke-linecap=\'round\' stroke-linejoin=\'round\'%3e%3cpolyline points=\'6 9 12 15 18 9\'%3e%3c/polyline%3e%3c/svg%3e')] bg-[length:1.2em] bg-[right_0.5rem_center] bg-no-repeat pr-8"
              >
                <option value="formal">رسمی و تخصصی</option>
                <option value="casual">غیررسمی و ساده</option>
                <option value="academic">آکادمیک و علمی</option>
                <option value="simple">ساده و قابل فهم</option>
              </select>
            </div>

            {/* سطح جزئیات */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                سطح جزئیات
              </label>
              <select
                value={settings.detail_level}
                onChange={(e) => setSettings({ ...settings, detail_level: e.target.value as any })}
                className="w-full p-2 text-sm border-2 border-gray-200 dark:border-gray-700 rounded-lg 
                         bg-white dark:bg-gray-900 text-gray-900 dark:text-white
                         focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 outline-none appearance-none
                         bg-[url('data:image/svg+xml;charset=UTF-8,%3csvg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 24 24\' fill=\'none\' stroke=\'currentColor\' stroke-width=\'2\' stroke-linecap=\'round\' stroke-linejoin=\'round\'%3e%3cpolyline points=\'6 9 12 15 18 9\'%3e%3c/polyline%3e%3c/svg%3e')] bg-[length:1.2em] bg-[right_0.5rem_center] bg-no-repeat pr-8"
              >
                <option value="brief">خلاصه و مختصر</option>
                <option value="moderate">متوسط</option>
                <option value="comprehensive">جامع و کامل</option>
                <option value="detailed">با جزئیات کامل</option>
              </select>
            </div>

            {/* سبک زبان */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                سبک زبان
              </label>
              <select
                value={settings.language_style}
                onChange={(e) => setSettings({ ...settings, language_style: e.target.value as any })}
                className="w-full p-2 text-sm border-2 border-gray-200 dark:border-gray-700 rounded-lg 
                         bg-white dark:bg-gray-900 text-gray-900 dark:text-white
                         focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 outline-none appearance-none
                         bg-[url('data:image/svg+xml;charset=UTF-8,%3csvg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 24 24\' fill=\'none\' stroke=\'currentColor\' stroke-width=\'2\' stroke-linecap=\'round\' stroke-linejoin=\'round\'%3e%3cpolyline points=\'6 9 12 15 18 9\'%3e%3c/polyline%3e%3c/svg%3e')] bg-[length:1.2em] bg-[right_0.5rem_center] bg-no-repeat pr-8"
              >
                <option value="simple">زبان ساده</option>
                <option value="technical">اصطلاحات تخصصی</option>
                <option value="mixed">ترکیبی</option>
              </select>
            </div>

            {/* فرمت پاسخ */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                فرمت پاسخ
              </label>
              <select
                value={settings.format}
                onChange={(e) => setSettings({ ...settings, format: e.target.value as any })}
                className="w-full p-2 text-sm border-2 border-gray-200 dark:border-gray-700 rounded-lg 
                         bg-white dark:bg-gray-900 text-gray-900 dark:text-white
                         focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 outline-none appearance-none
                         bg-[url('data:image/svg+xml;charset=UTF-8,%3csvg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 24 24\' fill=\'none\' stroke=\'currentColor\' stroke-width=\'2\' stroke-linecap=\'round\' stroke-linejoin=\'round\'%3e%3cpolyline points=\'6 9 12 15 18 9\'%3e%3c/polyline%3e%3c/svg%3e')] bg-[length:1.2em] bg-[right_0.5rem_center] bg-no-repeat pr-8"
              >
                <option value="paragraph">پاراگراف‌های منسجم</option>
                <option value="bullet_points">نکات کلیدی</option>
                <option value="numbered_list">لیست شماره‌دار</option>
              </select>
            </div>

            {/* شامل مثال */}
            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                id="include_examples"
                checked={settings.include_examples}
                onChange={(e) => setSettings({ ...settings, include_examples: e.target.checked })}
                className="w-5 h-5 rounded border-gray-300 text-blue-500 focus:ring-blue-500"
              />
              <label htmlFor="include_examples" className="text-sm font-medium text-gray-700 dark:text-gray-300">
                شامل مثال‌های عملی
              </label>
            </div>
          </div>

          {/* 3. انتخاب پکیج مالی */}
          <div className="space-y-2">
            <label className="flex items-center gap-2 text-base font-semibold text-gray-900 dark:text-white">
              <CreditCard className="w-4 h-4" />
              پکیج اشتراک
            </label>
            <div className="grid grid-cols-1 gap-2">
              {/* Free */}
              <button
                onClick={() => setSettings({ ...settings, subscription: 'free' })}
                className={`p-3 rounded-lg border-2 transition-all text-right text-sm ${
                  settings.subscription === 'free'
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                    : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-bold text-gray-900 dark:text-white">رایگان</div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">50 سوال در روز</div>
                  </div>
                  <div className="text-2xl font-bold text-gray-900 dark:text-white">رایگان</div>
                </div>
              </button>

              {/* Basic */}
              <button
                onClick={() => setSettings({ ...settings, subscription: 'basic' })}
                className={`p-3 rounded-lg border-2 transition-all text-right text-sm ${
                  settings.subscription === 'basic'
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                    : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-bold text-gray-900 dark:text-white">پایه</div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">200 سوال در روز</div>
                  </div>
                  <div className="text-2xl font-bold text-gray-900 dark:text-white">
                    99,000 <span className="text-sm">تومان/ماه</span>
                  </div>
                </div>
              </button>

              {/* Premium */}
              <button
                onClick={() => setSettings({ ...settings, subscription: 'premium' })}
                className={`p-3 rounded-lg border-2 transition-all text-right text-sm ${
                  settings.subscription === 'premium'
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                    : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-bold text-gray-900 dark:text-white">حرفه‌ای</div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">نامحدود + ویژگی‌های پیشرفته</div>
                  </div>
                  <div className="text-2xl font-bold text-gray-900 dark:text-white">
                    299,000 <span className="text-sm">تومان/ماه</span>
                  </div>
                </div>
              </button>

              {/* Enterprise */}
              <button
                onClick={() => setSettings({ ...settings, subscription: 'enterprise' })}
                className={`p-3 rounded-lg border-2 transition-all text-right text-sm ${
                  settings.subscription === 'enterprise'
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                    : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-bold text-gray-900 dark:text-white">سازمانی</div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">برای سازمان‌ها و شرکت‌ها</div>
                  </div>
                  <div className="text-lg font-bold text-gray-900 dark:text-white">تماس بگیرید</div>
                </div>
              </button>
            </div>
          </div>

          {/* Save Message */}
          {saveMessage && (
            <div className={`p-3 rounded-lg text-center ${
              saveMessage.includes('موفقیت') 
                ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300'
                : 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300'
            }`}>
              {saveMessage}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 p-4 flex gap-2">
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="flex-1 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-300 dark:disabled:bg-gray-700
                     text-white font-medium py-3 px-6 rounded-xl transition-colors
                     disabled:cursor-not-allowed"
          >
            {isSaving ? 'در حال ذخیره...' : 'ذخیره تنظیمات'}
          </button>
          <button
            onClick={onClose}
            className="px-6 py-3 border-2 border-gray-200 dark:border-gray-700 
                     hover:bg-gray-50 dark:hover:bg-gray-700 rounded-xl font-medium
                     text-gray-700 dark:text-gray-300 transition-colors"
          >
            انصراف
          </button>
        </div>
      </div>
    </div>
  );
};

export default SettingsModal;
