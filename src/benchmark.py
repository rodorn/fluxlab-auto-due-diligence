"""Benchmark ceny oferty vs zbior porownywalnych aut.

Logika:
1. Odfiltruj porownywalne do podobnych (rok, moc, ten sam typ paliwa).
2. Oszacuj wplyw przebiegu na cene (regresja liniowa cena~przebieg).
3. Znormalizuj ceny porownywalnych do przebiegu badanego auta.
4. Fair value = mediana znormalizowanych cen. Odchylka = (cena - fair)/fair.
"""

from __future__ import annotations

from statistics import median
from typing import List, Optional

from .models import Offer, BenchmarkResult


def _similar(
    target: Offer, comp: Offer, year_tol: int = 2, power_tol: float = 0.20
) -> bool:
    if comp.price_pln is None or comp.mileage_km is None:
        return False
    if target.year and comp.year and abs(comp.year - target.year) > year_tol:
        return False
    if target.power_hp and comp.power_hp:
        if abs(comp.power_hp - target.power_hp) > max(15, target.power_hp * power_tol):
            return False
    if target.fuel and comp.fuel and target.fuel.lower() != comp.fuel.lower():
        return False
    return True


def _linreg_slope(xs: List[float], ys: List[float]) -> Optional[float]:
    """Slope regresji ys~xs metoda najmniejszych kwadratow."""
    n = len(xs)
    if n < 3:
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    denom = sum((x - mx) ** 2 for x in xs)
    if denom == 0:
        return None
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / denom


def benchmark_price(target: Offer, comparables: List[Offer]) -> BenchmarkResult:
    used = [c for c in comparables if _similar(target, c)]

    # Fallback: jesli filtr za ostry, poluzuj kryteria.
    if len(used) < 5:
        used = [
            c
            for c in comparables
            if c.price_pln is not None
            and c.mileage_km is not None
            and (not (target.year and c.year) or abs(c.year - target.year) <= 4)
        ]

    n_total = len([c for c in comparables if c.price_pln is not None])
    if len(used) < 3:
        return BenchmarkResult(
            fair_value_pln=None,
            n_used=len(used),
            n_total=n_total,
            deviation_pct=None,
            price_low=None,
            price_high=None,
            per_km_pln=None,
            verdict="Za malo danych porownawczych do wiarygodnej wyceny.",
            confidence="niska",
        )

    mileages = [float(c.mileage_km) for c in used]
    prices = [float(c.price_pln) for c in used]

    slope = _linreg_slope(mileages, prices)
    # Slope powinien byc ujemny (wiekszy przebieg = nizsza cena). Jesli dodatni
    # lub brak, uzyj konserwatywnego domyslnego (utrata ~0.2 zl/km).
    if slope is None or slope > 0:
        slope = -0.20

    target_mileage = (
        float(target.mileage_km) if target.mileage_km is not None else median(mileages)
    )

    adjusted = [p + slope * (target_mileage - m) for p, m in zip(prices, mileages)]
    adjusted = [
        max(a, 1000.0) for a in adjusted
    ]  # cena nie moze zejsc ponizej resztowej

    fair = median(adjusted)
    lo = min(adjusted)
    hi = max(adjusted)

    deviation = None
    verdict = ""
    if target.price_pln is not None and fair > 0:
        deviation = (target.price_pln - fair) / fair * 100.0
        if deviation <= -12:
            verdict = "Cena WYRAZNIE ponizej rynku. Okazja albo ukryta wada, sprawdz dokladnie."
        elif deviation <= -4:
            verdict = "Cena lekko ponizej sredniej rynkowej."
        elif deviation < 6:
            verdict = "Cena zgodna z rynkiem (fair value)."
        elif deviation < 15:
            verdict = "Cena powyzej rynku, jest pole do negocjacji."
        else:
            verdict = "Cena ZNACZNIE powyzej rynku. Silny argument negocjacyjny."
    else:
        verdict = "Brak ceny oferty, podano tylko wycene rynkowa."

    if len(used) >= 15:
        confidence = "wysoka"
    elif len(used) >= 7:
        confidence = "srednia"
    else:
        confidence = "niska"

    return BenchmarkResult(
        fair_value_pln=int(round(fair)),
        n_used=len(used),
        n_total=n_total,
        deviation_pct=round(deviation, 1) if deviation is not None else None,
        price_low=int(round(lo)),
        price_high=int(round(hi)),
        per_km_pln=round(slope, 3),
        verdict=verdict,
        confidence=confidence,
    )
