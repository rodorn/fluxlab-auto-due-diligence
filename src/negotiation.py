"""Generator gotowego skryptu negocjacji na podstawie analizy."""

from __future__ import annotations

from typing import Dict, List

from .models import Offer, BenchmarkResult, RedFlag, ChecklistItem


def _cost_midpoint(cost_str: str) -> int:
    """Szacuje srodek widelka kosztu z tekstu typu '2500-6000'."""
    import re

    nums = [int(n) for n in re.findall(r"\d{3,}", cost_str.replace(" ", ""))]
    if not nums:
        return 0
    if len(nums) == 1:
        return nums[0]
    return (min(nums) + max(nums)) // 2


def build_negotiation(
    offer: Offer,
    benchmark: BenchmarkResult,
    red_flags: List[RedFlag],
    checklist: List[ChecklistItem],
) -> Dict:
    points: List[Dict] = []

    # 1. Argument cenowy z benchmarku.
    if benchmark.deviation_pct is not None and benchmark.fair_value_pln:
        if benchmark.deviation_pct > 3:
            over = (
                int(round(offer.price_pln - benchmark.fair_value_pln))
                if offer.price_pln
                else 0
            )
            points.append(
                {
                    "label": "Cena powyzej rynku",
                    "amount": max(over, 0),
                    "script": (
                        f"Sprawdzilem {benchmark.n_used} porownywalnych ofert (rocznik, przebieg, moc). "
                        f"Wycena rynkowa to okolo {benchmark.fair_value_pln:,} zl".replace(
                            ",", " "
                        )
                        + f", a Panska cena jest wyzsza o okolo {abs(round(benchmark.deviation_pct))}%. "
                        f"Realna cena to {benchmark.fair_value_pln:,} zl".replace(
                            ",", " "
                        )
                        + "."
                    ),
                }
            )

    # 2. Argumenty z red-flag (HIGH/MED) powiazane z kosztem.
    hi = [f for f in red_flags if f.severity in ("HIGH", "MED")]
    for f in hi[:3]:
        points.append(
            {
                "label": f.tag.replace("-", " ").capitalize(),
                "amount": None,
                "script": f.message,
            }
        )

    # 3. Najdrozsze pozycje z checklisty jako karta przetargowa.
    ranked = sorted(checklist, key=lambda c: _cost_midpoint(c.cost_pln), reverse=True)
    top = [c for c in ranked if _cost_midpoint(c.cost_pln) >= 2000][:3]
    for c in top:
        mid = _cost_midpoint(c.cost_pln)
        points.append(
            {
                "label": f"{c.system}: {c.issue.split(':')[0][:40]}",
                "amount": mid // 2,  # bufor = polowa sredniego kosztu ryzyka
                "script": (
                    f"To model, w ktorym typowo pojawia sie: {c.issue.split(':')[0].strip()}. "
                    f"Naprawa to koszt rzedu {c.cost_pln} zl. Prosze o zapas w cenie na to ryzyko."
                ),
            }
        )

    total_leverage = sum(p["amount"] for p in points if p.get("amount"))

    # Rekomendowana cena docelowa.
    target_price = None
    if offer.price_pln:
        base = benchmark.fair_value_pln or offer.price_pln
        target_price = int(max(base - total_leverage * 0.5, base * 0.85))

    summary = ""
    if offer.price_pln and target_price:
        summary = (
            f"Punkt startowy negocjacji: {target_price:,} zl".replace(",", " ")
            + f" (z ceny ofertowej {offer.price_pln:,} zl".replace(",", " ")
            + f"). Laczny material negocjacyjny to okolo {total_leverage:,} zl".replace(
                ",", " "
            )
            + " argumentow (cena vs rynek + ryzyka techniczne)."
        )

    opening = (
        "Dzien dobry, jestem realnie zainteresowany. Zrobilem analize tej oferty na tle rynku "
        "i typowych usterek tego modelu. Mam trzy konkretne punkty, ktore obnizaja wartosc auta. "
        "Jesli sie dogadamy co do ceny, jestem gotowy sfinalizowac szybko."
    )

    return {
        "opening": opening,
        "points": points,
        "total_leverage_pln": total_leverage,
        "target_price_pln": target_price,
        "summary": summary,
    }
