import {
  Zap,
  Sparkles,
  BarChart2,
  Activity,
  ShoppingBag
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from 'recharts';
import { useAppStore } from '../store/useAppStore';
import { useCurrency } from '../hooks/useCurrency';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { cn } from '../utils/cn';

export function CashFlowPage() {
  const { cashFlowHistory } = useAppStore();
  const { format } = useCurrency();

  return (
    <div className="space-y-8 animate-in fade-in duration-700">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-2">
          <div className="px-3 py-1 bg-primary dark:bg-emerald-500 text-white text-[10px] font-bold rounded-full uppercase w-fit flex items-center gap-2">
            <Zap size={12} fill="white" />
            IA Insights Activado
          </div>
          <h2 className="text-4xl font-display font-bold text-primary dark:text-white leading-[1.1]">Análisis de Flujo <br /> de Caja Predictivo.</h2>
          <p className="text-slate-500 dark:text-slate-400 max-w-2xl">
            Visualice cómo Incomia estabiliza su volatilidad financiera. Nuestros algoritmos transforman ingresos irregulares en un flujo constante y predecible.
          </p>
        </div>

        <div className="flex items-center gap-8">
          <div className="text-right">
            <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest mb-1">Saldo Estabilizado</p>
            <p className="text-3xl font-display font-bold text-primary dark:text-white">{format(4250)}</p>
          </div>
          <div className="text-right">
            <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest mb-1">Puntuación Salud</p>
            <p className="text-3xl font-display font-bold text-emerald-500">94/100</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Main Comparison Chart */}
        <Card className="lg:col-span-8 p-10 flex flex-col relative overflow-hidden italic border-slate-100 dark:border-white/5">
          <div className="flex justify-between items-start mb-10">
            <div>
              <h4 className="text-xl font-bold text-primary dark:text-white italic">Ingresos Reales vs. Estabilizados</h4>
              <p className="text-xs text-slate-400 italic">Comparativa de los últimos 6 meses</p>
            </div>
            <div className="flex gap-6">
              <div className="flex items-center gap-2">
                <div className="w-2.5 h-2.5 rounded-full bg-slate-100 dark:bg-white/10" />
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-[0.15em] italic">Real (Volátil)</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2.5 h-2.5 rounded-full bg-emerald-700 dark:bg-emerald-500" />
                <span className="text-[10px] font-bold text-emerald-700 dark:text-emerald-400 uppercase tracking-[0.15em] italic">Incomia (Estable)</span>
              </div>
            </div>
          </div>

          <div className="h-[350px] w-full mt-auto italic">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={cashFlowHistory} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" opacity={0.1} />
                <XAxis
                  dataKey="month"
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: '#94a3b8', fontSize: 10, fontWeight: 700, fontStyle: 'italic' }}
                  dy={10}
                />
                <YAxis
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: '#94a3b8', fontSize: 10, fontWeight: 700, fontStyle: 'italic' }}
                />
                <Tooltip
                  cursor={{ fill: 'rgba(255, 255, 255, 0.05)' }}
                  contentStyle={{
                    backgroundColor: 'rgba(13, 22, 39, 0.9)',
                    borderRadius: '12px',
                    border: 'none',
                    boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.5)',
                    backdropFilter: 'blur(8px)',
                    color: '#fff'
                  }}
                  itemStyle={{ color: '#fff' }}
                  formatter={(value: any) => [format(value), '']}
                />
                <Bar dataKey="real" radius={[4, 4, 0, 0]} barSize={28} fill="#f1f5f9" opacity={0.3} />
                <Bar dataKey="stabilized" radius={[4, 4, 0, 0]} barSize={28} fill="#10B981" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Metrics Column */}
        <div className="lg:col-span-4 space-y-6 italic">
          <Card className="bg-primary dark:bg-primary-dark text-white p-8 relative overflow-hidden flex flex-col gap-6 italic border-none shadow-premium">
            <div className="absolute bottom-0 right-0 w-32 h-32 bg-emerald-500/10 rounded-full blur-3xl -mr-10 -mb-10" />
            <div>
              <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest mb-1 italic">Índice de Volatilidad</p>
              <h3 className="text-5xl font-display font-bold italic">12.4%</h3>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed italic">
              Su variabilidad de ingresos se ha reducido en un <span className="text-emerald-400 font-bold italic">68%</span> desde que utiliza Incomia.
            </p>
          </Card>

          <Card className="p-8 space-y-8 flex flex-col justify-center italic border-slate-100 dark:border-white/5">
            <div className="space-y-1">
              <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest italic">Pico de ingreso máximo</p>
              <p className="text-2xl font-display font-bold text-primary dark:text-white italic">{format(7840)}</p>
            </div>

            <div className="space-y-1">
              <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest italic">Déficit Cubierto</p>
              <div className="flex items-center gap-2">
                <p className="text-2xl font-display font-bold text-red-500 italic">-{format(1200)}</p>
                <span className="px-2 py-0.5 bg-red-50 dark:bg-red-500/10 text-[8px] font-bold text-red-500 dark:text-red-400 rounded-full uppercase italic">Reserva utilizada en Marzo</span>
              </div>
            </div>
          </Card>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 italic">
        {/* Income Sources */}
        <Card className="p-8 italic border-slate-100 dark:border-white/5">
          <h4 className="text-xl font-bold text-primary dark:text-white mb-8 italic">Fuentes de Ingresos</h4>
          <div className="space-y-8 italic">
            {[
              { label: 'Freelance Development', sub: 'Contratos por proyecto', amount: 3200, icon: BarChart2, color: 'bg-primary dark:bg-emerald-500' },
              { label: 'UX Consulting', sub: 'Asesorías mensuales', amount: 1850, icon: Activity, color: 'bg-emerald-700 dark:bg-emerald-600' },
              { label: 'Dividendos & Renta', sub: 'Ingresos pasivos', amount: 940, icon: Zap, color: 'bg-slate-900 dark:bg-slate-700' },
            ].map((source, i) => (
              <div key={i} className="flex items-center gap-4 italic group">
                <div className="w-10 h-10 bg-slate-100 dark:bg-white/5 rounded-xl flex items-center justify-center text-primary dark:text-white group-hover:bg-primary dark:group-hover:bg-emerald-500 group-hover:text-white transition-colors italic">
                  <source.icon size={20} />
                </div>
                <div className="flex-1 italic">
                  <p className="text-sm font-bold text-primary dark:text-white italic">{source.label}</p>
                  <p className="text-[10px] text-slate-400 dark:text-slate-500 italic">{source.sub}</p>
                </div>
                <div className="text-right italic">
                  <p className="font-bold text-primary dark:text-white italic">{format(source.amount)}</p>
                  <div className="w-24 h-1.5 bg-slate-100 dark:bg-white/10 rounded-full mt-1 italic">
                    <div className={cn("h-full rounded-full italic", source.color)} style={{ width: `${(source.amount / 6000) * 100}%` }} />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Reserve History */}
        <Card className="p-8 italic border-slate-100 dark:border-white/5">
          <h4 className="text-xl font-bold text-primary dark:text-white mb-8 italic">Histórico de Reserva</h4>
          <div className="space-y-6 italic">
            {[
              { label: 'Aporte Excedente Junio', date: '15 de Junio, 2026', amount: 640.20, type: 'plus' },
              { label: 'Aporte Automático IA', date: '01 de Junio, 2026', amount: 200.00, type: 'plus' },
              { label: 'Retiro por Estabilización', date: '28 de Mayo, 2026', amount: -450.00, type: 'minus' },
            ].map((item, i) => (
              <div key={i} className="flex items-center justify-between pb-6 border-b border-slate-50 dark:border-white/5 last:border-0 italic">
                <div className="flex items-center gap-4 italic">
                  <div className={cn(
                    "w-1 h-8 rounded-full italic",
                    item.type === 'plus' ? "bg-emerald-500" : "bg-red-500"
                  )} />
                  <div>
                    <p className="text-sm font-bold text-primary dark:text-white italic">{item.label}</p>
                    <p className="text-[10px] text-slate-400 dark:text-slate-500 italic">{item.date}</p>
                  </div>
                </div>
                <p className={cn(
                  "font-bold italic",
                  item.type === 'plus' ? "text-emerald-600 dark:text-emerald-400" : "text-red-500"
                )}>
                  {item.type === 'plus' ? '+' : ''}{format(item.amount)}
                </p>
              </div>
            ))}

            <div className="flex justify-between items-center pt-4 italic">
              <p className="text-sm font-bold text-slate-400 italic">Total en Reserva</p>
              <p className="text-2xl font-display font-bold text-primary dark:text-white italic">{format(12450.32)}</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Hero Action Card */}
      <Card className="bg-primary dark:bg-primary-dark text-white p-0 relative overflow-hidden italic group border-none">
        <img
          src="https://images.unsplash.com/photo-1554224155-6726b3ff858f?auto=format&fit=crop&q=80&w=1600"
          className="absolute inset-0 w-full h-full object-cover opacity-10 grayscale italic group-hover:scale-105 transition-transform duration-1000"
          alt="Business background"
        />
        <div className="absolute inset-0 bg-gradient-to-r from-primary via-primary/95 dark:from-primary-dark dark:via-primary-dark/95 to-transparent italic" />

        <div className="relative z-10 p-12 flex flex-col lg:flex-row items-center justify-between gap-12 italic">
          <div className="max-w-xl italic">
            <h3 className="text-3xl font-display font-bold mb-4 italic leading-tight">Optimice su previsión para <br /> el próximo trimestre.</h3>
            <p className="text-slate-400 text-sm italic leading-relaxed">
              Nuestra IA sugiere ajustar su aporte a la reserva un <span className="text-emerald-400 font-bold italic">5% adicional</span> basado en la tendencia de sus contratos Freelance. Esto le permitiría un retiro de bonificación en Diciembre.
            </p>
          </div>

          <div className="flex gap-4 italic flex-shrink-0">
            <Button variant="emerald" className="h-20 w-20 rounded-full flex-col text-[10px] font-bold p-0 italic">
              <Sparkles size={20} className="mb-1 italic" />
              Aplicar <br /> Ajuste <br /> IA
            </Button>
            <Button variant="outline" className="h-20 w-20 rounded-full border-white/20 text-white hover:bg-white hover:text-primary p-0 italic text-[10px] font-bold">
              Ver <br /> Detalles
            </Button>
          </div>
        </div>

        <div className="absolute bottom-4 right-4 bg-white dark:bg-emerald-500 rounded-full p-2 italic">
          <ShoppingBag size={18} className="text-primary dark:text-white italic" />
        </div>
      </Card>
    </div>
  );
}
