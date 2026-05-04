'use client'
import { useEffect, useMemo, useState } from 'react'
import { API_BASE } from '@/lib/api'
import type { Incident } from './types'

export default function IncidentsTable({ incidents }: { incidents: Incident[] }) {
  const [rowsState, setRowsState] = useState(incidents)
  const [severity, setSeverity] = useState('all')
  const [page, setPage] = useState(1)
  const pageSize = 5

  useEffect(() => {
    const ws = new WebSocket(`${API_BASE.replace('http', 'ws')}/ws/events`)
    ws.onmessage = (ev) => {
      const msg = JSON.parse(ev.data)
      if (msg.type !== 'incident_update') return
      setRowsState((prev) => {
        const existing = prev.find((p) => p.id === msg.data.id)
        if (existing) return prev.map((p) => (p.id === msg.data.id ? { ...p, ...msg.data } : p))
        return [{ ...msg.data }, ...prev]
      })
    }
    return () => ws.close()
  }, [])

  const filtered = useMemo(() => rowsState.filter(i => severity === 'all' || i.severity === severity), [rowsState, severity])
  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize))
  const rows = filtered.slice((page - 1) * pageSize, page * pageSize)

  return <div>
    <label>Severity: <select value={severity} onChange={e => {setSeverity(e.target.value);setPage(1)}}><option value='all'>All</option><option value='critical'>critical</option><option value='high'>high</option><option value='medium'>medium</option><option value='low'>low</option></select></label>
    <table><thead><tr><th>ID</th><th>Title</th><th>Severity</th><th>Status</th></tr></thead><tbody>{rows.map(i => <tr key={i.id}><td>{i.id}</td><td>{i.title}</td><td>{i.severity}</td><td>{i.status}</td></tr>)}</tbody></table>
    <button disabled={page===1} onClick={()=>setPage(p=>p-1)}>Prev</button> <span>{page}/{totalPages}</span> <button disabled={page===totalPages} onClick={()=>setPage(p=>p+1)}>Next</button>
  </div>
}
