import './globals.css'

export const metadata = {
  title: 'Production Dashboard',
  description: 'Fish production analytics',
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className="bg-gray-950 text-white">{children}</body>
    </html>
  )
}
