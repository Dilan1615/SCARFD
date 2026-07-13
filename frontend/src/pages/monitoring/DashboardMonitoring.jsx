import { useCallback, useEffect, useRef, useState } from 'react'
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
} from 'lucide-react'

import monitoringService from '../../services/monitoringService'
import ServiceStatusCard from '../../components/ServiceStatusCard'
import MetricCard from '../../components/MetricCard'
import LineChart from '../../components/LineChart'
import BarChartComp from '../../components/BarChart'
import AlertPanel, { generarAlertas } from '../../components/AlertPanel'
import MaintenanceBanner from '../../components/MaintenanceBanner'

const INTERVALO_REFRESCO_MS = 15000

export default function DashboardMonitoring() {
  const [datos, setDatos] = useState(null)
  const [cargando, setCargando] = useState(true)
  const [monitoringDown, setMonitoringDown] = useState(false)
  const [ultimaActualizacion, setUltimaActualizacion] = useState(null)
  const intervaloRef = useRef(null)

  const cargarDatos = useCallback(async () => {
    try {
      const resumen = await monitoringService.getResumen()
      setDatos(resumen)
      setMonitoringDown(false)
      setUltimaActualizacion(new Date())
    } catch (err) {
      // Mismo patrón que el resto del proyecto: 5xx o error de red -> banner
      if (!err.response || err.response.status >= 500) {
        setMonitoringDown(true)
      }
    } finally {
      setCargando(false)
    }
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
    return <MaintenanceBanner servicio="monitoreo" />
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
    </div>
  )
}
