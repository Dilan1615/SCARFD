import { CheckCircle2, XCircle, Clock } from 'lucide-react'

const NOMBRES_VISIBLES = {
  usuario: 'Usuario',
  academico: 'Académico',
  asistencia: 'Asistencia',
  reportes: 'Reportes',
}

/**
 * Tarjeta de estado de un microservicio SACARF.
 * @param {{ servicio: string, estado: 'activo'|'caido', tiempo_respuesta_ms: number, puerto: number }} props
 */
export default function ServiceStatusCard({ servicio, estado, tiempo_respuesta_ms, puerto }) {
  const activo = estado === 'activo'

  return (
    <div
      className={`rounded-xl border bg-white p-4 shadow-sm transition-colors ${
        activo ? 'border-slate-200' : 'border-red-200 bg-red-50'
      }`}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-slate-500">
            {NOMBRES_VISIBLES[servicio] || servicio}
          </p>
          <p className="mt-0.5 text-xs text-slate-400">puerto :{puerto}</p>
        </div>
        {activo ? (
          <CheckCircle2 className="h-5 w-5 shrink-0 text-emerald-500" />
        ) : (
          <XCircle className="h-5 w-5 shrink-0 text-red-500" />
        )}
      </div>

      <div className="mt-4 flex items-center justify-between">
        <span
          className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${
            activo ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'
          }`}
        >
          {activo ? 'Activo' : 'Caído'}
        </span>

        <div className="flex items-center gap-1 text-xs text-slate-500">
          <Clock className="h-3.5 w-3.5" />
          {activo ? `${tiempo_respuesta_ms} ms` : '—'}
        </div>
      </div>
    </div>
  )
}
