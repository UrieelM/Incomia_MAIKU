/**
 * ProtectedRoute — Guard de rutas autenticadas
 *
 * Lógica:
 *  1. Mientras initAuth() resuelve la sesión → muestra spinner
 *  2. Si hay sesión activa → renderiza la ruta hija (Outlet)
 *  3. Si no hay sesión → redirige a /login
 *
 * initAuth() se llama en App.tsx al montar la aplicación.
 */

import { Navigate, Outlet } from 'react-router-dom';
import { useAppStore } from '../../store/useAppStore';

export function ProtectedRoute() {
  const isAuthenticated = useAppStore((s) => s.isAuthenticated);
  const isAuthLoading = useAppStore((s) => s.isAuthLoading);

  // Mientras Cognito verifica la sesión local, mostramos un loader
  if (isAuthLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-[#fdfeff]">
        <div className="flex flex-col items-center gap-4">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-emerald-500 border-t-transparent" />
          <p className="text-sm text-slate-400 font-medium">Verificando sesión...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}
