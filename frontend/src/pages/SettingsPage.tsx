import { 
  Eye, 
  Sun, 
  Moon, 
  Bell, 
  Coins, 
  ChevronRight,
  Sparkles,
  Check
} from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { cn } from '../utils/cn';

export function SettingsPage() {
  const { user, settings, updateSettings } = useAppStore();

  const handleCurrencyChange = (curr: string) => {
    updateSettings({ currency: curr as any });
  };

  const handleAlgorithmChange = (val: string) => {
    updateSettings({ aiAggressiveness: val as any });
  };

  const handleThemeChange = (theme: 'light' | 'dark') => {
    updateSettings({ theme });
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-700 italic">
      <div className="italic">
        <h2 className="text-4xl font-display font-bold text-primary dark:text-white italic">Configuración de <span className="text-emerald-500 italic">Clarity</span></h2>
        <p className="text-slate-500 dark:text-slate-400 mt-2 max-w-2xl italic">
          Personaliza tu entorno financiero de Incomia. Define la precisión de la IA y el control de tus activos con un diseño minimalista.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 italic">
        {/* Profile and Visualization */}
        <div className="lg:col-span-8 space-y-8 italic">
           <Card className="p-10 italic">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-10 italic">
                 <div className="flex items-center gap-6 italic">
                    <div className="relative group italic">
                       <img 
                         src={user?.avatar} 
                         className="w-24 h-24 rounded-full border-4 border-slate-50 dark:border-primary-light italic" 
                         alt="Profile" 
                       />
                       <button className="absolute bottom-0 right-0 w-8 h-8 bg-primary text-white rounded-full flex items-center justify-center border-4 border-white dark:border-primary italic">
                          <EditIcon size={14} />
                       </button>
                    </div>
                    <div className="italic">
                       <h3 className="text-2xl font-display font-bold text-primary dark:text-white italic">{user?.name}</h3>
                       <p className="text-slate-400 text-sm font-medium italic">Premium Member • CDMX, MX</p>
                    </div>
                 </div>
                 <Button variant="primary" className="h-11 px-8 italic">Ver Perfil Público</Button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-8 italic">
                 <Input 
                   label="Correo Electrónico" 
                   defaultValue={user?.email} 
                   icon={<Check size={18} className="text-emerald-500" />} 
                 />
                 <div className="space-y-2 italic">
                    <label className="text-[10px] text-slate-400 font-bold uppercase tracking-widest italic">Seguridad de cuenta</label>
                    <button className="w-full h-12 px-4 bg-slate-50 dark:bg-white/5 rounded-xl flex items-center justify-between text-sm font-semibold text-primary dark:text-white hover:bg-slate-100 dark:hover:bg-white/10 transition-colors italic">
                       Cambiar Contraseña
                       <ChevronRight size={18} className="text-slate-400 italic" />
                    </button>
                 </div>
              </div>
           </Card>

           <div className="grid grid-cols-1 md:grid-cols-2 gap-8 italic">
              {/* Main Currency */}
              <Card className="p-8 italic">
                 <div className="flex items-center gap-3 mb-6 italic">
                    <div className="w-10 h-10 bg-emerald-50 text-emerald-600 rounded-xl flex items-center justify-center italic">
                       <Coins size={20} />
                    </div>
                    <h4 className="font-bold text-primary dark:text-white italic">Moneda Base</h4>
                 </div>
                 <div className="space-y-4 italic">
                    <select 
                      value={settings.currency}
                      onChange={(e) => handleCurrencyChange(e.target.value)}
                      className="w-full h-14 bg-slate-100 dark:bg-white/5 border-none rounded-2xl px-6 text-sm font-bold text-primary dark:text-white focus:ring-2 focus:ring-emerald-100 italic"
                    >
                       <option value="MXN">MXN — Peso Mexicano</option>
                       <option value="USD">USD — Dólar Americano</option>
                       <option value="EUR">EUR — Euro</option>
                    </select>
                    <p className="text-[10px] text-slate-400 leading-relaxed italic">
                      Esta moneda se utilizará para todos tus dashboards y el cálculo automático de flujos de efectivo.
                    </p>
                 </div>
              </Card>

              {/* Notifications */}
              <Card className="p-8 italic">
                 <h4 className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-8 italic">Notificaciones</h4>
                 <div className="space-y-6 italic">
                    <div className="flex items-center justify-between italic">
                       <div className="flex items-center gap-4 italic">
                          <div className="w-8 h-8 bg-emerald-50 text-emerald-600 rounded-lg flex items-center justify-center italic">
                             <Check size={16} />
                          </div>
                          <div className="italic">
                             <p className="text-xs font-bold text-primary dark:text-white italic">Depósitos Recibidos</p>
                             <p className="text-[10px] text-slate-400 italic">Alertas inmediatas de ingresos.</p>
                          </div>
                       </div>
                       <div className="h-6 w-11 bg-emerald-500 rounded-full relative cursor-pointer italic">
                          <div className="absolute top-1 right-1 w-4 h-4 bg-white rounded-full italic" />
                       </div>
                    </div>

                    <div className="flex items-center justify-between italic">
                       <div className="flex items-center gap-4 italic">
                          <div className="w-8 h-8 bg-red-50 text-red-600 rounded-lg flex items-center justify-center italic">
                             <Bell size={16} />
                          </div>
                          <div className="italic">
                             <p className="text-xs font-bold text-primary dark:text-white italic">Recordatorio de Gastos</p>
                             <p className="text-[10px] text-slate-400 italic">Alertas sobre facturas próximas.</p>
                          </div>
                       </div>
                       <div className="h-6 w-11 bg-emerald-500 rounded-full relative cursor-pointer italic">
                          <div className="absolute top-1 right-1 w-4 h-4 bg-white rounded-full italic" />
                       </div>
                    </div>
                 </div>
              </Card>
           </div>
        </div>

        {/* Sidebar Settings (Theme & AI) */}
        <div className="lg:col-span-4 space-y-8 italic">
           {/* Theme Toggle */}
           <Card className="bg-primary dark:bg-primary-dark text-white p-8 border-none italic">
              <div className="flex items-center gap-3 mb-8 italic">
                 <div className="w-10 h-10 bg-white/10 rounded-xl flex items-center justify-center text-emerald-400 italic">
                    <Eye size={20} />
                 </div>
                 <h4 className="font-bold text-white italic">Visualización</h4>
              </div>
              
              <div className="space-y-6 italic">
                 <p className="text-xs text-slate-400 leading-relaxed italic">
                    Optimiza el contraste según tu iluminación.
                 </p>
                 
                 <div className="flex bg-white/5 p-1.5 rounded-2xl italic">
                    <button 
                      onClick={() => handleThemeChange('light')}
                      className={cn(
                        "flex-1 flex items-center justify-center gap-2 py-3 rounded-xl text-xs font-bold transition-all italic",
                        settings.theme === 'light' ? "bg-white/10 text-white shadow-lg" : "text-slate-500 hover:text-white"
                      )}
                    >
                       <Sun size={14} />
                       Claro
                    </button>
                    <button 
                      onClick={() => handleThemeChange('dark')}
                      className={cn(
                        "flex-1 flex items-center justify-center gap-2 py-3 rounded-xl text-xs font-bold transition-all italic",
                        settings.theme === 'dark' ? "bg-white/10 text-white shadow-lg" : "text-slate-500 hover:text-white"
                      )}
                    >
                       <Moon size={14} />
                       Oscuro
                    </button>
                 </div>
              </div>
           </Card>

           {/* AI Algorithm Slider */}
           <div className="bg-emerald-50/50 dark:bg-emerald-950/20 rounded-[40px] p-1 border border-emerald-100 dark:border-emerald-900/50 italic">
              <Card className="p-8 border-none italic">
                 <div className="flex items-center gap-3 mb-8 italic">
                    <span className="bg-emerald-500 text-white text-[8px] font-bold px-2 py-0.5 rounded italic">AI DRIVEN</span>
                    <h4 className="text-xl font-display font-bold text-primary dark:text-white italic">Algoritmo de Reserva</h4>
                 </div>

                 <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed mb-8 italic">
                    Ajusta la 'agresividad' con la que la IA de Incomia aparta capital para tu fondo de reserva basado en tus proyecciones de gasto.
                 </p>

                 <div className="space-y-6 italic">
                    <div className="relative italic">
                       <input 
                         type="range" 
                         min="0" 
                         max="2" 
                         step="1"
                         className="w-full h-1.5 bg-slate-100 dark:bg-white/10 rounded-full appearance-none cursor-pointer accent-emerald-500 italic"
                         value={settings.aiAggressiveness === 'cauto' ? 0 : settings.aiAggressiveness === 'balanceado' ? 1 : 2}
                         onChange={(e) => {
                           const val = Number(e.target.value);
                           handleAlgorithmChange(val === 0 ? 'cauto' : val === 1 ? 'balanceado' : 'agresivo');
                         }}
                       />
                       <div className="flex justify-between text-[10px] font-bold text-slate-400 mt-4 uppercase italic">
                          <span>Cauto</span>
                          <span>Balanceado</span>
                          <span>Agresivo</span>
                       </div>
                    </div>

                    <Card className="bg-emerald-50 dark:bg-emerald-900/10 border-none p-5 italic">
                       <div className="flex items-center gap-2 text-emerald-800 dark:text-emerald-300 mb-3 italic">
                          <Sparkles size={14} />
                          <span className="text-[10px] font-bold tracking-wider uppercase italic font-display">Insight de Precisión</span>
                       </div>
                       <p className="text-[10px] text-emerald-700/80 dark:text-emerald-400/80 leading-relaxed italic">
                          Con un ajuste del 65%, la IA priorizará el ahorro sobre el gasto discrecional, proyectando un fondo de emergencia completo en 8 meses.
                       </p>
                    </Card>

                    <div className="pt-4 space-y-4 italic">
                       <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest italic">Proyección de Impacto</p>
                       <div className="flex justify-between items-end italic">
                          <p className="text-xs font-medium text-slate-500 italic">Ahorro Mensual Sugerido</p>
                          <p className="text-xl font-display font-bold text-primary dark:text-white italic">$12,450 MXN</p>
                       </div>
                       
                       <div className="grid grid-cols-2 gap-4 italic pt-2">
                          <div className="p-4 bg-slate-50 dark:bg-white/5 rounded-2xl italic">
                             <p className="text-[10px] text-slate-400 font-bold uppercase italic">Crecimiento</p>
                             <p className="text-lg font-bold text-emerald-600 italic">+12.4%</p>
                          </div>
                          <div className="p-4 bg-slate-50 dark:bg-white/5 rounded-2xl italic">
                             <p className="text-[10px] text-slate-400 font-bold uppercase italic text-right">Riesgo</p>
                             <p className="text-lg font-bold text-primary dark:text-white italic text-right">Bajo</p>
                          </div>
                       </div>
                    </div>
                 </div>
              </Card>
           </div>
        </div>
      </div>

      <div className="flex flex-col md:flex-row items-center justify-between pt-12 border-t border-slate-100 dark:border-white/5 italic gap-6">
         <div className="italic">
            <h5 className="text-sm font-bold text-primary dark:text-white italic">¿Necesitas ayuda avanzada?</h5>
            <p className="text-xs text-slate-400 italic">Nuestro equipo de soporte técnico financiero está disponible 24/7.</p>
         </div>
         <div className="flex gap-4 italic">
            <Button variant="ghost" className="h-12 px-8 font-bold italic">Descartar</Button>
            <Button variant="primary" className="h-12 px-10 font-bold italic shadow-xl">Guardar Cambios</Button>
         </div>
      </div>
    </div>
  );
}

const EditIcon = ({ size, className }: { size: number, className?: string }) => (
  <svg 
    xmlns="http://www.w3.org/2000/svg" 
    width={size} 
    height={size} 
    viewBox="0 0 24 24" 
    fill="none" 
    stroke="currentColor" 
    strokeWidth="2" 
    strokeLinecap="round" 
    strokeLinejoin="round" 
    className={className}
  >
    <path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>
  </svg>
);
