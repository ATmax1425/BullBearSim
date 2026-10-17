// The simulated market runs on Indian Standard Time; show every timestamp in
// IST regardless of the viewer's own timezone.
const TIME_FORMAT: Intl.DateTimeFormatOptions = {
  timeZone: 'Asia/Kolkata',
  hour12: false,
  hour: '2-digit',
  minute: '2-digit',
  second: '2-digit',
};

export function formatTime(value: string | number): string {
  return new Date(value).toLocaleTimeString('en-IN', TIME_FORMAT);
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
  return '₹' + toIndianNumber(price);
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

export function formatChangeShort(changePct: number): string {
  const rounded = Number(changePct.toFixed(2));
  if (rounded === 0) return '0.00%'; // avoid "-0.00%" / "+0.00%"
  const sign = rounded > 0 ? '+' : '';
  return `${sign}${rounded.toFixed(2)}%`;
}
