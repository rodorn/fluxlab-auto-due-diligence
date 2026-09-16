"""Model-specific checklista typowych usterek.

Baza realnych, powszechnie znanych usterek dla popularnych modeli premium i
popularnych diesli. Dopasowanie po marce + generacji + jednostce napedowej.
Kwoty to orientacyjne koszty naprawy w PL (warsztat niezalezny, 2025/2026).
"""

from __future__ import annotations

from typing import List

from .models import Offer, ChecklistItem

# Kazdy wpis: klucze dopasowania + lista usterek.
# match: (make, generations[], engine_keywords[])
DEFECTS_DB = [
    {
        "id": "bmw_e60_e63_e64",
        "label": "BMW serii 5 (E60/E61) i 6 (E63/E64) 2003-2010",
        "make": ["bmw"],
        "generations": [
            "e60",
            "e61",
            "e63",
            "e64",
            "serii 5",
            "serii 6",
            "645",
            "650",
            "545",
            "550",
            "535",
            "530",
            "525",
        ],
        "items": [
            (
                "Silnik",
                "N62 (V8 benzyna): uszczelki alternatora i pokrywy zaworow, zbieranie oleju, pekajaca chlodnica oleju miedzy blokami",
                "Slady oleju pod alternatorem, dym, poziom oleju; historia wymian uszczelek",
                "2500-6000",
            ),
            (
                "Silnik",
                "M57 (3.0d): wirki w kolektorze ssacym (swirl flaps) urywaja sie i niszcza silnik",
                "Czy wirki usuniete/zaslepione; blad DDE; szarpanie",
                "800-2500 (usuniecie) / 15000+ (jesli urwane)",
            ),
            (
                "Skrzynia biegow",
                "Automat GA6HP: brak wymian oleju, szarpanie przy niskich predkosciach, mechatronik",
                "Historia wymiany oleju co 60-80 tys; jazda probna w korku; komunikaty transmisji",
                "1500-8000",
            ),
            (
                "Elektronika",
                "iDrive/CCC, moduly komfortu, czujniki, akumulator komorkowy zawodny",
                "Wszystkie funkcje elektryczne; bledy na skanerze; wiek akumulatora",
                "500-3000",
            ),
            (
                "Zawieszenie",
                "Wahacze przednie, lozyska, u E63/E64 amortyzatory i tuleje",
                "Stuki na nierownosciach; luzy; rownomierne zuzycie opon",
                "1500-4000",
            ),
        ],
    },
    {
        "id": "bmw_f01_f02_7",
        "label": "BMW serii 7 (F01/F02) 2008-2015",
        "make": ["bmw"],
        "generations": ["f01", "f02", "serii 7", "730", "740", "750", "760"],
        "items": [
            (
                "Silnik",
                "N57 (3.0d) / N63 (V8 twin-turbo): lancuch rozrzadu (N57 wczesne), turbo, chlodnica oleju; N63 zuzycie oleju i turbiny",
                "Historia serwisowa; poziom i dolewki oleju; dym z wydechu; praca turbin",
                "5000-20000",
            ),
            (
                "Uklad wtryskowy",
                "Diesel: wtryskiwacze piezo, pompa wysokiego cisnienia, DPF przy jezdzie miejskiej",
                "Rowna praca na zimno; bledy wtrysku; zapchany DPF (regeneracje)",
                "1500-9000",
            ),
            (
                "Zawieszenie pneumatyczne",
                "Miechy pneumatyczne tylnej (i przedniej) osi, sprezarka",
                "Czy auto sie podnosi rowno po nocy; syk powietrza; komunikaty EDC",
                "1200-6000",
            ),
            (
                "Skrzynia biegow",
                "Automat ZF 8HP/6HP: wymagana wymiana oleju, mechatronik",
                "Historia wymiany oleju; plynnosc zmian; kickdown",
                "1500-8000",
            ),
            (
                "Elektronika",
                "Bogate wyposazenie = duzo modulow do awarii; akumulatory (2 szt)",
                "Test wszystkich funkcji; pelny odczyt bledow; kondycja akumulatorow",
                "1000-5000",
            ),
        ],
    },
    {
        "id": "bmw_nseries_engines",
        "label": "Silniki BMW N-series (N47/N57 diesel, N20/N63 benzyna)",
        "make": ["bmw"],
        "generations": [
            "n47",
            "n57",
            "n20",
            "n63",
            "118d",
            "120d",
            "320d",
            "520d",
            "x3",
            "x5",
        ],
        "items": [
            (
                "Rozrzad",
                "N47/N20: lancuch rozrzadu z tylu silnika, rozciaga sie i zrywa (kosztowna naprawa, silnik do wyjecia)",
                "Charakterystyczny halas z tylu silnika na zimno; historia wymiany lancucha",
                "4000-9000",
            ),
            (
                "Turbosprezarka",
                "Zuzycie turbo, luz walka, wycieki oleju",
                "Dym niebieski/czarny; swist; ubytki oleju",
                "2500-6000",
            ),
            (
                "EGR/DPF",
                "Zaklejanie zaworu EGR i chlodnicy EGR, zapychanie DPF przy krotkich trasach",
                "Historia napraw EGR; regeneracje DPF; jazda glownie miejska = ryzyko",
                "800-4000",
            ),
        ],
    },
    {
        "id": "audi_a6_c6_c7",
        "label": "Audi A6 C6 (2004-2011) i C7 (2011-2018)",
        "make": ["audi"],
        "generations": ["c6", "c7", "a6"],
        "items": [
            (
                "Silnik",
                "2.0 TDI (CR): zawor EGR, DPF; 3.0 TDI: chlodnica EGR i lancuchy; 2.0 TFSI: zuzycie oleju (tloki/pierscienie)",
                "2.0 TFSI: dolewki oleju (nawet 1l/1000km); 3.0 TDI: halas lancucha na zimno",
                "1500-12000",
            ),
            (
                "Rozrzad",
                "Lancuch rozrzadu w 2.0 TFSI i niektorych TDI, napinacz slabnie",
                "Halas przy rozruchu; historia wymiany lancucha i napinacza",
                "3000-7000",
            ),
            (
                "Skrzynia multitronic",
                "CVT multitronic (przod): awaryjny, kosztowna regeneracja; S tronic (DSG) sprzeglo/mechatronik",
                "Szarpanie, wibracje przy ruszaniu; historia serwisu skrzyni",
                "3000-9000",
            ),
            (
                "Zawieszenie",
                "Wahacze wieloelementowe (duzo elementow), zawieszenie pneumatyczne (allroad/adaptive)",
                "Stuki; luzy wahaczy; poziomowanie pneumatyki",
                "2000-6000",
            ),
            (
                "Elektronika",
                "Moduly komfortu, MMI, czujniki, korozja zlacz",
                "Test MMI, klimatyzacji, elektryki; pelny odczyt bledow",
                "800-4000",
            ),
        ],
    },
    {
        "id": "merc_w211_w212",
        "label": "Mercedes klasy E W211 (2002-2009) i W212 (2009-2016)",
        "make": ["mercedes", "mercedes-benz", "merc"],
        "generations": [
            "w211",
            "w212",
            "klasy e",
            "e220",
            "e250",
            "e280",
            "e320",
            "e350",
        ],
        "items": [
            (
                "Nadwozie/korozja",
                "W211: korozja (blotniki, klapa, progi, drzwi) mimo wieku; W212 lepiej ale sprawdz",
                "Ogniska rdzy, pecherze pod lakierem, spody drzwi i klapy",
                "1000-8000",
            ),
            (
                "Uklad SBC (W211)",
                "Hamulce elektrohydrauliczne SBC: pompa z licznikiem cykli, kosztowna wymiana",
                "Komunikat 'Visit workshop / brake'; wiek i przebieg pompy SBC",
                "3000-6000",
            ),
            (
                "Silnik diesel (OM642 3.0 V6)",
                "Chlodnica oleju (wycieki na V silnika), przewody, wtryskiwacze",
                "Slady oleju w widelku V; dolewki; rowna praca",
                "2000-7000",
            ),
            (
                "Skrzynia 7G-Tronic",
                "Plyta sterujaca (konduktor) i wymiana oleju; przekladnia sprawna przy serwisie",
                "Historia wymiany oleju; szarpniecia; komunikaty",
                "1500-6000",
            ),
            (
                "Zawieszenie Airmatic",
                "Pneumatyka Airmatic: miechy i sprezarka (wersje z zawieszeniem powietrznym)",
                "Rowne poziomowanie; syk; komunikaty poziomu",
                "1500-6000",
            ),
        ],
    },
    {
        "id": "vag_20_tdi_cr",
        "label": "Popularny diesel 2.0 TDI (VAG: VW/Audi/Skoda/Seat) common rail",
        "make": ["volkswagen", "vw", "skoda", "seat", "audi"],
        "generations": [
            "2.0 tdi",
            "tdi",
            "passat",
            "golf",
            "octavia",
            "superb",
            "a4",
            "a3",
        ],
        "engine_keywords": ["2.0 tdi", "2.0tdi", "tdi"],
        "items": [
            (
                "Silnik",
                "Pekanie glowicy / zawirowywacze; wersje CR: wtryskiwacze; pompa oleju (walek szescioboczny w starszych)",
                "Rowna praca; dym; kontrolki; historia wtryskiwaczy",
                "2000-9000",
            ),
            (
                "EGR + DPF",
                "Zapchany DPF i EGR przy jezdzie miejskiej, kosztowna regeneracja/wymiana",
                "Regeneracje w historii; jazda glownie krotkie trasy = ryzyko; poziom AdBlue (nowsze)",
                "800-5000",
            ),
            (
                "Dwumasa + sprzeglo",
                "Kolo dwumasowe i sprzeglo, glosna praca na luzie/przy wysprzeglaniu",
                "Halas kolo dwumasy; wibracje; historia wymiany",
                "2500-5000",
            ),
            (
                "Skrzynia DSG",
                "DSG (DQ250/DQ200): mechatronik i sprzegla, wymagana wymiana oleju",
                "Szarpanie; historia serwisu DSG; komunikaty",
                "2500-8000",
            ),
        ],
    },
    {
        "id": "generic_30_diesel",
        "label": "Ogolny diesel 3.0 (premium, duza moc)",
        "make": [],
        "generations": [],
        "engine_keywords": ["3.0d", "3.0 tdi", "3.0 d", "30d", "3.0 cdi", "3.0d"],
        "items": [
            (
                "Turbodoladowanie",
                "Pojedyncze/bi-turbo: zuzycie, luzy, wycieki; przy duzej mocy obciazone",
                "Swist, dym, ubytki oleju; kondycja turbin",
                "3000-12000",
            ),
            (
                "DPF + EGR",
                "Zapychanie przy jezdzie miejskiej; kosztowna wymiana DPF; AdBlue w nowszych",
                "Regeneracje; nie kupuj auta jezdzacego tylko po miescie bez tras",
                "1500-7000",
            ),
            (
                "Uklad wtryskowy",
                "Wtryskiwacze i pompa wysokiego cisnienia, drogie w duzych dieslach",
                "Rowna praca na zimno; bledy wtrysku",
                "2000-9000",
            ),
        ],
    },
]

# Uniwersalne pozycje dodawane zawsze (auta uzywane, kazdy model).
UNIVERSAL_ITEMS = [
    (
        "Historia i dokumenty",
        "Cofniety licznik / niespojna historia przebiegu",
        "Sprawdz VIN w CEPiK (Historia Pojazdu), Carfax/AutoDNA, wpisy serwisowe wg dat i przebiegow",
        "raport 30-90 zl",
    ),
    (
        "Nadwozie/lakier",
        "Ukryte szkody powypadkowe mimo opisu 'bezwypadkowy'",
        "Miernik grubosci lakieru na kazdym elemencie; rownosc szczelin; slady spawania/kitowania",
        "pomiar gratis-100 zl",
    ),
    (
        "Ogledziny",
        "Stan techniczny wymaga fizycznej weryfikacji",
        "Ogledziny u niezaleznego mechanika + jazda probna + odczyt bledow (OBD)",
        "150-350 zl",
    ),
]


def _norm(s: str) -> str:
    return (s or "").lower()


def build_checklist(offer: Offer) -> List[ChecklistItem]:
    """Buduje checkliste dopasowana do konkretnej oferty."""
    make = _norm(offer.make)
    hay = " ".join(
        _norm(x)
        for x in (
            offer.make,
            offer.model,
            offer.generation,
            offer.engine,
            offer.title,
            offer.fuel,
        )
    )

    matched = []
    seen_ids = set()
    for entry in DEFECTS_DB:
        if entry["id"] in seen_ids:
            continue
        make_ok = (not entry["make"]) or any(
            m in make or m in hay for m in entry["make"]
        )
        gen_ok = (not entry["generations"]) or any(
            g in hay for g in entry["generations"]
        )
        eng_ok = any(k in hay for k in entry.get("engine_keywords", []))

        # Wpis dopasowany, gdy marka+generacja pasuja, albo slowo-klucz silnika pasuje.
        if (make_ok and gen_ok and (entry["make"] or entry["generations"])) or eng_ok:
            matched.append(entry)
            seen_ids.add(entry["id"])

    items: List[ChecklistItem] = []
    for entry in matched:
        for system, issue, check, cost in entry["items"]:
            items.append(
                ChecklistItem(system=system, issue=issue, check=check, cost_pln=cost)
            )

    for system, issue, check, cost in UNIVERSAL_ITEMS:
        items.append(
            ChecklistItem(system=system, issue=issue, check=check, cost_pln=cost)
        )

    return items


def matched_models(offer: Offer) -> List[str]:
    """Zwraca etykiety dopasowanych baz (do naglowka raportu)."""
    make = _norm(offer.make)
    hay = " ".join(
        _norm(x)
        for x in (
            offer.make,
            offer.model,
            offer.generation,
            offer.engine,
            offer.title,
            offer.fuel,
        )
    )
    labels = []
    for entry in DEFECTS_DB:
        make_ok = (not entry["make"]) or any(
            m in make or m in hay for m in entry["make"]
        )
        gen_ok = (not entry["generations"]) or any(
            g in hay for g in entry["generations"]
        )
        eng_ok = any(k in hay for k in entry.get("engine_keywords", []))
        if (make_ok and gen_ok and (entry["make"] or entry["generations"])) or eng_ok:
            labels.append(entry["label"])
    return labels
