/**
 * financialService.ts — Capa de comunicación con la API de Incomia
 *
 * Cada método mapea directamente a un endpoint de API Gateway / Lambda.
 * El cliente Axios (apiClient) inyecta el JWT de Cognito automáticamente.
 *
 * Si VITE_API_BASE_URL no está definida, el servicio cae en los mocks
 * para poder trabajar en modo offline/desarrollo.
 */

import { apiClient } from '../lib/api';
import type {
  DashboardResponse,
  CreateUserRequest,
  CreateUserResponse,
  LogIncomeRequest,
  LogIncomeResponse,
  LogExpenseRequest,
  LogExpenseResponse,
  AnalyzeExpensesResponse,
  InflationResponse,
  ForecastResponse,
  AIAdviceResponse,
  FinancialSummary,
  SalaryConfig,
  Transaction,
  FinancialAdvice,
  LiquidityPrediction,
  CashFlowData,
} from '../types';
import {
  mockFinancialSummary,
  mockSalaryConfig,
  mockTransactions,
  mockFinancialAdvice,
  mockLiquidityPredictions,
  mockCashFlowHistory,
} from '../mocks/financialData';

// ── Helpers ───────────────────────────────────────────────────────────────────

const IS_MOCK = true; // Forzado para Demo Estable

const delay = (ms: number) => new Promise((r) => setTimeout(r, ms));

/**
 * Convierte la respuesta de get_dashboard al tipo FinancialSummary del frontend.
 */
function mapDashboardToSummary(
  res: DashboardResponse,
  recent: Transaction[]
): FinancialSummary {
  const { user, next_payment } = res;

  // Estado de reserva → mensaje legible
  const reserveMessages: Record<string, string> = {
    green: `Tu reserva cubre más de 2 meses. Incomia está distribuyendo tu sueldo de forma óptima.`,
    yellow: `Tu reserva cubre entre 1 y 2 meses. Considera reducir gastos secundarios este mes.`,
    red: `Tu reserva está por debajo de 1 mes. Incomia priorizará reconstruirla con tus próximos ingresos.`,
  };

  // Progreso de la reserva: target = 3× simulated_salary (3 meses)
  const reserveTarget = user.simulated_salary * 3;
  const reserveProgress =
    reserveTarget > 0
      ? Math.min(100, Math.round((user.reserve_balance / reserveTarget) * 100))
      : 0;

  // Formatear fecha de próximo pago
  const nextDate = new Date(next_payment.date + 'T00:00:00');
  const formattedDate = nextDate.toLocaleDateString('es-MX', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });

  const freqLabel: Record<string, string> = {
    weekly: 'semanal',
    biweekly: 'quincenal',
    monthly: 'mensual',
  };

  return {
    nextIncome: {
      amount: next_payment.amount,
      date: formattedDate,
      description: `Tu ${freqLabel[user.salary_frequency] || 'pago'} simulado garantizado por Incomia. Faltan ${next_payment.days_until} día${next_payment.days_until !== 1 ? 's' : ''}.`,
    },
    stabilityReserve: {
      current: user.reserve_balance,
      target: reserveTarget,
      progress: reserveProgress,
      message: reserveMessages[user.reserve_status] || '',
    },
    recentTransactions: recent,
  };
}

/**
 * Convierte los datos del dashboard al tipo SalaryConfig del frontend.
 */
function mapDashboardToSalaryConfig(res: DashboardResponse): SalaryConfig {
  const { user } = res;
  return {
    desiredAmount: user.simulated_salary,
    frequency: user.salary_frequency,
    recommendedAmount: user.simulated_salary,
    impact: 0,
    confidence: 0,
  };
}

/**
 * Convierte los ingresos del mes actual en datos de cash flow para la gráfica.
 * Genera los últimos 6 meses usando los totales del mes real.
 */
function buildCashFlowData(dashboard: DashboardResponse): CashFlowData[] {
  // Sin historial por ahora — devolvemos datos del mes actual + mock del resto
  const monthNames = ['ENE', 'FEB', 'MAR', 'ABR', 'MAY', 'JUN', 'JUL', 'AGO', 'SEP', 'OCT', 'NOV', 'DIC'];
  const now = new Date();
  const months: CashFlowData[] = [];

  for (let i = 5; i >= 0; i--) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
    const isCurrentMonth = i === 0;
    months.push({
      month: monthNames[d.getMonth()],
      real: isCurrentMonth ? dashboard.current_month.total_income : 0,
      stabilized: dashboard.user.simulated_salary,
    });
  }

  return months;
}

/**
 * Convierte las alertas sin ver en FinancialAdvice para el componente del dashboard.
 */
function mapAlertsToAdvice(dashboard: DashboardResponse): FinancialAdvice[] {
  return dashboard.unseen_alerts.slice(0, 3).map((alert) => ({
    id: alert.alertId,
    title:
      alert.type === 'expense_pattern'
        ? 'Análisis de Gastos'
        : alert.type === 'reserve_low'
        ? 'Alerta de Reserva'
        : 'Inflación Personalizada',
    content: alert.message,
    type:
      alert.type === 'reserve_low'
        ? 'warning'
        : alert.type === 'expense_pattern'
        ? 'opportunity'
        : 'saving',
    date: new Date(alert.created_at).toLocaleDateString('es-MX', {
      day: 'numeric',
      month: 'short',
    }),
  }));
}

// ── API del servicio ──────────────────────────────────────────────────────────

export const financialService = {
  // ── Dashboard (GET /users/{userId}/dashboard) ─────────────────────────────

  getDashboard: async (userId: string): Promise<DashboardResponse> => {
    if (IS_MOCK) {
      await delay(800);
      // Retornamos un mock compatible con DashboardResponse
      return {
        user: {
          name: 'Roberto Domínguez',
          mode: 'suggestion',
          salary_frequency: 'monthly',
          simulated_salary: mockFinancialSummary.nextIncome.amount,
          reserve_balance: mockFinancialSummary.stabilityReserve.current,
          reserve_status: 'green',
        },
        current_month: {
          total_income: 4500,
          total_expenses: 1800,
          primary_expenses: 1200,
          secondary_expenses: 600,
        },
        next_payment: {
          date: new Date(Date.now() + 7 * 86400_000).toISOString().split('T')[0],
          amount: mockFinancialSummary.nextIncome.amount,
          days_until: 7,
        },
        unseen_alerts: [],
      };
    }

    const res = await apiClient.get<DashboardResponse>(
      `/users/${userId}/dashboard`
    );
    return res.data;
  },

  // ── Summary compuesto para el DashboardPage ───────────────────────────────

  getSummary: async (userId: string): Promise<FinancialSummary> => {
    if (IS_MOCK) {
      await delay(800);
      return mockFinancialSummary;
    }

    const [dashboard, transactions] = await Promise.all([
      financialService.getDashboard(userId),
      financialService.getTransactions(userId),
    ]);

    const recent = transactions.slice(0, 5);
    return mapDashboardToSummary(dashboard, recent);
  },

  // ── Salary config mapeado desde dashboard ────────────────────────────────

  getSalaryConfig: async (userId: string): Promise<SalaryConfig> => {
    if (IS_MOCK) {
      await delay(600);
      return mockSalaryConfig;
    }

    const dashboard = await financialService.getDashboard(userId);
    return mapDashboardToSalaryConfig(dashboard);
  },

  // ── Cash flow data para la gráfica ───────────────────────────────────────

  getCashFlowData: async (userId: string): Promise<CashFlowData[]> => {
    if (IS_MOCK) {
      await delay(600);
      return mockCashFlowHistory;
    }

    const dashboard = await financialService.getDashboard(userId);
    return buildCashFlowData(dashboard);
  },

  // ── Transacciones (via dashboard reciente) ────────────────────────────────

  getTransactions: async (userId: string): Promise<Transaction[]> => {
    if (IS_MOCK) {
      await delay(700);
      return mockTransactions;
    }

    // Por ahora retornamos las transacciones del mes actual desde el dashboard
    // En el futuro se puede agregar GET /users/{userId}/transactions
    const dashboard = await financialService.getDashboard(userId);
    return [
      {
        id: `month-summary-${Date.now()}`,
        date: new Date().toISOString().split('T')[0],
        source: 'Ingresos del mes',
        category: 'Income',
        amount: dashboard.current_month.total_income,
        status: 'processed',
        type: 'income',
      },
    ];
  },

  // ── Consejos financieros (analyze_expenses) ───────────────────────────────

  getFinancialAdvice: async (userId: string): Promise<FinancialAdvice[]> => {
    if (IS_MOCK) {
      await delay(1200);
      return mockFinancialAdvice;
    }

    try {
      // Intentamos disparar análisis (solo ejecuta si no hubo uno en 7 días)
      const res = await apiClient.post<AnalyzeExpensesResponse>(
        `/users/${userId}/analyze`
      );
      if (res.data.alert_created && res.data.alert) {
        const alert = res.data.alert;
        return [
          {
            id: `analysis-${Date.now()}`,
            title: 'Análisis de Gastos',
            content: alert.message,
            type: 'opportunity',
            date: 'Hoy',
            impact: alert.data.suggestion,
          },
        ];
      }
    } catch {
      // Si Bedrock falla o no hay gastos suficientes, usamos alertas del dashboard
    }

    // Fallback: alertas no vistas del dashboard
    const dashboard = await financialService.getDashboard(userId);
    const advice = mapAlertsToAdvice(dashboard);
    return advice.length > 0 ? advice : mockFinancialAdvice;
  },

  // ── Predicciones de liquidez ──────────────────────────────────────────────

  getPredictions: async (userId: string): Promise<LiquidityPrediction[]> => {
    if (IS_MOCK) {
      await delay(900);
      return mockLiquidityPredictions;
    }

    try {
      const res = await apiClient.get<InflationResponse>(
        `/users/${userId}/inflation`
      );
      const { personal_inflation, national_inflation } = res.data;

      // Construimos predicciones simples basadas en los datos de inflación
      const now = new Date();
      return [1, 2, 3].map((months) => {
        const d = new Date(now.getFullYear(), now.getMonth() + months, 1);
        const riskFactor = personal_inflation / national_inflation;
        const riskLevel: 'low' | 'medium' | 'high' =
          riskFactor > 1.2 ? 'high' : riskFactor > 1.05 ? 'medium' : 'low';

        return {
          date: d.toISOString().split('T')[0],
          probability: Math.max(50, Math.round(95 - months * 5 * riskFactor)),
          expectedBalance: 0,
          riskLevel,
        };
      });
    } catch {
      return mockLiquidityPredictions;
    }
  },

  // ── Registrar ingreso (POST /users/{userId}/income) ───────────────────────

  logIncome: async (
    userId: string,
    data: LogIncomeRequest
  ): Promise<LogIncomeResponse> => {
    if (IS_MOCK) {
      await delay(1000);
      return {
        transaction_id: `mock-${Date.now()}`,
        simulated_salary: 3200,
        reserve_balance: 12840,
        reserve_status: 'green',
        message: 'Ingreso registrado (modo mock).',
      };
    }

    const res = await apiClient.post<LogIncomeResponse>(
      `/users/${userId}/income`,
      data
    );
    return res.data;
  },

  // ── Registrar gasto (POST /users/{userId}/expense) ────────────────────────

  logExpense: async (
    userId: string,
    data: LogExpenseRequest
  ): Promise<LogExpenseResponse> => {
    if (IS_MOCK) {
      await delay(1000);
      return {
        transaction_id: `mock-${Date.now()}`,
        category: 'secondary',
        category_label: 'Entretenimiento',
        message: 'Gasto registrado (modo mock).',
      };
    }

    const res = await apiClient.post<LogExpenseResponse>(
      `/users/${userId}/expense`,
      data
    );
    return res.data;
  },

  // ── Crear usuario (POST /users) ───────────────────────────────────────────

  createUser: async (data: CreateUserRequest): Promise<CreateUserResponse> => {
    if (IS_MOCK) {
      await delay(800);
      return {
        userId: `mock-${Date.now()}`,
        ...data,
        mode: data.mode || 'suggestion',
        salary_frequency: data.salary_frequency || 'monthly',
        simulated_salary: 0,
        reserve_balance: 0,
        reserve_status: 'green',
        created_at: new Date().toISOString(),
      };
    }

    const res = await apiClient.post<CreateUserResponse>('/users', data);
    return res.data;
  },

  // ── Pronóstico de liquidez (GET /users/{userId}/ai/forecast) ─────────────

  getForecast: async (userId: string): Promise<ForecastResponse> => {
    if (IS_MOCK) {
      await delay(1400);
      // Mock mínimo para desarrollo
      const today = new Date();
      return {
        model_used: 'moving_average_fallback',
        horizon_days: 14,
        risk_score: 38,
        risk_level: 'low',
        risk_label: 'Bajo',
        risk_color: 'green',
        bankruptcy_probability: 5,
        trigger_alert: false,
        alert_message: '[OK] Liquidez estable para las próximas 2 semanas.',
        min_projected_balance: 9200,
        min_balance_on_day: 12,
        final_balance: 10100,
        days_below_zero: 0,
        prediction_date: today.toISOString(),
        daily_projection: Array.from({ length: 14 }, (_, i) => ({
          day: i + 1,
          date: new Date(today.getTime() + (i + 1) * 86400_000)
            .toISOString()
            .split('T')[0],
          projected_balance: 12000 - i * 180,
        })),
      };
    }

    const res = await apiClient.get<ForecastResponse>(
      `/users/${userId}/ai/forecast`
    );
    return res.data;
  },

  // ── Consejo IA con Bedrock (GET /users/{userId}/ai/advice) ───────────────

  getAIAdvice: async (userId: string): Promise<AIAdviceResponse> => {
    if (IS_MOCK) {
      await delay(1800);
      return {
        advice:
          '**Tu Panorama**\n' +
          'Tus ingresos del mes son estables. Tu fondo de estabilización cubre más de 2 meses.\n\n' +
          '**Consejo Principal**\n' +
          'Considera aumentar tu fondo 10% este mes — estás cerca de tu meta de resiliencia.\n\n' +
          '**Plan de Acción**\n' +
          '1. Reserva el 15% de cada pago grande inmediatamente.\n' +
          '2. Revisa tus suscripciones activas y cancela las que no usas.\n' +
          '3. Investiga CETES Directo para tu fondo (inversión mínima $100 MXN).\n\n' +
          '**Meta del Mes**\n' +
          'Incrementar tu fondo de estabilización en $500 MXN.',
        metadata: {
          source: 'rule_based_fallback',
          reason: 'mock_mode',
          timestamp: new Date().toISOString(),
        },
        forecast: null,
      };
    }

    const res = await apiClient.get<AIAdviceResponse>(
      `/users/${userId}/ai/advice`
    );
    return res.data;
  },

  // ── updateSalaryConfig (placeholder — no hay Lambda dedicada aún) ─────────

  updateSalaryConfig: async (
    userId: string,
    config: Partial<SalaryConfig>
  ): Promise<SalaryConfig> => {
    if (IS_MOCK) {
      await delay(500);
      return { ...mockSalaryConfig, ...config };
    }

    // Mapeo UI -> Backend
    const body: Record<string, any> = {};
    if (config.desiredAmount !== undefined) body.simulated_salary = config.desiredAmount;
    if (config.frequency !== undefined) body.salary_frequency = config.frequency;

    if (Object.keys(body).length === 0) return { ...mockSalaryConfig, ...config };

    const res = await apiClient.patch(`/users/${userId}`, body);
    
    // El backend retorna el objeto de usuario completo
    const userData = res.data;
    return {
      desiredAmount: userData.simulated_salary,
      frequency: userData.salary_frequency,
      recommendedAmount: userData.simulated_salary,
      impact: 0,
      confidence: 0,
    };
  },


  // ── uploadData (S3 pre-signed URL) ────────────────────────────────────────

  uploadData: async (
    _file: File
  ): Promise<{ success: boolean; dataPoints: number }> => {
    await delay(2000);
    // TODO: Implementar pre-signed URL desde Lambda
    return { success: true, dataPoints: 0 };
  },
};
