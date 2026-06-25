import { useState, useEffect } from 'react'
import api from '../../api/axios'
import DataTable from '../../components/DataTable'
import FormModal from '../../components/FormModal'
import { useAuth } from '../../contexts/AuthContext'
import { useToast } from '../../contexts/ToastContext'
import { GraduationCap } from 'lucide-react'

const columns = [
  { key: 'codigo', label: 'Código' },
  { key: 'nombre', label: 'Nombre' },
  { key: 'descripcion', label: 'Descripción' },
  { key: 'duracion', label: 'Duración', render: (v) => `${v} semestres` },
  { key: 'modalidad_display', label: 'Modalidad' },
]

const formFields = [
  { key: 'codigo', label: 'Código', type: 'text', required: true },
  { key: 'nombre', label: 'Nombre', type: 'text', required: true },
  { key: 'descripcion', label: 'Descripción', type: 'textarea' },
  { key: 'duracion', label: 'Duración (semestres)', type: 'number', required: true, min: 1 },
  { key: 'modalidad', label: 'Modalidad', type: 'select', required: true,
    options: [
      { value: 'VIRTUAL', label: 'Virtual' },
      { value: 'PRESENCIAL', label: 'Presencial' },
      { value: 'HIBRIDA', label: 'Híbrida' },
    ]
  },
]

export default function CarrerasList() {
  const { user } = useAuth()
  const { addToast } = useToast()
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)
  const [modal, setModal] = useState(false)
  const [editItem, setEditItem] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const isAdmin = user?.rol === 'ADMIN'

  const load = () => {
    setLoading(true)
    api.get('/academico/carreras/').then(({ data: res }) => setData(res.results || res)).catch(() => addToast('Error al cargar carreras', 'error')).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const handleSubmit = async (form) => {
    setSubmitting(true)
    try {
      if (editItem) {
        await api.put(`/academico/carreras/${editItem.id}/`, form)
        addToast('Carrera actualizada exitosamente')
      } else {
        await api.post('/academico/carreras/', form)
        addToast('Carrera creada exitosamente')
      }
      setModal(false)
      setEditItem(null)
      load()
    } catch {
      addToast('Error al guardar la carrera', 'error')
    } finally { setSubmitting(false) }
  }

  const handleDelete = async (item) => {
    if (!confirm(`¿Eliminar carrera "${item.nombre}"?`)) return
    try {
      await api.delete(`/academico/carreras/${item.id}/`)
      addToast('Carrera eliminada exitosamente')
      load()
    } catch {
      addToast('Error al eliminar la carrera', 'error')
    }
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-4">
        <div className="w-10 h-10 rounded-2xl bg-unl-red/10 flex items-center justify-center">
          <GraduationCap size={20} className="text-unl-red" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-unl-black">Gestión de Carreras</h2>
          <p className="text-sm text-gray-500">Administrar carreras universitarias</p>
        </div>
      </div>
      <DataTable title="Carreras" columns={columns} data={data} loading={loading}
        onAdd={isAdmin ? () => { setEditItem(null); setModal(true) } : undefined}
        onEdit={isAdmin ? (item) => { setEditItem(item); setModal(true) } : undefined}
        onDelete={isAdmin ? handleDelete : undefined}
      />
      {isAdmin && (
        <FormModal open={modal} onClose={() => { setModal(false); setEditItem(null) }}
          title={editItem ? 'Editar Carrera' : 'Nueva Carrera'} fields={formFields}
          initialData={editItem} onSubmit={handleSubmit} loading={submitting}
        />
      )}
    </div>
  )
}
