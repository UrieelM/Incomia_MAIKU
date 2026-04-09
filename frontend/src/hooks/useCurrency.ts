import { useAppStore } from '../store/useAppStore';

export function useCurrency() {
  const currency = useAppStore((state) => state.settings.currency);

  const format = (amount: number) => {
    return new Intl.NumberFormat('es-MX', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 2,
    }).format(amount);
  };

  return { format, currency };
}
