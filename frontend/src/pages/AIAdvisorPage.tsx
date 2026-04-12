/**
 * AIAdvisorPage — Asesor Financiero IA
 *
 * Página principal de la integración de IA:
 *  - Pronóstico de liquidez a 14 días (Prophet / Moving Average)
 *  - Consejo personalizado generado por Amazon Bedrock Nova Pro
 *  - Gráfica de proyección de saldo día a día
 *  - Semáforo de riesgo financiero
 */

import React, { useEffect, useState } from 'react';
import { useAppStore } from '../store/useAppStore';
import {
  Brain,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle,
  RefreshCw,
  Cpu,
  ChevronRight,
} from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { cn } from '../utils/cn';

// ── Helpers ───────────────────────────────────────────────────────────────────

function formatMXN(value: number): string {
  return new Intl.NumberFormat('es-MX', {
    style: 'currency',
    currency: 'MXN',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

/** Convierte markdown ligero a JSX (solo bold y bullets) */
function renderMarkdown(text: string): React.ReactNode[] {

  return text.split('\n').map((line, i) => {
    // Encabezados **texto**
    const boldLine = line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    if (line.startsWith('**') && line.endsWith('**')) {
      const clean = line.replace(/\*\*/g, '');
      return (
        <p key={i} className="font-semibold text-primary dark:text-white mt-3 mb-1">
          {clean}
        </p>
      );
    }
    // Líneas numeradas
    if (/^\d+\./.test(line)) {
      return (
        <p key={i} className="ml-4 text-slate-600 dark:text-slate-300 my-0.5">
          {line}
        </p>
      );
    }
    // Líneas con _cursiva_ al final (metadata)
    if (line.startsWith('_') && line.endsWith('_')) {
      return (
        <p key={i} className="text-xs text-slate-400 mt-3 italic">
          {line.replace(/_/g, '')}
        </p>
      );
    }
    // Texto normal
    if (!line.trim()) return <br key={i} />;
    return (
      <p
        key={i}
        className="text-slate-600 dark:text-slate-300 leading-relaxed my-0.5"
        dangerouslySetInnerHTML={{ __html: boldLine }}
      />
    );
  });
}

// ── Componente Risk Badge ─────────────────────────────────────────────────────

function RiskBadge({ level, label }: { level: string; label: string }) {
  const colors: Record<string, string> = {
    low: 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-900/30 dark:text-emerald-300 dark:border-emerald-700',
    medium: 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-900/30 dark:text-amber-300 dark:border-amber-700',
    high: 'bg-red-50 text-red-700 border-red-200 dark:bg-red-900/30 dark:text-red-300 dark:border-red-700',
  };
  const icons: Record<string, React.ReactNode> = {
    low: <CheckCircle size={14} />,
    medium: <AlertTriangle size={14} />,
    high: <AlertTriangle size={14} />,
  };


  return (
    <span className={cn(
      'inline-flex items-center gap-1.5 px-3 py-1 rounded-full border text-sm font-semibold',
      colors[level] ?? colors.medium
    )}>
      {icons[level]}
      Riesgo {label}
    </span>
  );
}

// ── Componente Tooltip de la gráfica ─────────────────────────────────────────

function ChartTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white dark:bg-gray-800 border border-slate-200 dark:border-slate-600 rounded-xl p-3 shadow-lg text-xs">
      <p className="text-slate-500 dark:text-slate-400 mb-1">Día {label}</p>
      <p className="font-semibold text-primary dark:text-white">
        {formatMXN(payload[0]?.value ?? 0)}
      </p>
    </div>
  );
}

// ── Página principal ──────────────────────────────────────────────────────────

export function AIAdvisorPage() {
  const {
    forecast,
    aiAdvice,
    fetchForecast,
    fetchAIAdvice,
    isLoadingForecast,
    isLoadingAIAdvice,
    totalIncome,
    totalExpenses,
    salaryConfig
  } = useAppStore();

  const [activeTab, setActiveTab] = useState<'advice' | 'forecast'>('advice');

  // Lógica de Colchón Local
  const cushion = totalIncome - totalExpenses;
  const desiredSalary = salaryConfig?.desiredAmount || 3200;
  const monthsOfSurvival = desiredSalary > 0 ? Number((cushion / desiredSalary).toFixed(1)) : 0;


  // Carga inicial automática
  useEffect(() => {
    if (!forecast && !isLoadingForecast) {
      fetchForecast();
    }
    if (!aiAdvice && !isLoadingAIAdvice) {
      fetchAIAdvice();
    }
  }, [forecast, aiAdvice, fetchForecast, fetchAIAdvice, isLoadingForecast, isLoadingAIAdvice]);

  const handleRefresh = () => {
    fetchForecast();
    fetchAIAdvice();
  };

  // ── Chart data ─────────────────────────────────────────────────────────────
  const chartData = forecast?.daily_projection.map((d) => ({
    day: d.day,
    date: d.date,
    balance: Math.round(d.projected_balance),
  })) ?? [];


  const minBalance = forecast?.min_projected_balance ?? 0;

  return (
    <div className="p-6 lg:p-8 max-w-5xl mx-auto space-y-6">

      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-display font-bold text-primary dark:text-white flex items-center gap-2">
            <Brain className="text-emerald-500" size={26} />
            Asesor IA
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
            Pronóstico de liquidez · Consejo personalizado Bedrock
          </p>
        </div>

        <button
          onClick={handleRefresh}
          disabled={isLoadingForecast || isLoadingAIAdvice}
          className={cn(
            'flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium',
            'bg-slate-100 dark:bg-white/10 text-slate-600 dark:text-slate-300',
            'hover:bg-emerald-50 hover:text-emerald-700 dark:hover:bg-emerald-900/30 dark:hover:text-emerald-300',
            'transition-colors disabled:opacity-50 disabled:cursor-not-allowed'
          )}
        >
          <RefreshCw size={15} className={cn((isLoadingForecast || isLoadingAIAdvice) && 'animate-spin')} />
          Actualizar
        </button>
      </div>

      {/* ── Risk summary cards ─────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <SummaryCard
          label="Colchón de Estabilidad"
          value={formatMXN(cushion)}
          sub="Disponible para meses bajos"
          valueClass="text-emerald-600 dark:text-emerald-400"
        />
        <SummaryCard
          label="Meses de Supervivencia"
          value={`${monthsOfSurvival} meses`}
          sub={`Basado en sueldo de ${formatMXN(desiredSalary)}`}
          valueClass={monthsOfSurvival < 3 ? 'text-amber-500' : 'text-emerald-500'}
        />
        <SummaryCard
          label="Sueldo Regularizado"
          value={formatMXN(desiredSalary)}
          sub="Monto fijo mensual"
        />
        <SummaryCard
          label="Estado de Calificación"
          value={monthsOfSurvival >= 3 ? 'Resiliente' : 'En Construcción'}
          valueClass={monthsOfSurvival >= 3 ? 'text-emerald-600' : 'text-slate-400'}
        />
      </div>

      {/* ── Forecast summary cards (Solo si hay forecast) ────────────────── */}
      {forecast && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 opacity-70">
          <SummaryCard
            label="Riesgo (Predicción)"
            value={<RiskBadge level={forecast.risk_level} label={forecast.risk_label} />}
          />
          <SummaryCard
            label="Prob. de quiebra"
            value={`${forecast.bankruptcy_probability.toFixed(1)}%`}
            valueClass={forecast.bankruptcy_probability > 60 ? 'text-red-600' : 'text-emerald-600'}
          />
        </div>
      )}


      {/* ── Alerta de liquidez ─────────────────────────────────────────────── */}
      {forecast?.trigger_alert && (
        <div className="flex items-start gap-3 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 rounded-2xl">
          <AlertTriangle className="text-red-600 dark:text-red-400 shrink-0 mt-0.5" size={18} />
          <p className="text-sm text-red-700 dark:text-red-300">{forecast.alert_message}</p>
        </div>
      )}

      {/* ── Tabs ───────────────────────────────────────────────────────────── */}
      <div className="flex gap-1 bg-slate-100 dark:bg-white/5 p-1 rounded-xl w-fit">
        {(['advice', 'forecast'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={cn(
              'px-5 py-2 rounded-lg text-sm font-medium transition-colors',
              activeTab === tab
                ? 'bg-white dark:bg-white/10 text-primary dark:text-white shadow-sm'
                : 'text-slate-500 dark:text-slate-400 hover:text-primary dark:hover:text-white'
            )}
          >
            {tab === 'advice' ? 'Consejo IA' : 'Proyección'}
          </button>
        ))}
      </div>

      {/* ── Panel: Consejo IA ─────────────────────────────────────────────── */}
      {activeTab === 'advice' && (
        <div className="bg-white dark:bg-primary rounded-2xl border border-slate-100 dark:border-primary-light p-6 shadow-sm">
          {isLoadingAIAdvice ? (
            <AdviceLoading />
          ) : aiAdvice ? (
            <>
              <div className="flex items-center justify-between mb-5">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-lg bg-emerald-50 dark:bg-emerald-900/30 flex items-center justify-center">
                    <Cpu size={16} className="text-emerald-600 dark:text-emerald-400" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-primary dark:text-white">Asesor Incomia</p>
                    <p className="text-[11px] text-slate-400">
                      {aiAdvice.metadata.source === 'bedrock_amazon_nova_pro'
                        ? 'Amazon Bedrock · Nova Pro'
                        : 'Modo offline · Reglas'}
                    </p>
                  </div>
                </div>
                <span className="text-[11px] text-slate-400">
                  {new Date(aiAdvice.metadata.timestamp).toLocaleTimeString('es-MX', {
                    hour: '2-digit', minute: '2-digit'
                  })}
                </span>
              </div>

              <div className="prose prose-sm max-w-none">
                {renderMarkdown(aiAdvice.advice)}
              </div>

              {aiAdvice.metadata.input_tokens && (
                <p className="text-[11px] text-slate-400 mt-5 pt-4 border-t border-slate-50 dark:border-white/5">
                  Tokens: {aiAdvice.metadata.input_tokens} entrada · {aiAdvice.metadata.output_tokens} salida
                </p>
              )}
            </>
          ) : (
            <EmptyState
              icon={<Brain size={32} className="text-slate-300 dark:text-slate-600" />}
              title="Sin consejo cargado"
              action="Obtener consejo"
              onAction={fetchAIAdvice}
            />
          )}
        </div>
      )}

      {/* ── Panel: Proyección ─────────────────────────────────────────────── */}
      {activeTab === 'forecast' && (
        <div className="bg-white dark:bg-primary rounded-2xl border border-slate-100 dark:border-primary-light p-6 shadow-sm">
          {isLoadingForecast ? (
            <div className="h-64 flex items-center justify-center">
              <RefreshCw size={24} className="animate-spin text-slate-300" />
            </div>
          ) : chartData.length > 0 ? (
            <>
              <div className="flex items-center justify-between mb-5">
                <div>
                  <p className="text-sm font-semibold text-primary dark:text-white">
                    Proyección de saldo — próximos 14 días
                  </p>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Modelo: {forecast?.model_used === 'prophet' ? 'Prophet (ML)' : 'Media Móvil (fallback)'}
                  </p>
                </div>
                <div className="flex items-center gap-1.5 text-xs text-slate-400">
                  {forecast && forecast.final_balance >= (forecast.min_projected_balance ?? 0) ? (
                    <TrendingUp size={14} className="text-emerald-500" />
                  ) : (
                    <TrendingDown size={14} className="text-red-500" />
                  )}
                  {forecast && forecast.final_balance >= 0 ? 'Positivo' : 'En riesgo'}
                </div>
              </div>

              <ResponsiveContainer width="100%" height={240}>
                <LineChart data={chartData} margin={{ top: 5, right: 10, bottom: 5, left: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis
                    dataKey="day"
                    tickLine={false}
                    axisLine={false}
                    tick={{ fontSize: 11, fill: '#94a3b8' }}
                    tickFormatter={(v) => `D${v}`}
                  />
                  <YAxis
                    tickLine={false}
                    axisLine={false}
                    tick={{ fontSize: 11, fill: '#94a3b8' }}
                    tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
                    width={45}
                  />
                  <Tooltip content={<ChartTooltip />} />
                  {minBalance < 0 && (
                    <ReferenceLine y={0} stroke="#ef4444" strokeDasharray="4 4" strokeWidth={1.5} />
                  )}
                  <Line
                    type="monotone"
                    dataKey="balance"
                    stroke="#10b981"
                    strokeWidth={2.5}
                    dot={{ r: 3, fill: '#10b981', strokeWidth: 0 }}
                    activeDot={{ r: 5, fill: '#10b981' }}
                  />
                </LineChart>
              </ResponsiveContainer>

              {/* Tabla de días críticos */}
              {forecast && forecast.days_below_zero > 0 && (
                <div className="mt-4 p-3 bg-red-50 dark:bg-red-900/20 rounded-xl">
                  <p className="text-xs font-semibold text-red-700 dark:text-red-300 flex items-center gap-1.5">
                    <AlertTriangle size={13} />
                    {forecast.days_below_zero} día{forecast.days_below_zero !== 1 ? 's' : ''} con saldo negativo proyectado
                  </p>
                </div>
              )}
            </>
          ) : (
            <EmptyState
              icon={<TrendingUp size={32} className="text-slate-300 dark:text-slate-600" />}
              title="Sin datos de proyección"
              action="Calcular pronóstico"
              onAction={fetchForecast}
            />
          )}
        </div>
      )}
    </div>
  );
}

// ── Sub-componentes ───────────────────────────────────────────────────────────

function SummaryCard({
  label,
  value,
  sub,
  valueClass,
}: {
  label: string;
  value: React.ReactNode;
  sub?: string;
  valueClass?: string;
}) {
  return (
    <div className="bg-white dark:bg-primary rounded-2xl border border-slate-100 dark:border-primary-light p-4 shadow-sm">
      <p className="text-xs text-slate-400 mb-1.5">{label}</p>
      <div className={cn('text-base font-bold text-primary dark:text-white', valueClass)}>
        {value}
      </div>
      {sub && <p className="text-[11px] text-slate-400 mt-1">{sub}</p>}
    </div>
  );
}

function AdviceLoading() {

  return (
    <div className="space-y-3 animate-pulse">
      <div className="flex items-center gap-3 mb-5">
        <div className="w-8 h-8 bg-slate-100 dark:bg-white/10 rounded-lg" />
        <div className="space-y-1.5">
          <div className="h-3 bg-slate-100 dark:bg-white/10 rounded w-24" />
          <div className="h-2.5 bg-slate-100 dark:bg-white/10 rounded w-32" />
        </div>
      </div>
      {[80, 60, 90, 50, 70].map((w, i) => (
        <div key={i} className={`h-3 bg-slate-100 dark:bg-white/10 rounded w-[${w}%]`} />
      ))}
    </div>
  );
}

function EmptyState({
  icon, title, action, onAction,
}: {
  icon: React.ReactNode;
  title: string;
  action: string;
  onAction: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center py-10 gap-3">
      {icon}
      <p className="text-sm text-slate-400">{title}</p>
      <button
        onClick={onAction}
        className="flex items-center gap-2 px-4 py-2 bg-emerald-500 text-white rounded-xl text-sm font-medium hover:bg-emerald-600 transition-colors"
      >
        {action}
        <ChevronRight size={14} />
      </button>
    </div>
  );
}
