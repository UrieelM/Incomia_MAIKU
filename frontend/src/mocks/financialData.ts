import type {
  FinancialSummary,
  Transaction,
  SalaryConfig,
  SavingGoal,
  CashFlowData,
  Expense,
  AppSettings,
  FinancialAdvice,
  LiquidityPrediction
} from '../types';

export const mockTransactions: Transaction[] = [
  {
    id: '1',
    date: '2026-11-15',
    source: 'Uber Earnings',
    category: 'Income',
    amount: 1450.00,
    status: 'processed',
    type: 'income',
  },
  {
    id: '2',
    date: '2026-11-14',
    source: 'Upwork Project',
    category: 'Freelance',
    amount: 850.00,
    status: 'processed',
    type: 'income',
  },
  {
    id: '3',
    date: '2026-11-12',
    source: 'Local Client',
    category: 'Consultoría',
    amount: 300.00,
    status: 'validating',
    type: 'income',
  },
  {
    id: '4',
    date: '2026-11-10',
    source: 'Uber Earnings',
    category: 'Income',
    amount: 1100.00,
    status: 'processed',
    type: 'income',
  },
  {
    id: '5',
    date: '2026-11-08',
    source: 'Digital Ocean Drop',
    category: 'Server Info',
    amount: 45.00,
    status: 'failed',
    type: 'expense',
  }
];

export const mockFinancialSummary: FinancialSummary = {
  nextIncome: {
    amount: 3200.00,
    date: '15 de Diciembre, 2026',
    description: 'Tu ingreso suavizado garantizado por Incomia.',
  },
  stabilityReserve: {
    current: 12840.45,
    target: 15000,
    progress: 85.6,
    message: '"Estás al 85% de tu reserva de seguridad. Incomia sugiere mantener el ajuste actual para alcanzar el 100% en Enero."',
  },
  recentTransactions: mockTransactions.slice(0, 5),
};

export const mockSalaryConfig: SalaryConfig = {
  desiredAmount: 3200,
  frequency: 'monthly',
  recommendedAmount: 2850,
  impact: 12,
  confidence: 94,
};

export const mockSavingGoals: SavingGoal[] = [
  {
    id: 'g1',
    title: 'Fondo de Emergencia',
    currentAmount: 8500,
    targetAmount: 10000,
    priority: 'high',
    estimatedDate: 'Enero, 2026',
  },
  {
    id: 'g2',
    title: 'Fondo para Impuestos',
    currentAmount: 2400,
    targetAmount: 5000,
    priority: 'high',
    estimatedDate: 'Abril, 2026',
  }
];

/**
 * Representación visual del valor de Incomia:
 * 'real' muestra la volatilidad típica de un freelance (serrucho).
 * 'stabilized' muestra la línea constante que ofrece el producto.
 */
export const mockCashFlowHistory: CashFlowData[] = [
  { month: 'JUL', real: 4200, stabilized: 3200 }, // Superávit -> a reserva
  { month: 'AGO', real: 1800, stabilized: 3200 }, // Déficit -> cubierto por reserva
  { month: 'SEP', real: 5100, stabilized: 3200 }, // Superávit -> a reserva
  { month: 'OCT', real: 2400, stabilized: 3200 }, // Déficit -> cubierto por reserva
  { month: 'NOV', real: 6350, stabilized: 3200 }, // Salto alto
  { month: 'DIC', real: 1200, stabilized: 3200 }, // Caída fuerte (Navidad/Baja demanda)
];

export const mockExpenses: Expense[] = [
  { id: 'e1', category: 'Fijo', concept: 'Renta', amount: 1200, type: 'fixed' },
  { id: 'e2', category: 'Variable', concept: 'Alimentación', amount: 600, type: 'variable' },
  { id: 'e3', category: 'Fijo', concept: 'Seguro Médico', amount: 250, type: 'fixed' },
];

export const mockFinancialAdvice: FinancialAdvice[] = [
  {
    id: 'a1',
    title: 'Optimización de Reserva',
    content: 'Tus ingresos han sido un 15% superiores al promedio. Incomia recomienda aumentar tu fondo de reserva un 5% para cubrir el hueco proyectado en Enero.',
    type: 'opportunity',
    date: 'Hoy',
    impact: '+$450 en liquidez futura'
  },
  {
    id: 'a2',
    title: 'Alerta de Volatilidad',
    content: 'Se detecta una tendencia a la baja en tus ingresos de los lunes. Considera ajustar tu presupuesto semanal.',
    type: 'warning',
    date: 'Ayer'
  }
];

export const mockLiquidityPredictions: LiquidityPrediction[] = [
  { date: '2026-12-30', probability: 92, expectedBalance: 4500, riskLevel: 'low' },
  { date: '2026-01-30', probability: 78, expectedBalance: 3100, riskLevel: 'medium' },
  { date: '2026-02-28', probability: 85, expectedBalance: 3250, riskLevel: 'low' },
];

export const mockAppSettings: AppSettings = {
  language: 'es',
  currency: 'USD',
  theme: 'light',
  notifications: {
    deposits: true,
    expenses: true,
  },
  aiAggressiveness: 'balanceado',
};
