import { Search, Bell, Settings } from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';

export function Navbar() {
  const user = useAppStore((state) => state.user);

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
        <div className="flex items-center gap-3">
          <button className="w-10 h-10 flex items-center justify-center rounded-xl hover:bg-slate-100 dark:hover:bg-white/10 text-slate-500 dark:text-slate-400 premium-transition relative">
            <Bell size={20} />
            <span className="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full border-2 border-white dark:border-primary" />
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
