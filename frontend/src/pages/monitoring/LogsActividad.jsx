import { useEffect, useState } from 'react'
import { AlertTriangle, ChevronLeft, ChevronRight, RefreshCw } from 'lucide-react'

import monitoringService from '../../services/monitoringService'
import ActivityLogTable from '../../components/ActivityLogTable'
import ActivityLogFilters from '../../components/ActivityLogFilters'
import MaintenanceBanner from '../../components/MaintenanceBanner'

export default function LogsActividad() {
  const [filtros, setFiltros] = useState({ page: 1, page_size: 20 })
  const [resultado, setResultado] = useState({ count: 0, results: [] })
  const [cargando, setCargando] = useState(true)
  const [monitoringDown, setMonitoringDown] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelado = false
    setCargando(true)
    setError(null)
    monitoringService
      .getAuditoria(filtros)
      .then((data) => {
        if (!cancelado) {
          setResultado(data)
          setMonitoringDown(false)
        }
      })
      .catch((err) => {
        if (cancelado) return
        // Antes este catch solo distinguía "red/5xx -> banner de
        // mantenimiento" y para cualquier otro error (403, 404...) no
        // hacía nada: la tabla se quedaba en su estado inicial vacío
        // ({count: 0, results: []}) sin ningún aviso de que algo falló.
        console.error('Error al cargar /api/monitoring/auditoria/:', err?.response?.status, err?.response?.data || err)
        if (!err.response || err.response.status >= 500) {
          setMonitoringDown(true)
        } else {
          setError(
            `No se pudieron cargar los logs (HTTP ${err.response.status}). ` +
            (err.response.status === 403
              ? 'Verifica los permisos del usuario actual.'
              : 'Revisa la consola del navegador para más detalle.')
          )
        }
      })
      .finally(() => !cancelado && setCargando(false))
    return () => {
      cancelado = true
    }
  }, [filtros])

  if (monitoringDown) {
    return <MaintenanceBanner service="monitoreo" />
  }

  const totalPaginas = Math.max(1, Math.ceil(resultado.count / (filtros.page_size || 20)))

  return (
    <div className="space-y-4 p-6">
      <header>
        <h1 className="text-xl font-semibold text-slate-900">Logs de actividad del sistema</h1>
        <p className="text-sm text-slate-500">
          Historial de acciones CRUD realizadas por los usuarios en todos los microservicios
        </p>
      </header>

      <div className="flex items-center justify-between gap-4">
        <ActivityLogFilters filtros={filtros} onChange={setFiltros} />
        <span className="shrink-0 text-xs text-slate-400">
          {resultado.count} {resultado.count === 1 ? 'registro' : 'registros'}
        </span>
      </div>

      {cargando ? (
        <div className="flex h-40 items-center justify-center text-slate-400">
          <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
          Cargando logs…
        </div>
      ) : error ? (
        <div className="flex items-center gap-2 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          {error}
        </div>
      ) : (
        <>
          <ActivityLogTable logs={resultado.results} />

          <div className="flex items-center justify-between pt-2">
            <button
              disabled={filtros.page <= 1}
              onClick={() => setFiltros((f) => ({ ...f, page: f.page - 1 }))}
              className="flex items-center gap-1 rounded-lg border border-slate-200 px-3 py-1.5 text-sm text-slate-600 disabled:opacity-40 hover:bg-slate-50"
            >
              <ChevronLeft className="h-4 w-4" />
              Anterior
            </button>
            <span className="text-xs text-slate-400">
              Página {filtros.page} de {totalPaginas}
            </span>
            <button
              disabled={filtros.page >= totalPaginas}
              onClick={() => setFiltros((f) => ({ ...f, page: f.page + 1 }))}
              className="flex items-center gap-1 rounded-lg border border-slate-200 px-3 py-1.5 text-sm text-slate-600 disabled:opacity-40 hover:bg-slate-50"
            >
              Siguiente
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </>
      )}
    </div>
  )
}
