import { useCallback, useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Cpu,
  MemoryStick,
  HardDrive,
  Activity,
  Timer,
  AlertOctagon,
  Server,
  Database,
  Users,
  UserCheck,
  ScanFace,
  FileBarChart,
  RefreshCw,
  ArrowRight,
  AlertTriangle,
} from 'lucide-react'

import monitoringService from '../../services/monitoringService'
import ServiceStatusCard from '../../components/ServiceStatusCard'
import MetricCard from '../../components/MetricCard'
import LineChart from '../../components/LineChart'
import BarChartComp from '../../components/BarChart'
import AlertPanel, { generarAlertas } from '../../components/AlertPanel'
import ActivityLogTable from '../../components/ActivityLogTable'
import MaintenanceBanner from '../../components/MaintenanceBanner'

const INTERVALO_REFRESCO_MS = 15000

export default function DashboardMonitoring() {
  const [datos, setDatos] = useState(null)
  const [logsRecientes, setLogsRecientes] = useState([])
  const [errorLogs, setErrorLogs] = useState(null)
  const [cargando, setCargando] = useState(true)
  const [monitoringDown, setMonitoringDown] = useState(false)
  const [ultimaActualizacion, setUltimaActualizacion] = useState(null)
  const intervaloRef = useRef(null)

  const cargarDatos = useCallback(async () => {
    // ── IMPORTANTE ────────────────────────────────────────────────────
    // Antes esto iba en un único Promise.all([getResumen(), getAuditoria()]):
    // si CUALQUIERA de las dos fallaba, la promesa combinada rechazaba
    // completa y setDatos(resumen) nunca se llamaba, aunque el resumen
    // general sí hubiera respondido bien. Un 4xx en /auditoria/ (no
    // capturado por el chequeo "!err.response || status >= 500") dejaba
    // todo el dashboard en blanco sin ningún indicio en pantalla.
    //
    // Ahora cada fetch se resuelve de forma independiente: un fallo en
    // logs de auditoría no debe tumbar el resto del dashboard, y viceversa.
    const resultados = await Promise.allSettled([
      monitoringService.getResumen(),
      monitoringService.getAuditoria({ page: 1, page_size: 5 }),
    ])
    const [resResumen, resLogs] = resultados

    if (resResumen.status === 'fulfilled') {
      setDatos(resResumen.value)
      setMonitoringDown(false)
      setUltimaActualizacion(new Date())
    } else {
      const err = resResumen.reason
      console.error('Error al cargar el resumen de monitoreo:', err?.response?.status, err?.response?.data || err)
      if (!err?.response || err.response.status >= 500) {
        setMonitoringDown(true)
      }
    }

    if (resLogs.status === 'fulfilled') {
      setLogsRecientes(resLogs.value.results || [])
      setErrorLogs(null)
    } else {
      const err = resLogs.reason
      console.error('Error al cargar logs de auditoría:', err?.response?.status, err?.response?.data || err)
      setErrorLogs(
        err?.response
          ? `No se pudieron cargar los logs (HTTP ${err.response.status}).`
          : 'No se pudieron cargar los logs: error de red.'
      )
    }

    setCargando(false)
  }, [])

  useEffect(() => {
    cargarDatos()
    intervaloRef.current = setInterval(cargarDatos, INTERVALO_REFRESCO_MS)
    return () => clearInterval(intervaloRef.current)
  }, [cargarDatos])

  if (cargando) {
    return (
      <div className="flex h-64 items-center justify-center text-slate-400">
        <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
        Cargando panel de monitoreo…
      </div>
    )
  }

  if (monitoringDown) {
    // Antes: <MaintenanceBanner servicio="monitoreo" /> — el componente
    // espera la prop `service`, no `servicio`; con el nombre equivocado
    // el banner mostraba "undefined" en vez de "MONITOREO".
    return <MaintenanceBanner service="monitoreo" />
  }

  const { servicios = [], infraestructura, backend, base_datos: baseDatos, negocio } = datos || {}
  const alertas = generarAlertas({ servicios, infraestructura, backend })

  return (
    <div className="space-y-8 p-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Monitoreo del sistema</h1>
          <p className="text-sm text-slate-500">
            SACARF — estado en tiempo real de servicios, infraestructura y negocio
          </p>
        </div>
        {ultimaActualizacion && (
          <span className="flex items-center gap-1.5 text-xs text-slate-400">
            <RefreshCw className="h-3.5 w-3.5" />
            Actualizado {ultimaActualizacion.toLocaleTimeString('es-EC')}
          </span>
        )}
      </header>

      <AlertPanel alertas={alertas} />

      {/* ── Estado del sistema ─────────────────────────────────────── */}
      <section>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-400">
          Estado del sistema
        </h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {servicios.map((s) => (
            <ServiceStatusCard key={s.servicio} {...s} />
          ))}
        </div>
      </section>

      {/* ── Infraestructura ────────────────────────────────────────── */}
      <section>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-400">
          Infraestructura
        </h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <MetricCard
            titulo="Uso de CPU"
            valor={infraestructura?.cpu_percent}
            unidad="%"
            icono={Cpu}
            barra
            umbralAdvertencia={75}
            umbralCritico={90}
          />
          <MetricCard
            titulo="Uso de RAM"
            valor={infraestructura?.ram_percent}
            unidad="%"
            icono={MemoryStick}
            barra
            umbralAdvertencia={80}
            umbralCritico={90}
          />
          <MetricCard
            titulo="Uso de disco"
            valor={infraestructura?.disco_percent}
            unidad="%"
            icono={HardDrive}
            barra
            umbralAdvertencia={80}
            umbralCritico={90}
          />
          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium text-slate-500">Contenedores Docker</p>
              <Server className="h-4 w-4 text-slate-400" />
            </div>
            <ul className="mt-3 max-h-28 space-y-1 overflow-y-auto pr-1 text-xs">
              {infraestructura?.contenedores?.map((c) => (
                <li key={c.nombre} className="flex items-center justify-between">
                  <span className="text-slate-600">{c.nombre.replace('sacarf_', '')}</span>
                  <span
                    className={
                      c.estado === 'corriendo'
                        ? 'font-medium text-emerald-600'
                        : 'font-medium text-red-500'
                    }
                  >
                    {c.estado}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      {/* ── Backend ─────────────────────────────────────────────────── */}
      <section>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-400">
          Backend
        </h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <MetricCard
            titulo="Peticiones/min"
            valor={backend?.peticiones_por_minuto}
            icono={Activity}
          />
          <MetricCard
            titulo="Tiempo prom. de respuesta"
            valor={backend?.tiempo_promedio_respuesta_ms}
            unidad="ms"
            icono={Timer}
          />
          <MetricCard
            titulo="Errores 4xx/min"
            valor={backend?.errores_4xx_por_minuto}
            icono={AlertOctagon}
          />
          <MetricCard
            titulo="Errores 5xx/min"
            valor={backend?.errores_5xx_por_minuto}
            icono={AlertOctagon}
          />
        </div>
        <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
          <LineChart
            titulo="Peticiones por minuto (últimos 30 min)"
            datos={backend?.serie_peticiones_por_minuto}
            color="#3b82f6"
          />
          <LineChart
            titulo="Tiempo de respuesta (últimos 30 min)"
            datos={backend?.serie_tiempo_respuesta_ms}
            color="#8b5cf6"
            unidad=" ms"
          />
        </div>
        <div className="mt-4">
          <BarChartComp
            titulo="Peticiones por microservicio (peticiones/min)"
            datos={backend?.peticiones_por_microservicio}
          />
        </div>
      </section>

      {/* ── Base de datos ───────────────────────────────────────────── */}
      <section>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-400">
          Base de datos
        </h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <MetricCard
            titulo="Conexiones activas"
            valor={baseDatos?.conexiones_activas}
            icono={Database}
          />
          <MetricCard
            titulo="Consultas/seg"
            valor={baseDatos?.consultas_por_segundo}
            icono={Activity}
          />
          <MetricCard
            titulo="Almacenamiento"
            valor={baseDatos?.almacenamiento_mb}
            unidad="MB"
            icono={HardDrive}
          />
        </div>
      </section>

      {/* ── Métricas de negocio SACARF ─────────────────────────────── */}
      <section>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-400">
          Negocio SACARF
        </h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
          <MetricCard titulo="Usuarios registrados" valor={negocio?.total_usuarios} icono={Users} />
          <MetricCard titulo="Asistencias hoy" valor={negocio?.asistencias_hoy} icono={UserCheck} />
          <MetricCard
            titulo="Reconocimientos exitosos"
            valor={negocio?.reconocimientos_exitosos_hoy}
            icono={ScanFace}
          />
          <MetricCard
            titulo="Reconocimientos fallidos"
            valor={negocio?.reconocimientos_fallidos_hoy}
            icono={ScanFace}
          />
          <MetricCard
            titulo="Reportes generados"
            valor={negocio?.reportes_generados}
            icono={FileBarChart}
          />
        </div>
      </section>

      {/* ── Logs de actividad del sistema ───────────────────────────── */}
      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
            Logs de actividad recientes
          </h2>
          <Link
            to="/monitoreo/logs"
            className="flex items-center gap-1 text-xs font-medium text-blue-600 hover:text-blue-700"
          >
            Ver todos los logs
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>

        {errorLogs ? (
          <div className="flex items-center gap-2 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            <AlertTriangle className="h-4 w-4 shrink-0" />
            {errorLogs} Revisa la consola del navegador para más detalle.
          </div>
        ) : (
          <ActivityLogTable logs={logsRecientes} compacto />
        )}
      </section>
    </div>
  )
}
