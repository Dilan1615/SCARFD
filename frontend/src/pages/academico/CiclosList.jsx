import { useState, useEffect } from 'react'
import api from '../../api/axios'
import DataTable from '../../components/DataTable'
import FormModal from '../../components/FormModal'
import { useAuth } from '../../contexts/AuthContext'
import { useToast } from '../../contexts/ToastContext'
import { Layers } from 'lucide-react'

const columns = [
  { key: 'num', label: 'Ciclo', render: (v) => <span className="font-medium">Ciclo {v}</span> },
  { key: 'carrera_nombre', label: 'Carrera' },
  { key: 'fecha_inicio', label: 'Inicio' },
  { key: 'fecha_fin', label: 'Fin' },
  { key: 'estado_display', label: 'Estado', render: (v, r) => (
    <span className={`px-2.5 py-1 text-xs font-semibold rounded-full ${r.estado === 'ACTIVO' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}>{v}</span>
  )},
]

export default function CiclosList() {
  const { user } = useAuth()
  const { addToast } = useToast()
  const [data, setData] = useState([])
  const [carreras, setCarreras] = useState([])
  const [loading, setLoading] = useState(true)
  const [modal, setModal] = useState(false)
  const [editItem, setEditItem] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const isAdmin = user?.rol === 'ADMIN'

  const load = () => {
    setLoading(true)
    Promise.all([
      api.get('/academico/ciclos/').then(r => r.data.results || r.data),
      api.get('/academico/carreras/').then(r => r.data.results || r.data),
    ]).then(([ciclos, carr]) => {
      setData(ciclos)
      setCarreras(carr)
    }).catch(() => addToast('Error al cargar datos', 'error')).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const formFields = [
    { key: 'num', label: 'Número de Ciclo', type: 'number', required: true, min: 1 },
    { key: 'carrera', label: 'Carrera', type: 'select', required: true,
      options: carreras.map(c => ({ value: c.id, label: c.nombre }))
    },
    { key: 'fecha_inicio', label: 'Fecha Inicio', type: 'date', required: true },
    { key: 'fecha_fin', label: 'Fecha Fin', type: 'date', required: true },
    { key: 'estado', label: 'Estado', type: 'select', required: true,
      options: [
        { value: 'ACTIVO', label: 'Activo' },
        { value: 'FINALIZADO', label: 'Finalizado' },
      ]
    },
  ]

  const handleSubmit = async (form) => {
    setSubmitting(true)
    try {
      const payload = { ...form, carrera: Number(form.carrera), num: Number(form.num) }
      if (editItem) {
        await api.put(`/academico/ciclos/${editItem.id}/`, payload)
        addToast('Ciclo actualizado exitosamente')
      } else {
        await api.post('/academico/ciclos/', payload)
        addToast('Ciclo creado exitosamente')
      }
      setModal(false)
      setEditItem(null)
      load()
    } catch (err) {
      const msg = err.response?.data?.error || err.response?.data?.non_field_errors?.[0] || 'Error al guardar el ciclo'
      addToast(msg, 'error')
    } finally { setSubmitting(false) }
  }

  const handleDelete = async (item) => {
    if (!confirm(`¿Eliminar ciclo ${item.num}?`)) return
    try {
      await api.delete(`/academico/ciclos/${item.id}/`)
      addToast('Ciclo eliminado exitosamente')
      load()
    } catch {
      addToast('Error al eliminar el ciclo', 'error')
    }
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-4">
        <div className="w-10 h-10 rounded-2xl bg-unl-green/10 flex items-center justify-center">
          <Layers size={20} className="text-unl-green" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-unl-black">Gestión de Ciclos</h2>
          <p className="text-sm text-gray-500">Administrar ciclos académicos por carrera</p>
        </div>
      </div>
      <DataTable title="Ciclos" columns={columns} data={data} loading={loading}
        onAdd={isAdmin ? () => { setEditItem(null); setModal(true) } : undefined}
        onEdit={isAdmin ? (item) => { setEditItem(item); setModal(true) } : undefined}
        onDelete={isAdmin ? handleDelete : undefined}
      />
      {isAdmin && (
        <FormModal open={modal} onClose={() => { setModal(false); setEditItem(null) }}
          title={editItem ? 'Editar Ciclo' : 'Nuevo Ciclo'} fields={formFields}
          initialData={editItem} onSubmit={handleSubmit} loading={submitting}
        />
      )}
    </div>
  )
}
