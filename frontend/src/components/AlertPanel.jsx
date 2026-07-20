import { AlertTriangle, ShieldAlert, Info } from 'lucide-react'

const ICONOS = {
  critica: ShieldAlert,
  advertencia: AlertTriangle,
  info: Info,
}

const ESTILOS = {
  critica: 'border-red-200 bg-red-50 text-red-700',
  advertencia: 'border-amber-200 bg-amber-50 text-amber-700',
  info: 'border-blue-200 bg-blue-50 text-blue-700',
}

/**
 * @param {{ alertas: { nivel: 'critica'|'advertencia'|'info', mensaje: string }[] }} props
 */
export default function AlertPanel({ alertas = [] }) {
  if (alertas.length === 0) {
    return (
      <div className="flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-700">
        <Info className="h-4 w-4 shrink-0" />
        Todo funciona con normalidad. No hay alertas activas.
      </div>
    )
  }

  return (
    <div className="space-y-2">
      {alertas.map((alerta, i) => {
        const Icono = ICONOS[alerta.nivel] || Info
        return (
          <div
            key={i}
            className={`flex items-start gap-2 rounded-xl border p-3 text-sm ${ESTILOS[alerta.nivel] || ESTILOS.info}`}
          >
            <Icono className="mt-0.5 h-4 w-4 shrink-0" />
            <span>{alerta.mensaje}</span>
          </div>
        )
      })}
    </div>
  )
}

// Contenedores cuyo estado "detenido" es normal y esperado (no son un
// problema real, por eso se excluyen de las alertas de infraestructura).
const CONTENEDORES_EFIMEROS = ['sacarf_init']

/**
 * Genera la lista de alertas a partir de la respuesta cruda del backend
 * de monitoreo. Se usa desde DashboardMonitoring.jsx.
 */
export function generarAlertas({ servicios = [], infraestructura, backend }) {
  const alertas = []

  servicios.forEach((s) => {
    if (s.estado === 'caido') {
      alertas.push({ nivel: 'critica', mensaje: `El servicio "${s.servicio}" no responde.` })
    }
  })

  if (infraestructura) {
    if (infraestructura.cpu_percent >= 90) {
      alertas.push({ nivel: 'critica', mensaje: `CPU al ${infraestructura.cpu_percent}%.` })
    } else if (infraestructura.cpu_percent >= 75) {
      alertas.push({ nivel: 'advertencia', mensaje: `CPU elevada: ${infraestructura.cpu_percent}%.` })
    }

    if (infraestructura.ram_percent >= 90) {
      alertas.push({ nivel: 'critica', mensaje: `Uso de RAM al ${infraestructura.ram_percent}%.` })
    } else if (infraestructura.ram_percent >= 80) {
      alertas.push({ nivel: 'advertencia', mensaje: `Uso de RAM elevado: ${infraestructura.ram_percent}%.` })
    }

    if (infraestructura.disco_percent >= 90) {
      alertas.push({ nivel: 'critica', mensaje: `Disco al ${infraestructura.disco_percent}%.` })
    }

    infraestructura.contenedores
      ?.filter((c) => c.estado === 'detenido' && !CONTENEDORES_EFIMEROS.includes(c.nombre))
      .forEach((c) => alertas.push({ nivel: 'advertencia', mensaje: `Contenedor "${c.nombre}" detenido.` }))
  }

  if (backend?.errores_5xx_por_minuto > 0) {
    alertas.push({
      nivel: 'critica',
      mensaje: `${backend.errores_5xx_por_minuto} errores 5xx/min en el backend.`,
    })
  }

  return alertas
}