import {
  LineChart as ReLineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'

const formatearHora = (ts) =>
  new Date(ts * 1000).toLocaleTimeString('es-EC', { hour: '2-digit', minute: '2-digit' })

/**
 * Gráfico de línea genérico para series temporales de Prometheus.
 * @param {{ titulo: string, datos: {timestamp:number, valor:number}[], color?: string, unidad?: string }} props
 */
export default function LineChart({ titulo, datos = [], color = '#3b82f6', unidad = '' }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <p className="mb-3 text-sm font-medium text-slate-500">{titulo}</p>

      {datos.length === 0 ? (
        <div className="flex h-56 items-center justify-center text-sm text-slate-400">
          Sin datos suficientes todavía
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={224}>
          <ReLineChart data={datos} margin={{ top: 5, right: 10, bottom: 0, left: -10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis
              dataKey="timestamp"
              tickFormatter={formatearHora}
              tick={{ fontSize: 11, fill: '#94a3b8' }}
              axisLine={{ stroke: '#e2e8f0' }}
              tickLine={false}
            />
            <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
            <Tooltip
              labelFormatter={formatearHora}
              formatter={(value) => [`${value}${unidad}`, titulo]}
              contentStyle={{ fontSize: 12, borderRadius: 8, borderColor: '#e2e8f0' }}
            />
            <Line
              type="monotone"
              dataKey="valor"
              stroke={color}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
            />
          </ReLineChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}
