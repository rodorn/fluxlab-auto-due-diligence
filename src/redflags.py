"""Detektor red-flag z tresci ogloszenia i danych oferty."""

from __future__ import annotations

import datetime
import re
from typing import List, Optional

from .models import Offer, RedFlag, BenchmarkResult

CURRENT_YEAR = datetime.date.today().year

# Frazy sugerujace szkody mimo deklaracji "bezwypadkowy".
DAMAGE_HINTS = [
    "lakierowan",
    "lakierowany",
    "malowan",
    "po malowaniu",
    "slady",
    "rysa",
    "rysy",
    "wgniec",
    "otarci",
    "uszkodz",
    "powypadk",
    "stluczk",
    "kolizj",
    "do poprawek",
    "do poprawki",
    "wymiana blotnika",
    "wymieniony blotnik",
    "wymiana zderzaka",
    "szpachl",
    "kit",
    "korozj",
    "rdza",
    "ognisko rdzy",
    "pekniet",
]

ACCIDENT_FREE = [
    "bezwypadkow",
    "bezwypadkowy",
    "100% bezwypadkowy",
    "auto bezwypadkowe",
]

# Frazy ryzyka technicznego.
TECH_RISK = {
    "silnik do remontu": "HIGH",
    "silnik do wymiany": "HIGH",
    "stukajacy silnik": "HIGH",
    "stuka silnik": "HIGH",
    "nie odpala": "HIGH",
    "spala olej": "HIGH",
    "bierze olej": "HIGH",
    "dwumasa do wymiany": "MED",
    "sprzeglo do wymiany": "MED",
    "turbina do": "HIGH",
    "swieci check": "MED",
    "kontrolka silnika": "MED",
    "dpf usuniet": "MED",
    "egr usuniet": "MED",
    "wirki usuniet": "LOW",
    "swap": "MED",
    "zamiennik silnika": "HIGH",
    "wymieniony silnik": "MED",
    "skrzynia szarpie": "HIGH",
    "do drobnych poprawek": "LOW",
    "usterka": "MED",
    "awaria": "MED",
}

# Frazy handlowe / naciski (soft flags).
HYPE = [
    "stan idealny",
    "stan bardzo dobry",
    "jak nowy",
    "nic nie inwestujesz",
    "gotowy do jazdy",
    "wsiadasz i jedziesz",
    "okazja",
    "pilnie",
    "pilna sprzedaz",
    "zamiana",
    "mozliwa zamiana",
]

IMPORT_HINTS = [
    "sprowadzon",
    "sprowadzony",
    "z niemiec",
    "importowany",
    "z zagranicy",
    "swiezo sprowadzony",
]


def _norm(s: str) -> str:
    return (s or "").lower()


def _mileage_from_text(text: str) -> List[int]:
    """Wyszukuje liczby przebiegu (km) w tresci, do wykrycia niespojnosci."""
    found = []
    for m in re.finditer(r"(\d[\d\s\.]{2,})\s*(?:tys\.?\s*)?km", _norm(text)):
        raw = m.group(1).replace(" ", "").replace(".", "")
        if not raw.isdigit():
            continue
        val = int(raw)
        # "150 tys km" -> 150000
        if "tys" in text.lower()[m.start() : m.end()] and val < 1000:
            val *= 1000
        if 1000 <= val <= 1_000_000:
            found.append(val)
    return found


def detect_red_flags(
    offer: Offer, benchmark: Optional[BenchmarkResult] = None
) -> List[RedFlag]:
    flags: List[RedFlag] = []
    desc = _norm(offer.description)
    title = _norm(offer.title)
    blob = desc + " " + title

    # 1. "bezwypadkowy" vs slady szkod.
    declares_accident_free = any(a in blob for a in ACCIDENT_FREE)
    damage_found = [h for h in DAMAGE_HINTS if h in blob]
    if declares_accident_free and damage_found:
        flags.append(
            RedFlag(
                "HIGH",
                "sprzecznosc-bezwypadkowy",
                "Ogloszenie deklaruje 'bezwypadkowy', a jednoczesnie wspomina o sladach/naprawach "
                "("
                + ", ".join(sorted(set(damage_found))[:4])
                + "). Zweryfikuj miernikiem lakieru.",
            )
        )
    elif damage_found and not declares_accident_free:
        flags.append(
            RedFlag(
                "MED",
                "slady-napraw",
                "Opis wspomina slady/naprawy blacharsko-lakiernicze ("
                + ", ".join(sorted(set(damage_found))[:4])
                + "). Sprawdz grubosc lakieru.",
            )
        )

    # 2. Niespojny przebieg (kilka roznych wartosci w tresci).
    text_mileages = _mileage_from_text(offer.description)
    all_m = set(text_mileages)
    if offer.mileage_km:
        all_m.add(offer.mileage_km)
    big = [m for m in all_m if m >= 5000]
    if (
        len(big) >= 2
        and (max(big) - min(big)) >= 10000
        and (max(big) - min(big)) / max(big) > 0.05
    ):
        flags.append(
            RedFlag(
                "HIGH",
                "niespojny-przebieg",
                "Rozne wartosci przebiegu w ofercie/opisie: "
                + ", ".join(f"{m:,} km".replace(",", " ") for m in sorted(big))
                + ". Mozliwy cofniety licznik, sprawdz historie VIN.",
            )
        )

    # 3. Podejrzanie niski przebieg do wieku (mozliwe cofniecie).
    if offer.year and offer.mileage_km and offer.year <= CURRENT_YEAR:
        age = max(CURRENT_YEAR - offer.year, 1)
        km_per_year = offer.mileage_km / age
        if age >= 6 and km_per_year < 8000:
            flags.append(
                RedFlag(
                    "MED",
                    "niski-przebieg",
                    f"Bardzo niski sredni przebieg {int(km_per_year):,} km/rok".replace(
                        ",", " "
                    )
                    + f" ({offer.mileage_km:,} km w {age} lat).".replace(",", " ")
                    + " Rzadkosc przy takim wieku, potwierdz przebieg w historii serwisowej i CEPiK.",
                )
            )

    # 4. Frazy ryzyka technicznego.
    for phrase, sev in TECH_RISK.items():
        if phrase in blob:
            flags.append(
                RedFlag(
                    sev,
                    "ryzyko-techniczne",
                    f"Opis zawiera: '{phrase}'. Potencjalny koszt lub ukryta wada, wyceň naprawe przed zakupem.",
                )
            )

    # 5. Cena mocno ponizej rynku bez uzasadnienia.
    if (
        benchmark
        and benchmark.deviation_pct is not None
        and benchmark.deviation_pct <= -15
    ):
        flags.append(
            RedFlag(
                "MED",
                "cena-podejrzanie-niska",
                f"Cena okolo {abs(round(benchmark.deviation_pct))}% ponizej wyceny rynkowej. "
                "Okazja albo sygnal ukrytej wady, zbadaj auto szczegolnie dokladnie.",
            )
        )

    # 6. Brak historii serwisowej.
    if desc and not any(
        k in blob
        for k in ["serwisow", "aso", "ksiazka serwisow", "faktury", "udokumentowan"]
    ):
        flags.append(
            RedFlag(
                "LOW",
                "brak-historii",
                "Brak wzmianki o udokumentowanej historii serwisowej. Popros o faktury/ksiazke i wpisy przebiegu.",
            )
        )

    # 7. Import.
    imp = [h for h in IMPORT_HINTS if h in blob]
    if imp:
        flags.append(
            RedFlag(
                "LOW",
                "import",
                "Auto sprowadzone. Sprawdz oryginalny przebieg za granica (raport historii) i stan po transporcie.",
            )
        )

    # 8. Frazy handlowe / presja.
    hype = [h for h in HYPE if h in blob]
    if len(hype) >= 2:
        flags.append(
            RedFlag(
                "LOW",
                "jezyk-marketingowy",
                "Duzo fraz sprzedazowych/presji ("
                + ", ".join(hype[:3])
                + "). Nie sugeruj sie opisem, licza sie fakty i ogledziny.",
            )
        )

    # Deduplikacja po (tag, message).
    uniq = []
    seen = set()
    order = {"HIGH": 0, "MED": 1, "LOW": 2}
    for f in flags:
        key = (f.tag, f.message)
        if key not in seen:
            seen.add(key)
            uniq.append(f)
    uniq.sort(key=lambda f: order.get(f.severity, 3))
    return uniq
