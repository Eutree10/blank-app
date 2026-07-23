// Modelo de datos central de la app de práctica OMA.

/** Instancias de OMA que maneja la app. La lógica de asignación depende de esto. */
export type Instancia = 'Intercolegial' | 'Zonal'

/** Estado de una asignación diaria. */
export type EstadoAsignacion = 'pending' | 'completed' | 'expired'

/** Un problema individual de OMA. */
export interface Problem {
  /** Identificador estable y único. Convención: `${instancia}-${anio}-N${nivel}-P${numero}`. */
  id: string
  anio: number
  instancia: Instancia
  nivel: number
  /** Número de problema dentro de la instancia/año. */
  numero: number
  /** Enunciado en texto plano (puede contener saltos de línea). */
  enunciado: string
  /** Fuente / referencia del problema (URL oficial de OMA o nota). */
  fuente: string
  /** true si es contenido de muestra que debería reemplazarse por datos oficiales. */
  muestra?: boolean
}

/** Asignación de un día concreto. Se guarda una por `dayKey`. */
export interface Assignment {
  /** Clave de día en hora local: `YYYY-MM-DD`. Corte a las 00:00. */
  dayKey: string
  /** Fecha ISO de creación de la asignación. */
  fecha: string
  instancia: Instancia
  anio: number
  nivel: number
  /** IDs de los problemas asignados ese día. */
  problemIds: string[]
  estado: EstadoAsignacion
  assignedAt: string
  completedAt?: string
}

/** Registro de completado por problema. */
export interface CompletionRecord {
  fecha_completado: string
  /** dayKey de la asignación en que se completó (para trazabilidad). */
  dayKey: string
}

/** Forma persistida en localStorage. */
export interface AppState {
  version: number
  /** Dataset de problemas disponibles. */
  problems: Problem[]
  /** Mapa problemId -> registro de completado. */
  completed: Record<string, CompletionRecord>
  /** Historial de asignaciones diarias (incluye vencidas). */
  assignments: Assignment[]
}

/** Estado derivado de un problema para la UI. */
export type EstadoProblema = 'completado' | 'asignado_hoy' | 'pendiente'
