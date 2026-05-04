import TopologyGraph from '@/components/topology-graph'
import type { Asset } from '@/components/types'
import { apiGet } from '@/lib/api'

export default async function TopologyPage() {
  const assets = await apiGet<Asset[]>('/api/v1/assets')
  return <><h2>Network Topology</h2><TopologyGraph assets={assets} /></>
}
