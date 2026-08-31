import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatMetric(val: any, isPercent: boolean = false): string {
  if (val === null || val === undefined) return 'N/A';
  if (typeof val === 'object' && 'mean' in val && 'std' in val) {
    const mean = val.mean;
    const std = val.std;
    if (isPercent) {
      return `${(mean * 100).toFixed(2)}% ± ${(std * 100).toFixed(2)}%`;
    }
    return `${Number(mean).toFixed(4)} ± ${Number(std).toFixed(4)}`;
  }
  if (typeof val === 'number') {
    if (isPercent) {
      return `${(val * 100).toFixed(2)}%`;
    }
    return val.toFixed(4);
  }
  return String(val);
}
