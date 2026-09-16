from src.models import Offer
from src.benchmark import benchmark_price, _linreg_slope


def _comps():
    # Cena maleje wraz z przebiegiem (spojny rynek).
    return [
        Offer(year=2011, mileage_km=km, power_hp=306, fuel="Diesel", price_pln=price)
        for km, price in [
            (150000, 70000),
            (160000, 68000),
            (170000, 66000),
            (180000, 64000),
            (190000, 62000),
            (200000, 60000),
            (210000, 58000),
            (220000, 56000),
            (230000, 54000),
            (240000, 52000),
        ]
    ]


def test_slope_is_negative_for_normal_market():
    xs = [c.mileage_km for c in _comps()]
    ys = [c.price_pln for c in _comps()]
    slope = _linreg_slope(xs, ys)
    assert slope is not None and slope < 0


def test_fair_value_matches_trend_at_target_mileage():
    target = Offer(
        year=2011, mileage_km=190000, power_hp=306, fuel="Diesel", price_pln=62000
    )
    res = benchmark_price(target, _comps())
    # Fair value dla 190000 km powinno byc bliskie 62000 wg trendu.
    assert res.fair_value_pln is not None
    assert 59000 <= res.fair_value_pln <= 65000
    assert abs(res.deviation_pct) < 6  # cena zgodna z rynkiem


def test_overpriced_offer_flagged():
    target = Offer(
        year=2011, mileage_km=190000, power_hp=306, fuel="Diesel", price_pln=80000
    )
    res = benchmark_price(target, _comps())
    assert res.deviation_pct > 15
    assert "powyzej rynku" in res.verdict.lower()


def test_underpriced_offer_flagged():
    target = Offer(
        year=2011, mileage_km=190000, power_hp=306, fuel="Diesel", price_pln=48000
    )
    res = benchmark_price(target, _comps())
    assert res.deviation_pct < -12


def test_too_few_comparables_low_confidence():
    target = Offer(
        year=2011, mileage_km=190000, power_hp=306, fuel="Diesel", price_pln=62000
    )
    res = benchmark_price(target, _comps()[:2])
    assert res.confidence == "niska"
    assert res.fair_value_pln is None


def test_higher_mileage_lowers_fair_value():
    comps = _comps()
    low = benchmark_price(
        Offer(
            year=2011, mileage_km=150000, power_hp=306, fuel="Diesel", price_pln=60000
        ),
        comps,
    )
    high = benchmark_price(
        Offer(
            year=2011, mileage_km=240000, power_hp=306, fuel="Diesel", price_pln=60000
        ),
        comps,
    )
    assert low.fair_value_pln > high.fair_value_pln
