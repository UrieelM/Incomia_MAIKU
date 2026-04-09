import { Search, Bell, Settings, ChevronLeft, ChevronRight } from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';

export function Navbar() {
  const { user, simulationOffset, advanceMonth, regressMonth, resetData } = useAppStore();

  return (
    <header className="h-20 bg-white/50 dark:bg-primary/50 backdrop-blur-md border-b border-slate-100 dark:border-white/5 flex items-center justify-between px-8 sticky top-0 z-30">
      <div className="flex-1 max-w-xl">
        <div className="relative group">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-primary dark:group-focus-within:text-white premium-transition" size={18} />
          <input 
            type="text" 
            placeholder="Buscar movimientos..." 
            className="w-full h-11 pl-12 pr-4 bg-slate-100 dark:bg-white/5 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/10 dark:focus:ring-white/10 focus:bg-white dark:focus:bg-white/10 dark:text-white dark:placeholder-slate-500 premium-transition"
          />
        </div>
      </div>

      <div className="flex items-center gap-6">
        {/* Simulación Temporal */}
        <div className="flex items-center gap-2 bg-slate-100 dark:bg-white/5 p-1 rounded-2xl border border-slate-200 dark:border-white/10 italic">
          <button 
            onClick={() => regressMonth()}
            disabled={simulationOffset <= 0}
            className="w-8 h-8 flex items-center justify-center rounded-xl hover:bg-white dark:hover:bg-white/10 text-slate-500 transition-all italic disabled:opacity-30 disabled:cursor-not-allowed"
          >
            <ChevronLeft size={18} />
          </button>
          
          <div className="px-3 min-w-[120px] text-center italic">
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest leading-none mb-1 italic">Mes Simulado</p>
            <p className="text-xs font-bold text-primary dark:text-white uppercase italic">
              {new Date(new Date().getFullYear(), new Date().getMonth() + simulationOffset, 1).toLocaleDateString('es-ES', { month: 'long', year: 'numeric' })}
            </p>
          </div>

          <button 
            onClick={() => advanceMonth()}
            disabled={simulationOffset >= 11}
            className="w-8 h-8 flex items-center justify-center rounded-xl hover:bg-white dark:hover:bg-white/10 text-slate-500 transition-all italic disabled:opacity-30 disabled:cursor-not-allowed"
          >
            <ChevronRight size={18} />
          </button>
        </div>


        <div className="flex items-center gap-3">
          <button 
            onClick={() => resetData()}
            className="w-10 h-10 flex items-center justify-center rounded-xl hover:bg-slate-100 dark:hover:bg-white/10 text-slate-500 dark:text-slate-400 premium-transition group"
            title="Sincronizar (Secret Reset)"
          >
            <Bell size={20} className="group-active:scale-95 transition-transform" />
          </button>


          <button className="w-10 h-10 flex items-center justify-center rounded-xl hover:bg-slate-100 dark:hover:bg-white/10 text-slate-500 dark:text-slate-400 premium-transition">
            <Settings size={20} />
          </button>
        </div>

        <div className="h-8 w-px bg-slate-200 dark:bg-white/10" />

        <div className="flex items-center gap-3">
          <div className="text-right hidden sm:block">
            <p className="text-sm font-semibold text-primary dark:text-white leading-tight">{user?.name || 'Invitado'}</p>
            <p className="text-[10px] text-slate-500 font-medium uppercase tracking-tight">Vidal Group</p>
          </div>
          <img 
            src={user?.avatar || 'https://api.dicebear.com/7.x/avataaars/svg?seed=Guest'} 
            alt="Profile" 
            className="w-10 h-10 rounded-xl border border-slate-100 dark:border-white/10 bg-white dark:bg-primary"
          />
        </div>
      </div>
    </header>
  );
}
