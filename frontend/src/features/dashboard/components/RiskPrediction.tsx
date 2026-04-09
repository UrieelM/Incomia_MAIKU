import { Activity, ShieldCheck, AlertCircle } from 'lucide-react';
import { Card } from '../../../components/ui/Card';
import type { LiquidityPrediction } from '../../../types';
import { cn } from '../../../utils/cn';
import { useCurrency } from '../../../hooks/useCurrency';

interface RiskPredictionProps {
  predictions: LiquidityPrediction[];
  className?: string;
}

/**
 * KPI COMPONENT - PREDICCIÓN DE RIESGO DE LIQUIDEZ
 * 
 * Este componente visualiza la probabilidad de solvencia futura
 * y el nivel de riesgo proyectado por los modelos de IA/SageMaker.
 */
export function RiskPrediction({ predictions, className }: RiskPredictionProps) {
  const { format } = useCurrency();
  const latest = predictions[0];

  if (!latest) return null;

  return (
    <Card className={cn("p-8 relative overflow-hidden group border-slate-100 dark:border-white/5", className)}>
      <div className="absolute top-0 right-0 w-32 h-32 bg-slate-50 dark:bg-primary-light rounded-full opacity-50 -mr-10 -mt-10 group-hover:scale-110 transition-transform" />

      <div className="relative z-10 flex flex-col h-full">
        <div className="flex justify-between items-start mb-6">
          <div>
            <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest italic mb-1">Score de Estabilidad IA</p>
            <h3 className="text-4xl font-display font-bold text-primary dark:text-white italic">{latest.probability}%</h3>
          </div>
          <div className={cn(
            "w-12 h-12 rounded-2xl flex items-center justify-center italic",
            latest.riskLevel === 'low' ? "bg-emerald-50 dark:bg-emerald-500/20 text-emerald-500 dark:text-emerald-400" :
              latest.riskLevel === 'medium' ? "bg-amber-50 dark:bg-amber-500/20 text-amber-500 dark:text-amber-400" :
                "bg-red-50 dark:bg-red-500/20 text-red-500 dark:text-red-400"
          )}>
            {latest.riskLevel === 'low' ? <ShieldCheck size={24} /> :
              latest.riskLevel === 'medium' ? <Activity size={24} /> :
                <AlertCircle size={24} />}
          </div>
        </div>

        <div className="space-y-6 mt-auto">
          <div>
            <div className="flex justify-between text-[10px] font-bold uppercase tracking-widest text-slate-400 italic mb-2">
              <span>Riesgo Proyectado</span>
              <span className={cn(
                "font-bold",
                latest.riskLevel === 'low' ? "text-emerald-600 dark:text-emerald-400" :
                  latest.riskLevel === 'medium' ? "text-amber-600 dark:text-amber-400" :
                    "text-red-600 dark:text-red-400"
              )}>
                {latest.riskLevel === 'low' ? 'Bajo - Solvente' :
                  latest.riskLevel === 'medium' ? 'Medio - Precaución' :
                    'Alto - Crítico'}
              </span>
            </div>
            <div className="h-2 bg-slate-100 dark:bg-white/10 rounded-full overflow-hidden">
              <div
                className={cn(
                  "h-full rounded-full transition-all duration-1000 ease-out",
                  latest.riskLevel === 'low' ? "bg-emerald-500" :
                    latest.riskLevel === 'medium' ? "bg-amber-500" :
                      "bg-red-500"
                )}
                style={{ width: `${latest.probability}%` }}
              />
            </div>
          </div>

          <div className="flex items-center justify-between p-4 bg-slate-50 dark:bg-white/5 rounded-2xl italic">
            <div className="flex flex-col">
              <span className="text-[10px] text-slate-400 font-bold uppercase italic">Balance Proyectado</span>
              <span className="text-sm font-bold text-primary dark:text-white italic">{format(latest.expectedBalance)}</span>
            </div>
            <div className="text-right">
              <span className="text-[10px] text-slate-400 font-bold uppercase italic">Próxima Alerta</span>
              <span className="block text-[10px] font-bold text-slate-600 dark:text-slate-400 italic">Dic 30, 2026</span>
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
}
