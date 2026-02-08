import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../lib/api'

export default function EnvIPDPage() {
  const [rows, setRows] = useState<
    Array<{ bot_id: number; bot_name: string; best_score: number; matches: number }>
  >([])
  const [error, setError] = useState<string | null>(null)

  async function load() {
    setError(null)
    try {
      const r = await api.ipdLeaderboard()
      setRows(r)
    } catch (err: any) {
      setError(String(err?.detail || err?.message || err))
    }
  }

  useEffect(() => {
    load()
  }, [])

  return (
    <div style={{ maxWidth: 900, display: 'grid', gap: 12 }}>
      <h2>Iterated Prisoner&apos;s Dilemma</h2>

      <section style={{ display: 'grid', gap: 8 }}>
        <div style={{ opacity: 0.85 }}>
          Two-player repeated game. Your bot must implement{' '}
          <code>act(observation, state)</code> and return{' '}
          <code>("C" | "D", new_state)</code>.
        </div>
        <pre
          style={{
            background: '#f6f6f6',
            padding: 12,
            borderRadius: 8,
            overflow: 'auto'
          }}
        >{`observation = { round: 17, max_rounds: 200, history: [['D','D'], ...] }`}</pre>
        <div style={{ opacity: 0.85 }}>
          To compete: go to <Link to="/bots">Bots</Link>, save a version, run a
          test.
        </div>
      </section>

      <section style={{ display: 'grid', gap: 8 }}>
        <h3 style={{ margin: 0 }}>Leaderboard (vs always_cooperate)</h3>
        {error ? <div style={{ color: 'crimson' }}>{error}</div> : null}
        {rows.length === 0 ? (
          <div style={{ opacity: 0.7 }}>No completed matches yet.</div>
        ) : (
          <ul style={{ paddingLeft: 18, margin: 0 }}>
            {rows.map((r, idx) => (
              <li key={r.bot_id}>
                <span style={{ display: 'inline-block', width: 26, opacity: 0.7 }}>
                  #{idx + 1}
                </span>{' '}
                <Link to={`/bots/${r.bot_id}`}>{r.bot_name}</Link> — best score:{' '}
                <b>{r.best_score}</b> ({r.matches} matches)
              </li>
            ))}
          </ul>
        )}
        <div>
          <button onClick={load}>Refresh</button>
        </div>
      </section>
    </div>
  )
}

