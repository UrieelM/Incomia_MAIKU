import { useState } from 'react';
import { 
  Upload, 
  FileSpreadsheet, 
  Plus, 
  Filter, 
  Download,
  AlertCircle,
  CheckCircle2,
  Clock,
  Sparkles,
  ArrowUpRight
} from 'lucide-react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { useAppStore } from '../store/useAppStore';
import { financialService } from '../services/financialService';
import { cn } from '../utils/cn';
import { useCurrency } from '../hooks/useCurrency';

export function DataTrainingPage() {
  const { summary, logIncome, iaMemory } = useAppStore();
  const [isUploading, setIsUploading] = useState(false);
  const { format } = useCurrency();

  // Estado para entrada manual
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [amount, setAmount] = useState('');
  const [source, setSource] = useState('Stripe Payments');

  const handleManualAdd = async () => {
    if (!amount || isNaN(Number(amount))) return;
    try {
      await logIncome({
        amount: Number(amount),
        date,
        source,
        merchant: source,
        notes: 'Registro manual quirúrgico'
      });
      setAmount('');
    } catch (error) {
      console.error('Failed to add income', error);
    }
  };


  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    try {
      await financialService.uploadData(file);
      // In a real app, we would refresh the data here
    } catch (error) {
      console.error('Upload failed', error);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-700 italic">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 italic">
        <div className="italic">
          <h2 className="text-4xl font-display font-bold text-primary dark:text-white italic">Entrenamiento de <span className="text-emerald-500 italic">Datos</span></h2>
          <p className="text-slate-500 dark:text-slate-400 mt-2 italic">Importa tu historial financiero para calificar para el Algoritmo de Suavizado de Incomia.</p>
        </div>
        <Button variant="emerald" className="gap-2 h-14 px-10 shadow-xl shadow-emerald-500/20 dark:shadow-none italic transition-all hover:scale-105 active:scale-95">
          <Sparkles size={18} />
          Optimizar Modelo IA
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 italic">
        <div className="lg:col-span-8 space-y-8 italic">
          {/* Upload Card - AWS S3 Integration Ready */}
          <div className="relative group italic">
            <input 
              type="file" 
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10" 
              onChange={handleFileUpload}
              disabled={isUploading}
            />
            <Card className={cn(
              "p-12 border-dashed border-2 flex flex-col items-center justify-center text-center gap-6 transition-all italic",
              isUploading ? "bg-slate-50 dark:bg-white/5 opacity-50" : "bg-slate-50/50 dark:bg-white/5 hover:bg-white dark:hover:bg-white/10 hover:border-emerald-400 dark:border-white/10 group-active:scale-[0.98]"
            )}>
              <div className={cn(
                "w-20 h-20 rounded-[28px] shadow-sm flex items-center justify-center transition-all italic",
                isUploading ? "animate-pulse bg-emerald-100 dark:bg-emerald-500/20 text-emerald-500" : "bg-white dark:bg-slate-800 text-slate-400 dark:text-slate-500 group-hover:text-emerald-500 group-hover:rotate-6 shadow-premium dark:shadow-none"
              )}>
                {isUploading ? <Sparkles size={40} /> : <Upload size={40} />}
              </div>
              <div className="italic">
                <h4 className="text-2xl font-display font-bold text-primary dark:text-white italic">Carga Masiva (CSV / Bank API)</h4>
                <p className="text-slate-500 dark:text-slate-400 text-sm mt-3 max-w-sm mx-auto leading-relaxed italic">
                  Arrastra tus extractos bancarios aquí. Incomia procesará automáticamente tus patrones de ingreso volátil para generar tu primer Salario Artificial.
                </p>
              </div>
              <div className="flex items-center gap-4 italic pt-2">
                <Button variant="outline" className="bg-white dark:bg-white/5 px-8 h-12 italic border-slate-200 dark:border-white/10">Elegir Archivos</Button>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest italic">ó arrastra aquí</span>
              </div>
            </Card>
          </div>

          {/* Manual Entry Section */}
          <div className="space-y-4 italic">
            <h4 className="text-xl font-display font-bold text-primary dark:text-white italic flex items-center gap-2">
              <Plus size={20} className="text-emerald-500" />
              Entrada Manual Quirúrgica
            </h4>
            <Card className="p-8 italic border-slate-100 dark:border-white/5">
              <div className="grid grid-cols-1 sm:grid-cols-4 gap-6 items-end italic">
                <Input 
                  label="Fecha Factura" 
                  type="date" 
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                  className="h-12 bg-slate-50 dark:bg-white/5 border-none italic" 
                />
                <Input 
                  label="Monto" 
                  placeholder="0.00" 
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  className="h-12 bg-slate-50 dark:bg-white/5 border-none italic" 
                />
                <div className="space-y-2 italic">
                  <label className="text-[10px] text-slate-400 font-bold uppercase tracking-widest italic">Proveedor / Origen</label>
                  <select 
                    value={source}
                    onChange={(e) => setSource(e.target.value)}
                    className="w-full h-12 bg-slate-50 dark:bg-white/5 border-none rounded-xl px-4 text-sm font-bold text-primary dark:text-white focus:ring-2 focus:ring-emerald-100 dark:focus:ring-emerald-500/20 italic outline-none"
                  >
                    <option className="dark:bg-slate-900">Stripe Payments</option>
                    <option className="dark:bg-slate-900">PayPal Freelance</option>
                    <option className="dark:bg-slate-900">Transferencia Directa</option>
                    <option className="dark:bg-slate-900">Efectivo / Otros</option>
                  </select>
                </div>
                <Button 
                  onClick={handleManualAdd}
                  className="h-12 shadow-lg dark:shadow-none italic"
                >
                  Añadir Registro
                </Button>

              </div>
            </Card>
          </div>

          {/* Table History */}
          <div className="space-y-6 italic">
            <div className="flex items-center justify-between italic">
              <h4 className="text-2xl font-display font-bold text-primary dark:text-white italic">Datos en Memoria IA</h4>
              <div className="flex gap-3 italic">
                <Button variant="ghost" size="sm" className="h-10 px-4 gap-2 text-[10px] font-bold uppercase tracking-widest text-slate-400 hover:text-primary dark:hover:text-white italic">
                  <Filter size={14} />
                  Filtrar Precisión
                </Button>
                <Button variant="ghost" size="sm" className="h-10 px-4 gap-2 text-[10px] font-bold uppercase tracking-widest text-slate-400 hover:text-primary dark:hover:text-white italic">
                  <Download size={14} />
                  Descargar Dataset
                </Button>
              </div>
            </div>

            <Card className="p-0 overflow-hidden border-none shadow-premium dark:shadow-none italic">
              <table className="w-full text-left border-collapse italic">
                <thead>
                  <tr className="bg-slate-50/50 dark:bg-white/5 border-b border-slate-100 dark:border-white/10 italic">
                    <th className="px-8 py-5 text-[10px] font-bold text-slate-400 uppercase tracking-widest italic">Timing</th>
                    <th className="px-8 py-5 text-[10px] font-bold text-slate-400 uppercase tracking-widest italic">Origen de Capital</th>
                    <th className="px-8 py-5 text-[10px] font-bold text-slate-400 uppercase tracking-widest italic text-right">Monto Bruto</th>
                    <th className="px-8 py-5 text-[10px] font-bold text-slate-400 uppercase tracking-widest italic text-center">Status Entrenamiento</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50 dark:divide-white/5 italic">
                  {iaMemory.map((tx, idx) => (
                    <tr key={idx} className="hover:bg-slate-50/30 dark:hover:bg-white/5 transition-colors group italic">
                      <td className="px-8 py-6 text-sm font-medium text-slate-500 italic">{tx.date}</td>
                      <td className="px-8 py-6 italic">
                        <div className="flex items-center gap-4 italic">
                          <div className="w-10 h-10 rounded-xl bg-slate-100 dark:bg-white/5 flex items-center justify-center text-slate-400 group-hover:bg-white dark:group-hover:bg-white/10 transition-colors italic">
                            <FileSpreadsheet size={18} />
                          </div>
                          <span className="text-sm font-bold text-primary dark:text-white italic">{tx.source}</span>
                        </div>
                      </td>
                      <td className="px-8 py-6 text-sm font-bold text-primary dark:text-white italic text-right">{format(tx.amount)}</td>
                      <td className="px-8 py-6 italic">
                        <div className="flex items-center justify-center gap-2 italic">
                          <div className="flex items-center gap-2 bg-emerald-50 dark:bg-emerald-500/20 px-3 py-1 rounded-full italic">
                            <CheckCircle2 size={12} className="text-emerald-500 italic" />
                            <span className="text-[10px] font-bold text-emerald-600 dark:text-emerald-400 uppercase italic">Memoria IA</span>
                          </div>
                        </div>
                      </td>
                    </tr>
                  ))}
                  {summary?.recentTransactions.filter(tx => tx.type === 'income').map((tx) => (

                    <tr key={tx.id} className="hover:bg-slate-50/30 dark:hover:bg-white/5 transition-colors group italic">
                      <td className="px-8 py-6 text-sm font-medium text-slate-500 italic">{tx.date}</td>
                      <td className="px-8 py-6 italic">
                        <div className="flex items-center gap-4 italic">
                          <div className="w-10 h-10 rounded-xl bg-slate-100 dark:bg-white/5 flex items-center justify-center text-slate-400 group-hover:bg-white dark:group-hover:bg-white/10 transition-colors italic">
                            <FileSpreadsheet size={18} />
                          </div>
                          <span className="text-sm font-bold text-primary dark:text-white italic">{tx.source}</span>
                        </div>
                      </td>
                      <td className="px-8 py-6 text-sm font-bold text-primary dark:text-white italic text-right">{format(tx.amount)}</td>
                      <td className="px-8 py-6 italic">
                        <div className="flex items-center justify-center gap-2 italic">
                          {tx.status === 'processed' ? (
                            <div className="flex items-center gap-2 bg-emerald-50 dark:bg-emerald-500/20 px-3 py-1 rounded-full italic">
                              <CheckCircle2 size={12} className="text-emerald-500 italic" />
                              <span className="text-[10px] font-bold text-emerald-600 dark:text-emerald-400 uppercase italic">Procesado</span>
                            </div>
                          ) : (
                            <div className="flex items-center gap-2 bg-amber-50 dark:bg-amber-500/20 px-3 py-1 rounded-full italic">
                              <Clock size={12} className="text-amber-500 italic" />
                              <span className="text-[10px] font-bold text-amber-600 dark:text-amber-400 uppercase italic">Validando</span>
                            </div>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Card>
          </div>
        </div>

        {/* Intelligence Sidebar */}
        <div className="lg:col-span-4 space-y-8 italic">
          <Card className="bg-primary dark:bg-primary-dark text-white p-10 relative overflow-hidden border-none italic">
            <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500 rounded-full opacity-20 blur-2xl -mr-10 -mt-10 italic" />
            <div className="relative z-10 space-y-8 italic">
              <div className="italic">
                <p className="text-slate-400 text-[10px] uppercase tracking-widest font-bold mb-2 italic">Estado de Entrenamiento IA</p>
                <div className="flex items-end gap-3 italic">
                  <span className="text-6xl font-display font-bold italic tracking-tight">{iaMemory.length * 12 + 84}</span>
                  <div className="flex flex-col mb-2 italic">
                    <span className="text-[10px] font-bold text-emerald-400 uppercase italic">Vectores Procesados</span>
                    <span className="text-[8px] text-zinc-400 dark:text-slate-500 uppercase italic">Modelo Local</span>
                  </div>
                </div>
              </div>


              <div className="space-y-3 italic">
                  <div className="p-6 bg-emerald-50 dark:bg-emerald-500/10 rounded-2xl italic">
                     <p className="text-[10px] text-emerald-600 dark:text-emerald-400 font-bold uppercase tracking-widest mb-1 italic">Tasa de Estabilidad</p>
                     <p className="text-xl font-display font-bold text-emerald-600 dark:text-emerald-400 italic">94.2%</p>
                  </div>

                 <div className="h-3 bg-white/10 rounded-full overflow-hidden italic">
                   <div className="h-full bg-emerald-500 w-[84%] rounded-full shadow-[0_0_15px_rgba(16,185,129,0.5)] italic" />
                 </div>
              </div>

              <Card className="bg-white/5 border-none p-5 italic">
                <p className="text-slate-400 text-[11px] leading-relaxed italic text-zinc-300">
                  <span className="text-white font-bold italic">AI INSIGHT:</span> Tu dataset es suficiente para garantizar una estabilización con desviación menor al 5%. Sube extractos de los últimos 2 meses para llegar al <span className="text-emerald-400 font-bold italic">95%</span>.
                </p>
              </Card>
            </div>
          </Card>

          <Card className="p-8 space-y-8 italic border-slate-100 dark:border-white/5">
            <h5 className="text-sm font-bold text-primary dark:text-white flex items-center gap-3 uppercase tracking-widest italic">
              <AlertCircle size={18} className="text-amber-500" />
              Protocolo de Datos
            </h5>
            
            <div className="space-y-6 italic">
              {[
                { title: 'Detección de Patrones', desc: 'Identificamos automáticamente ingresos cíclicos versus accidentales.' },
                { title: 'Normalización', desc: 'Convertimos todas tus fuentes a la moneda base de Incomia.' },
                { title: 'Anonimización', desc: 'Tus datos bancarios se cifran antes de entrar al modelo bedrock.' },
              ].map((item, i) => (
                <div key={i} className="flex gap-4 italic transition-all hover:translate-x-1">
                  <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 mt-1.5 flex-shrink-0" />
                  <div className="italic">
                    <p className="text-xs font-bold text-primary dark:text-white italic">{item.title}</p>
                    <p className="text-[10px] text-slate-500 dark:text-slate-400 leading-relaxed italic mt-1">{item.desc}</p>
                  </div>
                </div>
              ))}
            </div>

            <Button variant="ghost" className="w-full h-14 bg-slate-50 dark:bg-white/5 border-none font-bold text-xs gap-3 italic text-primary dark:text-white hover:translate-y-0 active:scale-100">
              Ver Certificado de Privacidad
              <ArrowUpRight size={14} />
            </Button>
          </Card>
        </div>
      </div>
    </div>
  );
}
