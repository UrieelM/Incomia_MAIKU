import * as React from 'react';
import { cn } from '../../utils/cn';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  glass?: boolean;
}

const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, glass = false, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          'rounded-2xl border border-slate-100 dark:border-primary-light bg-white dark:bg-primary p-6 shadow-premium transition-all duration-300',
          glass && 'bg-white/70 dark:bg-primary/70 backdrop-blur-md border-white/20 dark:border-white/5',
          className
        )}
        {...props}
      />
    );
  }
);

Card.displayName = 'Card';

export { Card };
