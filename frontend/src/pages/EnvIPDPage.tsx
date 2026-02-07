export default function EnvIPDPage() {
  return (
    <div style={{ maxWidth: 760 }}>
      <h2>Iterated Prisoner&apos;s Dilemma (MVP)</h2>
      <p style={{ opacity: 0.85 }}>
        Two-player repeated game. Your bot must implement <code>act(observation,
        state)</code> and return <code>(&quot;C&quot; | &quot;D&quot;, new_state)</code>.
      </p>
      <pre
        style={{
          background: '#f6f6f6',
          padding: 12,
          borderRadius: 8,
          overflow: 'auto'
        }}
      >{`observation = { round: 17, max_rounds: 200, history: [['D','D'], ...] }`}</pre>
      <p style={{ opacity: 0.7 }}>
        Leaderboards and match replays are not implemented in this scaffold.
      </p>
    </div>
  )
}

