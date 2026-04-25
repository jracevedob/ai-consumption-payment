export function eurToSats(eur: number, btcEurRate: number) {
  // sats = eur / (eur per btc) * 1e8
  const sats = Math.round((eur / btcEurRate) * 100_000_000);
  return Math.max(0, sats);
}

export function roundEur(eur: number) {
  return Math.round(eur * 100) / 100;
}

