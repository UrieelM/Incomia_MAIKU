import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  Legend
} from 'recharts';
import { Card } from '../../../components/ui/Card';
import type { CashFlowData } from '../../../types';
import { useCurrency } from '../../../hooks/useCurrency';

interface CashFlowChartProps {
  data: CashFlowData[];
  className?: string;
}

/**
 * DASHBOARD COMPONENT - GRÁFICA DE INGRESOS (REAL VS SUAVIZADO)
 * 
 * Este componente es el núcleo visual de Incomia. 
 * Muestra la volatilidad de los ingresos reales frente a la estabilidad 
 * que proporciona el servicio de suavizado.
 */
export function CashFlowChart({ data, className }: CashFlowChartProps) {
  const { format } = useCurrency();

  return (
    <Card className={className}>
      <div className="flex justify-between items-center mb-8">
        <div>
          <h4 className="font-display font-bold text-primary dark:text-white italic">Estabilización de Ingresos</h4>
          <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest italic mt-1">Ingreso Real vs. Salario Incomia</p>
        </div>
        <div className="flex gap-4">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-slate-200 dark:bg-slate-700" />
            <span className="text-[10px] uppercase tracking-widest font-bold text-slate-400 italic">Freelance (Volátil)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-emerald-500" />
            <span className="text-[10px] uppercase tracking-widest font-bold text-emerald-500 italic">Incomia (Estable)</span>
          </div>
        </div>
      </div>

      <div className="h-[300px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="colorReal" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#94a3b8" stopOpacity={0.1}/>
                <stop offset="95%" stopColor="#94a3b8" stopOpacity={0}/>
              </linearGradient>
              <linearGradient id="colorStabilized" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10b981" stopOpacity={0.1}/>
                <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
              </linearGradient>
            </defs>
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
              contentStyle={{ 
                backgroundColor: 'rgba(13, 22, 39, 0.8)',
                borderRadius: '12px', 
                border: 'none', 
                boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)',
                backdropFilter: 'blur(8px)',
                fontStyle: 'italic',
                color: '#fff'
              }}
              itemStyle={{ color: '#fff' }}
              formatter={(value: any) => [format(value), '']}
            />
            <Area 
              type="monotone" 
              dataKey="real" 
              stroke="#94a3b8" 
              strokeWidth={2}
              strokeDasharray="5 5"
              fillOpacity={1} 
              fill="url(#colorReal)" 
              name="Ingreso Real"
            />
            <Area 
              type="monotone" 
              dataKey="stabilized" 
              stroke="#059669" 
              strokeWidth={3}
              fillOpacity={1} 
              fill="url(#colorStabilized)" 
              name="Incomia Stable"
            />
            <Legend 
              verticalAlign="top" 
              align="right" 
              height={36}
              content={() => null} // We use our custom legend above
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}
