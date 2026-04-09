import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  User,
  Mail,
  Lock,
  ArrowRight,
  Eye,
  EyeOff,
  Sparkles,
  AlertCircle,
  CheckCircle2,
} from 'lucide-react';
import { Input } from '../components/ui/Input';
import { Button } from '../components/ui/Button';
import { useAppStore } from '../store/useAppStore';
import { confirmSignUp } from '../lib/cognito';

type Step = 'form' | 'verify';

export function RegisterPage() {
  const navigate = useNavigate();
  const { register, isAuthLoading, authError, clearAuthError } = useAppStore();

  // ─ Campos del formulario ──────────────────────────────────────────────────
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [salaryFrequency, setSalaryFrequency] =
    useState<'weekly' | 'biweekly' | 'monthly'>('monthly');
  const [accepted, setAccepted] = useState(false);

  // ─ Flujo de verificación de email ────────────────────────────────────────
  const [step, setStep] = useState<Step>('form');
  const [verifyCode, setVerifyCode] = useState('');
  const [verifyError, setVerifyError] = useState('');
  const [verifyLoading, setVerifyLoading] = useState(false);

  // ─ Handlers ───────────────────────────────────────────────────────────────

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    clearAuthError();

    try {
      await register(email, password, name, salaryFrequency, 'suggestion');
      // Registro exitoso → pedir código de verificación
      setStep('verify');
    } catch {
      // El error queda en authError del store
    }
  };

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    setVerifyError('');
    setVerifyLoading(true);

    try {
      await confirmSignUp(email, verifyCode);
      // Email verificado → redirigir al login
      navigate('/login', { state: { message: 'Cuenta verificada. ¡Inicia sesión!' } });
    } catch (err: any) {
      setVerifyError(err.message || 'Código inválido. Intenta de nuevo.');
    } finally {
      setVerifyLoading(false);
    }
  };

  // ─ Vista de verificación ──────────────────────────────────────────────────

  if (step === 'verify') {
    return (
      <div className="w-full max-w-md space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
        <div className="space-y-2">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-emerald-100 rounded-full flex items-center justify-center">
              <Mail className="w-5 h-5 text-emerald-600" />
            </div>
            <h2 className="text-3xl font-display font-bold text-primary tracking-tight">
              Verifica tu correo
            </h2>
          </div>
          <p className="text-slate-500 text-sm">
            Te enviamos un código de 6 dígitos a{' '}
            <span className="font-semibold text-primary">{email}</span>. Ingrésalo para activar tu cuenta.
          </p>
        </div>

        {verifyError && (
          <div className="flex items-start gap-3 bg-red-50 border border-red-200 text-red-700 rounded-xl p-4">
            <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <p className="text-sm font-medium">{verifyError}</p>
          </div>
        )}

        <form className="space-y-6" onSubmit={handleVerify}>
          <Input
            label="Código de Verificación"
            placeholder="123456"
            type="text"
            value={verifyCode}
            onChange={(e) => setVerifyCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
            maxLength={6}
            required
          />

          <Button
            className="w-full h-12 text-lg shadow-xl shadow-primary/10 group"
            type="submit"
            disabled={verifyLoading || verifyCode.length < 6}
          >
            {verifyLoading ? (
              <span className="flex items-center gap-2">
                <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Verificando...
              </span>
            ) : (
              <>
                <CheckCircle2 className="w-5 h-5 mr-2" />
                Verificar Cuenta
              </>
            )}
          </Button>
        </form>

        <p className="text-center text-sm text-slate-500">
          ¿No recibiste el correo?{' '}
          <button
            type="button"
            className="font-bold text-primary hover:text-emerald-600 transition-colors"
            onClick={() => setStep('form')}
          >
            Volver e intentar de nuevo.
          </button>
        </p>
      </div>
    );
  }

  // ─ Vista principal del formulario ─────────────────────────────────────────

  return (
    <div className="w-full max-w-md space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div className="space-y-2">
        <h2 className="text-4xl font-display font-bold text-primary tracking-tight">
          Crea tu cuenta.
        </h2>
        <p className="text-slate-500">
          Únete a la nueva era del manejo inteligente de ingresos con IA.
        </p>
      </div>

      {authError && (
        <div className="flex items-start gap-3 bg-red-50 border border-red-200 text-red-700 rounded-xl p-4">
          <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <p className="text-sm font-medium">{authError}</p>
        </div>
      )}

      <form className="space-y-6" onSubmit={handleRegister}>
        <div className="space-y-4">
          <Input
            label="Nombre Completo"
            placeholder="Juan Pérez"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            icon={<User className="w-5 h-5" />}
            required
          />
          <Input
            label="Correo Electrónico"
            placeholder="nombre@ejemplo.com"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            icon={<Mail className="w-5 h-5" />}
            required
          />
          <Input
            label="Contraseña"
            placeholder="Mínimo 8 caracteres"
            type={showPassword ? 'text' : 'password'}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            icon={<Lock className="w-5 h-5" />}
            rightIcon={
              <button
                type="button"
                className="text-slate-400 hover:text-primary transition-colors"
                onClick={() => setShowPassword((v) => !v)}
              >
                {showPassword ? (
                  <Eye className="w-5 h-5" />
                ) : (
                  <EyeOff className="w-5 h-5" />
                )}
              </button>
            }
            required
          />

          {/* Frecuencia de pago */}
          <div className="space-y-2">
            <label className="block text-sm font-semibold text-primary">
              ¿Con qué frecuencia quieres recibir tu sueldo?
            </label>
            <div className="grid grid-cols-3 gap-2">
              {(
                [
                  { value: 'weekly', label: 'Semanal' },
                  { value: 'biweekly', label: 'Quincenal' },
                  { value: 'monthly', label: 'Mensual' },
                ] as const
              ).map(({ value, label }) => (
                <button
                  key={value}
                  type="button"
                  onClick={() => setSalaryFrequency(value)}
                  className={`h-11 rounded-xl text-sm font-semibold border-2 transition-all ${
                    salaryFrequency === value
                      ? 'border-emerald-500 bg-emerald-50 text-emerald-700'
                      : 'border-slate-200 text-slate-500 hover:border-slate-300'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <label className="flex items-start gap-3 cursor-pointer group">
            <input
              type="checkbox"
              checked={accepted}
              onChange={(e) => setAccepted(e.target.checked)}
              className="mt-1 w-4 h-4 rounded border-slate-300 text-primary focus:ring-primary transition-colors cursor-pointer"
            />
            <span className="text-xs text-slate-500 leading-relaxed group-hover:text-primary transition-colors">
              Al registrarte, aceptas nuestros{' '}
              <a href="#" className="font-bold text-primary">
                Términos de Servicio
              </a>{' '}
              y la{' '}
              <a href="#" className="font-bold text-primary">
                Política de Privacidad
              </a>
              .
            </span>
          </label>
        </div>

        <Button
          className="w-full h-12 text-lg shadow-xl shadow-primary/10 group"
          type="submit"
          disabled={isAuthLoading || !name || !email || !password || !accepted}
        >
          {isAuthLoading ? (
            <span className="flex items-center gap-2">
              <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              Creando cuenta...
            </span>
          ) : (
            <>
              Crear Cuenta
              <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
            </>
          )}
        </Button>
      </form>

      <p className="text-center text-sm text-slate-500">
        ¿Ya tienes una cuenta?{' '}
        <Link
          to="/login"
          className="font-bold text-primary hover:text-emerald-600 transition-colors"
        >
          Inicia Sesión.
        </Link>
      </p>

      <div className="flex justify-center">
        <div className="flex items-center gap-2 bg-slate-50 px-4 py-2 rounded-full border border-slate-100">
          <Sparkles className="w-4 h-4 text-emerald-500" />
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
            IA Verification Ready
          </span>
        </div>
      </div>
    </div>
  );
}
