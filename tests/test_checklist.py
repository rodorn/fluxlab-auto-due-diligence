from src.models import Offer
from src.checklist import build_checklist, matched_models, UNIVERSAL_ITEMS
from src.negotiation import build_negotiation
from src.benchmark import benchmark_price


def test_bmw_f01_matches_series7_db():
    offer = Offer(
        make="BMW",
        model="Seria 7",
        generation="F01",
        engine="3.0d N57",
        fuel="Diesel",
        year=2011,
    )
    labels = matched_models(offer)
    assert any("serii 7" in lab.lower() or "F01" in lab for lab in labels)
    items = build_checklist(offer)
    assert any(
        "pneumat" in i.issue.lower() or "turbo" in i.issue.lower() for i in items
    )


def test_audi_a6_c6_matches():
    offer = Offer(
        make="Audi",
        model="A6",
        generation="C6",
        engine="2.0 TDI",
        fuel="Diesel",
        year=2008,
    )
    labels = matched_models(offer)
    assert any("A6" in lab for lab in labels)


def test_mercedes_w211_matches():
    offer = Offer(
        make="Mercedes-Benz",
        model="Klasa E",
        generation="W211",
        fuel="Diesel",
        year=2006,
    )
    items = build_checklist(offer)
    assert any("SBC" in i.issue or "korozj" in i.issue.lower() for i in items)


def test_generic_diesel_engine_keyword_match():
    # Marka nieznana bazie, ale slowo-klucz silnika laczy z ogolnym 3.0 diesel.
    offer = Offer(make="Jaguar", model="XF", engine="3.0d", fuel="Diesel", year=2012)
    labels = matched_models(offer)
    assert any("3.0" in lab for lab in labels)


def test_universal_items_always_present():
    offer = Offer(make="Fiat", model="Panda", year=2015, fuel="Benzyna")
    items = build_checklist(offer)
    # Nawet bez dopasowania modelu maja byc pozycje uniwersalne (VIN, lakier, ogledziny).
    assert len(items) >= len(UNIVERSAL_ITEMS)
    assert any("VIN" in i.check or "CEPiK" in i.check for i in items)


def test_negotiation_generates_points_and_target():
    offer = Offer(
        make="BMW",
        model="Seria 7",
        generation="F01",
        engine="3.0d N57",
        fuel="Diesel",
        year=2011,
        mileage_km=190000,
        power_hp=306,
        price_pln=80000,
        description="Auto bezwypadkowe, lakierowany blotnik.",
    )
    comps = [
        Offer(year=2011, mileage_km=190000, power_hp=306, fuel="Diesel", price_pln=p)
        for p in [60000, 61000, 62000, 63000, 59000, 60500, 61500]
    ]
    bench = benchmark_price(offer, comps)
    from src.redflags import detect_red_flags

    rf = detect_red_flags(offer, bench)
    cl = build_checklist(offer)
    neg = build_negotiation(offer, bench, rf, cl)
    assert neg["points"]
    assert neg["target_price_pln"] is not None
    assert neg["target_price_pln"] < offer.price_pln
