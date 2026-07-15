import { useState } from 'react'
import { ChevronDown, ChevronRight, Plus, Pencil, Trash2 } from 'lucide-react'

const ICONO_ACCION = {
  CREATE: { Icono: Plus, clase: 'bg-emerald-100 text-emerald-700' },
  UPDATE: { Icono: Pencil, clase: 'bg-amber-100 text-amber-700' },
  DELETE: { Icono: Trash2, clase: 'bg-red-100 text-red-700' },
}

const NOMBRES_SERVICIO = {
  usuario: 'Usuario',
  academico: 'Académico',
  asistencia: 'Asistencia',
  reportes: 'Reportes',
}

function formatearFecha(iso) {
  const d = new Date(iso)
  return d.toLocaleString('es-EC', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

function FilaLog({ log }) {
  const [expandido, setExpandido] = useState(false)
  const { Icono, clase } = ICONO_ACCION[log.accion] || ICONO_ACCION.UPDATE
  const tieneDatos = log.datos_modificados && Object.keys(log.datos_modificados).length > 0

  return (
    <>
      <tr
        className={`border-b border-slate-100 text-sm ${tieneDatos ? 'cursor-pointer hover:bg-slate-50' : ''}`}
        onClick={() => tieneDatos && setExpandido((v) => !v)}
      >
        <td className="w-6 px-2 py-2.5 text-slate-400">
          {tieneDatos ? (
            expandido ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />
          ) : null}
        </td>
        <td className="px-3 py-2.5 font-medium text-slate-700">{log.usuario_nombre}</td>
        <td className="px-3 py-2.5">
          <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-semibold ${clase}`}>
            <Icono className="h-3 w-3" />
            {log.accion}
          </span>
        </td>
        <td className="px-3 py-2.5 text-slate-500">{NOMBRES_SERVICIO[log.servicio] || log.servicio}</td>
        <td className="px-3 py-2.5 text-slate-500">{log.modelo}</td>
        <td className="px-3 py-2.5 text-slate-700">{log.descripcion}</td>
        <td className="whitespace-nowrap px-3 py-2.5 text-right text-xs text-slate-400">
          {formatearFecha(log.fecha_hora)}
        </td>
      </tr>
      {expandido && tieneDatos && (
        <tr className="bg-slate-50">
          <td />
          <td colSpan={6} className="px-3 pb-3 pt-1">
            <pre className="overflow-x-auto rounded-lg bg-slate-900 p-3 text-xs text-slate-100">
              {JSON.stringify(log.datos_modificados, null, 2)}
            </pre>
          </td>
        </tr>
      )}
    </>
  )
}

/**
 * Tabla de logs de auditoría. Muestra: usuario, acción, servicio, modelo,
 * descripción y fecha. Filas con `datos_modificados` son expandibles.
 * @param {{ logs: object[], compacto?: boolean }} props
 */
export default function ActivityLogTable({ logs = [], compacto = false }) {
  if (logs.length === 0) {
    return (
      <div className="flex h-32 items-center justify-center text-sm text-slate-400">
        No hay actividad registrada todavía.
      </div>
    )
  }

  return (
    <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <table className="w-full">
        <thead>
          <tr className="border-b border-slate-200 bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-400">
            <th className="w-6 px-2 py-2.5" />
            <th className="px-3 py-2.5">Usuario</th>
            <th className="px-3 py-2.5">Acción</th>
            <th className="px-3 py-2.5">Servicio</th>
            <th className="px-3 py-2.5">Modelo</th>
            <th className="px-3 py-2.5">Descripción</th>
            <th className="px-3 py-2.5 text-right">Fecha</th>
          </tr>
        </thead>
        <tbody>
          {(compacto ? logs.slice(0, 5) : logs).map((log) => (
            <FilaLog key={log.id} log={log} />
          ))}
        </tbody>
      </table>
    </div>
  )
}
