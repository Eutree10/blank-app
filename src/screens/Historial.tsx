import { useMemo, useState } from 'react'
import { useStore } from '../store/useStore'
import { fechaCorta } from '../lib/date'
import type { Assignment } from '../types'
import { EstadoBadge, InstanciaBadge, NivelBadge, ProblemCard } from '../components/ui'

export function Historial() {
  const { state, getProblem } = useStore()
  const [verVencidos, setVerVencidos] = useState(false)
  const [abierta, setAbierta] = useState<Assignment | null>(null)

  const completadas = useMemo(
    () =>
      state.assignments
        .filter((a) => a.estado === 'completed')
        .sort((a, b) => (b.completedAt ?? '').localeCompare(a.completedAt ?? '')),
    [state.assignments],
  )

  const vencidas = useMemo(
    () =>
      state.assignments
        .filter((a) => a.estado === 'expired')
        .sort((a, b) => b.dayKey.localeCompare(a.dayKey)),
    [state.assignments],
  )

  return (
    <div>
      <div className="page-head">
        <h1>Historial</h1>
        <p>Problemas que ya resolviste, con la fecha en que los completaste.</p>
      </div>

      {completadas.length === 0 ? (
        <div className="empty">
          <div className="empty__icon">📚</div>
          <h2>Todavía no completaste nada</h2>
          <p>Cuando marques una asignación como completada, va a aparecer acá.</p>
        </div>
      ) : (
        <div className="card">
          {completadas.map((a) => (
            <div className="history-item" key={a.dayKey}>
              <div className="history-item__date">
                {a.completedAt ? fechaCorta(a.completedAt) : fechaCorta(a.fecha)}
              </div>
              <div className="history-item__body">
                <div className="history-item__title">
                  {a.instancia} {a.anio}
                </div>
                <div className="chip-row">
                  <InstanciaBadge instancia={a.instancia} />
                  <NivelBadge nivel={a.nivel} />
                  <span className="badge badge--nivel">
                    {a.problemIds.length} problema{a.problemIds.length === 1 ? '' : 's'}
                  </span>
                </div>
              </div>
              <button className="link-btn" onClick={() => setAbierta(a)}>
                Ver de nuevo
              </button>
            </div>
          ))}
        </div>
      )}

      {vencidas.length > 0 && (
        <div className="mt-24">
          <button className="link-btn" onClick={() => setVerVencidos((v) => !v)}>
            {verVencidos ? 'Ocultar' : 'Ver'} no completados ({vencidas.length})
          </button>
          {verVencidos && (
            <div className="card mt-16">
              {vencidas.map((a) => (
                <div className="history-item" key={a.dayKey}>
                  <div className="history-item__date">{fechaCorta(a.fecha)}</div>
                  <div className="history-item__body">
                    <div className="history-item__title">
                      {a.instancia} {a.anio}
                    </div>
                    <div className="chip-row">
                      <EstadoBadge estado="expired" />
                      <span className="muted small">
                        Quedó sin completar — sus problemas volvieron al pool.
                      </span>
                    </div>
                  </div>
                  <button className="link-btn" onClick={() => setAbierta(a)}>
                    Ver
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {abierta && (
        <div className="modal-backdrop" onClick={() => setAbierta(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal__head">
              <strong>
                {abierta.instancia} {abierta.anio} · Nivel {abierta.nivel}
              </strong>
              <button className="modal__close" onClick={() => setAbierta(null)} aria-label="Cerrar">
                ×
              </button>
            </div>
            <div style={{ padding: 18 }}>
              {abierta.problemIds.map((id, i) => {
                const p = getProblem(id)
                return p ? (
                  <ProblemCard key={id} problem={p} orden={i + 1} />
                ) : (
                  <div key={id} className="muted small">
                    (Problema {id} ya no está en el dataset actual.)
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
