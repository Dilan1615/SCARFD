import { useState, useEffect } from 'react'
import api from '../../api/axios'
import DataTable from '../../components/DataTable'
import { CalendarCheck } from 'lucide-react'

const estadoColors = {
  PRESENTE: 'bg-green-100 text-green-700',
  AUSENTE: 'bg-red-100 text-red-700',
  TARDE: 'bg-amber-100 text-amber-700',
  JUSTIFICADO: 'bg-blue-100 text-blue-700',
}

const columns = [
  { key: 'estudiante_nombre', label: 'Estudiante' },
  { key: 'fecha', label: 'Fecha' },
  { key: 'hora_registro', label: 'Hora' },
  { key: 'estado_display', label: 'Estado', render: (v, r) => (
    <span className={`px-2.5 py-1 text-xs font-semibold rounded-full ${estadoColors[r.estado] || 'bg-gray-100 text-gray-700'}`}>{v}</span>
  )},
  { key: 'confianza', label: 'Confianza', render: (v) => {
    const pct = v?.toFixed(1) || '0.0'
    const color = Number(pct) >= 80 ? 'text-green-600' : Number(pct) >= 60 ? 'text-amber-600' : 'text-red-600'
    return <span className={`font-medium ${color}`}>{pct}%</span>
  }},
  { key: 'horario_info', label: 'Materia', render: (v) => v?.materia || '-' },
  { key: 'horario_info', label: 'Aula', render: (v) => v?.aula || '-' },
]

export default function AsistenciaList() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)

  const load = () => {
    setLoading(true)
    api.get('/asistencia/asistencias/').then(({ data: res }) => setData(res.results || res)).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-4">
        <div className="w-10 h-10 rounded-2xl bg-unl-red/10 flex items-center justify-center">
          <CalendarCheck size={20} className="text-unl-red" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-unl-black">Registro de Asistencia</h2>
          <p className="text-sm text-gray-500">Consultar asistencias registradas con reconocimiento facial</p>
        </div>
      </div>
      <DataTable title="Asistencias" columns={columns} data={data} loading={loading} />
    </div>
  )
}
