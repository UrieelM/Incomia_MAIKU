import { useState, useEffect } from 'react';
import { 
  Sparkles, 
  ShieldCheck, 
  Zap, 
  CheckCircle2,
  Clock,
  ArrowRight
} from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { cn } from '../utils/cn';
import { useCurrency } from '../hooks/useCurrency';

export function SalaryConfigPage() {
  const { salaryConfig, updateSalary, isLoading, stabilityReserveBalance } = useAppStore();

  const [amount, setAmount] = useState(salaryConfig?.desiredAmount ?? 0);
  const [frequency, setFrequency] = useState(salaryConfig?.frequency || 'monthly');
  const [isSaved, setIsSaved] = useState(false);
  const { format } = useCurrency();

  // Cálculos de inteligencia real
  const monthsOfCoverage = amount > 0 ? Math.max(0, Math.floor(stabilityReserveBalance / amount)) : 0;
  const recommendedSafeAmount = stabilityReserveBalance > 0 ? Math.floor(stabilityReserveBalance / 4) : 2500;
  const confidenceLevel = Math.min(100, Math.max(0, Math.round((stabilityReserveBalance / (amount * 3 || 1)) * 100)));

  useEffect(() => {
    if (salaryConfig) {
      setAmount(salaryConfig.desiredAmount);
      setFrequency(salaryConfig.frequency);
    }
  }, [salaryConfig]);

  const handleUpdate = async () => {
    await updateSalary({ 
      desiredAmount: amount, 
      frequency,
      recommendedAmount: recommendedSafeAmount,
      confidence: confidenceLevel,
      impact: Math.round((recommendedSafeAmount / (amount || 1)) * 10)
    });
    setIsSaved(true);
    setTimeout(() => setIsSaved(false), 3000);
  };



  return (
    <div className="space-y-8 animate-in fade-in duration-700 italic">
      <div className="italic">
        <p className="text-emerald-600 text-[10px] uppercase tracking-widest font-bold mb-2 italic">Configuración de Estabilidad Algorítmica</p>
        <h2 className="text-5xl font-display font-bold text-primary dark:text-white leading-[1.1] italic">Define tu <span className="text-emerald-500 italic">Sueldo Ideal</span>, <br /> <span className="text-slate-400 italic">nosotros absorbemos el riesgo.</span></h2>
        <p className="text-slate-500 dark:text-slate-400 mt-6 max-w-2xl leading-relaxed italic">
          Indica el monto que deseas recibir de forma recurrente. Nuestra IA analizará tu volatilidad histórica para garantizar este flujo mediante tu Fondo de Estabilización.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-start italic">
        {/* Main Config Card */}
        <Card className="lg:col-span-8 p-12 space-y-12 italic border-none shadow-premium dark:shadow-none dark:border dark:border-white/5">
          {/* Frequency Selector */}
          <div className="space-y-6 italic">
            <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest italic">Frecuencia de Dispersión</p>
            <div className="flex p-1.5 bg-slate-50 dark:bg-white/5 rounded-[22px] w-full sm:w-fit italic">
              {[
                { label: 'Semanal', value: 'weekly' },
                { label: 'Quincenal', value: 'biweekly' },
                { label: 'Mensual', value: 'monthly' }
              ].map((freq) => {
                const isActive = frequency === freq.value;
                return (
                  <button
                    key={freq.value}
                    onClick={() => setFrequency(freq.value as any)}
                    className={cn(
                      "px-10 py-3.5 rounded-[18px] text-xs font-bold transition-all duration-300 italic",
                      isActive 
                        ? "bg-white dark:bg-slate-800 text-primary dark:text-white shadow-lg ring-1 ring-slate-100 dark:ring-white/10" 
                        : "text-slate-400 dark:text-slate-500 hover:text-primary dark:hover:text-white"
                    )}
                  >
                    {freq.label}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Amount Slider */}
          <div className="space-y-8 italic">
            <div className="flex justify-between items-end italic">
              <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest italic">Monto de Salario Artificial</p>
              <div className="text-right italic">
                <span className="text-5xl font-display font-bold text-primary dark:text-white italic">{format(amount)}</span>
                <span className="text-slate-400 text-xs font-bold ml-2 uppercase italic tracking-widest">MXN</span>
              </div>
            </div>

            
            <div className="relative pt-6 italic">
              <input 
                type="range" 
                min="500" 
                max="10000" 
                step="100"
                value={amount}
                onChange={(e) => setAmount(Number(e.target.value))}
                className="w-full h-2 bg-slate-100 dark:bg-white/10 rounded-full appearance-none cursor-pointer accent-emerald-500 italic"
              />
              <div className="flex justify-between mt-6 text-[10px] text-slate-400 font-bold uppercase italic tracking-widest">
                <span>$500</span>
                <span>$5,000 (Sugerido)</span>
                <span>$10,000</span>
              </div>
            </div>
          </div>

          <div className="pt-6 border-t border-slate-100 dark:border-white/5 space-y-6 italic">
            <div className="flex items-center gap-4 p-6 bg-emerald-50/50 dark:bg-emerald-500/5 rounded-3xl border border-emerald-100/50 dark:border-emerald-500/10 italic">
              <div className="w-12 h-12 bg-white dark:bg-slate-800 rounded-2xl flex items-center justify-center text-emerald-500 shadow-sm italic">
                <Sparkles size={24} />
              </div>
              <div className="flex-1 italic">
                <p className="text-xs font-bold text-emerald-900 dark:text-emerald-400 italic">Listo para estabilizar</p>
                <p className="text-[10px] text-emerald-700/60 dark:text-emerald-400/50 italic leading-tight">Haz clic abajo para confirmar tu nuevo ingreso mensual de {format(amount)}.</p>
              </div>
            </div>

            <Button 
              variant="emerald" 
              className={cn(
                "w-full h-20 text-lg font-display font-bold gap-4 shadow-2xl transition-all italic rounded-[28px]",
                isSaved ? "bg-emerald-600 scale-[1.02]" : "shadow-emerald-500/20 hover:scale-[1.01] hover:shadow-emerald-500/30"
              )}
              onClick={handleUpdate}
              isLoading={isLoading}
            >
              {isSaved ? <CheckCircle2 size={24} /> : <Zap size={24} />}
              {isSaved ? "¡SALARIO GUARDADO!" : "GUARDAR Y ACTIVAR SUELDO"}
            </Button>
            <p className="text-center text-[10px] text-slate-400 dark:text-slate-500 italic font-medium">
              Al confirmar, Incomia recalibrará tu fondo de estabilidad inmediatamente.
            </p>
          </div>

        </Card>

        {/* Info/Stats Cards */}
        <div className="lg:col-span-4 space-y-8 italic">
          <Card className="bg-primary dark:bg-primary-dark text-white p-10 relative overflow-hidden border-none italic group shadow-premium dark:shadow-none">
            <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500 rounded-full opacity-10 blur-2xl -mr-10 -mt-10 group-hover:scale-125 transition-transform italic" />
            <div className="relative z-10 space-y-8 italic">
              <div className="flex items-center gap-3 text-emerald-400 italic">
                <ShieldCheck size={24} />
                <span className="text-xs font-bold uppercase tracking-widest italic">Simulación de Estrés</span>
              </div>
              
              <div className="h-28 flex items-end gap-2 px-2 italic">
                {[1, 2, 3, 4, 5, 6, 7].map((i) => (
                  <div 
                    key={i} 
                    className="flex-1 bg-white/5 rounded-t-lg relative group/bar italic"
                    style={{ height: `${Math.min(100, (monthsOfCoverage / i) * 100)}%` }}
                  >
                    <div 
                      className={cn(
                        "absolute bottom-0 left-0 right-0 bg-emerald-500 rounded-t-lg transition-all duration-1000 delay-300 italic shadow-[0_0_10px_rgba(16,185,129,0.3)]",
                        i <= monthsOfCoverage ? "opacity-100 h-full" : "opacity-0 h-0"
                      )}
                    />
                  </div>
                ))}
              </div>

              <div className="flex justify-between items-end border-t border-white/10 pt-6 italic">
                <div className="italic">
                  <p className="text-[10px] text-zinc-400 font-bold uppercase italic tracking-widest">Resiliencia (Meses)</p>
                  <p className="text-2xl font-display font-bold text-emerald-400 italic">+{monthsOfCoverage} meses</p>
                </div>

                <div className="text-right italic">
                  <p className="text-[10px] text-slate-400 font-bold uppercase italic">Confianza IA</p>
                  <p className="text-lg font-bold text-white italic">{salaryConfig?.confidence}%</p>
                </div>
              </div>
            </div>
          </Card>

          <div className="bg-emerald-50/50 dark:bg-emerald-500/10 rounded-[40px] p-1 border border-emerald-100/50 dark:border-emerald-500/20 italic">
            <div className="bg-emerald-50 dark:bg-emerald-950/20 rounded-[39px] p-10 text-center relative overflow-hidden italic">
              <div className="absolute top-6 right-6 text-emerald-300 dark:text-emerald-500/30 italic group-hover:rotate-12 transition-transform">
                <Sparkles size={28} />
              </div>
              <p className="text-emerald-600 dark:text-emerald-400 text-[10px] font-bold uppercase tracking-[0.2em] mb-4 italic">Monto Seguro Recomendado</p>
              <h4 className="text-4xl font-display font-bold text-emerald-900 dark:text-emerald-400 leading-tight italic">
                {format(recommendedSafeAmount)}
                <span className="text-emerald-500/50 text-xl ml-2 italic">/mes</span>
              </h4>
              <p className="text-[10px] text-emerald-700/80 dark:text-emerald-400/80 leading-relaxed italic">
                Tu configuración actual prioriza la estabilidad. Con este nivel de reserva, Incomia puede garantizar tu flujo de caja incluso ante caídas del 40% en tus depósitos brutos durante los próximos 6 meses.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Trust Builders */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-10 pt-12 border-t border-slate-100 dark:border-white/10 italic">
        {[
          { icon: CheckCircle2, title: 'Garantía Incomia', desc: 'Dispersamos tu sueldo incluso si tus facturas están pendientes de cobro.' },
          { icon: Clock, title: 'Recalibración Continua', desc: 'Nuestra IA ajusta tus límites cada 24h basándose en nuevos ingresos.' },
          { icon: ShieldCheck, title: 'Protección de Capital', desc: 'Tu fondo de estabilidad está segregado y asegurado contra insolvencia.' }
        ].map((feature, i) => (
          <div key={i} className="space-y-4 group hover:translate-y-[-4px] transition-all italic">
            <div className="w-12 h-12 bg-slate-50 dark:bg-white/5 rounded-2xl flex items-center justify-center text-primary dark:text-white group-hover:bg-emerald-50 dark:group-hover:bg-emerald-500/20 group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition-colors italic">
              <feature.icon size={24} />
            </div>
            <h5 className="font-bold text-primary dark:text-white italic text-lg">{feature.title}</h5>
            <p className="text-slate-500 dark:text-slate-400 text-sm leading-relaxed italic">
              {feature.desc}
            </p>
            <button className="text-[10px] font-bold text-emerald-600 dark:text-emerald-400 uppercase tracking-widest flex items-center gap-1 group-hover:gap-2 transition-all italic">
              Saber más <ArrowRight size={12} />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
