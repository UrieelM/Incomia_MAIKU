import { Link, useNavigate } from 'react-router-dom';
import { User, Mail, Lock, ArrowRight, EyeOff, Sparkles } from 'lucide-react';
import { Input } from '../components/ui/Input';
import { Button } from '../components/ui/Button';

export function RegisterPage() {
  const navigate = useNavigate();

  const handleRegister = (e: React.FormEvent) => {
    e.preventDefault();
    // Simulate successful registration and redirect to login
    navigate('/login');
  };

  return (
    <div className="w-full max-w-md space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div className="space-y-2">
        <h2 className="text-4xl font-display font-bold text-primary tracking-tight">Crea tu cuenta.</h2>
        <p className="text-slate-500">
          Únete a la nueva era del manejo inteligente de ingresos con IA.
        </p>
      </div>

      <form className="space-y-6" onSubmit={handleRegister}>
        <div className="space-y-4">
          <Input 
            label="Nombre Completo" 
            placeholder="Juan Pérez" 
            type="text"
            icon={<User className="w-5 h-5" />}
          />
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

        <div className="space-y-4">
          <label className="flex items-start gap-3 cursor-pointer group">
            <input type="checkbox" className="mt-1 w-4 h-4 rounded border-slate-300 text-primary focus:ring-primary transition-colors cursor-pointer" />
            <span className="text-xs text-slate-500 leading-relaxed group-hover:text-primary transition-colors">
              Al registrarte, aceptas nuestros <a href="#" className="font-bold text-primary">Términos de Servicio</a> y la <a href="#" className="font-bold text-primary">Política de Privacidad</a>.
            </span>
          </label>
        </div>

        <Button className="w-full h-12 text-lg shadow-xl shadow-primary/10 group" type="submit">
          Crear Cuenta
          <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
        </Button>
      </form>

      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <span className="w-full border-t border-slate-200" />
        </div>
        <div className="relative flex justify-center text-xs uppercase">
          <span className="bg-[#fdfeff] px-4 text-slate-400 font-bold tracking-widest">O suscríbete con</span>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <Button variant="outline" className="h-11 border-slate-200 hover:bg-slate-50 p-0">
          <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
            <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
            <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
            <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" />
            <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
          </svg>
        </Button>
        <Button variant="outline" className="h-11 border-slate-200 hover:bg-slate-50 p-0">
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
            <path d="M22 12c0-5.52-4.48-10-10-10S2 6.48 2 12c0 4.99 3.66 9.12 8.44 9.88v-6.99H7.9v-2.89h2.54V9.8c0-2.51 1.49-3.89 3.78-3.89 1.09 0 2.23.19 2.23.19v2.47h-1.26c-1.24 0-1.63.77-1.63 1.56v1.88h2.78l-.45 2.89h-2.33v6.99C18.34 21.12 22 16.99 22 12z" />
          </svg>
        </Button>
        <Button variant="outline" className="h-11 border-slate-200 hover:bg-slate-50 p-0 text-primary font-bold">
          in
        </Button>
      </div>

      <p className="text-center text-sm text-slate-500">
        ¿Ya tienes una cuenta?{' '}
        <Link to="/login" className="font-bold text-primary hover:text-emerald-600 transition-colors">Inicia Sesión.</Link>
      </p>

      {/* Subtle UI Detail */}
      <div className="flex justify-center">
        <div className="flex items-center gap-2 bg-slate-50 px-4 py-2 rounded-full border border-slate-100">
          <Sparkles className="w-4 h-4 text-emerald-500" />
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">IA Verification Ready</span>
        </div>
      </div>
    </div>
  );
}
