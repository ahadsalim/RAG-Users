import type { Metadata } from 'next'
import './globals.css'
import { Providers } from '@/components/providers'

export const metadata: Metadata = {
  title: 'مشاور هوشمند کسب و کار',
  description: 'سیستم مشاوره حقوقی و کسب‌وکار مبتنی بر هوش مصنوعی',
  keywords: 'مشاوره حقوقی، هوش مصنوعی، چت‌بات، مشاور',
  authors: [{ name: 'مشاور هوشمند کسب و کار' }],
  viewport: 'width=device-width, initial-scale=1',
  icons: {
    icon: '/favicon.ico',
    apple: '/logo-small.png',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="fa" dir="rtl" suppressHydrationWarning>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
