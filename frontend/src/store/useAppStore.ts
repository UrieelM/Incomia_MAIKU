import { create } from 'zustand';
import type { 
  User, 
  FinancialSummary, 
  SalaryConfig, 
  SavingGoal, 
  CashFlowData, 
  Expense, 
  AppSettings,
  FinancialAdvice,
  LiquidityPrediction
} from '../types';
import { financialService } from '../services/financialService';
import { mockAppSettings, mockCashFlowHistory, mockExpenses, mockSavingGoals } from '../mocks/financialData';

/**
 * STATE MANAGEMENT - GLOBAL APP STORE
 * 
 * Incomia utiliza Zustand para la gestión de estado global. 
 * Este store centraliza la data financiera y orquestra las llamadas a servicios.
 * 
 * @see src/services/financialService.ts
 */

interface AppState {
  user: User | null;
  summary: FinancialSummary | null;
  salaryConfig: SalaryConfig | null;
  savingGoals: SavingGoal[];
  cashFlowHistory: CashFlowData[];
  expenses: Expense[];
  advice: FinancialAdvice[];
  predictions: LiquidityPrediction[];
  settings: AppSettings;
  isLoading: boolean;
  error: string | null;

  // Actions
  setUser: (user: User | null) => void;
  /** Dispara la carga inicial de todos los KPIs del Dashboard */
  fetchDashboardData: () => Promise<void>;
  /** Persiste los cambios de configuración salarial en el backend */
  updateSalary: (config: Partial<SalaryConfig>) => Promise<void>;
  /** Actualiza preferencias locales (moneda, notificaciones, etc.) */
  updateSettings: (settings: Partial<AppSettings>) => void;
  /** Cambia el tema global (Light/Dark) */
  setTheme: (theme: 'light' | 'dark') => void;
}

export const useAppStore = create<AppState>((set) => ({
  user: {
    id: 'user-1',
    name: 'Roberto Domínguez',
    email: 'roberto.d@incomia.ai',
    avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Roberto',
  },
  summary: null,
  salaryConfig: null,
  savingGoals: mockSavingGoals,
  cashFlowHistory: mockCashFlowHistory,
  expenses: mockExpenses,
  advice: [],
  predictions: [],
  settings: mockAppSettings,
  isLoading: false,
  error: null,

  setUser: (user) => set({ user }),

  /**
   * FLUJO: FETCH DASHBOARD DATA
   * 
   * Orquestra múltiples peticiones asíncronas para construir la vista principal.
   * Si alguna falla, se captura el error globalmente en el estado 'error'.
   */
  fetchDashboardData: async () => {
    set({ isLoading: true, error: null });
    try {
      const [summary, salaryConfig, advice, predictions] = await Promise.all([
        financialService.getSummary(),
        financialService.getSalaryConfig(),
        financialService.getFinancialAdvice(),
        financialService.getPredictions(),
      ]);
      set({ 
        summary, 
        salaryConfig, 
        advice, 
        predictions, 
        isLoading: false 
      });
    } catch (err) {
      set({ error: 'Failed to fetch financial data', isLoading: false });
    }
  },

  /**
   * FLUJO: UPDATE SALARY
   * 
   * Llama al servicio de actualización y sincroniza el estado local con la respuesta.
   */
  updateSalary: async (config) => {
    set({ isLoading: true, error: null });
    try {
      const updatedConfig = await financialService.updateSalaryConfig(config);
      set({ salaryConfig: updatedConfig, isLoading: false });
    } catch (err) {
      set({ error: 'Failed to update salary configuration', isLoading: false });
    }
  },

  updateSettings: (newSettings) => {
    set((state) => ({
      settings: { ...state.settings, ...newSettings }
    }));
  },

  setTheme: (theme) => {
    set((state) => ({
      settings: { ...state.settings, theme }
    }));
  },
}));
