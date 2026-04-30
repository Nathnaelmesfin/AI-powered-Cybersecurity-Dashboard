import Link from 'next/link'

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body style={{ fontFamily: 'sans-serif', margin: 0 }}>
        <nav style={{ padding: 12, background: '#111', color: '#fff', display: 'flex', gap: 12 }}>
          <Link href="/" style={{ color: '#fff' }}>Home</Link>
          <Link href="/dashboard" style={{ color: '#fff' }}>Dashboard</Link>
          <Link href="/incidents" style={{ color: '#fff' }}>Incidents</Link>
          <Link href="/assets" style={{ color: '#fff' }}>Assets</Link>
          <Link href="/playbooks" style={{ color: '#fff' }}>Playbooks</Link>
          <Link href="/topology" style={{ color: '#fff' }}>Topology</Link>
        </nav>
        <div style={{ padding: 20 }}>{children}</div>
      </body>
    </html>
  )
}
