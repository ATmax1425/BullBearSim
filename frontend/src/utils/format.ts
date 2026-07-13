export function formatTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleTimeString('en-IN', { hour12: false });
}

export function formatTimeShort(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleTimeString('en-IN', {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

function toIndianNumber(n: number): string {
  const [intPart, fracPart] = n.toFixed(2).split('.');
  const lastThree = intPart.slice(-3);
  const rest = intPart.slice(0, -3);
  const grouped =
    rest.length > 0
      ? rest.replace(/\B(?=(\d{2})+(?!\d))/g, ',') + ',' + lastThree
      : lastThree;
  return fracPart ? grouped + '.' + fracPart : grouped;
}

export function formatIndianPrice(price: number): string {
  return '\u20B9' + toIndianNumber(price);
}

export function formatIndianNumber(n: number): string {
  return toIndianNumber(n);
}

export function formatIndianVolume(volume: number): string {
  if (volume >= 10_000_000) {
    return (volume / 10_000_000).toFixed(1) + 'Cr';
  }
  if (volume >= 100_000) {
    return (volume / 100_000).toFixed(1) + 'L';
  }
  if (volume >= 1_000) {
    return (volume / 1_000).toFixed(1) + 'K';
  }
  return volume.toString();
}

export function formatChange(change: number, changePct: number): string {
  const sign = change >= 0 ? '+' : '';
  return `${sign}\u20B9${toIndianNumber(Math.abs(change))} (${sign}${changePct.toFixed(2)}%)`;
}

export function formatChangeShort(changePct: number): string {
  const sign = changePct >= 0 ? '+' : '';
  return `${sign}${changePct.toFixed(2)}%`;
}

export function timeAgo(timestamp: number): string {
  const seconds = Math.floor((Date.now() - timestamp) / 1000);
  if (seconds < 5) return 'just now';
  if (seconds < 60) return `${seconds}s ago`;
  const mins = Math.floor(seconds / 60);
  return `${mins}m ago`;
}