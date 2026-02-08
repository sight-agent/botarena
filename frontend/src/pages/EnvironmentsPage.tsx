import { Link } from 'react-router-dom'

const ENVS = [
  {
    id: 'ipd',
    name: "Iterated Prisoner's Dilemma",
    desc: 'Repeated 2-player game. Actions: C/D. 200 rounds.'
  }
]

export default function EnvironmentsPage() {
  return (
    <div style={{ maxWidth: 820, display: 'grid', gap: 12 }}>
      <h2>Environments</h2>
      <div style={{ opacity: 0.8 }}>
        Pick an environment to see rules, leaderboard, and replays.
      </div>
      <ul style={{ paddingLeft: 18 }}>
        {ENVS.map((e) => (
          <li key={e.id}>
            <div style={{ display: 'grid', gap: 2 }}>
              <div>
                <Link to={`/env/${e.id}`}>{e.name}</Link>
              </div>
              <div style={{ opacity: 0.75 }}>{e.desc}</div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}
