'use client'

import { useState, useEffect } from 'react'
import { Users, UserPlus, Trash2, Shield, User, BarChart3, AlertCircle } from 'lucide-react'
import axiosInstance from '@/lib/axios'

interface Member {
  id: string
  email: string
  first_name: string
  last_name: string
  organization_role: 'admin' | 'member'
  is_active: boolean
  is_owner: boolean
  monthly_usage: number
  created_at: string
}

interface OrganizationInfo {
  has_organization: boolean
  is_admin: boolean
  organization?: {
    id: string
    name: string
    company_name: string
    phone: string
    logo: string | null
  }
  members_count: number
  max_members: number
  can_add_members: boolean
  message?: string
}

interface UsageData {
  daily: { used: number; limit: number; percentage: number }
  monthly: { used: number; limit: number; percentage: number }
  by_member: { email: string; count: number }[]
  daily_trend: { date: string; count: number }[]
}

export default function OrganizationSection() {
  const [orgInfo, setOrgInfo] = useState<OrganizationInfo | null>(null)
  const [members, setMembers] = useState<Member[]>([])
  const [usage, setUsage] = useState<UsageData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  
  // Add member form
  const [showAddForm, setShowAddForm] = useState(false)
  const [newMember, setNewMember] = useState({
    email: '',
    phone_number: '',
    first_name: '',
    last_name: '',
    role: 'member' as 'admin' | 'member'
  })
  const [addingMember, setAddingMember] = useState(false)
  
  // Active tab
  const [activeTab, setActiveTab] = useState<'members' | 'usage'>('members')

  useEffect(() => {
    loadOrganizationData()
  }, [])

  const loadOrganizationData = async () => {
    try {
      setLoading(true)
      setError('')
      
      // Get organization info
      const infoRes = await axiosInstance.get('/api/v1/auth/organization/')
      setOrgInfo(infoRes.data)
      
      if (infoRes.data.has_organization && infoRes.data.is_admin) {
        // Get members
        const membersRes = await axiosInstance.get('/api/v1/auth/organization/members/')
        setMembers(membersRes.data.members || [])
        
        // Get usage
        const usageRes = await axiosInstance.get('/api/v1/auth/organization/usage/')
        setUsage(usageRes.data)
      }
    } catch (err: any) {
      console.error('Error loading organization data:', err)
      setError(err.response?.data?.error || 'خطا در بارگذاری اطلاعات سازمان')
    } finally {
      setLoading(false)
    }
  }

  const handleAddMember = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newMember.email || !newMember.phone_number) return
    
    try {
      setAddingMember(true)
      await axiosInstance.post('/api/v1/auth/organization/members/', newMember)
      
      // Reset form and reload
      setNewMember({ email: '', phone_number: '', first_name: '', last_name: '', role: 'member' })
      setShowAddForm(false)
      loadOrganizationData()
    } catch (err: any) {
      setError(err.response?.data?.error || 'خطا در افزودن عضو')
    } finally {
      setAddingMember(false)
    }
  }

  const handleChangeRole = async (memberId: string, newRole: 'admin' | 'member') => {
    try {
      await axiosInstance.patch(`/api/v1/auth/organization/members/${memberId}/`, {
        role: newRole
      })
      loadOrganizationData()
    } catch (err: any) {
      setError(err.response?.data?.error || 'خطا در تغییر نقش')
    }
  }

  const handleDeleteMember = async (memberId: string, email: string) => {
    if (!confirm(`آیا از حذف ${email} مطمئن هستید؟ تمام گفتگوهای این کاربر حذف خواهد شد.`)) {
      return
    }
    
    try {
      await axiosInstance.delete(`/api/v1/auth/organization/members/${memberId}/`)
      loadOrganizationData()
    } catch (err: any) {
      setError(err.response?.data?.error || 'خطا در حذف عضو')
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
      </div>
    )
  }

  // Not a business user
  if (!orgInfo?.has_organization) {
    return (
      <div className="text-center py-12">
        <Users className="w-16 h-16 mx-auto text-gray-300 mb-4" />
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
          مدیریت سازمان
        </h3>
        <p className="text-gray-500 dark:text-gray-400">
          {orgInfo?.message || 'این قابلیت فقط برای کاربران حقوقی فعال است'}
        </p>
      </div>
    )
  }

  // Not an admin
  if (!orgInfo.is_admin) {
    return (
      <div className="text-center py-12">
        <Shield className="w-16 h-16 mx-auto text-gray-300 mb-4" />
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
          دسترسی محدود
        </h3>
        <p className="text-gray-500 dark:text-gray-400">
          شما به عنوان عضو سازمان دسترسی به این بخش ندارید
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">
            {orgInfo.organization?.name}
          </h2>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {orgInfo.members_count} از {orgInfo.max_members} عضو
          </p>
        </div>
        
        {orgInfo.can_add_members && (
          <button
            onClick={() => setShowAddForm(true)}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
          >
            <UserPlus className="w-4 h-4" />
            افزودن عضو
          </button>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 p-3 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-lg">
          <AlertCircle className="w-5 h-5" />
          {error}
          <button onClick={() => setError('')} className="mr-auto text-sm underline">بستن</button>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 border-b border-gray-200 dark:border-gray-700">
        <button
          onClick={() => setActiveTab('members')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'members'
              ? 'border-purple-600 text-purple-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <Users className="w-4 h-4 inline ml-2" />
          اعضا
        </button>
        <button
          onClick={() => setActiveTab('usage')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'usage'
              ? 'border-purple-600 text-purple-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <BarChart3 className="w-4 h-4 inline ml-2" />
          مصرف
        </button>
      </div>

      {/* Add Member Form */}
      {showAddForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 w-full max-w-md mx-4">
            <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4">
              افزودن عضو جدید
            </h3>
            
            <form onSubmit={handleAddMember} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  ایمیل *
                </label>
                <input
                  type="email"
                  value={newMember.email}
                  onChange={(e) => setNewMember({ ...newMember, email: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder="email@example.com"
                  required
                  dir="ltr"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  شماره موبایل *
                </label>
                <input
                  type="tel"
                  value={newMember.phone_number}
                  onChange={(e) => setNewMember({ ...newMember, phone_number: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder="09123456789"
                  pattern="09[0-9]{9}"
                  required
                  dir="ltr"
                />
                <p className="text-xs text-gray-500 mt-1">
                  این شماره نمی‌تواند برای ورود حقیقی استفاده شود
                </p>
              </div>
              
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    نام
                  </label>
                  <input
                    type="text"
                    value={newMember.first_name}
                    onChange={(e) => setNewMember({ ...newMember, first_name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    نام خانوادگی
                  </label>
                  <input
                    type="text"
                    value={newMember.last_name}
                    onChange={(e) => setNewMember({ ...newMember, last_name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  نقش
                </label>
                <select
                  value={newMember.role}
                  onChange={(e) => setNewMember({ ...newMember, role: e.target.value as 'admin' | 'member' })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  <option value="member">عضو عادی</option>
                  <option value="admin">مدیر</option>
                </select>
                <p className="text-xs text-gray-500 mt-1">
                  مدیر می‌تواند اعضا را مدیریت کند
                </p>
              </div>
              
              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddForm(false)}
                  className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
                >
                  انصراف
                </button>
                <button
                  type="submit"
                  disabled={addingMember}
                  className="flex-1 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
                >
                  {addingMember ? 'در حال افزودن...' : 'افزودن'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Members Tab */}
      {activeTab === 'members' && (
        <div className="space-y-3">
          {members.map((member) => (
            <div
              key={member.id}
              className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg"
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-purple-100 dark:bg-purple-900 flex items-center justify-center">
                  {member.is_owner ? (
                    <Shield className="w-5 h-5 text-purple-600" />
                  ) : (
                    <User className="w-5 h-5 text-purple-600" />
                  )}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-gray-900 dark:text-white">
                      {member.first_name && member.last_name 
                        ? `${member.first_name} ${member.last_name}`
                        : member.email}
                    </span>
                    {member.is_owner && (
                      <span className="text-xs px-2 py-0.5 bg-purple-100 dark:bg-purple-900 text-purple-600 rounded-full">
                        مالک
                      </span>
                    )}
                    {!member.is_owner && member.organization_role === 'admin' && (
                      <span className="text-xs px-2 py-0.5 bg-blue-100 dark:bg-blue-900 text-blue-600 rounded-full">
                        مدیر
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">{member.email}</p>
                </div>
              </div>
              
              <div className="flex items-center gap-4">
                <span className="text-sm text-gray-500">
                  {member.monthly_usage} پیام این ماه
                </span>
                
                {!member.is_owner && (
                  <div className="flex items-center gap-2">
                    <select
                      value={member.organization_role}
                      onChange={(e) => handleChangeRole(member.id, e.target.value as 'admin' | 'member')}
                      className="text-sm px-2 py-1 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    >
                      <option value="member">عضو</option>
                      <option value="admin">مدیر</option>
                    </select>
                    
                    <button
                      onClick={() => handleDeleteMember(member.id, member.email)}
                      className="p-2 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg"
                      title="حذف عضو"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
          
          {members.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              هنوز عضوی اضافه نشده است
            </div>
          )}
        </div>
      )}

      {/* Usage Tab */}
      {activeTab === 'usage' && usage && (
        <div className="space-y-6">
          {/* Summary Cards */}
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <h4 className="text-sm font-medium text-blue-600 dark:text-blue-400 mb-2">مصرف امروز</h4>
              <div className="text-2xl font-bold text-blue-700 dark:text-blue-300">
                {usage.daily.used} / {usage.daily.limit}
              </div>
              <div className="w-full bg-blue-200 dark:bg-blue-800 rounded-full h-2 mt-2">
                <div 
                  className="bg-blue-600 h-2 rounded-full transition-all"
                  style={{ width: `${Math.min(usage.daily.percentage, 100)}%` }}
                />
              </div>
            </div>
            
            <div className="p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
              <h4 className="text-sm font-medium text-purple-600 dark:text-purple-400 mb-2">مصرف این ماه</h4>
              <div className="text-2xl font-bold text-purple-700 dark:text-purple-300">
                {usage.monthly.used} / {usage.monthly.limit}
              </div>
              <div className="w-full bg-purple-200 dark:bg-purple-800 rounded-full h-2 mt-2">
                <div 
                  className="bg-purple-600 h-2 rounded-full transition-all"
                  style={{ width: `${Math.min(usage.monthly.percentage, 100)}%` }}
                />
              </div>
            </div>
          </div>
          
          {/* Usage by Member */}
          <div>
            <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              مصرف به تفکیک اعضا (این ماه)
            </h4>
            <div className="space-y-2">
              {usage.by_member.map((item, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                  <span className="text-sm text-gray-700 dark:text-gray-300">{item.email}</span>
                  <span className="text-sm font-medium text-gray-900 dark:text-white">{item.count} پیام</span>
                </div>
              ))}
              
              {usage.by_member.length === 0 && (
                <div className="text-center py-4 text-gray-500 text-sm">
                  هنوز مصرفی ثبت نشده
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
