import { useState, useEffect } from 'react'
import api from '../../api/axios'
import DataTable from '../../components/DataTable'
import MaintenanceBanner from '../../components/MaintenanceBanner'
import { ClipboardList, FileText, FileSpreadsheet, Download } from 'lucide-react'
import GenerarReporteModal from './GenerarReporteModal'
import { useAuth } from '../../contexts/AuthContext'

export default function ReportesList() {
  const { user } = useAuth()
  const puedeGenerar = user?.rol === 'ADMIN' || user?.rol === 'DOCENTE'

  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)
  const [serviceDown, setServiceDown] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [descargando, setDescargando] = useState(null)

  const load = () => {
    setLoading(true)
    setServiceDown(false)
    api.get('/reportes/reportes/').then(({ data: res }) => setData(res.results || res)).catch((err) => {
      if (!err.response || err.response.status >= 500) setServiceDown(true)
    }).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const handleDescargar = async (row) => {
    setDescargando(row.id)
    try {
      const res = await api.get(`/reportes/reportes/${row.id}/descargar/`, { responseType: 'blob' })
      const ext = row.formato === 'PDF' ? 'pdf' : 'xlsx'
      const url = window.URL.createObjectURL(new Blob([res.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `${row.nombre}.${ext}`)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (err) {
      alert(err.response?.data?.error || 'No se pudo descargar el reporte.')
    } finally {
      setDescargando(null)
    }
  }

  const columns = [
    { key: 'nombre', label: 'Nombre' },
    { key: 'tipo_display', label: 'Tipo' },
    { key: 'formato_display', label: 'Formato', render: (v) => (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-full bg-gray-100">
        {v === 'PDF' ? <FileText size={14} className="text-red-500" /> : <FileSpreadsheet size={14} className="text-green-600" />}
        {v}
      </span>
    )},
    { key: 'fecha_generacion', label: 'Generado', render: (v) => new Date(v).toLocaleString('es-EC', { dateStyle: 'short', timeStyle: 'short' }) },
    { key: 'generado_por_nombre', label: 'Generado por' },
    { key: 'id', label: 'Descargar', render: (_, row) => (
      <button
        onClick={() => handleDescargar(row)}
        disabled={descargando === row.id}
        className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-unl-red hover:bg-unl-red/10 rounded-lg transition-colors disabled:opacity-50"
      >
        {descargando === row.id
          ? <div className="w-3.5 h-3.5 border-2 border-unl-red border-t-transparent rounded-full animate-spin" />
          : <Download size={14} />}
        Descargar
      </button>
    )},
  ]

  return (
    <div className="space-y-5">
      {serviceDown && <MaintenanceBanner service="reportes" />}
      <div className="flex items-center gap-4">
        <div className="w-10 h-10 rounded-2xl bg-unl-black/10 flex items-center justify-center">
          <ClipboardList size={20} className="text-unl-black" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-unl-black">Reportes Generados</h2>
          <p className="text-sm text-gray-500">Visualizar y generar reportes académicos</p>
        </div>
      </div>
      <DataTable title="Reportes" columns={columns} data={data} loading={loading} searchable={false}
        onAdd={puedeGenerar ? () => setModalOpen(true) : undefined}
      />
      {puedeGenerar && (
        <GenerarReporteModal open={modalOpen} onClose={() => setModalOpen(false)} onGenerated={load} />
      )}
    </div>
  )
}