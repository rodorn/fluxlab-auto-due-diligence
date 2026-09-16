"""Wspolne struktury danych dla narzedzia due-diligence."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class Offer:
    """Pojedyncza oferta auta (badana lub porownawcza)."""

    title: str = ""
    make: str = ""
    model: str = ""
    generation: str = ""  # np. "E60", "C6", "W212", "F01"
    year: Optional[int] = None
    mileage_km: Optional[int] = None  # przebieg
    power_hp: Optional[int] = None  # moc
    fuel: str = ""  # diesel / benzyna / hybryda
    engine: str = ""  # np. "3.0d N57", "2.0 TDI CR"
    price_pln: Optional[int] = None
    url: str = ""
    description: str = ""  # tresc ogloszenia (dla red-flag detektora)
    seller: str = ""  # prywatny / firma
    location: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class BenchmarkResult:
    fair_value_pln: Optional[int]
    n_used: int
    n_total: int
    deviation_pct: Optional[float]  # + = drozej od fair value, - = taniej
    price_low: Optional[int]
    price_high: Optional[int]
    per_km_pln: Optional[float]  # oszacowana utrata wartosci na 1 km
    verdict: str = ""
    confidence: str = ""  # wysoka / srednia / niska


@dataclass
class RedFlag:
    severity: str  # HIGH / MED / LOW
    tag: str
    message: str


@dataclass
class ChecklistItem:
    system: str  # np. "Silnik", "Skrzynia biegow"
    issue: str
    check: str  # co sprawdzic / jak zweryfikowac
    cost_pln: str  # orientacyjny koszt naprawy


@dataclass
class Report:
    offer: Offer
    benchmark: BenchmarkResult
    red_flags: list = field(default_factory=list)
    checklist: list = field(default_factory=list)
    negotiation: dict = field(default_factory=dict)
    is_sample: bool = False
