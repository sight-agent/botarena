import { Link, Route, Routes, useNavigate } from 'react-router-dom'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import EnvironmentsPage from './pages/EnvironmentsPage'
import EnvIPDPage from './pages/EnvIPDPage'
import BotsPage from './pages/BotsPage'
import BotDetailPage from './pages/BotDetailPage'
import { clearToken, getToken } from './lib/api'

export default function App() {
  const nav = useNavigate()
  const authed = Boolean(getToken())

  return (
    <div style={{ fontFamily: 'system-ui, sans-serif', padding: 16 }}>
      <header style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
        <h1 style={{ margin: 0, fontSize: 20 }}>botarena</h1>
        <nav style={{ display: 'flex', gap: 10 }}>
          <Link to="/env">Environments</Link>
          <Link to="/bots">Bots</Link>
        </nav>
        <div style={{ marginLeft: 'auto' }}>
          {authed ? (
            <button
              onClick={() => {
                clearToken()
                nav('/login')
              }}
            >
              Logout
            </button>
          ) : (
            <span style={{ opacity: 0.7 }}>Not logged in</span>
          )}
        </div>
      </header>

      <main style={{ marginTop: 16 }}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/env" element={<EnvironmentsPage />} />
          <Route path="/env/ipd" element={<EnvIPDPage />} />
          <Route path="/bots" element={<BotsPage />} />
          <Route path="/bots/:botId" element={<BotDetailPage />} />
          <Route path="*" element={<EnvironmentsPage />} />
        </Routes>
      </main>
    </div>
  )
}

