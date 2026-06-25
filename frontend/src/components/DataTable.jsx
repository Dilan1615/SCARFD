import { useState } from 'react'
import { Search, ChevronLeft, ChevronRight, Plus, Pencil, Trash2, FileSearch } from 'lucide-react'

export default function DataTable({ columns, data, onAdd, onEdit, onDelete, title, loading, searchable = true }) {
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const perPage = 10

  const filtered = searchable && search
    ? data.filter((row) =>
        columns.some((col) =>
          String(row[col.key] || '').toLowerCase().includes(search.toLowerCase())
        )
      )
    : data

  const totalPages = Math.ceil(filtered.length / perPage) || 1
  const paginated = filtered.slice((page - 1) * perPage, page * perPage)

  if (loading) {
    return (
      <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-center h-48">
          <div className="w-8 h-8 border-2 border-unl-red border-t-transparent rounded-full animate-spin" />
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
      <div className="p-5 border-b border-gray-100">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <h2 className="text-lg font-bold text-unl-black">{title}</h2>
          {onAdd && (
            <button
              onClick={onAdd}
              className="inline-flex items-center gap-2 bg-unl-red hover:bg-unl-red-dark text-white px-4 py-2.5 rounded-xl transition-all text-sm font-medium shadow-sm hover:shadow-md hover:-translate-y-0.5 active:translate-y-0"
            >
              <Plus size={16} /> Nuevo
            </button>
          )}
        </div>
        {searchable && (
          <div className="relative mt-4">
            <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Buscar..."
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1) }}
              className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-xl focus:ring-2 focus:ring-unl-red/20 focus:border-unl-red outline-none text-sm bg-gray-50 focus:bg-white transition-all"
            />
          </div>
        )}
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-unl-black">
              {columns.map((col) => (
                <th key={col.key} className="px-5 py-3.5 text-left text-xs font-semibold text-white/80 uppercase tracking-wider whitespace-nowrap">
                  {col.label}
                </th>
              ))}
              {(onEdit || onDelete) && (
                <th className="px-5 py-3.5 text-right text-xs font-semibold text-white/80 uppercase tracking-wider whitespace-nowrap w-24">
                  Acciones
                </th>
              )}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {paginated.length === 0 ? (
              <tr>
                <td colSpan={(onEdit || onDelete ? columns.length + 1 : columns.length)} className="px-5 py-20 text-center text-gray-400">
                  <div className="flex flex-col items-center gap-3">
                    <div className="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center">
                      <FileSearch size={24} className="text-gray-300" />
                    </div>
                    <span className="font-medium">No se encontraron registros</span>
                  </div>
                </td>
              </tr>
            ) : (
              paginated.map((row, idx) => (
                <tr
                  key={row.id || idx}
                  className="hover:bg-unl-red/[0.02] transition-colors group"
                >
                  {columns.map((col) => (
                    <td key={col.key} className="px-5 py-3 text-sm text-gray-700">
                      {col.render ? col.render(row[col.key], row) : row[col.key] ?? '-'}
                    </td>
                  ))}
                  {(onEdit || onDelete) && (
                    <td className="px-5 py-3">
                      <div className="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        {onEdit && (
                          <button
                            onClick={() => onEdit(row)}
                            className="p-2 text-gray-400 hover:text-unl-green hover:bg-unl-green/10 rounded-lg transition-all"
                            title="Editar"
                          >
                            <Pencil size={15} />
                          </button>
                        )}
                        {onDelete && (
                          <button
                            onClick={() => onDelete(row)}
                            className="p-2 text-gray-400 hover:text-unl-red hover:bg-unl-red/10 rounded-lg transition-all"
                            title="Eliminar"
                          >
                            <Trash2 size={15} />
                          </button>
                        )}
                      </div>
                    </td>
                  )}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between px-5 py-3 border-t border-gray-100 bg-gray-50/50">
          <span className="text-sm text-gray-500">
            <span className="hidden sm:inline">Mostrando </span>
            {(page - 1) * perPage + 1}-{Math.min(page * perPage, filtered.length)} de {filtered.length}
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page === 1}
              className="p-2 text-gray-600 hover:bg-unl-red/10 rounded-xl disabled:opacity-30 disabled:hover:bg-transparent transition-colors"
            >
              <ChevronLeft size={16} />
            </button>
            <div className="flex items-center gap-1">
              {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
                let pageNum
                if (totalPages <= 5) {
                  pageNum = i + 1
                } else if (page <= 3) {
                  pageNum = i + 1
                } else if (page >= totalPages - 2) {
                  pageNum = totalPages - 4 + i
                } else {
                  pageNum = page - 2 + i
                }
                return (
                  <button
                    key={pageNum}
                    onClick={() => setPage(pageNum)}
                    className={`w-8 h-8 text-sm rounded-xl transition-all ${
                      page === pageNum
                        ? 'bg-unl-red text-white font-bold shadow-sm shadow-unl-red/20'
                        : 'text-gray-600 hover:bg-gray-100'
                    }`}
                  >
                    {pageNum}
                  </button>
                )
              })}
            </div>
            <button
              onClick={() => setPage(Math.min(totalPages, page + 1))}
              disabled={page === totalPages}
              className="p-2 text-gray-600 hover:bg-unl-red/10 rounded-xl disabled:opacity-30 disabled:hover:bg-transparent transition-colors"
            >
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
