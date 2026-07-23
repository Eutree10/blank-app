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

export function ProblemCard({ problem, orden }: { problem: Problem; orden?: number }) {
  return (
    <article className="problem">
      <header className="problem__head">
        <div className="problem__num">{orden ?? problem.numero}</div>
        <div>
          <div className="problem__label">Problema {problem.numero}</div>
          <div className="problem__meta">
            {problem.instancia} · {problem.anio} · Nivel {problem.nivel}
          </div>
        </div>
      </header>
      <div className="problem__body">{problem.enunciado}</div>
      <footer className="problem__foot">
        {problem.muestra && <span className="muestra-flag">Problema de muestra · </span>}
        Fuente: {problem.fuente || '—'}
      </footer>
    </article>
  )
}
