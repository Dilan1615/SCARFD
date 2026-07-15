import { useState, useEffect } from 'react'
import api from '../../api/axios'
import DataTable from '../../components/DataTable'
import FormModal from '../../components/FormModal'
import MaintenanceBanner from '../../components/MaintenanceBanner'
import { useAuth } from '../../contexts/AuthContext'
import { useToast } from '../../contexts/ToastContext'
import { ScrollText } from 'lucide-react'

const columns = [
  { key: 'estudiante_nombre', label: 'Estudiante' },
  { key: 'carrera_nombre', label: 'Carrera' },
  { key: 'ciclo_info', label: 'Ciclo' },
  { key: 'fecha_matricula', label: 'Fecha Matrícula' },
  { key: 'estado_display', label: 'Estado', render: (v, r) => (
    <span className={`px-2.5 py-1 text-xs font-semibold rounded-full ${r.estado === 'ACTIVA' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}>{v}</span>
  )},
]

export default function MatriculasList() {
  const { user } = useAuth()
  const { addToast } = useToast()
  const [data, setData] = useState([])
  const [estudiantes, setEstudiantes] = useState([])
  const [carreras, setCarreras] = useState([])
  const [ciclos, setCiclos] = useState([])
  const [loading, setLoading] = useState(true)
  const [serviceDown, setServiceDown] = useState(false)
  const [modal, setModal] = useState(false)
  const [editItem, setEditItem] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const isAdmin = user?.rol === 'ADMIN'

  const load = () => {
    setLoading(true)
    setServiceDown(false)

    const safeGet = (url, params) =>
      api.get(url, params)
        .then(r => r.data.results || r.data)
        .catch(() => [])

    Promise.all([
      api.get('/academico/matriculas/')
        .then(r => r.data.results || r.data)
        .catch(err => { throw err }),
      safeGet('/usuario/usuarios/', { params: { rol: 'ESTUDIANTE' } }),
      safeGet('/academico/carreras/'),
      safeGet('/academico/ciclos/'),
    ]).then(([matriculas, est, carr, cic]) => {
      setData(matriculas)
      setEstudiantes(est.filter(u => u.rol === 'ESTUDIANTE'))
      setCarreras(carr)
      setCiclos(cic)
    }).catch((err) => {
      if (!err.response || err.response.status >= 500) setServiceDown(true)
      else addToast('Error al cargar matrículas', 'error')
    }).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const formFields = [
    { key: 'estudiante_id', label: 'Estudiante', type: 'select', required: true,
      options: estudiantes.map(e => ({ value: e.id, label: `${e.first_name} ${e.last_name} (${e.cedula})` }))
    },
    { key: 'carrera', label: 'Carrera', type: 'select', required: true,
      options: carreras.map(c => ({ value: c.id, label: c.nombre }))
    },
    { key: 'ciclo', label: 'Ciclo', type: 'select', required: true,
      options: ciclos.filter(c => editItem ? true : c.estado === 'ACTIVO').map(c => ({
        value: c.id,
        label: `${c.carrera_nombre} - Ciclo ${c.num}`
      }))
    },
    { key: 'estado', label: 'Estado', type: 'select', required: true,
      options: [
        { value: 'ACTIVA', label: 'Activa' },
        { value: 'FINALIZADA', label: 'Finalizada' },
      ]
    },
  ]

  const handleSubmit = async (form) => {
    setSubmitting(true)
    try {
      const payload = {
        estudiante_id: Number(form.estudiante_id),
        carrera: Number(form.carrera),
        ciclo: Number(form.ciclo),
        estado: form.estado,
      }
      if (editItem) {
        await api.put(`/academico/matriculas/${editItem.id}/`, payload)
        addToast('Matrícula actualizada exitosamente')
      } else {
        await api.post('/academico/matriculas/', payload)
        addToast('Matrícula creada exitosamente')
      }
      setModal(false)
      setEditItem(null)
      load()
    } catch (err) {
      const data = err.response?.data
      let msg = 'Error al guardar la matrícula'
      if (data) {
        if (data.error) msg = data.error
        else if (data.non_field_errors?.[0]) msg = data.non_field_errors[0]
        else {
          const first = Object.entries(data).find(([, v]) => v?.[0])
          if (first) msg = first[1][0]
        }
      }
      addToast(msg, 'error')
    } finally { setSubmitting(false) }
  }

  const handleDelete = async (item) => {
    if (!confirm(`¿Eliminar matrícula de "${item.estudiante_nombre}"?`)) return
    try {
      await api.delete(`/academico/matriculas/${item.id}/`)
      addToast('Matrícula eliminada exitosamente')
      load()
    } catch {
      addToast('Error al eliminar la matrícula', 'error')
    }
  }

  return (
    <div className="space-y-5">
      {serviceDown && <MaintenanceBanner service="academico" />}
      <div className="flex items-center gap-4">
        <div className="w-10 h-10 rounded-2xl bg-unl-red/10 flex items-center justify-center">
          <ScrollText size={20} className="text-unl-red" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-unl-black">Gestión de Matrículas</h2>
          <p className="text-sm text-gray-500">Asignar estudiantes a carreras y ciclos</p>
        </div>
      </div>
      <DataTable title="Matrículas" columns={columns} data={data} loading={loading}
        onAdd={isAdmin ? () => { setEditItem(null); setModal(true) } : undefined}
        onEdit={isAdmin ? (item) => { setEditItem(item); setModal(true) } : undefined}
        onDelete={isAdmin ? handleDelete : undefined}
      />
      {isAdmin && (
        <FormModal open={modal} onClose={() => { setModal(false); setEditItem(null) }}
          title={editItem ? 'Editar Matrícula' : 'Nueva Matrícula'} fields={formFields}
          initialData={editItem} onSubmit={handleSubmit} loading={submitting}
          emptyMessage={
            estudiantes.length === 0 ? 'No hay estudiantes disponibles' :
            carreras.length === 0 ? 'No hay carreras registradas' :
            ciclos.filter(c => c.estado === 'ACTIVO').length === 0 ? 'No hay ciclos activos' :
            null
          }
        />
      )}
    </div>
  )
}
