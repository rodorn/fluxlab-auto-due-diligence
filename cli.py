#!/usr/bin/env python3
"""FluxLab: Sprawdz auto przed zakupem. Interfejs CLI.

Tryby:
  1) Scrape Otomoto (oferta + porownywalne z wyszukiwarki):
       python cli.py --url <URL_OFERTY> --search <URL_WYSZUKIWANIA> --pdf out/raport.pdf
  2) Fallback z plikow lokalnych:
       python cli.py --offer offer.json --comparables comps.csv --pdf out/raport.pdf

Gdy scrape sie nie powiedzie, uzyj trybu 2 (pliki lokalne).
"""

from __future__ import annotations

import argparse
import sys

from src.pipeline import build_report
from src.report import generate_report
from src.scrape import (
    scrape_offer,
    scrape_comparables,
    load_offer_json,
    load_comparables_csv,
)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        description="FluxLab: raport due-diligence auta przed zakupem"
    )
    p.add_argument("--url", help="URL oferty Otomoto do analizy")
    p.add_argument("--search", help="URL wynikow wyszukiwania Otomoto (porownywalne)")
    p.add_argument("--offer", help="Plik JSON z danymi oferty (fallback)")
    p.add_argument("--comparables", help="Plik CSV z porownywalnymi (fallback)")
    p.add_argument("--html", default="", help="Sciezka wyjsciowa HTML")
    p.add_argument("--pdf", default="out/raport.pdf", help="Sciezka wyjsciowa PDF")
    p.add_argument(
        "--sample", action="store_true", help="Oznacz raport jako PROBKA/DEMO"
    )
    args = p.parse_args(argv)

    offer = None
    comparables = []

    # Tryb scrape.
    if args.url:
        print(f"[scrape] Pobieram oferte: {args.url}")
        try:
            offer = scrape_offer(args.url)
        except Exception as e:
            print(f"[scrape] Blad pobierania oferty: {e}", file=sys.stderr)
        if offer:
            print(f"[scrape] OK: {offer.title or offer.make} cena={offer.price_pln}")
        else:
            print(
                "[scrape] Nie udalo sie sparsowac oferty. Uzyj trybu --offer/--comparables.",
                file=sys.stderr,
            )
    if args.search:
        print(f"[scrape] Pobieram porownywalne: {args.search}")
        try:
            comparables = scrape_comparables(args.search)
            print(f"[scrape] Pobrano {len(comparables)} porownywalnych")
        except Exception as e:
            print(f"[scrape] Blad pobierania porownywalnych: {e}", file=sys.stderr)

    # Tryb fallback (uzupelnia braki).
    if offer is None and args.offer:
        offer = load_offer_json(args.offer)
        print(f"[fallback] Wczytano oferte z {args.offer}")
    if not comparables and args.comparables:
        comparables = load_comparables_csv(args.comparables)
        print(
            f"[fallback] Wczytano {len(comparables)} porownywalnych z {args.comparables}"
        )

    if offer is None:
        print(
            "BLAD: brak danych oferty. Podaj --url (dzialajacy scrape) albo --offer plik.json",
            file=sys.stderr,
        )
        return 2
    if not comparables:
        print(
            "UWAGA: brak porownywalnych, benchmark bedzie ograniczony.", file=sys.stderr
        )

    report = build_report(offer, comparables, is_sample=args.sample)
    out = generate_report(report, out_html=args.html, out_pdf=args.pdf)

    print("\n=== WYNIK ===")
    print(
        f"Fair value: {report.benchmark.fair_value_pln} zl "
        f"(odchylka: {report.benchmark.deviation_pct}%, {report.benchmark.n_used} porownywalnych)"
    )
    print(
        f"Red-flagi: {len(report.red_flags)}  |  Pozycje checklisty: {len(report.checklist)}"
    )
    if out.get("html"):
        print(f"HTML: {out['html']}")
    if out.get("pdf"):
        print(f"PDF:  {out['pdf']}")
    else:
        print("PDF: NIE wygenerowano (brak Chrome?). HTML dziala zawsze.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
