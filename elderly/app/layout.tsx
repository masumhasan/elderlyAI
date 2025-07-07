import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Elderly AI Assistant',
  description: 'AI-powered voice assistant for elderly users',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        {children}
      </body>
    </html>
  )
}