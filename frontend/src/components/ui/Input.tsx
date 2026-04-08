import { forwardRef } from 'react';
import type { ReactNode } from 'react';
import { cn } from '../../utils/cn';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  icon?: ReactNode;
  rightIcon?: ReactNode;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, icon, rightIcon, ...props }, ref) => {
    return (
      <div className="w-full space-y-2 group">
        {label && (
          <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest px-1">
            {label}
          </label>
        )}
        <div className="relative">
          {icon && (
            <div className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-primary transition-colors">
              {icon}
            </div>
          )}
          <input
            ref={ref}
            className={cn(
              "w-full h-12 bg-slate-50 border border-slate-100 rounded-xl px-4 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-primary/5 focus:bg-white focus:border-primary/20 transition-all",
              icon && "pl-12",
              rightIcon && "pr-12",
              error && "border-red-500 focus:ring-red-500/5 focus:border-red-500",
              className
            )}
            {...props}
          />
          {rightIcon && (
            <div className="absolute right-4 top-1/2 -translate-y-1/2">
              {rightIcon}
            </div>
          )}
        </div>
        {error && <p className="text-[10px] font-bold text-red-500 px-1">{error}</p>}
      </div>
    );
  }
);

Input.displayName = 'Input';
