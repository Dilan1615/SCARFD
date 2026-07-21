import { useState, useEffect } from 'react'
import api from '../../api/axios'
import DataTable from '../../components/DataTable'
import FormModal from '../../components/FormModal'
import MaintenanceBanner from '../../components/MaintenanceBanner'
import { useAuth } from '../../contexts/AuthContext'
import { useToast } from '../../contexts/ToastContext'
import { CalendarCheck, FileCheck2 } from 'lucide-react'

const estadoColors = {
  PRESENTE: 'bg-green-100 text-green-700',
  AUSENTE: 'bg-red-100 text-red-700',
  TARDE: 'bg-amber-100 text-amber-700',
  JUSTIFICADO: 'bg-blue-100 text-blue-700',
}

export default function AsistenciaList() {
  const { user } = useAuth()
  const { addToast } = useToast()
  const isEstudiante = user?.rol === 'ESTUDIANTE'

  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)
  const [serviceDown, setServiceDown] = useState(false)
  const [justificando, setJustificando] = useState(null)
  const [saving, setSaving] = useState(false)

  const load = () => {
    setLoading(true)
    setServiceDown(false)
    api.get('/asistencia/asistencias/').then(({ data: res }) => setData(res.results || res)).catch((err) => {
      if (!err.response || err.response.status >= 500) setServiceDown(true)
    }).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const handleJustificar = async (form) => {
    setSaving(true)
    try {
      const formData = new FormData()
      formData.append('asistencia', justificando.id)
      formData.append('motivo', form.motivo)
      if (form.documento) {
        formData.append('documento', form.documento)
      }
      await api.post('/asistencia/justificaciones/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      addToast('Comprobante enviado, a la espera de validación', 'success')
      setJustificando(null)
      load()
    } catch (err) {
      addToast(err.response?.data?.error || Object.values(err.response?.data || {})[0]?.[0] || 'No se pudo enviar el comprobante', 'error')
    } finally {
      setSaving(false)
    }
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
    ...(isEstudiante ? [{
      key: 'id', label: 'Justificación', render: (_, r) => {
        const j = r.justificacion_info
        if (r.estado !== 'AUSENTE' || !j) {
          return r.estado === 'AUSENTE' ? (
            <button
              onClick={() => setJustificando(r)}
              className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-semibold text-unl-red bg-unl-red/10 hover:bg-unl-red/20 rounded-lg transition-all"
            >
              <FileCheck2 size={13} />
              <span>Subir comprobante</span>
            </button>
          ) : null
        }
        if (j.estado === 'PENDIENTE') {
          return <span className="text-xs text-amber-600 font-medium">En revisión</span>
        }
        if (j.estado === 'RECHAZADA') {
          return (
            <div className="space-y-1">
              <p className="text-xs text-red-600">Rechazado: {j.comentario_docente || 'sin comentario'}</p>
              <button
                onClick={() => setJustificando(r)}
                className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-semibold text-unl-red bg-unl-red/10 hover:bg-unl-red/20 rounded-lg transition-all"
              >
                <FileCheck2 size={13} />
                <span>Reenviar comprobante</span>
              </button>
            </div>
          )
        }
        return null
      }
    }] : []),
  ]

  return (
    <div className="space-y-5">
      {serviceDown && <MaintenanceBanner service="asistencia" />}
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

      <FormModal
        open={!!justificando}
        onClose={() => setJustificando(null)}
        title="Subir comprobante médico"
        loading={saving}
        initialData={{ motivo: '', documento: null }}
        onSubmit={handleJustificar}
        fields={[
          { key: 'motivo', label: 'Motivo de la falta', type: 'textarea', required: true },
          {
            key: 'documento',
            label: 'Comprobante médico (PNG o JPG)',
            type: 'file',
            required: true,
            accept: 'image/png, image/jpeg',
            allowedTypes: ['image/png', 'image/jpeg', 'image/jpg']
          },
        ]}
      />
    </div>
  )
}
