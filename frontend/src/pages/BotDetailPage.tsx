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
  const [savedCode, setSavedCode] = useState<string | null>(null)

  async function load() {
    if (!botId) return
    setError(null)
    try {
      const b = await api.getBot(botId)
      setBot(b)
      setCode(b.code)
      setSavedCode(b.code)
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

  const dirty = savedCode !== null && code !== savedCode

  return (
    <div style={{ maxWidth: 900, display: 'grid', gap: 12 }}>
      <h2>
        Bot: {bot.name}{' '}
        <span style={{ opacity: 0.7 }}>(env: {bot.env_id})</span>{' '}
        {bot.submitted ? <span style={{ opacity: 0.7 }}>(submitted)</span> : null}
      </h2>

      <section>
        <h3>Code</h3>
        <textarea
          value={code}
          onChange={(e) => setCode(e.target.value)}
          rows={16}
          style={{ width: '100%', fontFamily: 'ui-monospace, monospace' }}
        />
        <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
          <button
            disabled={!dirty}
            title={!dirty ? 'No changes to save.' : ''}
            onClick={async () => {
              try {
                await api.updateBotCode(botId, code)
                await load()
              } catch (err: any) {
                setError(String(err?.detail || err?.message || err))
              }
            }}
          >
            Save
          </button>
          <button
            disabled={dirty}
            title={dirty ? 'Save your changes before running a test.' : ''}
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
            onClick={async () => {
              try {
                await api.submitBot(botId)
                await load()
                alert('Submitted to leaderboard.')
              } catch (err: any) {
                setError(String(err?.detail || err?.message || err))
              }
            }}
          >
            Submit
          </button>
        </div>

        {dirty ? (
          <div style={{ marginTop: 8, opacity: 0.8 }}>
            You have unsaved changes. Save before running a test.
          </div>
        ) : null}
        {runStatus ? <div style={{ marginTop: 8 }}>{runStatus}</div> : null}
        {runResult ? (
          <div style={{ marginTop: 8 }}>
            Match #{runResult.match_id} complete. You: {runResult.cum_a} vs
            baseline: {runResult.cum_b}
          </div>
        ) : null}
      </section>
    </div>
  )
}
