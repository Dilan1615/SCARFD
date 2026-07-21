import { Search } from 'lucide-react'

const SERVICIOS = [
  { valor: '', etiqueta: 'Todos los servicios' },
  { valor: 'usuario', etiqueta: 'Usuario' },
  { valor: 'academico', etiqueta: 'Académico' },
  { valor: 'asistencia', etiqueta: 'Asistencia' },
  { valor: 'reportes', etiqueta: 'Reportes' },
]

const ACCIONES = [
  { valor: '', etiqueta: 'Todas las acciones' },
  { valor: 'CREATE', etiqueta: 'Creación' },
  { valor: 'UPDATE', etiqueta: 'Actualización' },
  { valor: 'DELETE', etiqueta: 'Eliminación' },
]

const clasesInput =
  'rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-700 focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-400'

/**
 * @param {{ filtros: object, onChange: (filtros: object) => void }} props
 */
export default function ActivityLogFilters({ filtros, onChange }) {
  const actualizar = (campo, valor) => onChange({ ...filtros, [campo]: valor, page: 1 })

  return (
    <div className="flex flex-wrap items-center gap-2">
      <div className="relative">
        <Search className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-400" />
        <input
          type="text"
          placeholder="Buscar en descripción…"
          value={filtros.buscar || ''}
          onChange={(e) => actualizar('buscar', e.target.value)}
          className={`${clasesInput} w-56 pl-8`}
        />
      </div>

      <select
        value={filtros.servicio || ''}
        onChange={(e) => actualizar('servicio', e.target.value)}
        className={clasesInput}
      >
        {SERVICIOS.map((s) => (
          <option key={s.valor} value={s.valor}>{s.etiqueta}</option>
        ))}
      </select>

      <select
        value={filtros.accion || ''}
        onChange={(e) => actualizar('accion', e.target.value)}
        className={clasesInput}
      >
        {ACCIONES.map((a) => (
          <option key={a.valor} value={a.valor}>{a.etiqueta}</option>
        ))}
      </select>

      <input
        type="text"
        placeholder="Usuario…"
        value={filtros.usuario || ''}
        onChange={(e) => actualizar('usuario', e.target.value)}
        className={`${clasesInput} w-36`}
      />

      <input
        type="date"
        value={filtros.fecha_desde ? filtros.fecha_desde.slice(0, 10) : ''}
        onChange={(e) => actualizar('fecha_desde', e.target.value ? `${e.target.value}T00:00:00` : '')}
        className={clasesInput}
      />
      <span className="text-xs text-slate-400">a</span>
      <input
        type="date"
        value={filtros.fecha_hasta ? filtros.fecha_hasta.slice(0, 10) : ''}
        onChange={(e) => actualizar('fecha_hasta', e.target.value ? `${e.target.value}T23:59:59` : '')}
        className={clasesInput}
      />
    </div>
  )
}
