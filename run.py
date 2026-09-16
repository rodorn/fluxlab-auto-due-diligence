#!/usr/bin/env python3
"""Demo end-to-end na przykladowych danych (PROBKA).

Generuje raport HTML + PDF w out/ na wbudowanym, przykladowym datasecie.
Sluzy jako smoke-test (CI) i probka do pokazania klientom.
"""

from __future__ import annotations

import os

from src.pipeline import build_report
from src.report import generate_report
from src.scrape import load_offer_json, load_comparables_csv

HERE = os.path.dirname(os.path.abspath(__file__))


def main() -> int:
    offer = load_offer_json(os.path.join(HERE, "data", "sample_offer.json"))
    comps = load_comparables_csv(os.path.join(HERE, "data", "sample_comparables.csv"))
    report = build_report(offer, comps, is_sample=True)

    out_html = os.path.join(HERE, "out", "sample_raport.html")
    out_pdf = os.path.join(HERE, "out", "sample_raport.pdf")
    result = generate_report(report, out_html=out_html, out_pdf=out_pdf)

    print("=== DEMO / PROBKA ===")
    print(f"Oferta: {offer.title}")
    print(f"Cena ofertowa: {offer.price_pln} zl")
    print(
        f"Fair value: {report.benchmark.fair_value_pln} zl "
        f"(odchylka {report.benchmark.deviation_pct}%, "
        f"{report.benchmark.n_used}/{report.benchmark.n_total} porownywalnych, "
        f"wiarygodnosc: {report.benchmark.confidence})"
    )
    print(f"Red-flagi ({len(report.red_flags)}):")
    for f in report.red_flags:
        print(f"  [{f.severity}] {f.message}")
    print(f"Pozycje checklisty: {len(report.checklist)}")
    print(
        f"Rekomendowany punkt startowy negocjacji: {report.negotiation.get('target_price_pln')} zl"
    )
    print(f"HTML: {result.get('html')}")
    print(f"PDF:  {result.get('pdf') or 'NIE wygenerowano (brak Chrome)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
