import { useState, useEffect } from 'react'
import api from '../../api/axios'
import DataTable from '../../components/DataTable'
import FormModal from '../../components/FormModal'
import { useAuth } from '../../contexts/AuthContext'
import { useToast } from '../../contexts/ToastContext'
import { BookOpen } from 'lucide-react'

const columns = [
  { key: 'codigo', label: 'Código' },
  { key: 'nombre', label: 'Nombre' },
  { key: 'creditos', label: 'Créditos Acad.' },
  { key: 'horas_semanales', label: 'Horas/Sem' },
  { key: 'carrera_nombre', label: 'Carrera' },
  { key: 'ciclo_info', label: 'Ciclo' },
  { key: 'docente_nombre', label: 'Docente' },
]

export default function MateriasList() {
  const { user } = useAuth()
  const { addToast } = useToast()
  const [data, setData] = useState([])
  const [carreras, setCarreras] = useState([])
  const [ciclos, setCiclos] = useState([])
  const [docentes, setDocentes] = useState([])
  const [loading, setLoading] = useState(true)
  const [modal, setModal] = useState(false)
  const [editItem, setEditItem] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const isAdmin = user?.rol === 'ADMIN'

  const load = () => {
    setLoading(true)
    Promise.all([
      api.get('/academico/materias/').then(r => r.data.results || r.data),
      api.get('/academico/carreras/').then(r => r.data.results || r.data),
      api.get('/academico/ciclos/').then(r => r.data.results || r.data),
      api.get('/usuario/usuarios/', { params: { rol: 'DOCENTE' } }).then(r => r.data.results || r.data),
    ]).then(([mats, carr, cic, docs]) => {
      setData(mats); setCarreras(carr); setCiclos(cic); setDocentes(docs)
    }).catch(() => addToast('Error al cargar datos', 'error')).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const formFields = [
    { key: 'codigo', label: 'Código', type: 'text', required: true },
    { key: 'nombre', label: 'Nombre', type: 'text', required: true },
    { key: 'descripcion', label: 'Descripción', type: 'textarea' },
    { key: 'creditos', label: 'Créditos Acad.', type: 'number', required: true, min: 1 },
    { key: 'horas_semanales', label: 'Horas Semanales', type: 'number', required: true, min: 1 },
    { key: 'carrera', label: 'Carrera', type: 'select', required: true,
      options: carreras.map(c => ({ value: c.id, label: c.nombre }))
    },
    { key: 'ciclo', label: 'Ciclo', type: 'select', required: true,
      options: ciclos.map(c => ({ value: c.id, label: `${c.carrera_nombre} - Ciclo ${c.num}` }))
    },
    { key: 'docente', label: 'Docente', type: 'select',
      options: docentes.map(d => ({ value: d.id, label: `${d.first_name} ${d.last_name}` }))
    },
  ]

  const handleSubmit = async (form) => {
    setSubmitting(true)
    try {
      const payload = { ...form, creditos: Number(form.creditos), horas_semanales: Number(form.horas_semanales), carrera: Number(form.carrera), ciclo: Number(form.ciclo), docente: form.docente ? Number(form.docente) : null }
      if (editItem) {
        await api.put(`/academico/materias/${editItem.id}/`, payload)
        addToast('Materia actualizada exitosamente')
      } else {
        await api.post('/academico/materias/', payload)
        addToast('Materia creada exitosamente')
      }
      setModal(false); setEditItem(null); load()
    } catch (err) {
      const msg = err.response?.data?.error || err.response?.data?.non_field_errors?.[0] || 'Error al guardar la materia'
      addToast(msg, 'error')
    } finally { setSubmitting(false) }
  }

  const handleDelete = async (item) => {
    if (!confirm(`¿Eliminar materia "${item.nombre}"?`)) return
    try {
      await api.delete(`/academico/materias/${item.id}/`)
      addToast('Materia eliminada exitosamente')
      load()
    } catch {
      addToast('Error al eliminar la materia', 'error')
    }
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-4">
        <div className="w-10 h-10 rounded-2xl bg-unl-green/10 flex items-center justify-center">
          <BookOpen size={20} className="text-unl-green" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-unl-black">Gestión de Materias</h2>
          <p className="text-sm text-gray-500">Administrar materias con docentes y horarios</p>
        </div>
      </div>
      <DataTable title="Materias" columns={columns} data={data} loading={loading}
        onAdd={isAdmin ? () => { setEditItem(null); setModal(true) } : undefined}
        onEdit={isAdmin ? (item) => { setEditItem(item); setModal(true) } : undefined}
        onDelete={isAdmin ? handleDelete : undefined}
      />
      {isAdmin && (
        <FormModal open={modal} onClose={() => { setModal(false); setEditItem(null) }}
          title={editItem ? 'Editar Materia' : 'Nueva Materia'} fields={formFields}
          initialData={editItem} onSubmit={handleSubmit} loading={submitting}
        />
      )}
    </div>
  )
}
