import { useEffect, useState } from 'react'
import { useStore } from '../store/useStore'
import { cuentaRegresiva, fechaLarga } from '../lib/date'
import { EstadoBadge, InstanciaBadge, NivelBadge, ProblemCard } from '../components/ui'

export function Home({ irADatos }: { irADatos: () => void }) {
  const { hoy, problemasDeHoy, finalizado, completarHoy, progreso } = useStore()
  const [countdown, setCountdown] = useState(() => cuentaRegresiva())

  useEffect(() => {
    const iv = window.setInterval(() => setCountdown(cuentaRegresiva()), 30_000)
    return () => window.clearInterval(iv)
  }, [])

  if (finalizado) {
    return (
      <div className="celebrate">
        <div className="celebrate__badge">🏅</div>
        <h1>¡Completaste todos los problemas!</h1>
        <p className="muted mt-16">
          Terminaste los {progreso.total} problemas de Nivel 2 disponibles. Podés cargar más
          años desde la pestaña <strong>Datos</strong> para seguir practicando.
        </p>
        <div className="mt-24">
          <button className="btn btn--primary" onClick={irADatos}>
            Cargar más problemas
          </button>
        </div>
      </div>
    )
  }

  if (!hoy) {
    return (
      <div className="empty">
        <div className="empty__icon">📭</div>
        <h2>No hay problemas disponibles</h2>
        <p>
          El dataset no tiene problemas de Nivel 2 sin completar. Cargá los enunciados oficiales
          desde la pestaña <strong>Datos</strong>.
        </p>
        <div className="mt-24">
          <button className="btn btn--primary" onClick={irADatos}>
            Ir a Datos
          </button>
        </div>
      </div>
    )
  }

  const esZonal = hoy.instancia === 'Zonal'
  const yaCompletado = hoy.estado === 'completed'

  return (
    <div>
      <section className="daily">
        <div className="daily__left">
          <div className="daily__date">{fechaLarga(hoy.fecha)}</div>
          <div className="daily__title">
            {hoy.instancia} {hoy.anio}
          </div>
          <div className="daily__sub">
            {esZonal
              ? `Certamen Zonal · ${problemasDeHoy.length} problema${problemasDeHoy.length === 1 ? '' : 's'} para hoy`
              : `Certamen Intercolegial · año completo (${problemasDeHoy.length} problemas)`}
          </div>
        </div>
        <div className="daily__right">
          <div className="daily__countdown-label">Vence en</div>
          <div className="daily__countdown">{countdown}</div>
        </div>
      </section>

      <div className="chip-row mt-16">
        <InstanciaBadge instancia={hoy.instancia} />
        <NivelBadge nivel={hoy.nivel} />
        <EstadoBadge estado={hoy.estado} />
        <span className="badge badge--nivel">Año {hoy.anio}</span>
      </div>

      <div className="mt-16">
        {problemasDeHoy.map((p, i) => (
          <ProblemCard key={p.id} problem={p} orden={i + 1} />
        ))}
      </div>

      <div className="card card--pad mt-16">
        {yaCompletado ? (
          <div className="field-row" style={{ justifyContent: 'space-between' }}>
            <div>
              <strong style={{ color: 'var(--ok)' }}>✓ Marcado como completado</strong>
              <div className="muted small">
                Pasó al historial. La próxima asignación llega mañana a las 00:00.
              </div>
            </div>
            <EstadoBadge estado="completed" />
          </div>
        ) : (
          <>
            <button className="btn btn--primary btn--lg btn--block" onClick={completarHoy}>
              Marcar como completado
            </button>
            <p className="muted small" style={{ textAlign: 'center', marginTop: 12, marginBottom: 0 }}>
              Tenés hasta las 00:00 de hoy. Si no lo completás, queda registrado como vencido y
              los problemas vuelven a estar disponibles más adelante.
            </p>
          </>
        )}
      </div>
    </div>
  )
}
