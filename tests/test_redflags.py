from src.models import Offer, BenchmarkResult
from src.redflags import detect_red_flags


def _tags(flags):
    return {f.tag for f in flags}


def test_accident_free_contradiction():
    offer = Offer(
        title="BMW",
        make="BMW",
        year=2012,
        mileage_km=150000,
        description="Auto bezwypadkowe, przedni blotnik lakierowany po otarciu.",
    )
    flags = detect_red_flags(offer)
    assert "sprzecznosc-bezwypadkowy" in _tags(flags)
    assert any(
        f.severity == "HIGH" for f in flags if f.tag == "sprzecznosc-bezwypadkowy"
    )


def test_inconsistent_mileage():
    offer = Offer(
        make="BMW",
        year=2012,
        mileage_km=180000,
        description="Przebieg 180000 km, w ksiazce ostatni wpis 215000 km.",
    )
    flags = detect_red_flags(offer)
    assert "niespojny-przebieg" in _tags(flags)


def test_low_mileage_for_age():
    offer = Offer(
        make="Audi", year=2010, mileage_km=60000, description="Zadbany egzemplarz."
    )
    flags = detect_red_flags(offer)
    assert "niski-przebieg" in _tags(flags)


def test_technical_risk_phrase():
    offer = Offer(
        make="BMW",
        year=2013,
        mileage_km=200000,
        description="Silnik do remontu, spala olej.",
    )
    flags = detect_red_flags(offer)
    assert "ryzyko-techniczne" in _tags(flags)
    assert any(f.severity == "HIGH" for f in flags if f.tag == "ryzyko-techniczne")


def test_price_far_below_market():
    offer = Offer(
        make="BMW",
        year=2013,
        mileage_km=150000,
        price_pln=40000,
        description="Sprzedam.",
    )
    bench = BenchmarkResult(
        fair_value_pln=60000,
        n_used=20,
        n_total=30,
        deviation_pct=-20.0,
        price_low=50000,
        price_high=70000,
        per_km_pln=-0.2,
        verdict="",
        confidence="wysoka",
    )
    flags = detect_red_flags(offer, bench)
    assert "cena-podejrzanie-niska" in _tags(flags)


def test_clean_listing_minimal_flags():
    offer = Offer(
        make="Toyota",
        year=2018,
        mileage_km=90000,
        price_pln=70000,
        description="Auto z pelna historia serwisowa w ASO, faktury, udokumentowany przebieg.",
    )
    flags = detect_red_flags(offer)
    # Nie powinno byc HIGH na czystym ogloszeniu.
    assert not any(f.severity == "HIGH" for f in flags)


def test_severity_sorting():
    offer = Offer(
        make="BMW",
        year=2010,
        mileage_km=50000,
        description="Auto bezwypadkowe ale lakierowane, silnik do remontu, sprowadzone z Niemiec.",
    )
    flags = detect_red_flags(offer)
    severities = [f.severity for f in flags]
    order = {"HIGH": 0, "MED": 1, "LOW": 2}
    assert severities == sorted(severities, key=lambda s: order[s])
