import type { Direction, Tick } from '../types';

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

/** Direction of a percentage change; moves within ±0.01% count as flat. */
export function calcDirection(changePct: number): Direction {
  if (changePct > 0.01) return 'up';
  if (changePct < -0.01) return 'down';
  return 'flat';
}

/** Direction of one tick versus the previous tick of the same symbol. */
export function calcTickDirection(price: number, previousPrice: number): Direction {
  if (price > previousPrice) return 'up';
  if (price < previousPrice) return 'down';
  return 'flat';
}

export const directionTextColor: Record<Direction, string> = {
  up: 'text-green-400',
  down: 'text-red-400',
  flat: 'text-gray-400',
};
