import { useState, useEffect } from 'react'
import api from '../../api/axios'
import DataTable from '../../components/DataTable'
import FormModal from '../../components/FormModal'
import MaintenanceBanner from '../../components/MaintenanceBanner'
import { useAuth } from '../../contexts/AuthContext'
import { useToast } from '../../contexts/ToastContext'
import { FileCheck2, Check, X as XIcon } from 'lucide-react'

const estadoColors = {
  PENDIENTE: 'bg-amber-100 text-amber-700',
  APROBADA: 'bg-green-100 text-green-700',
  RECHAZADA: 'bg-red-100 text-red-700',
}

export default function JustificacionesList() {
  const { user } = useAuth()
  const { addToast } = useToast()
  const isDocente = user?.rol === 'DOCENTE'
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)
  const [serviceDown, setServiceDown] = useState(false)
  const [imagenAmpliada, setImagenAmpliada] = useState(null)
  const [rechazando, setRechazando] = useState(null)
  const [saving, setSaving] = useState(false)

  const load = () => {
    setLoading(true)
    setServiceDown(false)
    api.get('/asistencia/justificaciones/').then(({ data: res }) => setData(res.results || res)).catch((err) => {
      if (!err.response || err.response.status >= 500) setServiceDown(true)
    }).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const validar = async (justificacion) => {
    try {
      await api.post('/asistencia/justificaciones/aprobar/', {
        justificacion_id: justificacion.id,
        aprobar: true,
      })
      addToast('Justificación marcada como válida', 'success')
      load()
    } catch (err) {
      addToast(err.response?.data?.error || 'No se pudo validar la justificación', 'error')
    }
  }

  const handleRechazar = async (form) => {
    setSaving(true)
    try {
      await api.post('/asistencia/justificaciones/aprobar/', {
        justificacion_id: rechazando.id,
        aprobar: false,
        comentario: form.comentario,
      })
      addToast('Justificación marcada como inválida', 'success')
      setRechazando(null)
      load()
    } catch (err) {
      addToast(err.response?.data?.error || 'No se pudo rechazar la justificación', 'error')
    } finally {
      setSaving(false)
    }
  }

  const columns = [
    { key: 'estudiante_nombre', label: 'Estudiante' },
    { key: 'motivo', label: 'Motivo' },
    { key: 'fecha_solicitud', label: 'Solicitado', render: (v) => v ? new Date(v).toLocaleString() : '-' },
    { key: 'documento', label: 'Comprobante', render: (v) => v ? (
      <button onClick={() => setImagenAmpliada(v)} className="block">
        <img src={v} alt="Comprobante médico" className="w-14 h-14 object-cover rounded-lg border border-gray-200 hover:opacity-80 transition-opacity" />
      </button>
    ) : '-' },
    { key: 'estado_display', label: 'Estado', render: (v, r) => (
      <div>
        <span className={`px-2.5 py-1 text-xs font-semibold rounded-full ${estadoColors[r.estado] || 'bg-gray-100 text-gray-700'}`}>{v}</span>
        {r.estado === 'RECHAZADA' && r.comentario_docente && (
          <p className="text-xs text-gray-500 mt-1 max-w-[180px]">{r.comentario_docente}</p>
        )}
      </div>
    )},
    ...(isDocente ? [{
      key: 'id', label: 'Acciones', render: (_, r) => r.estado !== 'PENDIENTE' ? (
        <span className="text-xs text-gray-400">—</span>
      ) : (
        <div className="flex items-center gap-2">
          <button
            onClick={() => validar(r)}
            className="flex items-center gap-1 px-2.5 py-1 text-xs font-semibold text-green-700 bg-green-50 hover:bg-green-100 border border-green-200 rounded-lg transition-all"
            title="Marcar como válida"
          >
            <Check size={13} />
            <span>Válido</span>
          </button>
          <button
            onClick={() => setRechazando(r)}
            className="flex items-center gap-1 px-2.5 py-1 text-xs font-semibold text-red-700 bg-red-50 hover:bg-red-100 border border-red-200 rounded-lg transition-all"
            title="Marcar como inválida"
          >
            <XIcon size={13} />
            <span>Inválido</span>
          </button>
        </div>
      )
    }] : []),
  ]

  return (
    <div className="space-y-5">
      {serviceDown && <MaintenanceBanner service="asistencia" />}
      <div className="flex items-center gap-4">
        <div className="w-10 h-10 rounded-2xl bg-unl-red/10 flex items-center justify-center">
          <FileCheck2 size={20} className="text-unl-red" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-unl-black">Justificación de Faltas</h2>
          <p className="text-sm text-gray-500">
            {isDocente ? 'Valida el comprobante médico de tus estudiantes' : 'Tus solicitudes de justificación de inasistencias'}
          </p>
        </div>
      </div>
      <DataTable title="Justificaciones" columns={columns} data={data} loading={loading} />

      {imagenAmpliada && (
        <div
          className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-6"
          onClick={() => setImagenAmpliada(null)}
        >
          <img
            src={imagenAmpliada}
            alt="Comprobante médico ampliado"
            className="max-w-full max-h-full rounded-xl shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          />
        </div>
      )}

      <FormModal
        open={!!rechazando}
        onClose={() => setRechazando(null)}
        title="Marcar justificación como inválida"
        loading={saving}
        initialData={{ comentario: '' }}
        onSubmit={handleRechazar}
        fields={[
          { key: 'comentario', label: 'Motivo del rechazo (el estudiante lo verá)', type: 'textarea', required: true },
        ]}
      />
    </div>
  )
}
