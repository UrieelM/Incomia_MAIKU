import { Sparkles, TrendingUp, AlertCircle, Lightbulb } from 'lucide-react';
import { Card } from '../../../components/ui/Card';
import type { FinancialAdvice as AdviceType } from '../../../types';
import { cn } from '../../../utils/cn';

interface FinancialAdviceProps {
  advice: AdviceType[];
  className?: string;
}

/**
 * FINANCIAL ADVICE COMPONENT - PREPARADO PARA AMAZON BEDROCK
 * 
 * Este componente renderiza recomendaciones generadas por IA.
 * Está diseñado para ser extensible para streaming de datos de LLMs.
 */
export function FinancialAdvice({ advice, className }: FinancialAdviceProps) {
  return (
    <div className={cn("space-y-4", className)}>
      <div className="flex items-center gap-2 mb-2">
        <Sparkles className="text-emerald-500" size={20} />
        <h3 className="font-display font-bold text-primary dark:text-white italic">Recomendaciones de IA Incomia</h3>
      </div>
      
      <div className="grid grid-cols-1 gap-4">
        {advice.map((item) => (
          <Card 
            key={item.id} 
            className={cn(
              "p-5 border-l-4 transition-all hover:translate-x-1",
              item.type === 'opportunity' ? "border-emerald-500 bg-emerald-50/30 dark:bg-emerald-950/10" : 
              item.type === 'warning' ? "border-amber-500 bg-amber-50/30 dark:bg-amber-950/10" : 
              "border-blue-500 bg-blue-50/30 dark:bg-blue-950/10"
            )}
          >
            <div className="flex gap-4">
              <div className={cn(
                "w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0",
                item.type === 'opportunity' ? "bg-emerald-100 dark:bg-emerald-500/20 text-emerald-600 dark:text-emerald-400" : 
                item.type === 'warning' ? "bg-amber-100 dark:bg-amber-500/20 text-amber-600 dark:text-amber-400" : 
                "bg-blue-100 dark:bg-blue-500/20 text-blue-600 dark:text-blue-400"
              )}>
                {item.type === 'opportunity' && <TrendingUp size={20} />}
                {item.type === 'warning' && <AlertCircle size={20} />}
                {item.type === 'saving' && <Lightbulb size={20} />}
              </div>
              
              <div className="space-y-1">
                <div className="flex items-center justify-between gap-2">
                  <h4 className="font-bold text-primary dark:text-white text-sm">{item.title}</h4>
                  <span className="text-[10px] font-bold text-slate-400 uppercase">{item.date}</span>
                </div>
                <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed italic">
                  {item.content}
                </p>
                {item.impact && (
                  <div className="pt-2">
                    <span className="text-[10px] font-bold text-emerald-600 dark:text-emerald-400 bg-emerald-100 dark:bg-emerald-500/20 px-2 py-0.5 rounded-full uppercase italic">
                      Impacto: {item.impact}
                    </span>
                  </div>
                )}
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
