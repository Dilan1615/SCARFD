import { useState, useEffect } from 'react'
import api from '../../api/axios'
import { X } from 'lucide-react'

const TIPOS = [
  { value: 'POR_ESTUDIANTE', label: 'Por Estudiante' },
  { value: 'POR_MATERIA', label: 'Por Materia' },
  { value: 'POR_CICLO', label: 'Por Ciclo' },
  { value: 'GENERAL', label: 'General' },
]
const FORMATOS = [
  { value: 'PDF', label: 'PDF' },
  { value: 'EXCEL', label: 'Excel' },
]

export default function GenerarReporteModal({ open, onClose, onGenerated }) {
  const [tipo, setTipo] = useState('POR_ESTUDIANTE')
  const [formato, setFormato] = useState('PDF')
  const [estudiantes, setEstudiantes] = useState([])
  const [materias, setMaterias] = useState([])
  const [ciclos, setCiclos] = useState([])
  const [form, setForm] = useState({})
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!open) return
    setForm({})
    setError('')
    api.get('/usuario/usuarios/', { params: { rol: 'ESTUDIANTE' } })
      .then(r => setEstudiantes(r.data.results || r.data)).catch(() => {})
    api.get('/academico/materias/')
      .then(r => setMaterias(r.data.results || r.data)).catch(() => {})
    api.get('/academico/ciclos/')
      .then(r => setCiclos(r.data.results || r.data)).catch(() => {})
  }, [open])

  const descargarArchivo = async (reporteId, nombre, ext) => {
    const res = await api.get(`/reportes/reportes/${reporteId}/descargar/`, { responseType: 'blob' })
    const url = window.URL.createObjectURL(new Blob([res.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `${nombre}.${ext}`)
    document.body.appendChild(link)
    link.click()
    link.remove()
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    if (tipo === 'POR_ESTUDIANTE' && !form.estudiante_id) return setError('Selecciona un estudiante.')
    if (tipo === 'POR_MATERIA' && !form.materia_id) return setError('Selecciona una materia.')
    if (tipo === 'POR_CICLO' && !form.ciclo_id) return setError('Selecciona un ciclo.')

    setLoading(true)
    try {
      const payload = { tipo, formato }
      Object.entries(form).forEach(([key, value]) => {
        if (value !== '' && value !== undefined && value !== null) {
          payload[key] = value
        }
      })
      const { data } = await api.post('/reportes/reportes/generar/', payload)
      await descargarArchivo(data.reporte_id, data.nombre, formato === 'PDF' ? 'pdf' : 'xlsx')
      onGenerated?.()
      onClose()
    } catch (err) {
      setError(err.response?.data?.error || 'No se pudo generar el reporte.')
    } finally {
      setLoading(false)
    }
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="fixed inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-white rounded-2xl shadow-xl w-full max-w-md max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <h3 className="text-lg font-bold text-unl-black">Generar Reporte</h3>
          <button onClick={onClose} className="p-1.5 text-gray-400 hover:text-unl-red hover:bg-unl-red/5 rounded-xl transition-colors">
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="px-6 py-5 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Tipo de reporte</label>
            <select value={tipo} onChange={(e) => { setTipo(e.target.value); setForm({}) }}
              className="w-full px-3.5 py-2.5 border border-gray-200 rounded-xl bg-gray-50 focus:bg-white text-sm outline-none focus:ring-2 focus:ring-unl-red/20">
              {TIPOS.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Formato</label>
            <select value={formato} onChange={(e) => setFormato(e.target.value)}
              className="w-full px-3.5 py-2.5 border border-gray-200 rounded-xl bg-gray-50 focus:bg-white text-sm outline-none focus:ring-2 focus:ring-unl-red/20">
              {FORMATOS.map(f => <option key={f.value} value={f.value}>{f.label}</option>)}
            </select>
          </div>

          {tipo === 'POR_ESTUDIANTE' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Estudiante</label>
              <select value={form.estudiante_id || ''} onChange={(e) => setForm({ ...form, estudiante_id: e.target.value })}
                className="w-full px-3.5 py-2.5 border border-gray-200 rounded-xl bg-gray-50 text-sm outline-none focus:ring-2 focus:ring-unl-red/20">
                <option value="">Seleccionar...</option>
                {estudiantes.map(e => <option key={e.id} value={e.id}>{e.first_name} {e.last_name}</option>)}
              </select>
            </div>
          )}

          {tipo === 'POR_MATERIA' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Materia</label>
              <select value={form.materia_id || ''} onChange={(e) => setForm({ ...form, materia_id: e.target.value })}
                className="w-full px-3.5 py-2.5 border border-gray-200 rounded-xl bg-gray-50 text-sm outline-none focus:ring-2 focus:ring-unl-red/20">
                <option value="">Seleccionar...</option>
                {materias.map(m => <option key={m.id} value={m.id}>{m.nombre}</option>)}
              </select>
            </div>
          )}

          {tipo === 'POR_CICLO' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Ciclo</label>
              <select value={form.ciclo_id || ''} onChange={(e) => setForm({ ...form, ciclo_id: e.target.value })}
                className="w-full px-3.5 py-2.5 border border-gray-200 rounded-xl bg-gray-50 text-sm outline-none focus:ring-2 focus:ring-unl-red/20">
                <option value="">Seleccionar...</option>
                {ciclos.map(c => <option key={c.id} value={c.id}>Ciclo {c.num}</option>)}
              </select>
            </div>
          )}

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Desde</label>
              <input type="date" value={form.fecha_desde || ''} onChange={(e) => setForm({ ...form, fecha_desde: e.target.value })}
                className="w-full px-3.5 py-2.5 border border-gray-200 rounded-xl bg-gray-50 text-sm outline-none focus:ring-2 focus:ring-unl-red/20" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Hasta</label>
              <input type="date" value={form.fecha_hasta || ''} onChange={(e) => setForm({ ...form, fecha_hasta: e.target.value })}
                className="w-full px-3.5 py-2.5 border border-gray-200 rounded-xl bg-gray-50 text-sm outline-none focus:ring-2 focus:ring-unl-red/20" />
            </div>
          </div>

          {error && <p className="text-sm text-red-600">{error}</p>}

          <div className="flex justify-end gap-3 pt-4 border-t border-gray-100">
            <button type="button" onClick={onClose} className="px-5 py-2.5 text-sm font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-xl">
              Cancelar
            </button>
            <button type="submit" disabled={loading}
              className="px-5 py-2.5 text-sm font-medium text-white bg-unl-red hover:bg-unl-red-dark rounded-xl disabled:opacity-50 flex items-center gap-2">
              {loading && <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />}
              {loading ? 'Generando...' : 'Generar y descargar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}