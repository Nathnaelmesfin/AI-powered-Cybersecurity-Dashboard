'use client'
import { useEffect, useMemo, useState } from 'react'
import ReactFlow, { Background, Controls, Edge, MiniMap, Node } from 'reactflow'
import 'reactflow/dist/style.css'
import type { Asset } from './types'
import { API_BASE } from '@/lib/api'

export default function TopologyGraph({ assets }: { assets: Asset[] }) {
  const [liveScore, setLiveScore] = useState<number | null>(null)
  const [groupByType, setGroupByType] = useState(true)
  const [clusterOffline, setClusterOffline] = useState(true)
  const [showAlerts, setShowAlerts] = useState(true)

  useEffect(() => {
    const ws = new WebSocket(`${API_BASE.replace('http', 'ws')}/ws/live`)
    ws.onmessage = (ev) => {
      const msg = JSON.parse(ev.data)
      setLiveScore(msg.summary.cyber_health_score)
    }
    return () => ws.close()
  }, [])

  const prepared = useMemo(() => {
    let list = assets
    if (clusterOffline) {
      const offline = list.filter(a => a.status !== 'online')
      const online = list.filter(a => a.status === 'online')
      if (offline.length > 1) {
        list = [...online, { id: 9999, name: `offline-cluster(${offline.length})`, asset_type: 'cluster', status: 'offline', risk_score: Math.max(...offline.map(o=>o.risk_score)) } as Asset]
      }
    }
    return list
  }, [assets, clusterOffline])

  const nodes: Node[] = useMemo(() => prepared.map((a, i) => ({
    id: String(a.id),
    position: groupByType ? { x: (a.asset_type.length % 5) * 180, y: i * 80 } : { x: 120 * (i % 5), y: 100 * Math.floor(i / 5) },
    data: { label: `${a.name} | ${a.asset_type} | risk:${a.risk_score}` },
    style: showAlerts && a.risk_score > 70 ? { border: '2px solid #ef4444', background: '#fee2e2' } : {}
  })), [prepared, groupByType, showAlerts])

  const edges: Edge[] = useMemo(() => prepared.slice(1).map((a, i) => ({
    id: `e${i}`,
    source: String(prepared[0].id),
    target: String(a.id),
    label: `lat:${8 + i}ms bw:${100 - i * 3}Mb/s`
  })), [prepared])

  return (
    <div style={{ height: 540, border: '1px solid #ddd' }}>
      <div style={{ padding: 8, display: 'flex', gap: 12, alignItems: 'center' }}>
        <span>Live Cyber Health: {liveScore ?? '...'}</span>
        <label><input type='checkbox' checked={groupByType} onChange={e=>setGroupByType(e.target.checked)} /> Group by type</label>
        <label><input type='checkbox' checked={clusterOffline} onChange={e=>setClusterOffline(e.target.checked)} /> Cluster offline nodes</label>
        <label><input type='checkbox' checked={showAlerts} onChange={e=>setShowAlerts(e.target.checked)} /> Alert overlays</label>
      </div>
      <ReactFlow nodes={nodes} edges={edges} fitView>
        <Background />
        <MiniMap />
        <Controls />
      </ReactFlow>
    </div>
  )
}
