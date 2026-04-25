def eur_to_sats(eur: float, btc_eur_rate: float) -> int:
    sats = round((eur / btc_eur_rate) * 100_000_000)
    return max(0, int(sats))

