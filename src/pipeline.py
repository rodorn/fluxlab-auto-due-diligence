"""Orkiestracja: oferta + porownywalne -> pelny raport."""

from __future__ import annotations

from typing import List

from .models import Offer, Report
from .benchmark import benchmark_price
from .redflags import detect_red_flags
from .checklist import build_checklist
from .negotiation import build_negotiation


def build_report(
    offer: Offer, comparables: List[Offer], is_sample: bool = False
) -> Report:
    benchmark = benchmark_price(offer, comparables)
    red_flags = detect_red_flags(offer, benchmark)
    checklist = build_checklist(offer)
    negotiation = build_negotiation(offer, benchmark, red_flags, checklist)
    return Report(
        offer=offer,
        benchmark=benchmark,
        red_flags=red_flags,
        checklist=checklist,
        negotiation=negotiation,
        is_sample=is_sample,
    )
