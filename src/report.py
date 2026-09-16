"""Generator raportu HTML i eksport do PDF (Chrome headless)."""

from __future__ import annotations

import datetime
import html
import os
import shutil
import subprocess
import tempfile
from typing import Optional

from .models import Report

DISCLAIMER = (
    "Raport to analiza danych z ogloszenia i rynku, nie jest gwarancja stanu technicznego pojazdu. "
    "Przed zakupem zalecane sa ogledziny u niezaleznego mechanika oraz jazda probna. "
    "FluxLab nie ponosi odpowiedzialnosci za decyzje zakupowe podjete na podstawie raportu."
)

SEV_LABEL = {"HIGH": "WYSOKI", "MED": "SREDNI", "LOW": "NISKI"}
SEV_COLOR = {"HIGH": "#c0392b", "MED": "#d68910", "LOW": "#7f8c8d"}


def _esc(s) -> str:
    return html.escape(str(s if s is not None else ""))


def _fmt_pln(v: Optional[int]) -> str:
    if v is None:
        return "brak danych"
    return f"{v:,}".replace(",", " ") + " zl"


def render_html(report: Report) -> str:
    o = report.offer
    b = report.benchmark
    from .checklist import matched_models

    models = matched_models(o)
    models_txt = (
        "; ".join(models)
        if models
        else "brak dopasowanej bazy (checklista uniwersalna)"
    )

    dev = b.deviation_pct
    if dev is None:
        dev_txt = "brak"
        dev_color = "#333"
    elif dev > 3:
        dev_txt = f"+{dev}% powyzej rynku"
        dev_color = "#c0392b"
    elif dev < -3:
        dev_txt = f"{dev}% ponizej rynku"
        dev_color = "#1e8449"
    else:
        dev_txt = f"{dev}% (zgodna z rynkiem)"
        dev_color = "#1e8449"

    # Red flags
    rf_rows = ""
    for f in report.red_flags:
        rf_rows += (
            f'<div class="flag"><span class="sev" style="background:{SEV_COLOR.get(f.severity, "#777")}">'
            f"{SEV_LABEL.get(f.severity, f.severity)}</span>"
            f'<span class="flag-msg">{_esc(f.message)}</span></div>'
        )
    if not rf_rows:
        rf_rows = '<div class="flag"><span class="flag-msg">Nie wykryto wyraznych red-flag w tresci ogloszenia.</span></div>'

    # Checklist (ograniczamy do najwazniejszych, zeby zmiescic 1 strone)
    cl_rows = ""
    for c in report.checklist[:11]:
        cl_rows += (
            f"<tr><td class='sys'>{_esc(c.system)}</td>"
            f"<td>{_esc(c.issue)}</td>"
            f"<td class='cost'>{_esc(c.cost_pln)}</td></tr>"
        )

    # Negotiation
    neg = report.negotiation
    neg_points = ""
    for i, p in enumerate(neg.get("points", [])[:4], 1):
        amt = f" (~{_fmt_pln(p['amount'])})" if p.get("amount") else ""
        neg_points += f"<li><b>{_esc(p['label'])}{amt}:</b> {_esc(p['script'])}</li>"

    target = neg.get("target_price_pln")
    lever = neg.get("total_leverage_pln", 0)

    sample_banner = ""
    if report.is_sample:
        sample_banner = (
            '<div class="sample-banner">PROBKA / DEMO. Dane oferty i porownywalnych sa '
            "przykladowe (nie dotycza realnego klienta), sluza pokazaniu dzialania narzedzia.</div>"
        )

    today = datetime.date.today().strftime("%d.%m.%Y")

    return f"""<!doctype html>
<html lang="pl"><head><meta charset="utf-8">
<style>
@page {{ size: A4; margin: 10mm 12mm; }}
* {{ box-sizing: border-box; }}
body {{ font-family: 'DejaVu Sans', Arial, sans-serif; color:#1c1c1c; font-size:9.3px; line-height:1.35; margin:0; }}
.header {{ display:flex; justify-content:space-between; align-items:flex-start; border-bottom:2px solid #16a085; padding-bottom:5px; }}
.brand {{ font-size:15px; font-weight:800; color:#16a085; }}
.brand small {{ display:block; font-size:8px; font-weight:400; color:#666; }}
h1 {{ font-size:13px; margin:6px 0 2px; }}
.sub {{ color:#555; font-size:8.5px; margin-bottom:6px; }}
.sample-banner {{ background:#fff3cd; border:1px solid #d68910; color:#8a6d00; padding:3px 6px; font-weight:700; font-size:8.5px; margin:5px 0; border-radius:3px; }}
.grid {{ display:flex; gap:8px; margin:6px 0; }}
.card {{ flex:1; border:1px solid #e0e0e0; border-radius:4px; padding:6px 8px; background:#fafafa; }}
.card .k {{ color:#666; font-size:8px; text-transform:uppercase; letter-spacing:.3px; }}
.card .v {{ font-size:13px; font-weight:800; }}
.section {{ margin:7px 0 3px; font-size:10px; font-weight:800; color:#16a085; border-bottom:1px solid #ddd; padding-bottom:2px; }}
table {{ width:100%; border-collapse:collapse; font-size:8.5px; }}
th {{ text-align:left; background:#f0f0f0; padding:3px 4px; font-size:8px; }}
td {{ padding:3px 4px; border-bottom:1px solid #eee; vertical-align:top; }}
td.sys {{ font-weight:700; width:16%; }}
td.cost {{ width:22%; color:#c0392b; font-weight:600; white-space:nowrap; }}
.flag {{ display:flex; gap:6px; align-items:baseline; margin:2px 0; }}
.sev {{ color:#fff; font-size:7.5px; font-weight:800; padding:1px 5px; border-radius:3px; min-width:52px; text-align:center; }}
.flag-msg {{ flex:1; }}
.neg {{ background:#eafaf1; border:1px solid #16a085; border-radius:4px; padding:6px 8px; }}
.neg ol {{ margin:4px 0 4px 16px; padding:0; }}
.neg li {{ margin:2px 0; }}
.target {{ font-size:12px; font-weight:800; color:#117a65; margin-top:4px; }}
.two {{ display:flex; gap:10px; }}
.two > div {{ flex:1; }}
.disclaimer {{ margin-top:8px; font-size:7.3px; color:#777; border-top:1px solid #ddd; padding-top:4px; font-style:italic; }}
.foot {{ margin-top:3px; font-size:7.3px; color:#999; text-align:center; }}
</style></head>
<body>
<div class="header">
  <div><div class="brand">FluxLab<small>fluxlab.pl</small></div></div>
  <div style="text-align:right; font-size:8px; color:#666;">Raport due-diligence<br>data: {today}</div>
</div>
<h1>Sprawdz auto przed zakupem</h1>
<div class="sub">{_esc(o.title) or (_esc(o.make) + " " + _esc(o.model))} &nbsp;|&nbsp; rocznik: {_esc(o.year) or "b/d"} &nbsp;|&nbsp; przebieg: {_fmt_pln(o.mileage_km).replace("zl", "km")} &nbsp;|&nbsp; moc: {_esc(o.power_hp) or "b/d"} KM &nbsp;|&nbsp; paliwo: {_esc(o.fuel) or "b/d"}</div>
{sample_banner}

<div class="grid">
  <div class="card"><div class="k">Cena ofertowa</div><div class="v">{_fmt_pln(o.price_pln)}</div></div>
  <div class="card"><div class="k">Wycena rynkowa (fair value)</div><div class="v">{_fmt_pln(b.fair_value_pln)}</div></div>
  <div class="card"><div class="k">Odchylka od rynku</div><div class="v" style="color:{dev_color}">{dev_txt}</div></div>
  <div class="card"><div class="k">Wiarygodnosc</div><div class="v" style="font-size:11px">{_esc(b.confidence)}<br><span style="font-size:8px;font-weight:400;color:#666">{b.n_used} z {b.n_total} porownywalnych</span></div></div>
</div>
<div style="font-size:8.5px;color:#444;margin:2px 0 2px">{_esc(b.verdict)} Widelek rynkowy: {_fmt_pln(b.price_low)} do {_fmt_pln(b.price_high)}.</div>

<div class="two">
<div>
<div class="section">Red-flagi z ogloszenia</div>
{rf_rows}
</div>
</div>

<div class="section">Checklista typowych usterek: {_esc(models_txt)}</div>
<table>
<tr><th>System</th><th>Typowa usterka i na co uwazac</th><th>Koszt naprawy</th></tr>
{cl_rows}
</table>

<div class="section">Gotowy skrypt negocjacji</div>
<div class="neg">
<div style="font-size:8.5px;font-style:italic;color:#117a65;margin-bottom:3px">"{_esc(neg.get("opening", ""))}"</div>
<b style="font-size:9px">Te punkty = argumenty w dol:</b>
<ol>{neg_points}</ol>
<div class="target">Rekomendowany punkt startowy negocjacji: {_fmt_pln(target)} &nbsp; (material negocjacyjny ~{_fmt_pln(lever)})</div>
</div>

<div class="disclaimer">{DISCLAIMER}</div>
<div class="foot">FluxLab &middot; fluxlab.pl &middot; raport wygenerowany automatycznie na podstawie danych oferty i porownywalnych ogloszen</div>
</body></html>"""


def _find_chrome() -> Optional[str]:
    for name in (
        "google-chrome-stable",
        "google-chrome",
        "chromium",
        "chromium-browser",
    ):
        path = shutil.which(name)
        if path:
            return path
    return None


def html_to_pdf(html_str: str, pdf_path: str) -> bool:
    """Konwertuje HTML na PDF przez Chrome headless. Zwraca True przy sukcesie."""
    chrome = _find_chrome()
    os.makedirs(os.path.dirname(os.path.abspath(pdf_path)), exist_ok=True)
    if not chrome:
        return False

    with tempfile.NamedTemporaryFile(
        "w", suffix=".html", delete=False, encoding="utf-8"
    ) as tf:
        tf.write(html_str)
        html_path = tf.name

    with tempfile.TemporaryDirectory() as profile:
        cmd = [
            chrome,
            "--headless=new",
            "--no-sandbox",
            "--disable-gpu",
            f"--user-data-dir={profile}",
            "--no-pdf-header-footer",
            "--run-all-compositor-stages-before-draw",
            "--virtual-time-budget=3000",
            f"--print-to-pdf={pdf_path}",
            "file://" + html_path,
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=60)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            # Fallback dla starszego trybu headless.
            cmd[1] = "--headless"
            try:
                subprocess.run(cmd, check=True, capture_output=True, timeout=60)
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                os.unlink(html_path)
                return False

    os.unlink(html_path)
    return os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0


def generate_report(report: Report, out_html: str = "", out_pdf: str = "") -> dict:
    """Zapisuje HTML i (jesli mozliwe) PDF. Zwraca sciezki."""
    html_str = render_html(report)
    result = {"html": None, "pdf": None}
    if out_html:
        os.makedirs(os.path.dirname(os.path.abspath(out_html)), exist_ok=True)
        with open(out_html, "w", encoding="utf-8") as f:
            f.write(html_str)
        result["html"] = out_html
    if out_pdf:
        if html_to_pdf(html_str, out_pdf):
            result["pdf"] = out_pdf
    return result
