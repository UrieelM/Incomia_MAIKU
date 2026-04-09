import * as React from 'react';
import { cn } from '../../utils/cn';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'emerald';
  size?: 'sm' | 'md' | 'lg' | 'icon';
  isLoading?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', isLoading, children, disabled, ...props }, ref) => {
    const variants = {
      primary: 'bg-primary dark:bg-primary-dark text-white hover:bg-primary-dark dark:hover:bg-slate-800 shadow-md dark:shadow-none',
      secondary: 'bg-slate-100 dark:bg-white/5 text-slate-900 dark:text-white hover:bg-slate-200 dark:hover:bg-white/10',
      emerald: 'bg-emerald-500 text-white hover:bg-emerald-600 shadow-md shadow-emerald-200 dark:shadow-none',
      outline: 'border border-slate-200 dark:border-white/10 bg-transparent hover:bg-slate-50 dark:hover:bg-white/5 dark:text-white',
      ghost: 'bg-transparent hover:bg-slate-100 dark:hover:bg-white/5 dark:text-white',
    };

    const sizes = {
      sm: 'h-9 px-3 text-xs',
      md: 'h-11 px-6 text-sm',
      lg: 'h-13 px-8 text-base font-semibold',
      icon: 'h-10 w-10 flex items-center justify-center',
    };

    return (
      <button
        ref={ref}
        disabled={isLoading || disabled}
        className={cn(
          'inline-flex items-center justify-center rounded-xl font-medium premium-transition disabled:opacity-50 disabled:pointer-events-none active:scale-95',
          variants[variant],
          sizes[size],
          className
        )}
        {...props}
      >
        {isLoading ? (
          <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
        ) : null}
        {children}
      </button>
    );
  }
);

Button.displayName = 'Button';

export { Button };
