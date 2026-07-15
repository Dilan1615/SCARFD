import { WifiOff } from 'lucide-react'

const SERVICE_ICONS = {
  academico: 'Académico',
  usuario: 'Usuarios',
  asistencia: 'Asistencia',
  monitoreo: 'Monitoreo',
  reportes: 'Reportes',
}

export default function MaintenanceBanner({ service }) {
  const label = SERVICE_ICONS[service] || service
  return (
    <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4 mb-5 shadow-sm">
      <div className="flex items-center gap-2.5">
        <WifiOff size={18} className="text-amber-600 shrink-0" />
        <p className="text-sm font-semibold text-amber-800">
          Servicio de <span className="uppercase">{label}</span> en mantenimiento
        </p>
      </div>
    </div>
  )
}
