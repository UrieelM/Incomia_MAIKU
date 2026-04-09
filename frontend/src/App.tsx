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
import { LandingPage } from './pages/LandingPage';


function App() {
  const initAuth = useAppStore((s) => s.initAuth);

  useEffect(() => {
    initAuth();
  }, [initAuth]);

  return (
    <BrowserRouter>
      <Routes>
        {/* Landing Page Bancaria */}
        <Route path="/" element={<LandingPage />} />

        {/* Auth Routes */}
        <Route element={<AuthLayout />}>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
        </Route>

        {/* Incomia App Flow */}
        <Route path="/app" element={<ProtectedRoute />}>
          <Route element={<MainLayout />}>
            <Route index element={<DashboardPage />} />
            <Route path="salary" element={<SalaryConfigPage />} />
            <Route path="cashflow" element={<CashFlowPage />} />
            <Route path="deposits" element={<DataTrainingPage />} />
            <Route path="expenses" element={<ExpensesPage />} />
            <Route path="savings" element={<SavingsPage />} />
            <Route path="settings" element={<SettingsPage />} />
            <Route path="ai" element={<AIAdvisorPage />} />
          </Route>
        </Route>
        
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}


export default App;
