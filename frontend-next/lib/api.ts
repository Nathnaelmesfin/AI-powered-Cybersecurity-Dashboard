export const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? 'http://127.0.0.1:8000'
export const API_TOKEN = process.env.NEXT_PUBLIC_API_TOKEN ?? 'change-me'
export const API_USER = process.env.NEXT_PUBLIC_API_USER ?? 'secops'
export const API_PASSWORD = process.env.NEXT_PUBLIC_API_PASSWORD ?? 'secops123'

export async function getBearerToken(): Promise<string> {
  const form = new URLSearchParams({ username: API_USER, password: API_PASSWORD })
  const res = await fetch(`${API_BASE}/auth/token`, {
    method: 'POST',
    headers: { 'X-API-Token': API_TOKEN, 'Content-Type': 'application/x-www-form-urlencoded' },
    body: form.toString(),
    cache: 'no-store'
  })
  if (!res.ok) throw new Error('Failed auth token fetch')
  const data = await res.json()
  return data.access_token
}

export async function apiGet<T>(path: string): Promise<T> {
  const bearer = await getBearerToken()
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'X-API-Token': API_TOKEN, Authorization: `Bearer ${bearer}` },
    cache: 'no-store'
  })
  if (!res.ok) throw new Error(`API error ${path}`)
  return res.json()
}
