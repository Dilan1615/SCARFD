/**
 * Tarjeta genérica de métrica: título, valor, unidad e icono.
 * Si se pasa `umbral`, colorea el valor en ámbar/rojo al superarlo (útil
 * para CPU/RAM/disco). Si se pasa `barra`, dibuja una barra de progreso.
 */
export default function MetricCard({
  titulo,
  valor,
  unidad = '',
  icono: Icono,
  umbralAdvertencia,
  umbralCritico,
  barra = false,
  descripcion,
}) {
  const numerico = typeof valor === 'number' ? valor : parseFloat(valor)
  const esPorcentaje = barra && !Number.isNaN(numerico)

  let colorValor = 'text-slate-900'
  let colorBarra = 'bg-blue-500'
  if (esPorcentaje && umbralCritico != null && numerico >= umbralCritico) {
    colorValor = 'text-red-600'
    colorBarra = 'bg-red-500'
  } else if (esPorcentaje && umbralAdvertencia != null && numerico >= umbralAdvertencia) {
    colorValor = 'text-amber-600'
    colorBarra = 'bg-amber-500'
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-slate-500">{titulo}</p>
        {Icono && <Icono className="h-4 w-4 text-slate-400" />}
      </div>

      <p className={`mt-2 text-2xl font-semibold ${colorValor}`}>
        {valor === null || valor === undefined ? '—' : valor}
        {unidad && <span className="ml-1 text-base font-normal text-slate-400">{unidad}</span>}
      </p>

      {esPorcentaje && (
        <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
          <div
            className={`h-full rounded-full ${colorBarra} transition-all`}
            style={{ width: `${Math.min(100, Math.max(0, numerico))}%` }}
          />
        </div>
      )}

      {descripcion && <p className="mt-2 text-xs text-slate-400">{descripcion}</p>}
    </div>
  )
}
