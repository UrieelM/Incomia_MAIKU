import { useState } from 'react';
import { 
  AlertTriangle, 
  Trash2, 
  Edit3, 
  Zap,
  ShoppingBag,
  Home,
  Book,
  Utensils,
  Car,
  Heart
} from 'lucide-react';
import { 
  PieChart, 
  Pie, 
  Cell, 
  ResponsiveContainer, 
  Tooltip 
} from 'recharts';
import { useAppStore } from '../store/useAppStore';
import { useCurrency } from '../hooks/useCurrency';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { cn } from '../utils/cn';

const categoryData = [
  { name: 'Vivienda', value: 45, color: '#10B981' }, // Changed to primary for consistency
  { name: 'Comida', value: 22, color: '#34d399' },
  { name: 'Otros', value: 33, color: '#6ee7b7' },
];

const quickAddCategories = [
  { icon: ShoppingBag, label: 'Suscripciones' },
  { icon: Book, label: 'Escuela' },
  { icon: Utensils, label: 'Comida' },
  { icon: Car, label: 'Carro' },
  { icon: Home, label: 'Vivienda' },
  { icon: Heart, label: 'Salud' },
];

export function ExpensesPage() {
  const { expenses, salaryConfig, logExpense, fetchDashboardData } = useAppStore();
  const { format } = useCurrency();
  const [activeTab, setActiveTab] = useState('mensual');
  const [isAdding, setIsAdding] = useState(false);

  // Helper para añadir gasto rápido
  const handleQuickAdd = async (category: string) => {
    setIsAdding(true);
    try {
      await logExpense({
        amount: 50, // Monto por defecto para demo
        merchant: `Gasto rápido: ${category}`,
        date: new Date().toISOString().split('T')[0],
      });
      await fetchDashboardData();
    } catch (e) {
      console.error(e);
    } finally {
      setIsAdding(false);
    }
  };

  const totalMonthly = expenses.reduce((acc, curr) => acc + curr.amount, 0);
  const salaryLimit = salaryConfig?.desiredAmount || 3400;
  const deficit = totalMonthly - salaryLimit;

  return (
    <div className="space-y-8 animate-in fade-in duration-700 italic">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 italic">
        <div className="italic">
          <h2 className="text-4xl font-display font-bold text-primary dark:text-white italic">Gestión de Gastos</h2>
          <p className="text-slate-500 dark:text-slate-400 mt-1 italic">Configura tus egresos recurrentes para permitir que la IA dimensione tu capacidad de ahorro real.</p>
        </div>
        
        {deficit > 0 && (
          <div className="bg-red-50 dark:bg-red-500/10 border border-red-100 dark:border-red-500/20 p-4 rounded-2xl flex items-center gap-4 max-w-sm italic">
            <div className="w-10 h-10 bg-red-100 dark:bg-red-500/20 rounded-xl flex items-center justify-center text-red-600 dark:text-red-400 flex-shrink-0 italic">
               <AlertTriangle size={20} />
            </div>
            <div className="italic">
               <p className="text-[10px] font-bold text-red-600 dark:text-red-400 uppercase tracking-widest italic">Alerta de Inteligencia</p>
               <p className="text-xs font-bold text-red-900 dark:text-red-100 leading-tight italic">Tu sueldo actual no cubre tus gastos base.</p>
               <p className="text-[10px] text-red-500 dark:text-red-400/80 font-medium italic">Déficit mensual: {format(deficit)}</p>
            </div>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 italic">
        {/* Expenditure Summary Hero */}
        <Card className="lg:col-span-8 p-10 flex flex-col justify-between italic border-slate-100 dark:border-white/5">
           <div className="flex justify-between items-start mb-8 italic">
              <div className="italic">
                <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest mb-1 italic">Resumen Operativo</p>
                <h4 className="text-xl font-bold text-primary dark:text-white italic">Gasto Total Mensual</h4>
              </div>
              <div className="text-right italic">
                 <h3 className="text-4xl font-display font-bold text-primary dark:text-white italic">{format(totalMonthly)}</h3>
                 <p className="text-[10px] text-slate-400 font-bold italic uppercase mt-1 italic">Sueldo Actual: {format(salaryLimit)}</p>
              </div>
           </div>

           <div className="space-y-8 italic">
              <div className="space-y-4 italic">
                 <div className="h-6 bg-slate-100 dark:bg-white/10 rounded-full overflow-hidden flex relative italic">
                    <div className="h-full bg-primary-dark dark:bg-emerald-500 w-[65%] border-r border-white/20 italic" />
                    <div className="h-full bg-red-400 w-[15%] italic" />
                    <div className="absolute inset-0 flex items-center justify-center italic">
                       <div className="h-10 w-px bg-red-500 absolute left-[88%] z-10 italic">
                          <span className="absolute top-12 left-1/2 -translate-x-1/2 text-[10px] font-bold text-red-500 whitespace-nowrap italic uppercase">Sueldo Límite ({format(salaryLimit)})</span>
                       </div>
                    </div>
                 </div>
                 <div className="flex justify-between text-[10px] font-bold text-slate-400 uppercase tracking-widest italic">
                    <span>Fijos ($2,400)</span>
                    <span>Total Gastos ({format(totalMonthly)})</span>
                 </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 pt-4 italic">
                 <div className="p-6 bg-red-50 dark:bg-red-500/10 rounded-2xl italic">
                    <p className="text-[10px] text-red-400 font-bold uppercase tracking-widest mb-1 italic">Eficiencia</p>
                    <p className="text-xl font-display font-bold text-red-600 dark:text-red-400 italic">-12.9%</p>
                 </div>
                 <div className="p-6 bg-slate-50 dark:bg-white/5 rounded-2xl italic">
                    <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest mb-1 italic">Gastos Fijos</p>
                    <p className="text-xl font-display font-bold text-primary dark:text-white italic">62.5%</p>
                 </div>
                 <div className="p-6 bg-emerald-50 dark:bg-emerald-500/10 rounded-2xl italic">
                    <p className="text-[10px] text-emerald-600 dark:emerald-400 font-bold uppercase tracking-widest mb-1 italic">Proyección</p>
                    <p className="text-xl font-display font-bold text-emerald-700 dark:text-emerald-500 italic">
                      {format(46080)}
                      <span className="text-[10px] ml-1 opacity-60">/año</span>
                    </p>
                 </div>
              </div>
           </div>
        </Card>

        {/* Categories Donut */}
        <Card className="lg:col-span-4 p-8 flex flex-col items-center justify-center italic border-slate-100 dark:border-white/5">
           <h4 className="text-[10px] text-slate-400 font-bold uppercase tracking-widest mb-6 self-start italic">Desglose por categoría</h4>
           
           <div className="h-[200px] w-full relative italic">
              <ResponsiveContainer width="100%" height="100%">
                 <PieChart>
                    <Pie
                      data={categoryData}
                      innerRadius={60}
                      outerRadius={80}
                      paddingAngle={5}
                      dataKey="value"
                      stroke="none"
                    >
                      {categoryData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip 
                       contentStyle={{ 
                         backgroundColor: '#0D1627', 
                         borderRadius: '12px', 
                         border: 'none', 
                         boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.5)',
                         color: '#fff' 
                       }}
                       itemStyle={{ color: '#fff' }}
                    />
                 </PieChart>
              </ResponsiveContainer>
              <div className="absolute inset-0 flex flex-col items-center justify-center italic">
                 <p className="text-3xl font-display font-bold text-primary dark:text-white italic">6 Cat.</p>
                 <p className="text-[10px] text-slate-400 font-bold uppercase italic tracking-widest italic">Activas</p>
              </div>
           </div>

           <div className="w-full space-y-3 mt-8 italic">
              {categoryData.map((cat, i) => (
                <div key={i} className="flex items-center justify-between text-xs italic">
                   <div className="flex items-center gap-2 italic">
                      <div className="w-2 h-2 rounded-full italic" style={{ backgroundColor: cat.color }} />
                      <span className="font-medium text-slate-600 dark:text-slate-400 italic">{cat.name}</span>
                   </div>
                   <span className="font-bold text-primary dark:text-white italic">{cat.value}%</span>
                </div>
              ))}
           </div>
        </Card>
      </div>

      {/* Quick Add Section */}
      <div className="space-y-6 italic">
         <div className="flex justify-between items-end italic">
            <h4 className="text-xl font-bold text-primary dark:text-white italic leading-tight">Agregar Nuevo Gasto</h4>
            <button className="text-xs font-bold text-emerald-600 hover:underline italic">Ver todas las categorías</button>
         </div>

         <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-4 italic">
            {quickAddCategories.map((cat, i) => (
              <button 
                key={i} 
                onClick={() => handleQuickAdd(cat.label)}
                disabled={isAdding}
                className="p-6 bg-white dark:bg-white/5 border border-slate-100 dark:border-white/10 rounded-[32px] flex flex-col items-center gap-4 hover:premium-hover premium-transition group italic disabled:opacity-50"
              >
                 <div className="w-12 h-12 bg-slate-50 dark:bg-white/5 rounded-2xl flex items-center justify-center text-slate-400 dark:text-slate-500 group-hover:bg-primary dark:group-hover:bg-emerald-500 group-hover:text-white transition-colors italic">
                    <cat.icon size={24} />
                 </div>
                 <span className="text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-widest italic">{cat.label}</span>
              </button>
            ))}
         </div>
      </div>


      {/* Expenses Table */}
      <div className="space-y-6 pt-4 italic">
         <div className="flex justify-between items-end italic">
            <h4 className="text-xl font-bold text-primary dark:text-white italic">Gastos Recurrentes</h4>
            <div className="flex p-0.5 bg-slate-100 dark:bg-white/10 rounded-lg italic">
               {['mensual', 'anual'].map((tab) => (
                  <button 
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={cn(
                      "px-4 py-1.5 rounded-md text-[10px] font-bold uppercase tracking-widest transition-all italic",
                      activeTab === tab ? "bg-white dark:bg-slate-800 text-primary dark:text-white shadow-sm" : "text-slate-400 dark:text-slate-500 hover:text-slate-600 dark:hover:text-slate-300"
                    )}
                  >
                    {tab}
                  </button>
               ))}
            </div>
         </div>

         <Card className="p-0 overflow-hidden italic border-slate-100 dark:border-white/5">
            <table className="w-full text-left italic">
               <thead>
                  <tr className="bg-slate-50 dark:bg-white/5 italic">
                     <th className="px-8 py-5 text-[10px] font-bold text-slate-400 uppercase tracking-widest italic">Categoría</th>
                     <th className="px-8 py-5 text-[10px] font-bold text-slate-400 uppercase tracking-widest italic">Concepto</th>
                     <th className="px-8 py-5 text-[10px] font-bold text-slate-400 uppercase tracking-widest italic">Monto</th>
                     <th className="px-8 py-5 text-[10px] font-bold text-slate-400 uppercase tracking-widest italic text-center">Tipo</th>
                     <th className="px-8 py-5 text-[10px] font-bold text-slate-400 uppercase tracking-widest italic text-right">Acciones</th>
                  </tr>
               </thead>
               <tbody className="divide-y divide-slate-50 dark:divide-white/5 italic">
                  {expenses.map((expense) => (
                    <tr key={expense.id} className="hover:bg-slate-50/50 dark:hover:bg-white/5 transition-all italic group">
                       <td className="px-8 py-6 italic">
                          <div className="flex items-center gap-3 italic">
                             <div className="w-8 h-8 rounded-lg bg-emerald-50 dark:bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 flex items-center justify-center italic">
                                <ShoppingBag size={14} />
                             </div>
                             <span className="text-xs font-bold text-primary dark:text-white italic">{expense.category}</span>
                          </div>
                       </td>
                       <td className="px-8 py-6 text-xs font-medium text-slate-500 dark:text-slate-400 italic">{expense.concept}</td>
                       <td className="px-8 py-6 italic">
                          <span className="text-sm font-bold text-primary dark:text-white italic">{format(expense.amount)}</span>
                       </td>
                       <td className="px-8 py-6 text-center italic">
                          <span className={cn(
                             "px-3 py-1 text-[8px] font-bold uppercase rounded-full italic",
                             expense.type === 'fixed' ? "bg-slate-100 dark:bg-white/10 text-slate-500 dark:text-slate-400" : "bg-amber-50 dark:bg-amber-500/20 text-amber-600 dark:text-amber-400"
                          )}>
                             {expense.type === 'fixed' ? 'Fijo' : 'Variable'}
                          </span>
                       </td>
                       <td className="px-8 py-6 text-right italic">
                          <div className="flex items-center justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity italic">
                             <Button variant="ghost" size="icon" className="h-8 w-8 text-slate-400 hover:text-primary dark:hover:text-emerald-400 italic">
                                <Edit3 size={14} />
                             </Button>
                             <Button variant="ghost" size="icon" className="h-8 w-8 text-slate-400 hover:text-red-500 dark:hover:text-red-400 italic">
                                <Trash2 size={14} />
                             </Button>
                          </div>
                       </td>
                    </tr>
                  ))}
               </tbody>
            </table>
            <div className="p-6 flex justify-center border-t border-slate-50 dark:border-white/5 italic">
               <Button variant="outline" className="text-[10px] font-bold uppercase tracking-widest h-10 italic">Cargar más gastos</Button>
            </div>
         </Card>
      </div>

      {/* Floating Action CTA */}
      <div className="fixed bottom-8 right-8 z-50 italic">
         <Button variant="emerald" className="h-14 pl-6 pr-8 rounded-full shadow-2xl dark:shadow-none gap-3 animate-bounce italic">
            <Zap size={20} className="fill-emerald-400 text-emerald-400 italic" />
            <span className="italic font-bold">Optimizar Gastos</span>
         </Button>
      </div>
    </div>
  );
}
