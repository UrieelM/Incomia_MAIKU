/**
 * DATA CONTRACTS - INCOMIA ARCHITECTURE
 *
 * Este archivo define los contratos de datos entre el Frontend y el Backend.
 * Sección A: tipos de UI (usados por componentes y el store).
 * Sección B: tipos de API (respuestas reales de las Lambdas).
 */

// ════════════════════════════════════════════════════════════════════════════
// SECCIÓN B — TIPOS DE RESPUESTA DE LA API (contratos Lambda → Frontend)
// ════════════════════════════════════════════════════════════════════════════

/** GET /users/{userId}/dashboard */
export interface DashboardResponse {
  user: {
    name: string;
    mode: 'auto' | 'suggestion' | 'educational';
    salary_frequency: 'weekly' | 'biweekly' | 'monthly';
    simulated_salary: number;
    reserve_balance: number;
    reserve_status: 'green' | 'yellow' | 'red';
  };
  current_month: {
    total_income: number;
    total_expenses: number;
    primary_expenses: number;
    secondary_expenses: number;
  };
  next_payment: {
    date: string;          // ISO date "YYYY-MM-DD"
    amount: number;
    days_until: number;
  };
  unseen_alerts: AlertItem[];
}

/** POST /users */
export interface CreateUserRequest {
  name: string;
  email: string;
  mode?: 'auto' | 'suggestion' | 'educational';
  salary_frequency?: 'weekly' | 'biweekly' | 'monthly';
}

export interface CreateUserResponse {
  userId: string;
  name: string;
  email: string;
  mode: string;
  salary_frequency: string;
  simulated_salary: number;
  reserve_balance: number;
  reserve_status: string;
  created_at: string;
}

/** POST /users/{userId}/income */
export interface LogIncomeRequest {
  amount: number;
  merchant?: string;
  date: string;          // ISO date "YYYY-MM-DD"
  source?: string;
  notes?: string;
}

export interface LogIncomeResponse {
  transaction_id: string;
  simulated_salary: number;
  reserve_balance: number;
  reserve_status: 'green' | 'yellow' | 'red';
  message: string;
}

/** POST /users/{userId}/expense */
export interface LogExpenseRequest {
  amount: number;
  merchant?: string;
  date: string;
  source?: string;
  notes?: string;
}

export interface LogExpenseResponse {
  transaction_id: string;
  category: 'primary' | 'secondary';
  category_label: string;
  message: string;
  warning?: string;
}

/** POST /users/{userId}/analyze */
export interface AnalyzeExpensesResponse {
  alert_created: boolean;
  message?: string;
  alert?: {
    type: string;
    message: string;
    data: {
      top_merchants: Array<{ merchant: string; count: number; total: number }>;
      total_secondary: number;
      suggestion: string;
    };
  };
}

/** GET /users/{userId}/inflation */
export interface InflationResponse {
  national_inflation: number;
  personal_inflation: number;
  breakdown: Array<{ category: string; weight: number; inflation: number }>;
  alert: {
    triggered: boolean;
    message?: string;
    suggested_adjustment?: number;
  };
}

/** Alerta del sistema */
export interface AlertItem {
  alertId: string;
  type: 'expense_pattern' | 'reserve_low' | 'inflation';
  message: string;
  created_at: string;
}

/** GET /users/{userId}/ai/forecast */
export interface ForecastDayProjection {
  day: number;
  date: string;
  projected_balance: number;
  /** Solo disponible con modelo Prophet */
  yhat?: number;
  yhat_lower?: number;
  yhat_upper?: number;
  lower_bound_balance?: number;
  /** Solo disponible con fallback de medias móviles */
  daily_net?: number;
  fixed_expenses?: number;
}

export interface ForecastResponse {
  model_used: 'prophet' | 'moving_average_fallback' | 'static_fallback';
  horizon_days: number;
  risk_score: number;
  risk_level: 'low' | 'medium' | 'high';
  risk_label: 'Bajo' | 'Medio' | 'Alto';
  risk_color: 'green' | 'yellow' | 'red';
  /** Probabilidad de quiebra en % (0–100) */
  bankruptcy_probability: number;
  trigger_alert: boolean;
  alert_message: string;
  min_projected_balance: number;
  min_balance_on_day: number;
  final_balance: number;
  days_below_zero: number;
  daily_projection: ForecastDayProjection[];
  prediction_date: string;
}

/** GET /users/{userId}/ai/advice */
export interface AIAdviceMetadata {
  source: 'bedrock_amazon_nova_pro' | 'rule_based_fallback' | 'static_fallback';
  reason?: string;
  model_id?: string;
  user_id?: string;
  input_tokens?: number;
  output_tokens?: number;
  timestamp: string;
  circuit_breaker?: {
    state: 'CLOSED' | 'OPEN' | 'HALF_OPEN';
    failure_count: number;
  };
}

export interface AIAdviceResponse {
  /** Texto en markdown del consejo personalizado */
  advice: string;
  metadata: AIAdviceMetadata;
  forecast: ForecastResponse | null;
}

// ════════════════════════════════════════════════════════════════════════════
// SECCIÓN A — TIPOS DE UI
// ════════════════════════════════════════════════════════════════════════════

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
  termMonths?: number;
  monthlySaving?: number;
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
