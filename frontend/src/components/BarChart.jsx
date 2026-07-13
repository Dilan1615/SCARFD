import {
  BarChart as ReBarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts'

const COLORES = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444']

/**
 * Gráfico de barras genérico, usado para "peticiones por microservicio".
 * @param {{ titulo: string, datos: {servicio:string, peticiones_por_minuto:number}[], unidad?: string }} props
 */
export default function BarChart({ titulo, datos = [], unidad = '' }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <p className="mb-3 text-sm font-medium text-slate-500">{titulo}</p>

      {datos.length === 0 ? (
        <div className="flex h-56 items-center justify-center text-sm text-slate-400">
          Sin datos suficientes todavía
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={224}>
          <ReBarChart data={datos} margin={{ top: 5, right: 10, bottom: 0, left: -10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
            <XAxis
              dataKey="servicio"
              tick={{ fontSize: 11, fill: '#94a3b8' }}
              axisLine={{ stroke: '#e2e8f0' }}
              tickLine={false}
            />
            <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
            <Tooltip
              formatter={(value) => [`${value}${unidad}`, titulo]}
              contentStyle={{ fontSize: 12, borderRadius: 8, borderColor: '#e2e8f0' }}
            />
            <Bar dataKey="peticiones_por_minuto" radius={[6, 6, 0, 0]}>
              {datos.map((_, i) => (
                <Cell key={i} fill={COLORES[i % COLORES.length]} />
              ))}
            </Bar>
          </ReBarChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}
