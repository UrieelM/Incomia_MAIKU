import { useState } from 'react';
import { Plus, Target, Flame, Bike, Car, Sparkles, Clock, DollarSign } from 'lucide-react';

import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { useAppStore } from '../store/useAppStore';
import { useCurrency } from '../hooks/useCurrency';
import { cn } from '../utils/cn';

export function SavingsPage() {
  const { savingGoals, settings, updateSettings, addSavingGoal } = useAppStore();
  const { format } = useCurrency();
  const [showModal, setShowModal] = useState(false);

  // Form state
  const [title, setTitle] = useState('');
  const [targetAmount, setTargetAmount] = useState('');
  const [termMonths, setTermMonths] = useState('12');
  const [priority, setPriority] = useState<'low' | 'medium' | 'high'>('medium');

  const handleAddGoal = () => {
    if (!title || !targetAmount || isNaN(Number(targetAmount))) return;

    const total = Number(targetAmount);
    const months = Number(termMonths);
    const monthly = Math.round(total / months);

    addSavingGoal({
      id: `goal-${Date.now()}`,
      title,
      targetAmount: total,
      currentAmount: 0,
      priority,
      termMonths: months,
      monthlySaving: monthly,
      estimatedDate: new Date(Date.now() + months * 30 * 24 * 60 * 60 * 1000).toLocaleDateString('es-MX', { month: 'short', year: 'numeric' }),
    });

    setShowModal(false);
    setTitle('');
    setTargetAmount('');
    setTermMonths('12');
  };


  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'bg-primary text-white';
      case 'medium': return 'bg-emerald-50 text-emerald-600';
      case 'low': return 'bg-slate-50 text-slate-400';
      default: return 'bg-slate-50 text-slate-400';
    }
  };

  const getGoalIcon = (title: string) => {
    if (title.includes('Emergencia')) return <Target size={24} />;
    if (title.includes('Japón')) return <Bike size={24} />;
    if (title.includes('Coche')) return <Car size={24} />;
    return <Flame size={24} />;
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-700">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <p className="text-emerald-600 text-[10px] uppercase tracking-widest font-bold mb-1">Resumen de Crecimiento</p>
          <h2 className="text-4xl font-display font-bold text-primary leading-tight">Tus metas están <br /> <span className="text-emerald-500">al alcance.</span></h2>
          <p className="text-slate-500 mt-2 max-w-xl">
            Incomia AI ha optimizado tu flujo de caja este mes, incrementando tu capacidad de ahorro en un 12%.
          </p>
        </div>
        <Button 
          onClick={() => setShowModal(true)}
          className="gap-2 h-12 px-8 flex-shrink-0"
        >
          <Plus size={18} />
          Crear Nuevo Objetivo
        </Button>

      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Smart Overflow Card */}
        <Card className="lg:col-span-4 p-8 flex flex-col justify-between italic relative overflow-hidden group border-emerald-100">
           <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/5 rounded-full -mr-10 -mt-10 group-hover:scale-110 transition-transform" />
           
           <div className="space-y-6 relative z-10">
             <div className="flex items-center gap-3">
               <div className="w-10 h-10 bg-emerald-100 rounded-xl flex items-center justify-center text-emerald-600">
                 <Sparkles size={20} />
               </div>
               <h4 className="font-bold text-primary">Excedentes Inteligentes</h4>
             </div>
             
             <p className="text-slate-500 text-sm leading-relaxed">
               La IA asigna automáticamente el dinero no gastado al final del ciclo según tus prioridades.
             </p>

             <div className="flex items-center justify-between p-4 bg-emerald-50 rounded-2xl">
               <span className="text-[10px] font-bold uppercase tracking-widest text-emerald-700">Estado IA</span>
               <span className="px-3 py-1 bg-emerald-500 text-white text-[10px] font-bold rounded-full uppercase">Activo</span>
             </div>

             <div className="flex justify-between items-center px-4">
               <p className="text-xs font-bold text-slate-400 uppercase tracking-widest">Asignación Mensual Est.</p>
               <p className="text-2xl font-display font-bold text-primary">{format(425)}</p>
             </div>
           </div>

           <div className="mt-12 pt-6 border-t border-slate-50 flex items-center justify-between">
              <label className="text-sm font-bold text-slate-700 cursor-pointer" htmlFor="auto-adjust">Auto-ajuste dinámico</label>
              <button 
                id="auto-adjust"
                onClick={() => updateSettings({ aiAggressiveness: settings.aiAggressiveness === 'cauto' ? 'agresivo' : 'cauto' })}
                className={cn(
                  "w-12 h-6 rounded-full transition-colors relative",
                  settings.aiAggressiveness === 'agresivo' ? "bg-emerald-500" : "bg-slate-200"
                )}
              >
                <div className={cn(
                  "absolute top-1 w-4 h-4 bg-white rounded-full transition-all",
                  settings.aiAggressiveness === 'agresivo' ? "left-7" : "left-1"
                )} />
              </button>
           </div>
        </Card>

        {/* Goals Grid */}
        <div className="lg:col-span-8 space-y-8">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {savingGoals.map((goal) => (

              <Card key={goal.id} className="p-8 group hover:premium-hover premium-transition">
                <div className="flex justify-between items-start mb-6">
                  <div className={cn("w-12 h-12 rounded-2xl flex items-center justify-center", getPriorityColor(goal.priority))}>
                    {getGoalIcon(goal.title)}
                  </div>
                  <div className="text-right">
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Prioridad {goal.priority}</p>
                    <p className="text-xl font-display font-bold text-primary">{Math.round((goal.currentAmount / goal.targetAmount) * 100)}%</p>
                  </div>
                </div>

                <div className="space-y-6">
                  <div>
                    <h4 className="text-xl font-bold text-primary mb-1">{goal.title}</h4>
                    <p className="text-xs text-slate-400 font-medium">Estimado: <span className="text-slate-600 font-bold uppercase">{goal.estimatedDate}</span></p>
                  </div>

                  <div className="space-y-2">
                    <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-primary rounded-full" 
                        style={{ width: `${(goal.currentAmount / goal.targetAmount) * 100}%` }}
                      />
                    </div>
                    <div className="flex justify-between text-[10px] font-bold uppercase tracking-widest text-slate-400">
                      <span>{format(goal.currentAmount)}</span>
                      <span>{format(goal.targetAmount)}</span>
                    </div>
                  </div>
                </div>
              </Card>
            ))}
          </div>

          {/* Large Investment Card */}
          <Card className="bg-primary text-white p-0 overflow-hidden flex flex-col md:flex-row min-h-[300px] border-none italic group">
             <div className="flex-1 p-10 flex flex-col justify-between">
                <div>
                  <span className="px-3 py-1 bg-white/10 rounded-full text-[10px] font-bold uppercase tracking-widest mb-6 inline-block italic">Inversión a largo plazo</span>
                  <h3 className="text-4xl font-display font-bold leading-tight mb-4">Nuevo Coche <br /> Eléctrico</h3>
                  <p className="text-slate-400 text-sm leading-relaxed max-w-sm">
                    Tu ahorro ha crecido exponencialmente gracias a las reinversiones de dividendos automáticas.
                  </p>
                </div>
                
                <div className="space-y-4">
                   <div className="h-2 bg-white/10 rounded-full overflow-hidden italic">
                      <div className="h-full bg-emerald-500 w-[15%] rounded-full italic" />
                   </div>
                   <div className="flex justify-between items-end">
                      <div>
                        <p className="text-emerald-400 font-bold text-lg">{format(5250)}</p>
                        <p className="text-[10px] text-slate-400 uppercase tracking-widest font-bold italic">ahorrados</p>
                      </div>
                      <div className="text-right">
                        <p className="text-slate-400 font-bold text-sm">Meta: {format(35000)}</p>
                      </div>
                   </div>
                </div>
             </div>
             
             <div className="flex-1 relative min-h-[250px] md:min-h-full">
                <img 
                  src="https://images.unsplash.com/photo-1593941707882-a5bba14938c7?auto=format&fit=crop&q=80&w=800" 
                  alt="Electric Car" 
                  className="absolute inset-0 w-full h-full object-cover grayscale opacity-60 group-hover:grayscale-0 group-hover:opacity-100 transition-all duration-700" 
                />
                <div className="absolute inset-0 bg-gradient-to-r from-primary via-transparent to-transparent " />
                
                <div className="absolute top-10 right-10 bg-white/10 backdrop-blur-md border border-white/20 p-6 rounded-2xl italic">
                   <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest mb-1 italic">Estimación AI</p>
                   <p className="text-2xl font-display font-bold mb-1 italic">Oct, 2027</p>
                   <p className="text-[10px] text-slate-400 leading-tight italic">Basado en ingresos <br /> proyectados</p>
                </div>
             </div>
          </Card>
        </div>
      </div>

      {/* New Goal Modal */}
      {showModal && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-6 italic">
          <div className="absolute inset-0 bg-primary/80 backdrop-blur-sm italic" onClick={() => setShowModal(false)} />
          <Card className="relative z-10 w-full max-w-lg p-10 space-y-8 animate-in zoom-in-95 duration-300 italic">
            <div className="italic">
              <h3 className="text-2xl font-display font-bold text-primary dark:text-white italic">Nuevo Objetivo de Ahorro</h3>
              <p className="text-slate-500 text-sm mt-1 italic">Define tu meta y deja que Incomia AI la financie por ti.</p>
            </div>

            <div className="space-y-6 italic">
              <div className="space-y-2 italic">
                <label className="text-[10px] text-slate-400 font-bold uppercase tracking-widest italic">Concepto</label>
                <input 
                  type="text"
                  placeholder="Ej. Fondo de Emergencia, Vacaciones..."
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full h-12 bg-slate-50 dark:bg-white/5 border-none rounded-xl px-4 text-sm font-bold text-primary dark:text-white focus:ring-2 focus:ring-emerald-100 dark:focus:ring-emerald-500/20 italic outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-6 italic">
                <div className="space-y-2 italic">
                  <label className="text-[10px] text-slate-400 font-bold uppercase tracking-widest italic">Monto Total</label>
                  <div className="relative italic">
                    <input 
                      type="number"
                      placeholder="0.00"
                      value={targetAmount}
                      onChange={(e) => setTargetAmount(e.target.value)}
                      className="w-full h-12 bg-slate-50 dark:bg-white/5 border-none rounded-xl pl-10 pr-4 text-sm font-bold text-primary dark:text-white focus:ring-2 focus:ring-emerald-100 dark:focus:ring-emerald-500/20 italic outline-none"
                    />
                    <DollarSign size={14} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 italic" />
                  </div>
                </div>

                <div className="space-y-2 italic">
                  <label className="text-[10px] text-slate-400 font-bold uppercase tracking-widest italic">Plazo (Meses)</label>
                  <div className="relative italic">
                    <input 
                      type="number"
                      placeholder="12"
                      value={termMonths}
                      onChange={(e) => setTermMonths(e.target.value)}
                      className="w-full h-12 bg-slate-50 dark:bg-white/5 border-none rounded-xl pl-10 pr-4 text-sm font-bold text-primary dark:text-white focus:ring-2 focus:ring-emerald-100 dark:focus:ring-emerald-500/20 italic outline-none"
                    />
                    <Clock size={14} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 italic" />
                  </div>
                </div>
              </div>

              {targetAmount && termMonths && Number(termMonths) > 0 && (
                <div className="p-4 bg-emerald-50 dark:bg-emerald-500/10 rounded-2xl border border-emerald-100 dark:border-emerald-500/20 italic">
                  <p className="text-[10px] font-bold text-emerald-600 dark:text-emerald-400 uppercase tracking-widest mb-1 italic">Ahorro Mensual Requerido</p>
                  <p className="text-2xl font-display font-bold text-primary dark:text-emerald-400">
                    {format(Number(targetAmount) / Number(termMonths))}
                    <span className="text-xs font-medium text-slate-400 ml-2 italic">/ mes</span>
                  </p>
                </div>
              )}

              <div className="space-y-2 italic">
                <label className="text-[10px] text-slate-400 font-bold uppercase tracking-widest italic">Prioridad</label>
                <div className="flex gap-2 italic">
                  {['low', 'medium', 'high'].map((p) => (
                    <button
                      key={p}
                      onClick={() => setPriority(p as any)}
                      className={cn(
                        "flex-1 h-10 rounded-lg text-[10px] font-bold uppercase tracking-widest transition-all italic",
                        priority === p ? "bg-primary text-white" : "bg-slate-50 dark:bg-white/5 text-slate-400"
                      )}
                    >
                      {p === 'low' ? 'Baja' : p === 'medium' ? 'Media' : 'Alta'}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="flex gap-4 pt-4 italic">
              <Button variant="outline" className="flex-1 h-14 italic" onClick={() => setShowModal(false)}>Cancelar</Button>
              <Button 
                variant="emerald" 
                className="flex-1 h-14 italic" 
                onClick={handleAddGoal}
              >
                Activar Meta
              </Button>
            </div>
          </Card>
        </div>
      )}

      {/* Quote Section */}

      <div className="py-20 text-center space-y-8 italic">
         <div className="w-px h-16 bg-slate-200 mx-auto" />
         <h2 className="text-5xl font-display font-bold text-primary max-w-3xl mx-auto leading-tight italic">
           La disciplina es el puente entre tus deseos y la realidad.
         </h2>
         <p className="text-slate-400 font-medium tracking-wide italic">Incomia AI — Curando tu futuro financiero.</p>
      </div>
    </div>
  );
}
