import { useState, useEffect } from 'react'
import api from '../../api/axios'
import { useAuth } from '../../contexts/AuthContext'
import { useToast } from '../../contexts/ToastContext'
import { User, Camera, Loader2, Save } from 'lucide-react'

export default function MiPerfil() {
  const { user, refreshUser } = useAuth()
  const { addToast } = useToast()
  const [form, setForm] = useState({})
  const [fotoFile, setFotoFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [loading, setLoading] = useState(false)
  const [showContent, setShowContent] = useState(false)

  useEffect(() => {
    setTimeout(() => setShowContent(true), 100)
  }, [])

  useEffect(() => {
    if (user) {
      setForm({
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        cedula: user.cedula || '',
        telefono: user.telefono || '',
      })
      setPreview(user.foto_referencia_url || null)
    }
  }, [user])

  const handleFileChange = (e) => {
    const file = e.target.files[0]
    if (file) {
      setFotoFile(file)
      setPreview(URL.createObjectURL(file))
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      const fd = new FormData()
      fd.append('first_name', form.first_name)
      fd.append('last_name', form.last_name)
      fd.append('cedula', form.cedula)
      fd.append('telefono', form.telefono)
      if (fotoFile) fd.append('foto', fotoFile)

      const { data } = await api.patch('/usuario/usuarios/perfil/', fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      addToast('Perfil actualizado exitosamente')
      await refreshUser()
    } catch (err) {
      const msg = err.response?.data?.error || err.response?.data?.cedula?.[0] || 'Error al actualizar el perfil'
      addToast(msg, 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (key) => (e) => setForm((prev) => ({ ...prev, [key]: e.target.value }))

  return (
    <div className={`max-w-2xl mx-auto transition-all duration-700 ${showContent ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}>
      <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="bg-gradient-to-r from-unl-black to-[#3C231E] px-6 py-8 text-center">
          <div className="relative inline-block">
            <div className="w-24 h-24 rounded-full border-4 border-white/20 overflow-hidden mx-auto shadow-lg">
              {preview ? (
                <img src={preview} alt="" className="w-full h-full object-cover" />
              ) : (
                <div className="w-full h-full bg-gray-700 flex items-center justify-center">
                  <User size={36} className="text-gray-400" />
                </div>
              )}
            </div>
            <label className="absolute -bottom-1 -right-1 w-8 h-8 bg-unl-red rounded-full flex items-center justify-center cursor-pointer hover:bg-red-700 transition-colors shadow-md border-2 border-white">
              <Camera size={14} className="text-white" />
              <input type="file" accept="image/*" onChange={handleFileChange} className="hidden" />
            </label>
          </div>
          <h2 className="text-white text-xl font-bold mt-4">{user?.first_name} {user?.last_name}</h2>
          <p className="text-gray-400 text-sm">{user?.email}</p>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">Nombres</label>
              <input type="text" value={form.first_name} onChange={handleChange('first_name')}
                className="w-full h-11 px-4 border border-gray-200 rounded-xl focus:ring-2 focus:ring-unl-red/20 focus:border-unl-red outline-none transition-all text-gray-900 bg-gray-50 focus:bg-white" />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">Apellidos</label>
              <input type="text" value={form.last_name} onChange={handleChange('last_name')}
                className="w-full h-11 px-4 border border-gray-200 rounded-xl focus:ring-2 focus:ring-unl-red/20 focus:border-unl-red outline-none transition-all text-gray-900 bg-gray-50 focus:bg-white" />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">Cédula</label>
              <input type="text" value={form.cedula} onChange={handleChange('cedula')} maxLength={10}
                className="w-full h-11 px-4 border border-gray-200 rounded-xl focus:ring-2 focus:ring-unl-red/20 focus:border-unl-red outline-none transition-all text-gray-900 bg-gray-50 focus:bg-white" />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">Teléfono</label>
              <input type="text" value={form.telefono} onChange={handleChange('telefono')} maxLength={10}
                className="w-full h-11 px-4 border border-gray-200 rounded-xl focus:ring-2 focus:ring-unl-red/20 focus:border-unl-red outline-none transition-all text-gray-900 bg-gray-50 focus:bg-white" />
            </div>
          </div>

          <div className="pt-2">
            <button type="submit" disabled={loading}
              className="w-full sm:w-auto h-11 px-8 bg-gradient-to-r from-unl-red to-red-700 hover:from-red-700 hover:to-unl-red text-white font-bold rounded-xl transition-all duration-300 flex items-center justify-center gap-2 disabled:opacity-50 shadow-md hover:shadow-lg text-sm">
              {loading ? <Loader2 size={18} className="animate-spin" /> : <><Save size={16} /> Guardar Cambios</>}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
