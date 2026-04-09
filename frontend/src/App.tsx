import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthLayout } from './layouts/AuthLayout';
import { MainLayout } from './layouts/MainLayout';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { DashboardPage } from './pages/DashboardPage';
import { SalaryConfigPage } from './pages/SalaryConfigPage';
import { DataTrainingPage } from './pages/DataTrainingPage';
import { SavingsPage } from './pages/SavingsPage';
import { CashFlowPage } from './pages/CashFlowPage';
import { ExpensesPage } from './pages/ExpensesPage';
import { SettingsPage } from './pages/SettingsPage';
import { AIAdvisorPage } from './pages/AIAdvisorPage';
import { ProtectedRoute } from './components/shared/ProtectedRoute';
import { useAppStore } from './store/useAppStore';

function App() {
  const initAuth = useAppStore((s) => s.initAuth);

  // Verifica si hay una sesión activa de Cognito al arrancar la app
  useEffect(() => {
    initAuth();
  }, [initAuth]);

  return (
    <BrowserRouter>
      <Routes>
        {/* Auth Routes */}
        <Route element={<AuthLayout />}>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
        </Route>

        {/* Main Protected Routes */}
        <Route element={<ProtectedRoute />}>
          <Route element={<MainLayout />}>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/salary" element={<SalaryConfigPage />} />
            <Route path="/cashflow" element={<CashFlowPage />} />
            <Route path="/deposits" element={<DataTrainingPage />} />
            <Route path="/expenses" element={<ExpensesPage />} />
            <Route path="/savings" element={<SavingsPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="/ai" element={<AIAdvisorPage />} />
          </Route>
        </Route>
        
        {/* Missing routes redirect to Dashboard */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
