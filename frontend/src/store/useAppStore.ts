import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type {
  User,
  FinancialSummary,
  SalaryConfig,
  SavingGoal,
  CashFlowData,
  Expense,
  AppSettings,
  FinancialAdvice,
  LiquidityPrediction,
  ForecastResponse,
  AIAdviceResponse,
  LogIncomeRequest,
  LogExpenseRequest,
  LogIncomeResponse,
  LogExpenseResponse,
} from '../types';
import { financialService } from '../services/financialService';
import { mockAppSettings, mockSavingGoals, mockExpenses } from '../mocks/financialData';
import {
  signIn as cognitoSignIn,
  signUp as cognitoSignUp,
  signOut as cognitoSignOut,
  getCurrentUserInfo,
} from '../lib/cognito';

/**
 * STATE MANAGEMENT — GLOBAL APP STORE (Zustand)
 *
 * Gestión centralizada de:
 *  - Auth: sesión Cognito (user, userId, isAuthenticated, isAuthLoading)
 *  - Datos financieros: summary, salaryConfig, cashFlow, expenses, advice, predictions
 *  - UI: settings, isLoading, error
 *
 * Flujo de auth:
 *   1. Al montar la app → initAuth() verifica sesión local de Cognito
 *   2. Login  → login(email, password) → setUser + fetchDashboardData
 *   3. Logout → logout() → limpia estado
 */

// ── Tipos del estado ──────────────────────────────────────────────────────────

interface AppState {
  // ─ Auth ────────────────────────────────────────────────────────────────────
  user: User | null;
  /** userId = sub de Cognito = PK en DynamoDB */
  userId: string | null;
  isAuthenticated: boolean;
  isAuthLoading: boolean;
  authError: string | null;

  // ─ Datos financieros ───────────────────────────────────────────────────────
  summary: FinancialSummary | null;
  salaryConfig: SalaryConfig | null;
  savingGoals: SavingGoal[];
  cashFlowHistory: CashFlowData[];
  expenses: Expense[];
  advice: FinancialAdvice[];
  predictions: LiquidityPrediction[];
  settings: AppSettings;

  // ─ IA ─────────────────────────────────────────────────────────────────────
  forecast: ForecastResponse | null;
  aiAdvice: AIAdviceResponse | null;
  isLoadingForecast: boolean;
  isLoadingAIAdvice: boolean;

  // ─ UI state ────────────────────────────────────────────────────────────────
  isLoading: boolean;
  error: string | null;

  // ─ Actions — Auth ──────────────────────────────────────────────────────────
  /** Verifica si hay sesión activa de Cognito al cargar la app */
  initAuth: () => Promise<void>;
  /** Autentica con Cognito y carga el dashboard */
  login: (email: string, password: string) => Promise<void>;
  /** Cierra sesión y limpia el estado */
  logout: () => void;
  /** Crea usuario en Cognito + Lambda POST /users */
  register: (
    email: string,
    password: string,
    name: string,
    salaryFrequency?: 'weekly' | 'biweekly' | 'monthly',
    mode?: 'auto' | 'suggestion' | 'educational'
  ) => Promise<void>;
  clearAuthError: () => void;

  // ─ Actions — Datos ─────────────────────────────────────────────────────────
  /** Carga todos los datos del Dashboard desde la API */
  fetchDashboardData: () => Promise<void>;
  /** Persiste cambios de configuración salarial */
  updateSalary: (config: Partial<SalaryConfig>) => Promise<void>;
  /** Registra un ingreso y actualiza el estado local */
  logIncome: (data: LogIncomeRequest) => Promise<LogIncomeResponse>;
  /** Registra un gasto y actualiza el estado local */
  logExpense: (data: LogExpenseRequest) => Promise<LogExpenseResponse>;
  /** Obtiene el pronóstico de liquidez a 14 días */
  fetchForecast: () => Promise<void>;
  /** Obtiene el consejo IA personalizado de Bedrock */
  fetchAIAdvice: () => Promise<void>;
  /** Actualiza preferencias de UI */
  updateSettings: (settings: Partial<AppSettings>) => void;
  setTheme: (theme: 'light' | 'dark') => void;
  setUser: (user: User | null) => void;
}

// ── Store ─────────────────────────────────────────────────────────────────────

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      // ─ Estado inicial ───────────────────────────────────────────────────────
      user: null,
      userId: null,
      isAuthenticated: false,
      isAuthLoading: true,
      authError: null,

      summary: null,
      salaryConfig: null,
      savingGoals: mockSavingGoals,
      cashFlowHistory: [],
      expenses: mockExpenses,
      advice: [],
      predictions: [],
      settings: mockAppSettings,

      forecast: null,
      aiAdvice: null,
      isLoadingForecast: false,
      isLoadingAIAdvice: false,

      isLoading: false,
      error: null,

      // ─ Auth actions ─────────────────────────────────────────────────────────

      /**
       * initAuth: se llama una vez al montar la app (en main.tsx o App.tsx).
       * Restaura la sesión local de Cognito si sigue vigente.
       */
      initAuth: async () => {
        set({ isAuthLoading: true });
        try {
          const userInfo = await getCurrentUserInfo();
          if (userInfo) {
            set({
              user: { id: userInfo.id, name: userInfo.name, email: userInfo.email },
              userId: userInfo.id,
              isAuthenticated: true,
            });
            // Carga silenciosa de datos en background
            get().fetchDashboardData().catch(() => {});
          }
        } catch {
          // Sin sesión activa — estado por defecto
        } finally {
          set({ isAuthLoading: false });
        }
      },

      /**
       * login: autentica con Cognito y carga el dashboard.
       */
      login: async (email, password) => {
        set({ isAuthLoading: true, authError: null });
        try {
          // 1. Auth Cognito
          await cognitoSignIn(email, password);

          // 2. Obtener info del usuario
          const userInfo = await getCurrentUserInfo();
          if (!userInfo) throw new Error('No se pudo obtener la sesión.');

          set({
            user: { id: userInfo.id, name: userInfo.name, email: userInfo.email },
            userId: userInfo.id,
            isAuthenticated: true,
            isAuthLoading: false,
          });

          // 3. Cargar dashboard
          await get().fetchDashboardData();
        } catch (err: any) {
          set({
            authError: err.message || 'Error de autenticación',
            isAuthLoading: false,
          });
          throw err;
        }
      },

      /**
       * logout: cierra sesión y limpia el estado completo.
       */
      logout: () => {
        cognitoSignOut();
        set({
          user: null,
          userId: null,
          isAuthenticated: false,
          summary: null,
          salaryConfig: null,
          cashFlowHistory: [],
          advice: [],
          predictions: [],
          error: null,
          authError: null,
        });
      },

      /**
       * register: crea el usuario en Cognito y luego llama a POST /users Lambda.
       * El usuario queda registrado pero debe verificar su email antes de iniciar sesión.
       */
      register: async (email, password, name, salaryFrequency = 'monthly', mode = 'suggestion') => {
        set({ isAuthLoading: true, authError: null });
        try {
          // 1. Crear usuario en Cognito → obtenemos el sub (userId)
          const userId = await cognitoSignUp(email, password, name);

          // 2. Crear registro en DynamoDB via Lambda POST /users
          // Usamos el sub de Cognito como userId para consistencia
          await financialService.createUser({
            name,
            email,
            mode,
            salary_frequency: salaryFrequency,
          });

          console.info(`[Incomia] Usuario creado: ${userId}`);
          set({ isAuthLoading: false });
        } catch (err: any) {
          set({
            authError: err.message || 'Error en el registro',
            isAuthLoading: false,
          });
          throw err;
        }
      },

      clearAuthError: () => set({ authError: null }),

      // ─ Datos actions ────────────────────────────────────────────────────────

      /**
       * fetchDashboardData: carga todos los KPIs del dashboard.
       * Mapea respuestas del backend a los tipos de la UI.
       */
      fetchDashboardData: async () => {
        const { userId } = get();
        if (!userId) return;

        set({ isLoading: true, error: null });
        try {
          const [summary, salaryConfig, advice, predictions, cashFlowHistory] =
            await Promise.all([
              financialService.getSummary(userId),
              financialService.getSalaryConfig(userId),
              financialService.getFinancialAdvice(userId),
              financialService.getPredictions(userId),
              financialService.getCashFlowData(userId),
            ]);

          set({ summary, salaryConfig, advice, predictions, cashFlowHistory, isLoading: false });
        } catch (err: any) {
          set({ error: err.message || 'Error al cargar datos', isLoading: false });
        }
      },

      /**
       * updateSalary: actualiza la configuración salarial.
       */
      updateSalary: async (config) => {
        const { userId } = get();
        if (!userId) return;

        set({ isLoading: true, error: null });
        try {
          const updatedConfig = await financialService.updateSalaryConfig(userId, config);
          set({ salaryConfig: updatedConfig, isLoading: false });
        } catch (err: any) {
          set({ error: err.message || 'Error al actualizar salario', isLoading: false });
        }
      },

      /**
       * logIncome: registra un ingreso y actualiza el salario simulado localmente.
       */
      logIncome: async (data) => {
        const { userId } = get();
        if (!userId) throw new Error('No autenticado');

        const result = await financialService.logIncome(userId, data);

        // Actualizar salaryConfig en el store con el nuevo simulated_salary
        const current = get().salaryConfig;
        if (current) {
          set({
            salaryConfig: {
              ...current,
              desiredAmount: result.simulated_salary,
              recommendedAmount: result.simulated_salary,
            },
          });
        }

        return result;
      },

      /**
       * logExpense: registra un gasto.
       */
      logExpense: async (data) => {
        const { userId } = get();
        if (!userId) throw new Error('No autenticado');

        return financialService.logExpense(userId, data);
      },

      /**
       * fetchForecast: obtiene el pronóstico de liquidez a 14 días.
       */
      fetchForecast: async () => {
        const { userId } = get();
        if (!userId) return;

        set({ isLoadingForecast: true });
        try {
          const forecast = await financialService.getForecast(userId);
          set({ forecast, isLoadingForecast: false });
        } catch (err: any) {
          set({ isLoadingForecast: false, error: err.message || 'Error al cargar pronóstico' });
        }
      },

      /**
       * fetchAIAdvice: obtiene el consejo personalizado de Bedrock.
       * Incluye el pronóstico de liquidez en el contexto.
       */
      fetchAIAdvice: async () => {
        const { userId } = get();
        if (!userId) return;

        set({ isLoadingAIAdvice: true });
        try {
          const aiAdvice = await financialService.getAIAdvice(userId);
          // Si el consejo incluye forecast, almacenarlo también
          if (aiAdvice.forecast) {
            set({ forecast: aiAdvice.forecast });
          }
          set({ aiAdvice, isLoadingAIAdvice: false });
        } catch (err: any) {
          set({ isLoadingAIAdvice: false, error: err.message || 'Error al cargar consejo IA' });
        }
      },

      // ─ UI actions ───────────────────────────────────────────────────────────

      updateSettings: (newSettings) => {
        set((state) => ({
          settings: { ...state.settings, ...newSettings },
        }));
      },

      setTheme: (theme) => {
        set((state) => ({
          settings: { ...state.settings, theme },
        }));
      },

      setUser: (user) => set({ user }),
    }),
    {
      name: 'incomia-storage',
      // Solo persistir settings y userId — la data financiera se recarga siempre
      partialize: (state) => ({
        settings: state.settings,
        userId: state.userId,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
