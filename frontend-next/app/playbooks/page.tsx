import { apiGet } from '@/lib/api'
import type { Playbook } from '@/components/types'

export default async function PlaybooksPage() {
  const playbooks = await apiGet<Playbook[]>('/api/v1/playbooks')
  return (
    <div>
      <h2>Automation Playbooks</h2>
      {playbooks.map(p => (
        <div key={p.id} style={{border:'1px solid #ddd',padding:10,marginBottom:10}}>
          <strong>{p.name}</strong> {p.risky ? '(Risky)' : '(Safe)'}
          <div>Trigger: {p.trigger}</div>
          <ol>{p.steps.map((s, idx) => <li key={idx}>{s}</li>)}</ol>
        </div>
      ))}
    </div>
  )
}
