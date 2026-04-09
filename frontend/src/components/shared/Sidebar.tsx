import { NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  Settings2,
  ArrowUpRight,
  History,
  PieChart,
  LifeBuoy,
  LogOut,
  Sparkles,
  Receipt,
  Settings,
  Brain
} from 'lucide-react';
import { cn } from '../../utils/cn';
import { useAppStore } from '../../store/useAppStore';

const menuItems = [
  { id: 'dashboard', icon: LayoutDashboard, label: 'Dashboard',    path: '/app' },
  { id: 'salary',    icon: Settings2,       label: 'Salary Config', path: '/app/salary' },
  { id: 'cashflow',  icon: ArrowUpRight,    label: 'Cash Flow',     path: '/app/cashflow' },
  { id: 'deposits',  icon: History,         label: 'Deposits',      path: '/app/deposits' },
  { id: 'expenses',  icon: Receipt,         label: 'Expenses',      path: '/app/expenses' },
  { id: 'savings',   icon: PieChart,        label: 'Savings',       path: '/app/savings' },
  { id: 'ai',        icon: Brain,           label: 'Asesor IA',     path: '/app/ai' },
];


export function Sidebar() {
  const navigate = useNavigate();
  const setUser = useAppStore((state) => state.setUser);

  const handleLogout = () => {
    setUser(null);
    navigate('/login');
  };

  return (
    <aside className="w-64 h-screen bg-white dark:bg-primary border-r border-slate-100 dark:border-primary-light flex flex-col fixed left-0 top-0 z-40 premium-transition">
      <div className="p-8 pb-4">
        <div className="flex items-center gap-2 mb-10">
          <div className="w-8 h-8 bg-primary dark:bg-white rounded-lg flex items-center justify-center">
            <div className="w-4 h-4 rounded-sm bg-white dark:bg-primary rotate-45" />
          </div>
          <div>
            <h1 className="text-xl font-display font-bold text-primary dark:text-white">Incomia</h1>
            <p className="text-[10px] text-slate-400 font-medium uppercase tracking-widest -mt-1">Precision Finance</p>
          </div>
        </div>

        <nav className="space-y-1">
          {menuItems.map((item) => (
            <NavLink
              key={item.id}
              to={item.path}
              className={({ isActive }) => cn(
                "flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium premium-transition italic",
                isActive 
                  ? "bg-slate-50 dark:bg-white/10 text-primary dark:text-white border-r-4 border-emerald-500 rounded-r-none" 
                  : "text-slate-500 hover:bg-slate-50 dark:hover:bg-white/5 hover:text-primary dark:hover:text-white"
              )}
            >
              <item.icon size={20} />
              {item.label}
            </NavLink>
          ))}
        </nav>
      </div>

      <div className="mt-auto p-8 space-y-4">
        <NavLink
          to="/app/ai"

          className={({ isActive }) => cn(
            'flex items-center justify-center gap-2 w-full px-4 py-2.5 rounded-xl text-sm font-semibold transition-colors',
            isActive
              ? 'bg-emerald-500 text-white shadow-lg shadow-emerald-100 dark:shadow-none'
              : 'bg-emerald-500 text-white hover:bg-emerald-600 shadow-lg shadow-emerald-100 dark:shadow-none'
          )}
        >
          <Sparkles size={16} />
          AI Insight
        </NavLink>

        <div className="space-y-1 pt-4 border-t border-slate-50 dark:border-white/5">
          <NavLink 
            to="/app/settings"

            className={({ isActive }) => cn(
              "flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium premium-transition italic",
              isActive 
                ? "bg-slate-50 dark:bg-white/10 text-primary dark:text-white" 
                : "text-slate-500 hover:bg-slate-50 dark:hover:bg-white/5 hover:text-primary dark:hover:text-white"
            )}
          >
            <Settings size={20} />
            Settings
          </NavLink>
          <button className="w-full flex items-center gap-3 px-4 py-3 text-sm font-medium text-slate-500 hover:text-primary dark:hover:text-white premium-transition italic">
            <LifeBuoy size={20} />
            Support
          </button>
          <button 
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-4 py-3 text-sm font-medium text-slate-500 hover:text-red-600 premium-transition italic"
          >
            <LogOut size={20} />
            Logout
          </button>
        </div>
      </div>
    </aside>
  );
}
