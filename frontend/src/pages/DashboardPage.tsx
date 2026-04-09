import { useEffect } from 'react';
import { 
  Calendar, 
  ShieldCheck, 
  ArrowRight,
  TrendingUp,
  CreditCard,
  Briefcase,
  Sparkles
} from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { CashFlowChart } from '../features/dashboard/components/CashFlowChart';
import { FinancialAdvice } from '../features/dashboard/components/FinancialAdvice';
import { RiskPrediction } from '../features/dashboard/components/RiskPrediction';
import { useCurrency } from '../hooks/useCurrency';
import { cn } from '../utils/cn';

export function DashboardPage() {
  const { 
    summary, 
    cashFlowHistory, 
    advice, 
    predictions, 
    fetchDashboardData, 
    isLoading,
    totalIncome,
    totalExpenses,
    salaryConfig,
    showReward,
    setShowReward,
    stabilityReserveBalance,
    simulationError,
    clearSimulationError
  } = useAppStore();


  const cushion = stabilityReserveBalance + (totalIncome - totalExpenses);
  const reserveTarget = (salaryConfig?.desiredAmount || 3200) * 3;
  const reserveProgress = reserveTarget > 0 ? Math.min(100, Math.round((cushion / reserveTarget) * 100)) : 0;

  
  const { format } = useCurrency();

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);


  if (isLoading || !summary) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-emerald-500 border-t-transparent" />
      </div>
    );
  }

  const nextIncomeAmount = salaryConfig?.desiredAmount !== undefined && salaryConfig.desiredAmount > 0 
    ? salaryConfig.desiredAmount 
    : summary.nextIncome.amount;



  return (
    <div className="space-y-8 animate-in fade-in duration-700 italic">
      <div className="italic">
        <h2 className="text-4xl font-display font-bold text-primary dark:text-white italic">Panel de <span className="text-emerald-500 italic">Control Inteligente</span></h2>
        <p className="text-slate-500 dark:text-slate-400 mt-1 italic">Visualiza la transformación de tu volatilidad en ingresos predecibles.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 italic">
        {/* Salary Artificial Card (Crítico) */}
        <Card className="lg:col-span-12 xl:col-span-5 bg-primary dark:bg-primary-dark text-white p-10 relative overflow-hidden group border-none italic">
          <div className="absolute top-0 right-0 w-64 h-64 bg-emerald-500 rounded-full opacity-10 -mr-20 -mt-20 group-hover:scale-110 transition-transform italic" />
          
          <div className="relative z-10 italic">
            <div className="flex items-center gap-2 mb-6 italic">
              <span className="bg-emerald-500 text-white text-[10px] font-bold px-2 py-0.5 rounded italic">ESTABILIZADO POR IA</span>
              <p className="text-slate-400 text-[10px] uppercase tracking-widest font-bold italic">Tu Próximo Salario Artificial</p>
            </div>
            
            <h3 className="text-5xl font-display font-bold mb-8 italic">{format(nextIncomeAmount)}</h3>
            
            <div className="flex flex-col md:flex-row gap-6 italic">

              <div className="flex items-center gap-3 bg-white/10 w-fit px-5 py-3 rounded-2xl backdrop-blur-sm italic">
                <Calendar size={20} className="text-emerald-400 italic" />
                <div className="italic">
                  <p className="text-[8px] text-zinc-300 uppercase font-bold italic">Fecha de Depósito</p>
                  <p className="text-sm font-bold italic">{summary.nextIncome.date}</p>
                </div>
              </div>

              <div className="flex items-center gap-3 bg-white/10 w-fit px-5 py-3 rounded-2xl backdrop-blur-sm italic">
                <TrendingUp size={20} className="text-emerald-400 italic" />
                <div className="italic">
                  <p className="text-[8px] text-zinc-300 uppercase font-bold italic">Estado de Flujo</p>
                  <p className="text-sm font-bold italic">Garantizado</p>
                </div>
              </div>
            </div>

            <p className="text-slate-400 text-sm mt-10 max-w-sm leading-relaxed italic text-zinc-300">
              {summary.nextIncome.description}
            </p>
          </div>
        </Card>

        {/* Stabilization Fund Card (KPI) */}
        <Card className="lg:col-span-12 xl:col-span-7 flex flex-col justify-between p-10 italic border-slate-100 dark:border-white/5">
          <div className="flex justify-between items-start mb-10 italic">
            <div className="italic">
              <p className="text-slate-400 text-[10px] uppercase tracking-widest font-bold mb-1 italic">Fondo de Estabilización (Colchón)</p>
              <h3 className="text-5xl font-display font-bold text-primary dark:text-white italic">{format(cushion)}</h3>
            </div>

            <div className="w-16 h-16 bg-emerald-50 dark:bg-emerald-500/20 rounded-[24px] flex items-center justify-center text-emerald-500 italic">
              <ShieldCheck size={32} />
            </div>
          </div>

          <div className="space-y-6 italic">
            <div className="italic">
              <div className="flex justify-between items-end mb-3 italic">
                <p className="text-xs font-bold text-emerald-600 dark:text-emerald-400 uppercase tracking-widest italic">Cobertura de Seguridad (Proyectada: {format(summary.stabilityReserve.target)})</p>
                <p className="text-lg font-display font-bold text-primary dark:text-white italic">{summary.stabilityReserve.progress}%</p>
              </div>
              
              <div className="h-4 bg-slate-100 dark:bg-white/10 rounded-full overflow-hidden italic">
                <div 
                  className="h-full bg-emerald-500 rounded-full transition-all duration-1000 ease-out italic"
                  style={{ width: `${reserveProgress}%` }}
                />
              </div>

            </div>

            <Card className="bg-slate-50 dark:bg-white/5 border-none p-5 italic">
              <p className="text-slate-600 dark:text-slate-400 text-sm leading-relaxed italic font-medium">
                {summary.stabilityReserve.message}
              </p>
            </Card>
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 italic">
        {/* Main Chart Section (Requirement #1) */}
        <div className="lg:col-span-8 italic">
          <CashFlowChart data={cashFlowHistory} className="h-full italic border-slate-100 dark:border-white/5" />
        </div>

        {/* Risk Prediction (Requirement #1) */}
        <div className="lg:col-span-4 italic">
          <RiskPrediction predictions={predictions} className="h-full italic border-slate-100 dark:border-white/5" />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 italic">
        {/* AI Advice (Requirement #5) */}
        <div className="lg:col-span-4 italic">
          <FinancialAdvice advice={advice} className="italic" />
        </div>

        {/* Recent Activity Table-like display */}
        <div className="lg:col-span-8 italic">
          <div className="flex justify-between items-end mb-6 italic">
            <div className="italic">
              <h4 className="text-2xl font-display font-bold text-primary dark:text-white italic">Historial de Volatilidad</h4>
              <p className="text-xs text-slate-400 italic">Últimos ingresos brutos analizados por la IA.</p>
            </div>
            <button className="text-sm font-bold text-emerald-600 hover:text-emerald-700 premium-transition flex items-center gap-1 italic">
              Explorar Data Training
              <ArrowRight size={14} />
            </button>
          </div>

          <div className="space-y-4 italic">
            {summary.recentTransactions.map((tx) => (
              <Card key={tx.id} className="flex items-center gap-6 p-5 hover:premium-hover premium-transition italic border-slate-100 dark:border-white/5">
                <div className="w-12 h-12 bg-slate-50 dark:bg-white/5 rounded-2xl flex items-center justify-center text-slate-400 italic">
                  {tx.category === 'Income' && <TrendingUp size={24} />}
                  {tx.category === 'Freelance' && <Briefcase size={24} />}
                  {tx.category === 'Consultoría' && <CreditCard size={24} />}
                </div>
                <div className="flex-1 italic">
                  <p className="font-bold text-primary dark:text-white italic leading-tight">{tx.source}</p>
                  <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest mt-1 italic">
                    {tx.date} • {tx.category} • <span className={cn(
                      tx.status === 'processed' ? "text-emerald-500" : "text-amber-500"
                    )}>{tx.status}</span>
                  </p>
                </div>
                <div className="text-right italic">
                  <p className="text-lg font-display font-bold text-emerald-600 dark:text-emerald-400 italic">
                    +{format(tx.amount)}
                  </p>
                </div>
              </Card>
            ))}
          </div>

          <Button variant="ghost" className="w-full mt-6 border-dashed border-2 italic h-14 font-bold text-slate-400 dark:text-slate-500 dark:border-white/10 dark:hover:bg-white/5 hover:translate-y-0 active:scale-100">
            Descargar Reporte de Estabilización (PDF)
          </Button>
        </div>
      </div>
      {/* Simulation Error Popup */}
      {simulationError && (
        <div className="fixed inset-0 z-[110] flex items-center justify-center p-6 italic">
          <div className="absolute inset-0 bg-red-900/40 backdrop-blur-md italic" onClick={() => clearSimulationError()} />
          <Card className="relative z-10 w-full max-w-sm p-10 text-center space-y-6 animate-in zoom-in duration-300 border-red-500/30 dark:bg-slate-900 italic">
            <div className="w-20 h-20 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-4 italic">
              <ShieldCheck size={40} className="text-red-500 italic" />
            </div>
            <div className="italic">
              <h3 className="text-2xl font-display font-bold text-primary dark:text-white italic leading-tight">¡Alerta de Liquidez!</h3>
              <p className="text-slate-400 text-sm mt-4 italic leading-relaxed">
                {simulationError}
              </p>
            </div>
            <div className="pt-4 italic">
              <Button variant="emerald" className="w-full h-14 text-sm font-bold shadow-xl italic" onClick={() => clearSimulationError()}>
                Entendido
              </Button>
            </div>
          </Card>
        </div>
      )}

      {/* Reward Popup */}

      {showReward && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-6 italic">
          <div className="absolute inset-0 bg-primary/90 backdrop-blur-md italic" onClick={() => setShowReward(false)} />
          <Card className="relative z-10 w-full max-w-lg p-12 text-center space-y-8 animate-in zoom-in duration-300 border-emerald-500/30 italic">
            <div className="w-24 h-24 bg-emerald-500/20 rounded-full flex items-center justify-center mx-auto mb-6 italic">
              <Sparkles size={48} className="text-emerald-500 animate-pulse italic" />
            </div>
            <div className="italic">
              <h3 className="text-4xl font-display font-bold text-primary dark:text-white italic leading-tight">¡Te mereces <br /> <span className="text-emerald-500 italic">un premio!</span></h3>
              <p className="text-slate-400 text-sm mt-4 italic leading-relaxed">
                Tus ingresos han superado con creces tu sueldo deseado y tu colchón de seguridad es robusto. Has trabajado duro para tener esta paz financiera. 
                <br /><br />
                <span className="text-white font-bold italic">Es momento de darte un pequeño regalo. ✨</span>
              </p>
            </div>
            <div className="pt-4 flex flex-col gap-4 italic">
              <Button variant="emerald" className="h-16 text-sm font-bold shadow-xl italic" onClick={() => setShowReward(false)}>
                ¡Lo celebraré!
              </Button>
              <Button variant="ghost" className="text-slate-500 text-xs italic" onClick={() => setShowReward(false)}>
                Quizás después
              </Button>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}

