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

export const mockTransactions: Transaction[] = [];

export const mockFinancialSummary: FinancialSummary = {
  nextIncome: {
    amount: 0.00,
    date: 'Pendiente',
    description: 'Registra ingresos para ver tu próximo sueldo.',
  },
  stabilityReserve: {
    current: 0.00,
    target: 0,
    progress: 0,
    message: '"Tu reserva está vacía. Comienza a registrar ingresos para construir tu estabilidad."',
  },
  recentTransactions: [],
};

export const mockSalaryConfig: SalaryConfig = {
  desiredAmount: 0,
  frequency: 'monthly',
  recommendedAmount: 0,
  impact: 0,
  confidence: 100,
};

export const mockSavingGoals: SavingGoal[] = [
  {
    id: '1',
    title: 'Colchón de 6 Meses',
    currentAmount: 0,
    targetAmount: 50000,
    priority: 'high',
    estimatedDate: '2026-10-15',
    icon: 'Shield'
  },
  {
    id: '2',
    title: 'Provisiones para Impuestos',
    currentAmount: 0,
    targetAmount: 12000,
    priority: 'medium',
    estimatedDate: '2026-06-01',
    icon: 'FileText'
  }
];


export const mockCashFlowHistory: CashFlowData[] = [
  { month: 'JUL', real: 0, stabilized: 0 },
  { month: 'AGO', real: 0, stabilized: 0 },
  { month: 'SEP', real: 0, stabilized: 0 },
  { month: 'OCT', real: 0, stabilized: 0 },
  { month: 'NOV', real: 0, stabilized: 0 },
  { month: 'DIC', real: 0, stabilized: 0 },
];

export const mockExpenses: Expense[] = [];

export const mockFinancialAdvice: FinancialAdvice[] = [
  {
    id: '1',
    title: 'Optimización de Reserva',
    content: 'Tu fondo de estabilidad ha crecido un 15% este mes. Esto te otorga un margen de seguridad de 2 meses adicionales frente a meses de baja facturación.',
    type: 'saving',
    date: new Date().toISOString(),
    impact: 'Alto',
  },
  {
    id: '2',
    title: 'Oportunidad de Incremento',
    content: 'Detectamos una baja volatilidad en tus últimos depósitos. Podrías aumentar tu "Sueldo Artificial" un 5% sin comprometer la salud de tu colchón.',
    type: 'opportunity',
    date: new Date().toISOString(),
    impact: 'Medio',
  },
  {
    id: '3',
    title: 'Alerta de Gastos recurrentes',
    content: 'La IA ha detectado suscripciones que impactan tu resiliencia. Considera optimizarlas para alcanzar tu meta de tranquilidad financiera más rápido.',
    type: 'warning',
    date: new Date().toISOString(),
    impact: 'Bajo',
  }
];

export const mockLiquidityPredictions: LiquidityPrediction[] = [
  {
    date: new Date().toISOString(),
    probability: 95,
    expectedBalance: 15400,
    riskLevel: 'low'
  },
  {
    date: new Date(Date.now() + 86400000 * 7).toISOString(),
    probability: 85,
    expectedBalance: 14800,
    riskLevel: 'medium'
  }
];



export const mockAppSettings: AppSettings = {
  language: 'es',
  currency: 'MXN',
  theme: 'light',

  notifications: {
    deposits: true,
    expenses: true,
  },
  aiAggressiveness: 'balanceado',
};
