"""Scraper Otomoto + loadery fallback (JSON oferta, CSV porownywalne).

Otomoto zwraca 200 na zadanie z naglowkiem przegladarki. Struktura strony bywa
zmienna (Next.js, __NEXT_DATA__), wiec parser probuje kilku metod, a przy
niepowodzeniu narzedzie i tak dziala w trybie fallback (pliki lokalne).
"""

from __future__ import annotations

import csv
import json
import re
import time
from typing import List, Optional

import requests
from bs4 import BeautifulSoup

from .models import Offer

UA = "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"
HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pl,en-US;q=0.7,en;q=0.3",
}


def _to_int(val) -> Optional[int]:
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return int(val)
    digits = re.sub(r"[^\d]", "", str(val))
    return int(digits) if digits else None


def fetch(url: str, timeout: int = 20) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=timeout)
    resp.raise_for_status()
    return resp.text


def _params_to_dict(node) -> dict:
    """Otomoto trzyma detale jako liste {key,value(s)} w __NEXT_DATA__."""
    out = {}
    if not isinstance(node, list):
        return out
    for item in node:
        if not isinstance(item, dict):
            continue
        key = item.get("key") or item.get("label")
        val = item.get("value") or item.get("values")
        if isinstance(val, list) and val:
            val = val[0]
        if key:
            out[str(key).lower()] = val
    return out


def parse_otomoto_offer(html: str, url: str = "") -> Optional[Offer]:
    """Parsuje pojedyncza oferte Otomoto. Zwraca None gdy sie nie uda."""
    soup = BeautifulSoup(html, "html.parser")

    # Metoda 1: __NEXT_DATA__ (najbardziej wiarygodna).
    script = soup.find("script", id="__NEXT_DATA__")
    if script and script.string:
        try:
            data = json.loads(script.string)
            advert = _find_advert(data)
            if advert:
                return _offer_from_advert(advert, url)
        except (json.JSONDecodeError, KeyError, TypeError):
            pass

    # Metoda 2: JSON-LD.
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            ld = json.loads(tag.string or "{}")
        except json.JSONDecodeError:
            continue
        items = ld if isinstance(ld, list) else [ld]
        for it in items:
            if isinstance(it, dict) and it.get("@type") in (
                "Car",
                "Product",
                "Vehicle",
            ):
                offer = Offer(url=url)
                offer.title = it.get("name", "")
                offer.make = (
                    (it.get("brand", {}) or {}).get("name", "")
                    if isinstance(it.get("brand"), dict)
                    else str(it.get("brand", ""))
                )
                offer.model = it.get("model", "")
                offer.year = _to_int(it.get("productionDate") or it.get("modelDate"))
                offer.mileage_km = (
                    _to_int((it.get("mileageFromOdometer", {}) or {}).get("value"))
                    if isinstance(it.get("mileageFromOdometer"), dict)
                    else None
                )
                offers_node = it.get("offers", {})
                if isinstance(offers_node, dict):
                    offer.price_pln = _to_int(offers_node.get("price"))
                offer.description = it.get("description", "")
                if offer.title or offer.price_pln:
                    return offer

    # Metoda 3: meta + heurystyki tekstowe.
    title_tag = soup.find("meta", property="og:title") or soup.find("title")
    if title_tag:
        title = (
            title_tag.get("content")
            if title_tag.has_attr("content")
            else title_tag.text
        )
        offer = Offer(url=url, title=(title or "").strip())
        offer.description = _visible_text(soup)[:4000]
        return offer

    return None


def _find_advert(data: dict):
    """Szuka wezla oferty w drzewie __NEXT_DATA__."""
    try:
        page = data["props"]["pageProps"]
    except (KeyError, TypeError):
        return None
    for key in ("advert", "advertData", "ad", "offer"):
        if isinstance(page.get(key), dict):
            return page[key]
    # Glebokie przeszukanie.
    stack = [page]
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            if "parameters" in node and ("price" in node or "title" in node):
                return node
            stack.extend(node.values())
        elif isinstance(node, list):
            stack.extend(node)
    return None


def _offer_from_advert(advert: dict, url: str) -> Offer:
    params = _params_to_dict(advert.get("parameters") or advert.get("details") or [])
    offer = Offer(url=url or advert.get("url", ""))
    offer.title = advert.get("title", "") or ""
    price = advert.get("price")
    if isinstance(price, dict):
        price = price.get("value") or price.get("amount")
    offer.price_pln = _to_int(price) or _to_int(params.get("price"))
    offer.make = str(params.get("make") or params.get("marka") or "")
    offer.model = str(params.get("model") or "")
    offer.generation = str(params.get("generation") or params.get("wersja") or "")
    offer.year = _to_int(params.get("year") or params.get("rok-produkcji"))
    offer.mileage_km = _to_int(params.get("mileage") or params.get("przebieg"))
    offer.power_hp = _to_int(params.get("engine_power") or params.get("moc"))
    offer.fuel = str(params.get("fuel_type") or params.get("rodzaj-paliwa") or "")
    offer.engine = str(params.get("engine_code") or params.get("engine_capacity") or "")
    offer.description = advert.get("description", "") or ""
    return offer


def _visible_text(soup: BeautifulSoup) -> str:
    for t in soup(["script", "style", "noscript"]):
        t.decompose()
    return re.sub(r"\s+", " ", soup.get_text(" "))


def scrape_offer(url: str) -> Optional[Offer]:
    """Pobiera i parsuje pojedyncza oferte. None przy niepowodzeniu."""
    html = fetch(url)
    return parse_otomoto_offer(html, url)


def extract_offer_links(html: str) -> List[str]:
    """Wyciaga linki do ofert ze strony wynikow wyszukiwania Otomoto."""
    links = re.findall(r'href="(https?://[^"]*?/oferta/[^"]+\.html[^"]*)"', html)
    return list(dict.fromkeys(links))


def scrape_comparables(
    search_url: str, limit: int = 30, throttle: float = 1.2
) -> List[Offer]:
    """Pobiera zbior ofert porownawczych z wynikow wyszukiwania Otomoto.

    Otomoto renderuje liste wynikow po stronie klienta (SSR ma puste edges),
    ale linki do ofert sa obecne w HTML. Zbieramy linki i pobieramy kazda
    oferte osobno (strona oferty ma pelne dane w SSR), z throttlingiem.
    """
    html = fetch(search_url)
    results: List[Offer] = []

    for url in extract_offer_links(html)[:limit]:
        try:
            off = scrape_offer(url)
            if off and off.price_pln:
                results.append(off)
        except requests.RequestException:
            pass
        time.sleep(throttle)

    # Metoda zapasowa: gdyby kiedys pojawil sie SSR z edges.
    if not results:
        soup = BeautifulSoup(html, "html.parser")
        script = soup.find("script", id="__NEXT_DATA__")
        if script and script.string:
            try:
                data = json.loads(script.string)
                for node in _find_search_edges(data)[:limit]:
                    off = _offer_from_search_node(node, search_url)
                    if off and off.price_pln:
                        results.append(off)
            except (json.JSONDecodeError, KeyError, TypeError):
                pass

    return results


def _find_search_edges(data: dict) -> list:
    stack = [data]
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            if "edges" in node and isinstance(node["edges"], list):
                return [e.get("node", e) for e in node["edges"] if isinstance(e, dict)]
            stack.extend(node.values())
        elif isinstance(node, list):
            stack.extend(node)
    return []


def _offer_from_search_node(node: dict, base_url: str) -> Optional[Offer]:
    if not isinstance(node, dict):
        return None
    params = _params_to_dict(node.get("parameters") or [])
    offer = Offer(url=node.get("url", base_url))
    offer.title = node.get("title", "")
    price = node.get("price")
    if isinstance(price, dict):
        amount = price.get("amount")
        if isinstance(amount, dict):
            amount = amount.get("units") or amount.get("value")
        price = amount
    offer.price_pln = _to_int(price) or _to_int(params.get("price"))
    offer.year = _to_int(params.get("year"))
    offer.mileage_km = _to_int(params.get("mileage"))
    offer.power_hp = _to_int(params.get("engine_power"))
    offer.fuel = str(params.get("fuel_type") or "")
    offer.make = str(params.get("make") or "")
    offer.model = str(params.get("model") or "")
    return offer if offer.price_pln else None


# ----- Fallback: pliki lokalne -----


def load_offer_json(path: str) -> Offer:
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    allowed = Offer().__dict__.keys()
    return Offer(**{k: v for k, v in d.items() if k in allowed})


def load_comparables_csv(path: str) -> List[Offer]:
    out: List[Offer] = []
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            out.append(
                Offer(
                    title=row.get("title", ""),
                    make=row.get("make", ""),
                    model=row.get("model", ""),
                    generation=row.get("generation", ""),
                    year=_to_int(row.get("year")),
                    mileage_km=_to_int(row.get("mileage_km")),
                    power_hp=_to_int(row.get("power_hp")),
                    fuel=row.get("fuel", ""),
                    engine=row.get("engine", ""),
                    price_pln=_to_int(row.get("price_pln")),
                    url=row.get("url", ""),
                )
            )
    return out
