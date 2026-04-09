import { useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from '../components/shared/Sidebar';
import { Navbar } from '../components/shared/Navbar';
import { useAppStore } from '../store/useAppStore';

export function MainLayout() {
  const theme = useAppStore((state) => state.settings.theme);

  useEffect(() => {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [theme]);

  return (
    <div className="min-h-screen bg-[#F8FAFC] dark:bg-primary-dark text-slate-900 dark:text-slate-100 flex premium-transition">
      <Sidebar />
      <div className="flex-1 ml-64 flex flex-col">
        <Navbar />
        <main className="flex-1 p-8">
          <div className="max-w-[1400px] mx-auto">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
