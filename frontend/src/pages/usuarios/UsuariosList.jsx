import { useState, useEffect, useMemo } from 'react'
import api from '../../api/axios'
import DataTable from '../../components/DataTable'
import FormModal from '../../components/FormModal'
import { useAuth } from '../../contexts/AuthContext'
import { useToast } from '../../contexts/ToastContext'
import { Users } from 'lucide-react'

const baseColumns = [
  { key: 'foto_referencia_url', label: 'Foto', render: (v) => v ? <img src={v} alt="" className="w-9 h-9 rounded-full object-cover border border-gray-200" /> : <div className="w-9 h-9 rounded-full bg-gray-100 border border-gray-200 flex items-center justify-center text-gray-400 text-xs">—</div> },
  { key: 'first_name', label: 'Nombres', render: (v, r) => `${r.first_name} ${r.last_name}` },
  { key: 'email', label: 'Email' },
  { key: 'cedula', label: 'Cédula' },
  { key: 'telefono', label: 'Teléfono' },
  { key: 'is_active', label: 'Estado', render: (v) => v === false ? <span className="px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-700">Inactivo</span> : <span className="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-700">Activo</span> },
]

const adminColumns = [
  ...baseColumns.slice(0, 6),
  { key: 'rol', label: 'Rol', render: (v) => {
    const colors = { ADMIN: 'bg-red-100 text-red-700', DOCENTE: 'bg-blue-100 text-blue-700', ESTUDIANTE: 'bg-green-100 text-green-700' }
    const labels = { ADMIN: 'Admin', DOCENTE: 'Docente', ESTUDIANTE: 'Estudiante' }
    return <span className={`px-2 py-1 text-xs font-semibold rounded-full ${colors[v] || 'bg-gray-100 text-gray-700'}`}>{labels[v] || v}</span>
  }},
  ...baseColumns.slice(6),
]

const formFields = [
  { key: 'email', label: 'Email', type: 'email' },
  { key: 'password', label: 'Contraseña', type: 'password', hint: 'Mín. 8 caracteres, 1 mayúscula, 1 número, 1 símbolo' },
  { key: 'first_name', label: 'Nombres', type: 'text' },
  { key: 'last_name', label: 'Apellidos', type: 'text' },
  { key: 'cedula', label: 'Cédula', type: 'text', required: true, numeric: true, maxLength: 10 },
  { key: 'telefono', label: 'Teléfono', type: 'text', numeric: true, maxLength: 10 },
  { key: 'rol', label: 'Rol', type: 'select', required: true,
    options: [
      { value: 'ADMIN', label: 'Administrador' },
      { value: 'DOCENTE', label: 'Docente' },
      { value: 'ESTUDIANTE', label: 'Estudiante' },
    ]
  },
  { key: 'foto', label: 'Foto de perfil', type: 'file', accept: 'image/*' },
]

export default function UsuariosList() {
  const { user } = useAuth()
  const { addToast } = useToast()
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)
  const [modal, setModal] = useState(false)
  const [editItem, setEditItem] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const isAdmin = user?.rol === 'ADMIN'

  const columns = useMemo(() => isAdmin ? adminColumns : baseColumns, [isAdmin])

  const load = () => {
    setLoading(true)
    api.get('/usuario/usuarios/').then(({ data: res }) => setData(res.results || res)).catch(() => addToast('Error al cargar usuarios', 'error')).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const hasFile = (form) => Object.values(form).some((v) => v instanceof File)

  const toFormData = (form) => {
    const fd = new FormData()
    for (const [key, value] of Object.entries(form)) {
      if (value instanceof File) {
        fd.append(key, value)
      } else if (value !== undefined && value !== null) {
        fd.append(key, value)
      }
    }
    return fd
  }

  const handleSubmit = async (form) => {
    setSubmitting(true)
    try {
      const isFileUpload = hasFile(form)
      if (editItem) {
        const payload = isFileUpload ? toFormData(form) : { ...form }
        if (!isFileUpload) delete payload.password
        await api.patch(`/usuario/usuarios/${editItem.id}/`, payload, isFileUpload ? { headers: { 'Content-Type': 'multipart/form-data' } } : {})
        addToast('Usuario actualizado exitosamente')
      } else {
        const payload = isFileUpload ? toFormData(form) : form
        await api.post('/usuario/usuarios/register/', payload, isFileUpload ? { headers: { 'Content-Type': 'multipart/form-data' } } : {})
        addToast('Usuario creado exitosamente')
      }
      setModal(false)
      setEditItem(null)
      load()
    } catch (err) {
      const data = err.response?.data || {}
      const msg = data.error || data.password?.[0] || data.email?.[0] || data.cedula?.[0] || data.first_name?.[0] || data.last_name?.[0] || data.non_field_errors?.[0] || 'Error al guardar el usuario'
      addToast(msg, 'error')
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async (item) => {
    if (!confirm(`¿Desactivar usuario "${item.email}"?`)) return
    try {
      await api.delete(`/usuario/usuarios/${item.id}/`)
      addToast('Usuario desactivado exitosamente')
      load()
    } catch {
      addToast('Error al desactivar el usuario', 'error')
    }
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-4">
        <div className="w-10 h-10 rounded-2xl bg-unl-red/10 flex items-center justify-center">
          <Users size={20} className="text-unl-red" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-unl-black">Gestión de Usuarios</h2>
          <p className="text-sm text-gray-500">{isAdmin ? 'Administrar usuarios del sistema' : 'Mi información'}</p>
        </div>
      </div>
      <DataTable
        title="Usuarios"
        columns={columns}
        data={data}
        loading={loading}
        onAdd={isAdmin ? () => { setEditItem(null); setModal(true) } : undefined}
        onEdit={isAdmin ? (item) => { setEditItem(item); setModal(true) } : undefined}
        onDelete={isAdmin ? handleDelete : undefined}
      />
      {isAdmin && (
        <FormModal
          open={modal}
          onClose={() => { setModal(false); setEditItem(null) }}
          title={editItem ? 'Editar Usuario' : 'Nuevo Usuario'}
          fields={editItem ? formFields.filter(f => f.key !== 'password') : formFields}
          initialData={editItem}
          onSubmit={handleSubmit}
          loading={submitting}
        />
      )}
    </div>
  )
}
