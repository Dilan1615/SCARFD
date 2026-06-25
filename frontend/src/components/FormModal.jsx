import { useState, useEffect } from 'react'
import { X } from 'lucide-react'

export default function FormModal({ open, onClose, title, fields, initialData, onSubmit, loading }) {
  const [form, setForm] = useState({})

  useEffect(() => {
    if (open) {
      setForm(initialData || {})
    }
  }, [open, initialData])

  const handleChange = (key, value, field) => {
    if (field?.type === 'file') {
      setForm((prev) => ({ ...prev, [key]: value }))
      return
    }
    if (field?.numeric) {
      value = value.replace(/\D/g, '')
    }
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    onSubmit(form)
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="fixed inset-0 bg-black/40 backdrop-blur-sm animate-fade-in" onClick={onClose} />
      <div className="relative bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto animate-scale-in">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <h3 className="text-lg font-bold text-unl-black">{title}</h3>
          <button
            onClick={onClose}
            className="p-1.5 text-gray-400 hover:text-unl-red hover:bg-unl-red/5 rounded-xl transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="px-6 py-5 space-y-4">
          {fields.map((field) => (
              <div key={field.key}>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                {field.label} {field.required && <span className="text-unl-red">*</span>}
              </label>
              {field.type === 'select' ? (
                <select
                  value={form[field.key] ?? ''}
                  onChange={(e) => handleChange(field.key, e.target.value, field)}
                  className="w-full px-3.5 py-2.5 border border-gray-200 rounded-xl focus:ring-2 focus:ring-unl-red/20 focus:border-unl-red outline-none text-sm bg-gray-50 focus:bg-white transition-all"
                  required={field.required}
                >
                  <option value="">Seleccionar...</option>
                  {field.options?.map((opt) => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              ) : field.type === 'textarea' ? (
                <textarea
                  value={form[field.key] ?? ''}
                  onChange={(e) => handleChange(field.key, e.target.value, field)}
                  className="w-full px-3.5 py-2.5 border border-gray-200 rounded-xl focus:ring-2 focus:ring-unl-red/20 focus:border-unl-red outline-none text-sm bg-gray-50 focus:bg-white transition-all resize-none"
                  rows={3}
                  required={field.required}
                />
              ) : field.type === 'file' ? (
                <input
                  type="file"
                  accept={field.accept || 'image/*'}
                  onChange={(e) => handleChange(field.key, e.target.files[0], field)}
                  className="w-full text-sm text-gray-500 file:mr-3 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-sm file:font-medium file:bg-unl-red/10 file:text-unl-red hover:file:bg-unl-red/20 transition-all cursor-pointer"
                />
              ) : (
                <input
                  type={field.type || 'text'}
                  value={form[field.key] ?? ''}
                  onChange={(e) => handleChange(field.key, e.target.value, field)}
                  className="w-full px-3.5 py-2.5 border border-gray-200 rounded-xl focus:ring-2 focus:ring-unl-red/20 focus:border-unl-red outline-none text-sm bg-gray-50 focus:bg-white transition-all"
                  required={field.required}
                  step={field.step}
                  min={field.min}
                  max={field.max}
                  inputMode={field.numeric ? 'numeric' : undefined}
                  maxLength={field.maxLength}
                />
              )}
              {field.hint && (
                <p className="text-xs text-gray-400 mt-1">{field.hint}</p>
              )}
            </div>
          ))}

          <div className="flex justify-end gap-3 pt-4 border-t border-gray-100">
            <button
              type="button"
              onClick={onClose}
              className="px-5 py-2.5 text-sm font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-xl transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-5 py-2.5 text-sm font-medium text-white bg-unl-red hover:bg-unl-red-dark rounded-xl transition-all disabled:opacity-50 flex items-center gap-2 shadow-sm hover:shadow-md hover:-translate-y-0.5 active:translate-y-0"
            >
              {loading && <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />}
              {loading ? 'Guardando...' : 'Guardar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
