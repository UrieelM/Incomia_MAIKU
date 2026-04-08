/**
 * DATA CONTRACTS - INCOMIA ARCHITECTURE
 * 
 * Este archivo define los contratos de datos entre el Frontend y el Backend.
 * Las interfaces aquí descritas deben ser respetadas por los modelos de datos
 * en AWS Lambda y las respuestas de API Gateway.
 */

/**
 * Representa un ingreso o egreso bruto cargado al sistema.
 */
export interface Transaction {
  /** Identificador único UUID */
  id: string;
  /** Fecha en formato ISO-8601 (YYYY-MM-DD) */
  date: string;
  /** Entidad origen (ej. "Stripe", "PayPal", "Bank Transfer") */
  source: string;
  /** Categorización IA (ej. "Freelance", "Consultoría", "Ingreso Fijo") */
  category: string;
  /** Monto en la divisa base (MXN/USD) */
  amount: number;
  /** Estado del procesamiento por el algoritmo de suavizado */
  status: 'processed' | 'pending' | 'failed' | 'validating';
  /** Clasificación contable */
  type: 'income' | 'expense';
}

/**
 * Resumen ejecutivo del estado financiero actual del usuario.
 */
export interface FinancialSummary {
  /** Datos del próximo depósito garantizado por Incomia */
  nextIncome: {
    amount: number;
    date: string;
    description: string;
  };
  /** Estado del fondo de reserva para absorber volatilidad */
  stabilityReserve: {
    current: number;
    target: number;
    progress: number;
    message: string;
  };
  /** Lista de transacciones recientes para el dashboard */
  recentTransactions: Transaction[];
}

/**
 * Configuración de la estrategia de suavizado de salario.
 */
export interface SalaryConfig {
  /** El sueldo mensual fijo que el usuario desea recibir */
  desiredAmount: number;
  /** Frecuencia con la que Incomia dispersa los fondos */
  frequency: 'weekly' | 'biweekly' | 'monthly';
  /** Recomendación generada por IA basada en histórico */
  recommendedAmount: number;
  /** Impacto proyectado en la salud financiera (+%) */
  impact: number;
  /** Nivel de confianza del algoritmo basado en la data disponible */
  confidence: number;
}

/**
 * Metas de ahorro inteligentes que se alimentan del "desbordamiento" de ingresos.
 */
export interface SavingGoal {
  id: string;
  title: string;
  currentAmount: number;
  targetAmount: number;
  priority: 'low' | 'medium' | 'high';
  /** Fecha estimada de cumplimiento calculada por IA */
  estimatedDate: string;
  icon?: string;
}

/**
 * Series de datos para visualización de gráficas de flujo de caja.
 */
export interface CashFlowData {
  month: string;
  /** Ingresos variables brutos (pre-suavizado) */
  real: number;
  /** Ingresos estables (post-suavizado Incomia) */
  stabilized: number;
}

/**
 * Egreso recurrente o variable del usuario.
 */
export interface Expense {
  id: string;
  category: string;
  concept: string;
  amount: number;
  type: 'fixed' | 'variable';
}

/**
 * Preferencias globales del usuario y de la IA.
 */
export interface AppSettings {
  language: 'es' | 'en';
  currency: 'USD' | 'EUR' | 'MXN';
  theme: 'light' | 'dark';
  notifications: {
    deposits: boolean;
    expenses: boolean;
  };
  /** Sensibilidad del algoritmo de reserva (Cauto: mayor reserva, Agresivo: menor reserva) */
  aiAggressiveness: 'cauto' | 'balanceado' | 'agresivo';
}

/**
 * Perfil de usuario autenticado (via AWS Cognito).
 */
export interface User {
  id: string;
  name: string;
  email: string;
  avatar?: string;
}

/**
 * Consejos financieros dinámicos generados por Amazon Bedrock.
 */
export interface FinancialAdvice {
  id: string;
  title: string;
  content: string;
  type: 'saving' | 'warning' | 'opportunity';
  date: string;
  impact?: string;
}

/**
 * Predicción de flujo de caja y liquidez futura.
 */
export interface LiquidityPrediction {
  date: string;
  /** Probabilidad de cumplimiento (0-100) */
  probability: number;
  expectedBalance: number;
  riskLevel: 'low' | 'medium' | 'high';
}
