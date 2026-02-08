import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../lib/api'

export default function BotsPage() {
  const nav = useNavigate()
  const [bots, setBots] = useState<Array<any>>([])
  const [error, setError] = useState<string | null>(null)
  const [authError, setAuthError] = useState(false)

  const [name, setName] = useState('mybot')
  const [description, setDescription] = useState('MVP bot')
  const [code, setCode] = useState(
    "def act(observation, state):\n    return 'C', state\n"
  )

  async function load() {
    setError(null)
    setAuthError(false)
    try {
      const b = await api.listBots()
      setBots(b)
    } catch (err: any) {
      if (err?.status === 401) setAuthError(true)
      setError(String(err?.detail || err?.message || err))
    }
  }

  useEffect(() => {
    load()
  }, [])

  return (
    <div style={{ display: 'grid', gap: 16, maxWidth: 820 }}>
      <section>
        <h2>Your bots</h2>
        {error ? (
          <div style={{ color: 'crimson' }}>
            {error}
            {authError ? (
              <div>
                <button onClick={() => nav('/login')}>Go to login</button>
              </div>
            ) : null}
          </div>
        ) : null}
        <ul>
          {bots.map((b) => (
            <li key={b.id} style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <Link to={`/bots/${b.id}`}>{b.name}</Link>{' '}
              <span style={{ opacity: 0.7 }}>
                (active v: {b.active_version_id ?? 'none'})
              </span>
              <button
                style={{ marginLeft: 'auto' }}
                onClick={async () => {
                  if (!confirm(`Delete bot "${b.name}"? This cannot be undone.`)) return
                  try {
                    await api.deleteBot(b.id)
                    await load()
                  } catch (err: any) {
                    if (err?.status === 401) setAuthError(true)
                    setError(String(err?.detail || err?.message || err))
                  }
                }}
              >
                Delete
              </button>
            </li>
          ))}
        </ul>
      </section>

      <section
        style={{ borderTop: '1px solid #ddd', paddingTop: 12, maxWidth: 520 }}
      >
        <h3>Create bot</h3>
        <form
          onSubmit={async (e) => {
            e.preventDefault()
            setError(null)
            setAuthError(false)
            try {
              const created = await api.createBot(name, description, code)
              await load()
              nav(`/bots/${created.id}`)
            } catch (err: any) {
              if (err?.status === 401) setAuthError(true)
              setError(String(err?.detail || err?.message || err))
            }
          }}
        >
          <div style={{ display: 'grid', gap: 8 }}>
            <label>
              Name
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                style={{ width: '100%' }}
              />
            </label>
            <label>
              Description
              <input
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                style={{ width: '100%' }}
              />
            </label>
            <label>
              Code
              <textarea
                value={code}
                onChange={(e) => setCode(e.target.value)}
                rows={6}
                style={{ width: '100%', fontFamily: 'ui-monospace, monospace' }}
              />
            </label>
            <button type="submit">Create</button>
          </div>
        </form>
      </section>
    </div>
  )
}

