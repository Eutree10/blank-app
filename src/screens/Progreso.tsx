import { useStore } from '../store/useStore'
import { InstanciaBadge, ProgressBar } from '../components/ui'

export function Progreso() {
  const { progreso } = useStore()

  return (
    <div>
      <div className="page-head">
        <h1>Progreso</h1>
        <p>Tu avance hacia completar todos los problemas de Nivel 2.</p>
      </div>

      <div className="stat-grid">
        <div className="stat">
          <div className="stat__num">{progreso.total}</div>
          <div className="stat__label">Disponibles</div>
        </div>
        <div className="stat">
          <div className="stat__num" style={{ color: 'var(--ok)' }}>
            {progreso.completados}
          </div>
          <div className="stat__label">Completados</div>
        </div>
        <div className="stat">
          <div className="stat__num">{progreso.pendientes}</div>
          <div className="stat__label">Pendientes</div>
        </div>
        <div className="stat">
          <div className="stat__num">{progreso.porcentaje}%</div>
          <div className="stat__label">Avance</div>
        </div>
      </div>

      <div className="card card--pad mt-16">
        <div className="instance-row__top">
          <strong>Avance general</strong>
          <span className="instance-row__count">
            {progreso.completados} / {progreso.total}
          </span>
        </div>
        <ProgressBar porcentaje={progreso.porcentaje} />
      </div>

      <div className="card card--pad mt-16">
        <h2 style={{ fontSize: 17, marginBottom: 6 }}>Por instancia</h2>
        {progreso.porInstancia.map((pi) => (
          <div className="instance-row" key={pi.instancia}>
            <div className="instance-row__main">
              <div className="instance-row__top">
                <InstanciaBadge instancia={pi.instancia} />
                <span className="instance-row__count">
                  {pi.completados} / {pi.total} · {pi.porcentaje}%
                </span>
              </div>
              <ProgressBar porcentaje={pi.porcentaje} />
              <div className="muted small" style={{ marginTop: 6 }}>
                {pi.pendientes} pendiente{pi.pendientes === 1 ? '' : 's'}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
