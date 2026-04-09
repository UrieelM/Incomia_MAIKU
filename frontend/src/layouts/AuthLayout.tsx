import { Outlet } from 'react-router-dom';

export function AuthLayout() {
  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-6">
      <div className="w-full max-w-[1200px] h-[800px] bg-white rounded-[40px] shadow-2xl overflow-hidden flex flex-col md:flex-row border border-slate-100 italic gap-2">
        {/* Abstract Side */}
        <div className="hidden md:flex md:w-[45%] bg-primary relative p-12 flex-col justify-between overflow-hidden">
          {/* Decorative background circles */}
          <div className="absolute top-[-20%] right-[-20%] w-96 h-96 bg-primary-light rounded-full opacity-20 blur-3xl animate-pulse" />
          <div className="absolute bottom-[-10%] left-[-10%] w-64 h-64 bg-emerald-500 rounded-full opacity-10 blur-3xl" />

          <div className="relative z-10">
            <div className="flex items-center gap-2 mb-12">
              <div className="w-8 h-8 bg-white rounded-lg flex items-center justify-center">
                <div className="w-4 h-4 rounded-sm bg-primary rotate-45" />
              </div>
              <span className="text-xl font-display font-bold text-white">Incomia</span>
            </div>

            <h2 className="text-5xl font-display font-bold text-white leading-[1.1] mb-6">
              Transforma tus ingresos irregulares en un <span className="text-emerald-400 italic">salario estable.</span>
            </h2>
            <p className="text-slate-400 text-lg max-w-md leading-relaxed">
              Nuestra inteligencia financiera cura tus flujos de caja para proporcionarte la previsibilidad que necesitas para crecer.
            </p>
          </div>

          <div className="relative z-10 flex gap-4">
            <div className="bg-white/10 backdrop-blur-md rounded-2xl p-4 flex-1 border border-white/10">
              <p className="text-white font-bold text-2xl">98%</p>
              <p className="text-slate-400 text-[10px] uppercase tracking-widest font-bold">Precisión IA</p>
            </div>
            <div className="bg-white/10 backdrop-blur-md rounded-2xl p-4 flex-1 border border-white/10">
              <p className="text-white font-bold text-2xl">+12k</p>
              <p className="text-slate-400 text-[10px] uppercase tracking-widest font-bold">Usuarios Activos</p>
            </div>
          </div>
        </div>

        {/* Content Side */}
        <div className="flex-1 bg-white p-8 md:p-16 flex flex-col justify-center overflow-y-auto">
          <Outlet />
        </div>
      </div>

      {/* Footer Links */}
      <div className="fixed bottom-8 left-0 right-0 flex justify-center gap-8 text-xs text-slate-400 font-medium tracking-wide italic">
        <p>© 2026 Incomia. Curated Financial Intelligence.</p>
        <div className="flex gap-4">
          <a href="#" className="hover:text-primary transition-colors">Privacy Policy</a>
          <a href="#" className="hover:text-primary transition-colors">Terms of Service</a>
          <a href="#" className="hover:text-primary transition-colors">Security Architecture</a>
        </div>
      </div>
    </div>
  );
}
