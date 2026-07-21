import { useState, useEffect } from 'react'
import { X, Shield, ShieldAlert, ShieldCheck } from 'lucide-react'

export default function FormModal({ open, onClose, title, fields, initialData, onSubmit, loading, emptyMessage }) {
  const [form, setForm] = useState({})
  const [errors, setErrors] = useState({})

  useEffect(() => {
    if (open) {
      setForm(initialData || {})
      setErrors({})
    }
  }, [open, initialData])

  const getFieldLabel = (field) => field?.label || 'Este campo'

  const validateField = (field, rawValue) => {
    const label = getFieldLabel(field)
    const value = rawValue ?? ''
    const textValue = typeof value === 'string' ? value.trim() : String(value)

    const isEmpty = value === '' || value === null || value === undefined || (field?.type === 'file' && !value)

    if (field?.required && isEmpty) {
      if (field.type === 'select') return `Seleccione una opción para ${label}.`
      if (field.type === 'file') return `Adjunte un archivo para ${label}.`
      return `El campo ${label} es obligatorio.`
    }

    if (isEmpty) return ''

    if (field?.numeric && !/^\d+$/.test(textValue)) {
      return `El campo ${label} solo admite números.`
    }

    if (field?.type === 'email') {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
      if (!emailRegex.test(textValue)) {
        return `Ingrese un correo electrónico válido para ${label}.`
      }
    }

    if (field?.type === 'number') {
      const numericValue = Number(textValue)
      if (!Number.isFinite(numericValue)) {
        return `El campo ${label} debe ser un número válido.`
      }
      if (field.min !== undefined && numericValue < Number(field.min)) {
        return `El campo ${label} debe ser mayor o igual a ${field.min}.`
      }
      if (field.max !== undefined && numericValue > Number(field.max)) {
        return `El campo ${label} debe ser menor o igual a ${field.max}.`
      }
    }

    if (field?.type === 'date' && Number.isNaN(Date.parse(textValue))) {
      return `Seleccione una fecha válida para ${label}.`
    }

    if (field?.type === 'time' && !/^\d{2}:\d{2}(:\d{2})?$/.test(textValue)) {
      return `Seleccione una hora válida para ${label}.`
    }

    if (field?.type === 'password') {
      if (textValue.length < 8) {
        return `La contraseña debe tener al menos 8 caracteres.`
      }
      if (!/[A-Z]/.test(textValue)) {
        return `La contraseña debe incluir al menos una letra mayúscula.`
      }
      if (!/[0-9]/.test(textValue)) {
        return `La contraseña debe incluir al menos un número.`
      }
      if (!/[^A-Za-z0-9]/.test(textValue)) {
        return `La contraseña debe incluir al menos un símbolo.`
      }
    }

    if (field?.minLength !== undefined && textValue.length < Number(field.minLength)) {
      return `El campo ${label} debe tener al menos ${field.minLength} caracteres.`
    }

    if (field?.maxLength !== undefined && textValue.length > Number(field.maxLength)) {
      return `El campo ${label} no puede superar ${field.maxLength} caracteres.`
    }

    return ''
  }

  const validateForm = () => {
    const nextErrors = {}

    fields.forEach((field) => {
      const error = validateField(field, form[field.key])
      if (error) nextErrors[field.key] = error
    })

    setErrors(nextErrors)
    return Object.keys(nextErrors).length === 0
  }

  const handleChange = (key, value, field) => {
    if (field?.type === 'file') {
      setForm((prev) => ({ ...prev, [key]: value }))
      setErrors((prev) => {
        const next = { ...prev }
        delete next[key]
        return next
      })
      return
    }
    if (field?.numeric) {
      value = value.replace(/\D/g, '')
    }
    setForm((prev) => ({ ...prev, [key]: value }))
    setErrors((prev) => {
      const next = { ...prev }
      delete next[key]
      return next
    })
  }

  const handleBlur = (field) => {
    const error = validateField(field, form[field.key])
    setErrors((prev) => ({ ...prev, [field.key]: error }))
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!validateForm()) return
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

        <form onSubmit={handleSubmit} noValidate className="px-6 py-5 space-y-4">

          {emptyMessage && (
            <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-700 text-center">
              {emptyMessage}
            </div>
          )}

          {fields.map((field) => (
              <div key={field.key}>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                {field.label} {field.required && <span className="text-unl-red">*</span>}
              </label>
              {field.type === 'select' ? (
                <select
                  value={form[field.key] ?? ''}
                  onChange={(e) => handleChange(field.key, e.target.value, field)}
                  onBlur={() => handleBlur(field)}
                  aria-invalid={Boolean(errors[field.key])}
                  className={`w-full px-3.5 py-2.5 border rounded-xl focus:ring-2 outline-none text-sm bg-gray-50 focus:bg-white transition-all ${errors[field.key] ? 'border-red-300 focus:ring-red-500/20 focus:border-red-500' : 'border-gray-200 focus:ring-unl-red/20 focus:border-unl-red'}`}
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
                  onBlur={() => handleBlur(field)}
                  aria-invalid={Boolean(errors[field.key])}
                  className={`w-full px-3.5 py-2.5 border rounded-xl focus:ring-2 outline-none text-sm bg-gray-50 focus:bg-white transition-all resize-none ${errors[field.key] ? 'border-red-300 focus:ring-red-500/20 focus:border-red-500' : 'border-gray-200 focus:ring-unl-red/20 focus:border-unl-red'}`}
                  rows={3}
                />
              ) : field.type === 'file' ? (
                <input
                  type="file"
                  accept={field.accept || 'image/*'}
                  onChange={(e) => handleChange(field.key, e.target.files[0], field)}
                  onBlur={() => handleBlur(field)}
                  aria-invalid={Boolean(errors[field.key])}
                  className="w-full text-sm text-gray-500 file:mr-3 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-sm file:font-medium file:bg-unl-red/10 file:text-unl-red hover:file:bg-unl-red/20 transition-all cursor-pointer"
                />
              ) : (
                <input
                  type={field.type || 'text'}
                  value={form[field.key] ?? ''}
                  onChange={(e) => handleChange(field.key, e.target.value, field)}
                  onBlur={() => handleBlur(field)}
                  aria-invalid={Boolean(errors[field.key])}
                  className={`w-full px-3.5 py-2.5 border rounded-xl focus:ring-2 outline-none text-sm bg-gray-50 focus:bg-white transition-all ${errors[field.key] ? 'border-red-300 focus:ring-red-500/20 focus:border-red-500' : 'border-gray-200 focus:ring-unl-red/20 focus:border-unl-red'}`}
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
              {errors[field.key] && (
                <p className="text-xs text-red-600 mt-1.5">{errors[field.key]}</p>
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
              disabled={loading || Boolean(emptyMessage)}
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
