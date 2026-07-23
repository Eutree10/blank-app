import { useMemo, useRef, useState } from 'react'
import { useStore } from '../store/useStore'
import { validarDataset } from '../lib/storage'

type Msg = { tipo: 'info' | 'ok' | 'error'; texto: string } | null

export function Datos() {
  const { state, importarDataset, resetProgreso, resetTotal } = useStore()
  const [texto, setTexto] = useState('')
  const [msg, setMsg] = useState<Msg>(null)
  const [advertencias, setAdvertencias] = useState<string[]>([])
  const fileRef = useRef<HTMLInputElement>(null)

  const resumen = useMemo(() => {
    const n2 = state.problems.filter((p) => p.nivel === 2)
    const muestra = n2.filter((p) => p.muestra).length
    const inter = n2.filter((p) => p.instancia === 'Intercolegial').length
    const zonal = n2.filter((p) => p.instancia === 'Zonal').length
    const anios = [...new Set(n2.map((p) => p.anio))].sort()
    return { total: n2.length, muestra, inter, zonal, anios }
  }, [state.problems])

  function cargarDesdeTexto(raw: string) {
    setAdvertencias([])
    let parsed: unknown
    try {
      parsed = JSON.parse(raw)
    } catch {
      setMsg({ tipo: 'error', texto: 'El texto no es JSON válido.' })
      return
    }
    const res = validarDataset(parsed)
    if (!res.ok) {
      setMsg({ tipo: 'error', texto: `No se pudo cargar: ${res.errores.slice(0, 3).join(' ')}` })
      setAdvertencias(res.errores)
      return
    }
    importarDataset(res.problems)
    setAdvertencias(res.advertencias)
    setMsg({
      tipo: 'ok',
      texto: `Se cargaron ${res.problems.length} problemas. Tu historial de completados se conservó por id.`,
    })
    setTexto('')
  }

  function onFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = () => cargarDesdeTexto(String(reader.result))
    reader.readAsText(file)
    e.target.value = ''
  }

  function descargar(nombre: string, contenido: string) {
    const blob = new Blob([contenido], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = nombre
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div>
      <div className="page-head">
        <h1>Datos</h1>
        <p>Cargá los enunciados oficiales de OMA o hacé una copia de tu progreso.</p>
      </div>

      <div className="card card--pad">
        <h2 style={{ fontSize: 17 }}>Dataset actual</h2>
        <div className="stat-grid mt-16">
          <div className="stat">
            <div className="stat__num">{resumen.total}</div>
            <div className="stat__label">Problemas N2</div>
          </div>
          <div className="stat">
            <div className="stat__num">{resumen.inter}</div>
            <div className="stat__label">Intercolegial</div>
          </div>
          <div className="stat">
            <div className="stat__num">{resumen.zonal}</div>
            <div className="stat__label">Zonal</div>
          </div>
          <div className="stat">
            <div className="stat__num">{resumen.anios.length}</div>
            <div className="stat__label">Años</div>
          </div>
        </div>
        {resumen.muestra > 0 && (
          <div className="notice notice--info">
            {resumen.muestra} de {resumen.total} son problemas de <strong>muestra</strong>. La
            red de este entorno bloquea oma.org.ar, así que no se pudieron descargar los
            enunciados oficiales automáticamente. Corré <span className="mono">scripts/scrape_oma.py</span>{' '}
            en una red con acceso a OMA y cargá el JSON generado acá abajo.
          </div>
        )}
        <div className="muted small mt-16">
          Años cargados: <span className="mono">{resumen.anios.join(', ') || '—'}</span>
        </div>
      </div>

      <div className="card card--pad mt-16">
        <h2 style={{ fontSize: 17 }}>Importar problemas (JSON)</h2>
        <p className="muted small">
          Pegá un array de problemas o un objeto <span className="mono">{'{ "problems": [...] }'}</span>.
          Reemplaza el dataset conservando tu historial (por id de problema).
        </p>
        <textarea
          className="json-input mt-16"
          placeholder={'[\n  {\n    "instancia": "Zonal",\n    "anio": 2020,\n    "numero": 1,\n    "nivel": 2,\n    "enunciado": "…",\n    "fuente": "https://www.oma.org.ar/enunciados/…"\n  }\n]'}
          value={texto}
          onChange={(e) => setTexto(e.target.value)}
        />
        <div className="field-row mt-16">
          <button
            className="btn btn--primary"
            onClick={() => cargarDesdeTexto(texto)}
            disabled={!texto.trim()}
          >
            Validar y cargar
          </button>
          <button className="btn btn--ghost" onClick={() => fileRef.current?.click()}>
            Subir archivo .json
          </button>
          <input ref={fileRef} type="file" accept="application/json,.json" hidden onChange={onFile} />
        </div>
        {msg && <div className={`notice notice--${msg.tipo}`}>{msg.texto}</div>}
        {advertencias.length > 0 && (
          <div className="notice notice--info">
            <strong>Detalles:</strong>
            <ul style={{ margin: '6px 0 0', paddingLeft: 18 }}>
              {advertencias.slice(0, 8).map((a, i) => (
                <li key={i} className="small">
                  {a}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      <div className="card card--pad mt-16">
        <h2 style={{ fontSize: 17 }}>Copias de seguridad</h2>
        <div className="field-row mt-16">
          <button
            className="btn btn--ghost"
            onClick={() =>
              descargar('oma-dataset.json', JSON.stringify(state.problems, null, 2))
            }
          >
            Exportar dataset
          </button>
          <button
            className="btn btn--ghost"
            onClick={() => descargar('oma-backup.json', JSON.stringify(state, null, 2))}
          >
            Exportar todo (con progreso)
          </button>
        </div>
      </div>

      <div className="card card--pad mt-16">
        <h2 style={{ fontSize: 17, color: 'var(--danger)' }}>Zona de riesgo</h2>
        <p className="muted small">
          Estas acciones no se pueden deshacer.
        </p>
        <div className="field-row mt-16">
          <button
            className="btn btn--danger"
            onClick={() => {
              if (confirm('¿Borrar todo tu progreso (completados y asignaciones)? El dataset se mantiene.')) {
                resetProgreso()
                setMsg({ tipo: 'ok', texto: 'Progreso reiniciado.' })
              }
            }}
          >
            Reiniciar progreso
          </button>
          <button
            className="btn btn--danger"
            onClick={() => {
              if (confirm('¿Reset total? Vuelve al dataset de muestra y borra el progreso.')) {
                resetTotal()
                setMsg({ tipo: 'ok', texto: 'Reset total realizado.' })
              }
            }}
          >
            Reset de fábrica
          </button>
        </div>
      </div>
    </div>
  )
}
