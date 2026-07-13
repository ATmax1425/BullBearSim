import type { Tick } from '../types';

export function calcChange(
  price: number,
  reference: number,
): { absolute: number; percent: number } {
  if (reference === 0) return { absolute: 0, percent: 0 };
  return {
    absolute: price - reference,
    percent: ((price - reference) / reference) * 100,
  };
}

export function calcChangeFromChartWindow(
  ticks: Tick[],
): { absolute: number; percent: number } | null {
  if (ticks.length < 2) return null;
  const latest = ticks[ticks.length - 1].price;
  const reference = ticks[0].price;
  return calcChange(latest, reference);
}

export function calcDirection(
  changePct: number,
): 'up' | 'down' | 'flat' {
  if (changePct > 0.01) return 'up';
  if (changePct < -0.01) return 'down';
  return 'flat';
}