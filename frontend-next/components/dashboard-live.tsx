'use client'

import { useEffect, useMemo, useState } from 'react'
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis, BarChart, Bar } from 'recharts'
import { API_BASE } from '@/lib/api'
import type { Summary } from './types'

export default function DashboardLive({ initial }: { initial: Summary }) {
  const [summary, setSummary] = useState(initial)
  const [history, setHistory] = useState<Array<{ t: string; health: number; incidents: number }>>([])

  useEffect(() => {
    const ws = new WebSocket(`${API_BASE.replace('http', 'ws')}/ws/live`)
    ws.onmessage = (ev) => {
      const msg = JSON.parse(ev.data)
      setSummary(msg.summary)
      setHistory((prev) => [...prev.slice(-19), { t: new Date().toLocaleTimeString(), health: msg.summary.cyber_health_score, incidents: msg.summary.open_incidents }])
    }
    return () => ws.close()
  }, [])

  const bars = useMemo(() => [
    { name: 'Critical', value: summary.critical_incidents },
    { name: 'Open', value: summary.open_incidents },
    { name: 'Offline', value: summary.offline_assets },
    { name: 'Failed Logins', value: summary.failed_logins_last_hour },
  ], [summary])

  return (
    <div style={{ display: 'grid', gap: 16 }}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <div style={{ border: '1px solid #ddd', padding: 12 }}><strong>Cyber Health</strong><div>{summary.cyber_health_score}</div></div>
        <div style={{ border: '1px solid #ddd', padding: 12 }}><strong>Patch Compliance</strong><div>{summary.patch_compliance_percent}%</div></div>
      </div>
      <div style={{ height: 260, border: '1px solid #ddd', padding: 8 }}>
        <h4>Live Health / Incidents Trend</h4>
        <ResponsiveContainer width="100%" height="90%">
          <LineChart data={history}>
            <XAxis dataKey="t" /><YAxis /><Tooltip />
            <Line dataKey="health" stroke="#2563eb" />
            <Line dataKey="incidents" stroke="#dc2626" />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div style={{ height: 260, border: '1px solid #ddd', padding: 8 }}>
        <h4>Risk Snapshot</h4>
        <ResponsiveContainer width="100%" height="90%">
          <BarChart data={bars}><XAxis dataKey="name"/><YAxis/><Tooltip/><Bar dataKey="value" fill="#0ea5e9"/></BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
