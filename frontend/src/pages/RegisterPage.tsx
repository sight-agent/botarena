import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../lib/api'

export default function RegisterPage() {
  const nav = useNavigate()
  const [username, setUsername] = useState('alice')
  const [password, setPassword] = useState('password123')
  const [error, setError] = useState<string | null>(null)

  return (
    <div style={{ maxWidth: 420 }}>
      <h2>Register</h2>
      <form
        onSubmit={async (e) => {
          e.preventDefault()
          setError(null)
          try {
            await api.register(username, password)
            nav('/login')
          } catch (err: any) {
            setError(String(err?.message || err))
          }
        }}
      >
        <div style={{ display: 'grid', gap: 8 }}>
          <label>
            Username
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              style={{ width: '100%' }}
            />
          </label>
          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={{ width: '100%' }}
            />
          </label>
          <button type="submit">Create account</button>
          {error ? <div style={{ color: 'crimson' }}>{error}</div> : null}
          <div style={{ opacity: 0.8 }}>
            Already have an account? <Link to="/login">Login</Link>
          </div>
        </div>
      </form>
    </div>
  )
}

