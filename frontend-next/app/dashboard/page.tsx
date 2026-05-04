import type { Summary } from '@/components/types'
import DashboardLive from '@/components/dashboard-live'
import { apiGet } from '@/lib/api'

export default async function DashboardPage() {
  const summary = await apiGet<Summary>('/api/v1/summary')
  return <><h2>Executive Dashboard</h2><DashboardLive initial={summary} /></>
}
