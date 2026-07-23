import { useState } from 'react'
import { StoreProvider } from './store/useStore'
import { Home } from './screens/Home'
import { Historial } from './screens/Historial'
import { Progreso } from './screens/Progreso'
import { Datos } from './screens/Datos'

type Tab = 'hoy' | 'historial' | 'progreso' | 'datos'

const TABS: { id: Tab; label: string }[] = [
  { id: 'hoy', label: 'Hoy' },
  { id: 'historial', label: 'Historial' },
  { id: 'progreso', label: 'Progreso' },
  { id: 'datos', label: 'Datos' },
]

function Nav({ tab, setTab, className }: { tab: Tab; setTab: (t: Tab) => void; className: string }) {
  return (
    <nav className={className}>
      {TABS.map((t) => (
        <button
          key={t.id}
          className={`nav__btn ${tab === t.id ? 'nav__btn--active' : ''}`}
          onClick={() => setTab(t.id)}
        >
          {t.label}
        </button>
      ))}
    </nav>
  )
}

export default function App() {
  const [tab, setTab] = useState<Tab>('hoy')

  return (
    <StoreProvider>
      <div className="app">
        <header className="site-header">
          <div className="site-header__inner">
            <div className="brand">
              <div className="brand__mark">Ω</div>
              <div>
                <div className="brand__title">OMA · Práctica diaria</div>
                <div className="brand__subtitle">Nivel 2 · Entrenamiento</div>
              </div>
            </div>
            <Nav tab={tab} setTab={setTab} className="nav" />
          </div>
        </header>

        <main>
          <div className="container">
            {tab === 'hoy' && <Home irADatos={() => setTab('datos')} />}
            {tab === 'historial' && <Historial />}
            {tab === 'progreso' && <Progreso />}
            {tab === 'datos' && <Datos />}
          </div>
        </main>

        <Nav tab={tab} setTab={setTab} className="nav-mobile" />

        <footer className="site-footer">
          <div className="container">
            Hecho para entrenar OMA · Los datos se guardan en tu navegador.
          </div>
        </footer>
      </div>
    </StoreProvider>
  )
}
