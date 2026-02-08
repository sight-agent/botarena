import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../lib/api'

export default function BotDetailPage() {
  const { botId } = useParams()
  const [bot, setBot] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const [runStatus, setRunStatus] = useState<string | null>(null)
  const [runResult, setRunResult] = useState<any>(null)
  const [code, setCode] = useState(
    "def act(observation, state):\n    return 'C', state\n"
  )

  async function load() {
    if (!botId) return
    setError(null)
    try {
      const b = await api.getBot(botId)
      setBot(b)
      const active = b.versions.find((v: any) => v.id === b.active_version_id)
      if (active) setCode(active.code)
    } catch (err: any) {
      setError(String(err?.detail || err?.message || err))
    }
  }

  useEffect(() => {
    load()
  }, [botId])

  if (!botId) return <div>Missing botId</div>
  if (error) return <div style={{ color: 'crimson' }}>{error}</div>
  if (!bot) return <div>Loading...</div>

  return (
    <div style={{ maxWidth: 900, display: 'grid', gap: 12 }}>
      <h2>
        Bot: {bot.name}{' '}
        <span style={{ opacity: 0.7 }}>
          (active v: {bot.active_version_id ?? 'none'})
        </span>
      </h2>

      <section>
        <h3>Versions</h3>
        <ul>
          {bot.versions.map((v: any) => (
            <li key={v.id} style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <button
                onClick={async () => {
                  await api.setActiveVersion(botId, v.id)
                  await load()
                }}
                disabled={v.id === bot.active_version_id}
              >
                Set active
              </button>
              <span>
                v{v.version_num} (id {v.id})
              </span>
              <button
                style={{ marginLeft: 'auto' }}
                disabled={v.id === bot.active_version_id}
                onClick={async () => {
                  if (!confirm(`Delete version v${v.version_num}? This cannot be undone.`)) return
                  try {
                    await api.deleteVersion(botId, v.id)
                    await load()
                  } catch (err: any) {
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

      <section>
        <h3>Code (new version)</h3>
        <textarea
          value={code}
          onChange={(e) => setCode(e.target.value)}
          rows={14}
          style={{ width: '100%', fontFamily: 'ui-monospace, monospace' }}
        />
        <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
          <button
            onClick={async () => {
              await api.createVersion(botId, code)
              await load()
            }}
          >
            Save new version
          </button>
          <button
            onClick={async () => {
              setRunStatus('Running sandbox match vs always_cooperate...')
              setRunResult(null)
              try {
                const r = await api.runTest(botId)
                setRunResult(r)
                setRunStatus(null)
              } catch (err: any) {
                setRunStatus(null)
                setError(String(err?.detail || err?.message || err))
              }
            }}
          >
            Run Test
          </button>
          <button
            onClick={() => {
              alert('Submit is intentionally not implemented in this scaffold.')
            }}
          >
            Submit (stub)
          </button>
        </div>
        {runStatus ? <div style={{ marginTop: 8 }}>{runStatus}</div> : null}
        {runResult ? (
          <div style={{ marginTop: 8 }}>
            <div>
              Match #{runResult.match_id} complete. You: {runResult.cum_a} vs
              baseline: {runResult.cum_b}
            </div>
          </div>
        ) : null}
      </section>
    </div>
  )
}
