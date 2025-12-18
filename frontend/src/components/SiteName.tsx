'use client'

import { useState, useEffect } from 'react'
import { getSiteSettings } from '@/services/settingsService'

interface SiteNameProps {
  fallback?: string
  style?: React.CSSProperties
  className?: string
}

export function SiteName({ fallback = 'تجارت چت', style, className }: SiteNameProps) {
  const [siteName, setSiteName] = useState(fallback)

  useEffect(() => {
    getSiteSettings()
      .then(settings => {
        if (settings.frontend_site_name) {
          setSiteName(settings.frontend_site_name)
        }
      })
      .catch(console.error)
  }, [])

  return <span style={style} className={className}>{siteName}</span>
}

export function SiteSubtitle({ fallback = 'سامانه مشاور هوشمند کسب و کار', style, className }: SiteNameProps) {
  const [siteName, setSiteName] = useState(fallback)

  useEffect(() => {
    getSiteSettings()
      .then(settings => {
        if (settings.frontend_site_name) {
          setSiteName(`سامانه ${settings.frontend_site_name}`)
        }
      })
      .catch(console.error)
  }, [])

  return <span style={style} className={className}>{siteName}</span>
}
