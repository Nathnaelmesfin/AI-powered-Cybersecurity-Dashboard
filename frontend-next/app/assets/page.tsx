import AssetsTable from '@/components/assets-table'
import type { Asset } from '@/components/types'
import { apiGet } from '@/lib/api'

export default async function AssetsPage() {
  const assets = await apiGet<Asset[]>('/api/v1/assets')
  return <><h2>Asset Inventory</h2><AssetsTable assets={assets} /></>
}
