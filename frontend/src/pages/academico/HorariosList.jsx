import { useState, useEffect } from 'react'
import api from '../../api/axios'
import DataTable from '../../components/DataTable'
import FormModal from '../../components/FormModal'
import { useAuth } from '../../contexts/AuthContext'
import { useToast } from '../../contexts/ToastContext'
import { Clock } from 'lucide-react'

const dias = [
  { value: 'LUNES', label: 'Lunes' },
  { value: 'MARTES', label: 'Martes' },
  { value: 'MIERCOLES', label: 'Miércoles' },
  { value: 'JUEVES', label: 'Jueves' },
  { value: 'VIERNES', label: 'Viernes' },
]

const columns = [
  { key: 'materia_nombre', label: 'Materia' },
  { key: 'dia_display', label: 'Día' },
  { key: 'hora_inicio', label: 'Inicio' },
  { key: 'hora_fin', label: 'Fin' },
  { key: 'minutos_tolerancia', label: 'Tolerancia', render: (v) => `${v} min` },
  { key: 'aula', label: 'Aula' },
]

export default function HorariosList() {
  const { user } = useAuth()
  const { addToast } = useToast()
  const [data, setData] = useState([])
  const [materias, setMaterias] = useState([])
  const [loading, setLoading] = useState(true)
  const [modal, setModal] = useState(false)
  const [editItem, setEditItem] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const isAdmin = user?.rol === 'ADMIN'

  const load = () => {
    setLoading(true)
    Promise.all([
      api.get('/academico/horarios/').then(r => r.data.results || r.data),
      api.get('/academico/materias/').then(r => r.data.results || r.data),
    ]).then(([hor, mats]) => { setData(hor); setMaterias(mats) }).catch(() => addToast('Error al cargar datos', 'error')).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const formFields = [
    { key: 'materia', label: 'Materia', type: 'select', required: true,
      options: materias.map(m => ({ value: m.id, label: `${m.codigo} - ${m.nombre}` }))
    },
    { key: 'dia_semana', label: 'Día', type: 'select', required: true, options: dias },
    { key: 'hora_inicio', label: 'Hora Inicio', type: 'time', required: true },
    { key: 'hora_fin', label: 'Hora Fin', type: 'time', required: true },
    { key: 'minutos_tolerancia', label: 'Minutos Tolerancia', type: 'number', required: true, min: 0 },
    { key: 'aula', label: 'Aula', type: 'text' },
  ]

  const handleSubmit = async (form) => {
    setSubmitting(true)
    try {
      const payload = { ...form, materia: Number(form.materia), minutos_tolerancia: Number(form.minutos_tolerancia) }
      if (editItem) {
        await api.put(`/academico/horarios/${editItem.id}/`, payload)
        addToast('Horario actualizado exitosamente')
      } else {
        await api.post('/academico/horarios/', payload)
        addToast('Horario creado exitosamente')
      }
      setModal(false); setEditItem(null); load()
    } catch (err) {
      const msg = err.response?.data?.error || err.response?.data?.non_field_errors?.[0] || 'Error al guardar el horario'
      addToast(msg, 'error')
    } finally { setSubmitting(false) }
  }

  const handleDelete = async (item) => {
    if (!confirm(`¿Eliminar horario?`)) return
    try {
      await api.delete(`/academico/horarios/${item.id}/`)
      addToast('Horario eliminado exitosamente')
      load()
    } catch {
      addToast('Error al eliminar el horario', 'error')
    }
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-4">
        <div className="w-10 h-10 rounded-2xl bg-unl-red/10 flex items-center justify-center">
          <Clock size={20} className="text-unl-red" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-unl-black">Gestión de Horarios</h2>
          <p className="text-sm text-gray-500">Administrar horarios académicos</p>
        </div>
      </div>
      <DataTable title="Horarios" columns={columns} data={data} loading={loading}
        onAdd={isAdmin ? () => { setEditItem(null); setModal(true) } : undefined}
        onEdit={isAdmin ? (item) => { setEditItem(item); setModal(true) } : undefined}
        onDelete={isAdmin ? handleDelete : undefined}
      />
      {isAdmin && (
        <FormModal open={modal} onClose={() => { setModal(false); setEditItem(null) }}
          title={editItem ? 'Editar Horario' : 'Nuevo Horario'} fields={formFields}
          initialData={editItem} onSubmit={handleSubmit} loading={submitting}
        />
      )}
    </div>
  )
}
