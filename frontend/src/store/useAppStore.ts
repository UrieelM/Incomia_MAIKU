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
import { 
  mockAppSettings, 
  mockFinancialSummary, 
  mockFinancialAdvice, 
  mockLiquidityPredictions,
  mockSavingGoals
} from '../mocks/financialData';




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
  
  // ─ Simulación Local (Cojinete/Cushion) ─────────────────────────────────────
  totalIncome: number;
  totalExpenses: number;
  iaMemory: LogIncomeRequest[];
  showReward: boolean;

  // ─ Simulación Temporal (Historial Mensual) ─────────────────────────────────
  simulationOffset: number;
  monthlyHistory: Record<string, {
    incomes: LogIncomeRequest[];
    expenses: Expense[];
    salaryDesired: number;
    totalIncome: number;
    totalExpenses: number;
  }>;
  stabilityReserveBalance: number;
  simulationError: string | null;



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
  addSavingGoal: (goal: SavingGoal) => void;
  setShowReward: (show: boolean) => void;
  resetData: () => void;
  advanceMonth: () => void;
  regressMonth: () => void;
  clearSimulationError: () => void;
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

      summary: mockFinancialSummary,
      salaryConfig: {

        desiredAmount: 0,
        frequency: 'monthly',
        recommendedAmount: 0,
        confidence: 100,
        impact: 0
      },
      savingGoals: mockSavingGoals,

      cashFlowHistory: [],
      expenses: [],
      advice: mockFinancialAdvice,
      predictions: mockLiquidityPredictions,
      settings: mockAppSettings,


      forecast: null,
      aiAdvice: null,
      isLoadingForecast: false,
      isLoadingAIAdvice: false,

      totalIncome: 0,
      totalExpenses: 0,
      iaMemory: [],
      showReward: false,

      simulationOffset: 0,
      monthlyHistory: {},
      stabilityReserveBalance: 0,
      simulationError: null,




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
          } else {
            // Bypass para Demo si no hay sesión
            set({
              user: { id: 'demo-user-id', name: 'Usuario Demo', email: 'demo@incomia.ai' },
              userId: 'demo-user-id',
              isAuthenticated: true,
            });
          }
          // Carga silenciosa de datos en background
          get().fetchDashboardData().catch(() => {});
        } catch {
          // Si Cognito falla totalmente (ej. falta red), forzamos login demo
          set({
            user: { id: 'demo-user-id', name: 'Usuario Demo', email: 'demo@incomia.ai' },
            userId: 'demo-user-id',
            isAuthenticated: true,
          });
          get().fetchDashboardData().catch(() => {});
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
          // Intentar Auth Real
          try {
            await cognitoSignIn(email, password);
            const userInfo = await getCurrentUserInfo();
            if (userInfo) {
              set({
                user: { id: userInfo.id, name: userInfo.name, email: userInfo.email },
                userId: userInfo.id,
                isAuthenticated: true,
              });
            }
          } catch (e) {
            console.warn("Cognito Login failed, switching to Demo Mode", e);
            // Si falla Cognito, entramos como demo
            set({
              user: { id: 'demo-user-id', name: 'Usuario Demo', email: email || 'demo@incomia.ai' },
              userId: 'demo-user-id',
              isAuthenticated: true,
            });
          }

          set({ isAuthLoading: false });
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
        const { userId, simulationOffset } = get();
        if (!userId) return;

        // Si estamos en simulación histórica, no sobrescribimos con mocks
        if (simulationOffset !== 0) {
          set({ isLoading: false });
          return;
        }

        set({ isLoading: true, error: null });
        try {
          const [summary, salaryConfig, advice, predictions, cashFlowHistory, expenses] =
            await Promise.all([
              financialService.getSummary(userId),
              financialService.getSalaryConfig(userId),
              financialService.getFinancialAdvice(userId),
              financialService.getPredictions(userId),
              financialService.getCashFlowData(userId),
              financialService.getTransactions(userId),
            ]);

          const expenseList = expenses
            .filter(tx => tx.amount < 0 || tx.type === 'expense')
            .map(tx => ({
              id: tx.id,
              category: tx.category,
              concept: tx.source,
              amount: Math.abs(tx.amount),
              type: 'fixed' as const,
            }));

          const currentConfig = get().salaryConfig;
          const finalConfig = (currentConfig?.desiredAmount && currentConfig.desiredAmount > 0) 
            ? currentConfig 
            : (salaryConfig || currentConfig);

          set({ 
            summary, 
            salaryConfig: finalConfig, 
            advice, 
            predictions, 
            cashFlowHistory, 
            expenses: expenseList.length > 0 ? expenseList : get().expenses,
            isLoading: false 
          });


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

        set((state) => {
          const currentMonthKey = new Date(new Date().getFullYear(), new Date().getMonth() + state.simulationOffset, 1).toISOString().slice(0, 7);
          const history = { ...state.monthlyHistory };
          if (!history[currentMonthKey]) {
            history[currentMonthKey] = { incomes: [], expenses: [], salaryDesired: state.salaryConfig?.desiredAmount || 0, totalIncome: 0, totalExpenses: 0 };
          }
          history[currentMonthKey].incomes.push(data);
          history[currentMonthKey].totalIncome += data.amount;

          return {
            totalIncome: state.totalIncome + data.amount,
            iaMemory: [...state.iaMemory, data],
            monthlyHistory: history
          };
        });


        // Lógica de Recompensa: Si ingreso > (sueldo deseado + 5000) y colchón > 10000
        const currentSalary = get().salaryConfig?.desiredAmount || 0;
        const cushion = get().totalIncome - get().totalExpenses;
        if (data.amount > currentSalary + 5000 && cushion > 10000) {
          set({ showReward: true });
        }

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

        const result = await financialService.logExpense(userId, data);
        
        set((state) => {
          const currentMonthKey = new Date(new Date().getFullYear(), new Date().getMonth() + state.simulationOffset, 1).toISOString().slice(0, 7);
          const history = { ...state.monthlyHistory };
          if (!history[currentMonthKey]) {
            history[currentMonthKey] = { incomes: [], expenses: [], salaryDesired: state.salaryConfig?.desiredAmount || 0, totalIncome: 0, totalExpenses: 0 };
          }
          history[currentMonthKey].expenses.push({
            id: result.transaction_id,
            category: result.category_label || 'Otros',
            concept: data.merchant || data.notes || 'Gasto manual',
            amount: data.amount,
            type: 'variable'
          });

          history[currentMonthKey].totalExpenses += data.amount;

          return {
            totalExpenses: state.totalExpenses + data.amount,
            expenses: [
              {
                id: result.transaction_id,
                category: result.category_label || 'Otros',
                concept: data.merchant || data.notes || 'Gasto manual',
                amount: data.amount,
                date: data.date,
                type: 'variable'
              },
              ...state.expenses
            ],
            monthlyHistory: history
          };
        });

        return result;
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

      addSavingGoal: (goal) => {
        set((state) => ({
          savingGoals: [goal, ...state.savingGoals]
        }));
      },

      setShowReward: (show) => set({ showReward: show }),

      resetData: () => {
        set({
          totalIncome: 0,
          totalExpenses: 0,
          iaMemory: [],
          expenses: [],
          savingGoals: [],
          salaryConfig: {
            desiredAmount: 0,
            frequency: 'monthly',
            recommendedAmount: 0,
            confidence: 100,
            impact: 0
          },
          summary: {
            nextIncome: { amount: 0, date: 'Pendiente', description: 'Registra datos' },
            stabilityReserve: { current: 0, target: 0, progress: 0, message: 'Vacío' },
            recentTransactions: []
          },
          showReward: false,
          simulationOffset: 0,
          monthlyHistory: {},
          stabilityReserveBalance: 0,
          simulationError: null,
          cashFlowHistory: []
        });
        console.log("Incomia: Estado reiniciado a 0 (Secret Reset)");
      },

      advanceMonth: () => {
        const { totalIncome, stabilityReserveBalance, salaryConfig, simulationOffset, monthlyHistory } = get();
        
        // Límite de 12 meses (0 a 11)
        if (simulationOffset >= 11) {
          return;
        }

        const desired = salaryConfig?.desiredAmount || 0;
        const available = totalIncome + stabilityReserveBalance;

        if (available < desired && desired > 0) {
          set({ simulationError: `Atención: Fondos insuficientes para cubrir tu sueldo deseado de ${desired} MXN. La simulación continuará permitiendo un balance negativo en tu colchón.` });
          // No retornamos, permitimos avanzar (no-bloqueante)
        }


        const currentMonthKey = new Date(new Date().getFullYear(), new Date().getMonth() + simulationOffset, 1).toISOString().slice(0, 7);
        const currentRecord = monthlyHistory[currentMonthKey] || { incomes: [], expenses: [], salaryDesired: desired, totalIncome: 0, totalExpenses: 0 };
        
        const surplus = totalIncome - desired;
        const newBalance = stabilityReserveBalance + surplus;
        const monthLabel = new Date(new Date().getFullYear(), new Date().getMonth() + simulationOffset, 1)
          .toLocaleDateString('es-ES', { month: 'short' }).toUpperCase();

        set((state) => ({
          simulationOffset: state.simulationOffset + 1,
          stabilityReserveBalance: newBalance,
          totalIncome: 0,
          totalExpenses: 0,
          iaMemory: [],
          expenses: [],
          cashFlowHistory: [...state.cashFlowHistory, { month: monthLabel, real: totalIncome, stabilized: desired }],
          summary: {
            ...state.summary!,
            stabilityReserve: {
              ...state.summary!.stabilityReserve,
              current: newBalance,
              message: newBalance > stabilityReserveBalance 
                ? "¡Excelente! Has fortalecido tu colchón este mes." 
                : "Se ha utilizado parte de la reserva para estabilizar tu sueldo deseado."
            },

            nextIncome: {
              ...state.summary!.nextIncome,
              amount: desired
            },
            recentTransactions: []
          },
          monthlyHistory: {
            ...state.monthlyHistory,
            [currentMonthKey]: {
              ...currentRecord,
              totalIncome,
              salaryDesired: desired,
              incomes: state.iaMemory,
              expenses: state.expenses
            }
          }
        }));
      },

      regressMonth: () => {
        const { simulationOffset } = get();
        if (simulationOffset <= 0) return;

        set((state) => {
          const newOffset = state.simulationOffset - 1;

          const monthKey = new Date(new Date().getFullYear(), new Date().getMonth() + newOffset, 1).toISOString().slice(0, 7);
          const history = state.monthlyHistory[monthKey];

          if (history) {
            return {
              simulationOffset: newOffset,
              totalIncome: history.totalIncome,
              totalExpenses: history.totalExpenses,
              expenses: history.expenses,
              iaMemory: history.incomes,
              summary: {
                ...state.summary!,
                stabilityReserve: {
                  ...state.summary!.stabilityReserve,
                  current: state.stabilityReserveBalance
                },
                nextIncome: {
                  ...state.summary!.nextIncome,
                  amount: history.salaryDesired
                },
                recentTransactions: history.incomes.map((inc, i) => ({
                  id: `sim-inc-hist-${i}`,
                  date: inc.date,
                  source: inc.merchant || 'Depósito',
                  category: 'Income',
                  amount: inc.amount,
                  status: 'processed',
                  type: 'income' as const
                }))

              }
            };
          }

          return { simulationOffset: newOffset };
        });
      },

      clearSimulationError: () => set({ simulationError: null }),
    }),

    {
      name: 'incomia-storage',
      partialize: (state) => ({
        settings: state.settings,
        userId: state.userId,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
        totalIncome: state.totalIncome,
        totalExpenses: state.totalExpenses,
        iaMemory: state.iaMemory,
        salaryConfig: state.salaryConfig,
        savingGoals: state.savingGoals,
        expenses: state.expenses,
        summary: state.summary,
        monthlyHistory: state.monthlyHistory,
        stabilityReserveBalance: state.stabilityReserveBalance,
        cashFlowHistory: state.cashFlowHistory,
        simulationOffset: state.simulationOffset
      }),
    }

  )
);


