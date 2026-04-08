import { Link, useNavigate } from 'react-router-dom';
import { Mail, Lock, ArrowRight, EyeOff, Sparkles } from 'lucide-react';
import { Input } from '../components/ui/Input';
import { Button } from '../components/ui/Button';
import { useAppStore } from '../store/useAppStore';

export function LoginPage() {
  const navigate = useNavigate();
  const setUser = useAppStore((state) => state.setUser);

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    // Simulate successful login
    setUser({
      id: 'user-1',
      name: 'Roberto Domínguez',
      email: 'roberto.d@incomia.ai',
      avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Roberto',
    });
    navigate('/');
  };

  return (
    <div className="w-full max-w-md space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div className="space-y-2">
        <h2 className="text-4xl font-display font-bold text-primary tracking-tight">Bienvenido de nuevo.</h2>
        <p className="text-slate-500">
          Ingresa tus credenciales para acceder a tu panel de control de IA.
        </p>
      </div>

      <form className="space-y-6" onSubmit={handleLogin}>
        <div className="space-y-4">
          <Input 
            label="Correo Electrónico" 
            placeholder="nombre@ejemplo.com" 
            type="email"
            icon={<Mail className="w-5 h-5" />}
          />
          <Input 
            label="Contraseña" 
            placeholder="••••••••" 
            type="password"
            icon={<Lock className="w-5 h-5" />}
            rightIcon={<button type="button" className="text-slate-400 hover:text-primary transition-colors"><EyeOff className="w-5 h-5" /></button>}
          />
        </div>

        <div className="flex items-center justify-between">
          <label className="flex items-center gap-2 cursor-pointer group">
            <input type="checkbox" className="w-4 h-4 rounded border-slate-300 text-primary focus:ring-primary transition-colors cursor-pointer" />
            <span className="text-sm text-slate-500 group-hover:text-primary transition-colors">Recordarme</span>
          </label>
          <a href="#" className="text-sm font-semibold text-emerald-600 hover:text-emerald-700 transition-colors">¿Olvidaste tu contraseña?</a>
        </div>

        <Button className="w-full h-12 text-lg shadow-xl shadow-primary/10 group" type="submit">
          Iniciar Sesión
          <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
        </Button>
      </form>

      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <span className="w-full border-t border-slate-200" />
        </div>
        <div className="relative flex justify-center text-xs uppercase">
          <span className="bg-[#fdfeff] px-4 text-slate-400 font-bold tracking-widest">O continúa con</span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Button variant="outline" className="h-11 border-slate-200 hover:bg-slate-50">
          <svg className="w-5 h-5 mr-4" viewBox="0 0 24 24" fill="currentColor">
            <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
            <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
            <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" />
            <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
          </svg>
          Google
        </Button>
        <Button variant="outline" className="h-11 border-slate-200 hover:bg-slate-50">
          <svg className="w-5 h-5 mr-4" fill="currentColor" viewBox="0 0 24 24">
            <path d="M22 12c0-5.52-4.48-10-10-10S2 6.48 2 12c0 4.99 3.66 9.12 8.44 9.88v-6.99H7.9v-2.89h2.54V9.8c0-2.51 1.49-3.89 3.78-3.89 1.09 0 2.23.19 2.23.19v2.47h-1.26c-1.24 0-1.63.77-1.63 1.56v1.88h2.78l-.45 2.89h-2.33v6.99C18.34 21.12 22 16.99 22 12z" />
          </svg>
          Facebook
        </Button>
      </div>

      <p className="text-center text-sm text-slate-500">
        ¿Aún no tienes cuenta?{' '}
        <Link to="/register" className="font-bold text-primary hover:text-emerald-600 transition-colors">Crea una ahora.</Link>
      </p>

      {/* Subtle UI Detail */}
      <div className="flex justify-center">
        <div className="flex items-center gap-2 bg-slate-50 px-4 py-2 rounded-full border border-slate-100">
          <Sparkles className="w-4 h-4 text-emerald-500" />
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">AI Security Enabled</span>
        </div>
      </div>
    </div>
  );
}
