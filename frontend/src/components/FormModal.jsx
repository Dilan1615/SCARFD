import { useState, useEffect, useMemo } from 'react'
import { X, Shield, ShieldAlert, ShieldCheck } from 'lucide-react'

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

  const getPasswordStrength = (password) => {
    let score = 0
    if (password.length >= 8) score += 25
    if (password.length >= 12) score += 10
    if (/[A-Z]/.test(password)) score += 20
    if (/[0-9]/.test(password)) score += 20
    if (/[^A-Za-z0-9]/.test(password)) score += 25
    return Math.min(score, 100)
  }

  const strengthLabel = (score) => {
    if (score < 25) return { label: 'Muy débil', color: 'bg-red-500', text: 'text-red-600', icon: ShieldAlert }
    if (score < 50) return { label: 'Débil', color: 'bg-orange-500', text: 'text-orange-600', icon: ShieldAlert }
    if (score < 75) return { label: 'Media', color: 'bg-yellow-500', text: 'text-yellow-600', icon: Shield }
    return { label: 'Segura', color: 'bg-green-500', text: 'text-green-600', icon: ShieldCheck }
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
              {field.key === 'password' && form[field.key] && (() => {
                const score = getPasswordStrength(form[field.key])
                const { label, color, text, icon: Icon } = strengthLabel(score)
                return (
                  <div className="mt-2 space-y-1">
                    <div className="flex gap-1">
                      {[1,2,3,4].map((i) => (
                        <div
                          key={i}
                          className={`h-1.5 flex-1 rounded-full transition-all duration-300 ${
                            score >= i * 25 ? color : 'bg-gray-200'
                          }`}
                        />
                      ))}
                    </div>
                    <div className={`flex items-center gap-1 text-xs ${text}`}>
                      <Icon size={12} />
                      <span>{label}</span>
                    </div>
                  </div>
                )
              })()}
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
