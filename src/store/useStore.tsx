import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import type { AppState, Assignment, Problem } from '../types'
import {
  alternarProblema,
  asegurarAsignacionDeHoy,
  completarAsignacion,
} from '../lib/assignment'
import { calcularProgreso, type Progreso } from '../lib/progress'
import { dayKeyOf } from '../lib/date'
import {
  borrarEstado,
  cargarEstado,
  estadoInicial,
  guardarEstado,
} from '../lib/storage'

interface StoreValue {
  state: AppState
  /** Asignación de hoy (o null si ya no quedan problemas). */
  hoy: Assignment | null
  /** true si se completó todo el dataset. */
  finalizado: boolean
  /** Progreso general y por instancia. */
  progreso: Progreso
  /** Problemas de la asignación de hoy, resueltos a objetos. */
  problemasDeHoy: Problem[]
  /** Devuelve un problema por id. */
  getProblem: (id: string) => Problem | undefined
  /** true si el problema está marcado como completado. */
  estaCompletado: (id: string) => boolean
  /** Marca/desmarca un problema individual de la asignación de hoy. */
  alternarProblemaHoy: (id: string) => void
  /** Marca TODA la asignación de hoy como completada. */
  completarHoy: () => void
  /** Reemplaza el dataset conservando el historial de completados por id. */
  importarDataset: (problems: Problem[]) => void
  /** Borra el progreso (completados + asignaciones) manteniendo el dataset. */
  resetProgreso: () => void
  /** Reset de fábrica completo (vuelve al dataset de muestra). */
  resetTotal: () => void
}

const StoreContext = createContext<StoreValue | null>(null)

export function StoreProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AppState>(() => {
    const cargado = cargarEstado()
    // Asegura la asignación de hoy en el primer render.
    const res = asegurarAsignacionDeHoy(cargado)
    if (res.changed) guardarEstado(res.state)
    return res.state
  })

  // Persistir en cada cambio de estado.
  useEffect(() => {
    guardarEstado(state)
  }, [state])

  // Re-chequear la asignación al volver a la pestaña o cruzar la medianoche.
  useEffect(() => {
    function revisar() {
      setState((prev) => {
        const res = asegurarAsignacionDeHoy(prev)
        return res.changed ? res.state : prev
      })
    }
    document.addEventListener('visibilitychange', revisar)
    const iv = window.setInterval(revisar, 60_000)
    return () => {
      document.removeEventListener('visibilitychange', revisar)
      window.clearInterval(iv)
    }
  }, [])

  const todayKey = dayKeyOf()
  const hoy = useMemo(
    () => state.assignments.find((a) => a.dayKey === todayKey) ?? null,
    [state.assignments, todayKey],
  )

  const finalizado = useMemo(() => {
    const totalN2 = state.problems.filter((p) => p.nivel === 2).length
    const completadosN2 = state.problems.filter(
      (p) => p.nivel === 2 && state.completed[p.id],
    ).length
    return totalN2 > 0 && completadosN2 === totalN2
  }, [state.problems, state.completed])

  const progreso = useMemo(() => calcularProgreso(state), [state])

  const problemById = useMemo(() => {
    const m = new Map<string, Problem>()
    for (const p of state.problems) m.set(p.id, p)
    return m
  }, [state.problems])

  const getProblem = useCallback((id: string) => problemById.get(id), [problemById])

  const problemasDeHoy = useMemo(() => {
    if (!hoy) return []
    return hoy.problemIds
      .map((id) => problemById.get(id))
      .filter((p): p is Problem => Boolean(p))
  }, [hoy, problemById])

  const estaCompletado = useCallback(
    (id: string) => Boolean(state.completed[id]),
    [state.completed],
  )

  const alternarProblemaHoy = useCallback((id: string) => {
    setState((prev) => alternarProblema(prev, id, dayKeyOf()))
  }, [])

  const completarHoy = useCallback(() => {
    setState((prev) => {
      const key = dayKeyOf()
      const existe = prev.assignments.find((a) => a.dayKey === key)
      if (!existe || existe.estado === 'completed') return prev
      return completarAsignacion(prev, key)
    })
  }, [])

  const importarDataset = useCallback((problems: Problem[]) => {
    setState((prev) => {
      // Conserva completados cuyos ids sigan existiendo en el nuevo dataset.
      const nuevosIds = new Set(problems.map((p) => p.id))
      const completed = Object.fromEntries(
        Object.entries(prev.completed).filter(([id]) => nuevosIds.has(id)),
      )
      const base: AppState = {
        ...prev,
        problems,
        completed,
        // Las asignaciones viejas cuyos problemas ya no existan se descartan
        // en la práctica al no poder resolverse; se mantiene el registro.
      }
      const res = asegurarAsignacionDeHoy(base)
      return res.state
    })
  }, [])

  const resetProgreso = useCallback(() => {
    setState((prev) => {
      const base: AppState = { ...prev, completed: {}, assignments: [] }
      const res = asegurarAsignacionDeHoy(base)
      return res.state
    })
  }, [])

  const resetTotal = useCallback(() => {
    borrarEstado()
    const res = asegurarAsignacionDeHoy(estadoInicial())
    setState(res.state)
  }, [])

  const value: StoreValue = {
    state,
    hoy,
    finalizado,
    progreso,
    problemasDeHoy,
    getProblem,
    estaCompletado,
    alternarProblemaHoy,
    completarHoy,
    importarDataset,
    resetProgreso,
    resetTotal,
  }

  return <StoreContext.Provider value={value}>{children}</StoreContext.Provider>
}

export function useStore(): StoreValue {
  const ctx = useContext(StoreContext)
  if (!ctx) throw new Error('useStore debe usarse dentro de <StoreProvider>')
  return ctx
}
