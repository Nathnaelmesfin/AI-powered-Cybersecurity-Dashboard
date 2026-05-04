import IncidentsTable from '@/components/incidents-table'
import type { Incident } from '@/components/types'
import { apiGet } from '@/lib/api'

export default async function IncidentsPage() {
  const incidents = await apiGet<Incident[]>('/api/v1/incidents')
  return <><h2>SOC Incident Queue</h2><IncidentsTable incidents={incidents} /></>
}
