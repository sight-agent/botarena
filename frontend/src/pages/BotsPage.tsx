import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../lib/api'

const ENVS = [{ id: 'ipd', label: "Iterated Prisoner's Dilemma" }]

export default function BotsPage() {
  const nav = useNavigate()
  const [bots, setBots] = useState<Array<any>>([])
  const [error, setError] = useState<string | null>(null)
  const [authError, setAuthError] = useState(false)

  const [envId, setEnvId] = useState('ipd')
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

  const grouped = useMemo(() => {
    const by: Record<string, any[]> = {}
    for (const b of bots) {
      const k = b.env_id || 'unknown'
      by[k] = by[k] || []
      by[k].push(b)
    }
    return by
  }, [bots])

  return (
    <div style={{ display: 'grid', gap: 16, maxWidth: 900 }}>
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

        {Object.keys(grouped).length === 0 ? (
          <div style={{ opacity: 0.7 }}>No bots yet.</div>
        ) : (
          <div style={{ display: 'grid', gap: 12 }}>
            {Object.entries(grouped).map(([env, list]) => (
              <section key={env}>
                <h3 style={{ margin: 0 }}>{env.toUpperCase()}</h3>
                <ul>
                  {list.map((b) => (
                    <li
                      key={b.id}
                      style={{ display: 'flex', gap: 8, alignItems: 'center' }}
                    >
                      <Link to={`/bots/${b.id}`}>{b.name}</Link>
                      {b.submitted ? (
                        <span style={{ opacity: 0.7 }}>(submitted)</span>
                      ) : null}
                      <button
                        style={{ marginLeft: 'auto' }}
                        onClick={async () => {
                          if (
                            !confirm(
                              `Delete bot "${b.name}"? This cannot be undone.`
                            )
                          )
                            return
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
            ))}
          </div>
        )}
      </section>

      <section style={{ borderTop: '1px solid #ddd', paddingTop: 12 }}>
        <h3>Create bot</h3>
        <form
          onSubmit={async (e) => {
            e.preventDefault()
            setError(null)
            setAuthError(false)
            try {
              const created = await api.createBot(envId, name, description, code)
              await load()
              nav(`/bots/${created.id}`)
            } catch (err: any) {
              if (err?.status === 401) setAuthError(true)
              setError(String(err?.detail || err?.message || err))
            }
          }}
        >
          <div style={{ display: 'grid', gap: 8, maxWidth: 520 }}>
            <label>
              Environment
              <select
                value={envId}
                onChange={(e) => setEnvId(e.target.value)}
                style={{ width: '100%' }}
              >
                {ENVS.map((e) => (
                  <option key={e.id} value={e.id}>
                    {e.label}
                  </option>
                ))}
              </select>
            </label>
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
                rows={8}
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
