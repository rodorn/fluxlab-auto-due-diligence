# Sprawdz auto przed zakupem (FluxLab)

> Sprawdzenie auta przed zakupem w przeglądarce: [fluxlab.pl/sprawdz-auto](https://fluxlab.pl/sprawdz-auto?utm_source=github&utm_campaign=fluxlab-auto-due-diligence)

Narzedzie CLI, ktore dla oferty auta uzywanego (Otomoto URL albo wklejone dane) generuje
1-stronicowy raport PDF due-diligence dla kupujacego. Zamiast czytac dziesiatki ogloszen i
zgadywac, czy cena jest uczciwa i czego szukac, dostajesz konkretna analize na jednej stronie.

Czesc oferty FluxLab (fluxlab.pl): automatyzacja i analiza danych dla realnych decyzji.

## Co robi raport

1. **Benchmark ceny** vs 20-50 porownywalnych ofert (rocznik, przebieg, moc, wersja, paliwo).
   Liczy fair value (mediana cen znormalizowanych do przebiegu badanego auta metoda regresji)
   i pokazuje odchylke od rynku plus widelek cenowy.
2. **Checklista typowych usterek** dopasowana do modelu (baza dla popularnych aut premium i
   diesli): BMW E60/E63/E64, BMW serii 7 F01/F02, silniki BMW N-series (N47/N57/N20/N63),
   Audi A6 C6/C7, Mercedes W211/W212, diesle 2.0 TDI (VAG) i ogolne 3.0. Realne usterki
   (lancuchy rozrzadu, turbo, DPF/EGR, skrzynie, pneumatyka, korozja, elektronika) z
   orientacyjnym kosztem naprawy w PL.
3. **Red-flagi z tresci ogloszenia**: sprzecznosc "bezwypadkowy" vs slady napraw, niespojny
   przebieg (mozliwy cofniety licznik), podejrzanie niski przebieg do wieku, frazy ryzyka
   technicznego, cena mocno ponizej rynku, brak historii serwisowej, import, jezyk presji.
4. **Gotowy skrypt negocjacji**: "te 3 rzeczy = X zl w dol" plus rekomendowany punkt startowy
   negocjacji, policzony z benchmarku i ryzyk technicznych.

Kazdy raport konczy sie klauzula: analiza danych, nie gwarancja stanu technicznego, zalecane
ogledziny u niezaleznego mechanika.

## Wymagania

- Python 3.10+ (`requests`, `beautifulsoup4`, `pytest`)
- Google Chrome / Chromium (do eksportu PDF; bez niego narzedzie generuje sam HTML)

## Instalacja

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Uruchomienie

### Demo / probka (na wbudowanych przykladowych danych)

```bash
.venv/bin/python run.py
# wynik: out/sample_raport.html + out/sample_raport.pdf
```

### Tryb 1: scrape Otomoto (URL oferty + URL wyszukiwania porownywalnych)

```bash
.venv/bin/python cli.py \
  --url "https://www.otomoto.pl/osobowe/oferta/....html" \
  --search "https://www.otomoto.pl/osobowe/bmw/seria-7?..." \
  --pdf out/raport.pdf
```

Strona pojedynczej oferty Otomoto ma pelne dane w kodzie (SSR) i parsuje sie na zywo. Liste
porownywalnych narzedzie zbiera z linkow na stronie wynikow i pobiera oferta po ofercie z
throttlingiem. Filtruj wyszukiwanie do tego samego modelu/generacji/paliwa, zeby benchmark
byl trafny.

### Tryb 2: fallback z plikow lokalnych (gdy scrape sie nie uda albo dane masz recznie)

```bash
.venv/bin/python cli.py \
  --offer data/sample_offer.json \
  --comparables data/sample_comparables.csv \
  --pdf out/raport.pdf
```

Format `offer.json` i `comparables.csv`: patrz przyklady w `data/` (oznaczone jako PRZYKLAD).

## Testy

```bash
.venv/bin/pytest -q
```

Testy pokrywaja logike benchmarku (regresja, odchylka, wiarygodnosc), detektor red-flag
(sprzecznosci, niespojny przebieg, ryzyka techniczne) i dopasowanie checklisty modeli.

## Cennik (usluga)

| Pakiet       | Cena       | Zakres                                                                 |
| ------------ | ---------- | ---------------------------------------------------------------------- |
| Price-check  | 49 zl      | sam benchmark ceny vs rynek + odchylka od fair value                   |
| Pelny raport | 149-249 zl | benchmark + checklista modelu + red-flagi + skrypt negocjacji (1 auto) |
| Pakiet       | 300-500 zl | 3-5 raportow dla kupujacego, ktory porownuje kilka aut                 |

Zwrot z inwestycji dla klienta: jeden trafiony argument negocjacyjny albo unikniecie auta z
ukryta wada to setki lub tysiace zlotych, wielokrotnosc ceny raportu.

## Zastrzezenie

Raport to analiza danych z ogloszenia i rynku, nie jest gwarancja stanu technicznego pojazdu.
Przed zakupem zalecane sa ogledziny u niezaleznego mechanika i jazda probna. Autor narzedzia
nie ponosi odpowiedzialnosci za decyzje zakupowe podjete na podstawie raportu.

## Uwagi techniczne

- Zadne sekrety ani tokeny nie sa trzymane w kodzie. Scraper uzywa jedynie publicznych stron.
- Respektuj throttling i regulamin serwisu przy scrapowaniu.
- Dane przykladowe w `data/` sa fikcyjne (oznaczone PRZYKLAD) i sluza tylko demonstracji.
