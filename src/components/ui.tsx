import type { EstadoAsignacion, Instancia, Problem } from '../types'

export function InstanciaBadge({ instancia }: { instancia: Instancia }) {
  const cls = instancia === 'Intercolegial' ? 'badge--intercolegial' : 'badge--zonal'
  return <span className={`badge ${cls}`}>{instancia}</span>
}

export function NivelBadge({ nivel }: { nivel: number }) {
  return <span className="badge badge--nivel">Nivel {nivel}</span>
}

const ESTADO_TEXTO: Record<EstadoAsignacion, string> = {
  pending: 'Pendiente',
  completed: 'Completado',
  expired: 'Vencido',
}

export function EstadoBadge({ estado }: { estado: EstadoAsignacion }) {
  return <span className={`badge badge--${estado}`}>{ESTADO_TEXTO[estado]}</span>
}

export function ProgressBar({ porcentaje }: { porcentaje: number }) {
  return (
    <div className="progress-bar" role="progressbar" aria-valuenow={porcentaje} aria-valuemin={0} aria-valuemax={100}>
      <div className="progress-bar__fill" style={{ width: `${porcentaje}%` }} />
    </div>
  )
}

export function ProblemCard({
  problem,
  orden,
  done,
  onToggle,
}: {
  problem: Problem
  orden?: number
  /** Si está definido, el problema se muestra como completado/no. */
  done?: boolean
  /** Si está definido, muestra el botón para marcar/desmarcar el problema. */
  onToggle?: () => void
}) {
  return (
    <article className={`problem ${done ? 'problem--done' : ''}`}>
      <header className="problem__head">
        <div className="problem__num">{done ? '✓' : orden ?? problem.numero}</div>
        <div className="problem__headtext">
          <div className="problem__label">Problema {problem.numero}</div>
          <div className="problem__meta">
            {problem.instancia} · {problem.anio} · Nivel {problem.nivel}
          </div>
        </div>
        {onToggle && (
          <button
            type="button"
            className={`problem__check ${done ? 'problem__check--on' : ''}`}
            onClick={onToggle}
            aria-pressed={done}
          >
            {done ? '✓ Hecho' : 'Marcar'}
          </button>
        )}
      </header>
      <div className="problem__body">{problem.enunciado}</div>
      <footer className="problem__foot">
        {problem.muestra && <span className="muestra-flag">Problema de muestra · </span>}
        Fuente: {problem.fuente || '—'}
      </footer>
    </article>
  )
}
