'use client'
import { useEffect, useMemo, useState } from 'react'
import { API_BASE } from '@/lib/api'
import type { Asset } from './types'

export default function AssetsTable({ assets }: { assets: Asset[] }) {
  const [rowsState, setRowsState] = useState(assets)
  const [status, setStatus] = useState('all')
  const [page, setPage] = useState(1)
  const pageSize = 5

  useEffect(() => {
    const ws = new WebSocket(`${API_BASE.replace('http', 'ws')}/ws/events`)
    ws.onmessage = (ev) => {
      const msg = JSON.parse(ev.data)
      if (msg.type !== 'asset_update') return
      setRowsState((prev) => prev.map((a) => (a.id === msg.data.id ? { ...a, ...msg.data } : a)))
    }
    return () => ws.close()
  }, [])

  const filtered = useMemo(() => rowsState.filter(a => status === 'all' || a.status === status), [rowsState, status])
  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize))
  const rows = filtered.slice((page - 1) * pageSize, page * pageSize)

  return <div>
    <label>Status: <select value={status} onChange={e=>{setStatus(e.target.value);setPage(1)}}><option value='all'>All</option><option value='online'>online</option><option value='offline'>offline</option><option value='degraded'>degraded</option></select></label>
    <table><thead><tr><th>Name</th><th>Type</th><th>Status</th><th>Risk</th></tr></thead><tbody>{rows.map(a => <tr key={a.id}><td>{a.name}</td><td>{a.asset_type}</td><td>{a.status}</td><td>{a.risk_score}</td></tr>)}</tbody></table>
    <button disabled={page===1} onClick={()=>setPage(p=>p-1)}>Prev</button> <span>{page}/{totalPages}</span> <button disabled={page===totalPages} onClick={()=>setPage(p=>p+1)}>Next</button>
  </div>
}
