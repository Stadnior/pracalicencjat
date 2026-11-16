# Portfele – optymalizacja Markowitza

Trzy niezależne portfele analizowane metodą Markowitza (long-only, suma wag = 100%):

| Skrypt | Portfel | Aktywa |
|---|---|---|
| `src/portfel_1_wig_markowitz.py` | GPW (PLN) | 24 spółki + indeks WIG20 (25 aktywów) |
| `src/portfel_2_sp500_markowitz.py` | S&P 500 (USD) | 25 spółek |
| `src/portfel_3_etf_markowitz.py` | ETF (USD) | 7 funduszy |

Każdy skrypt wyznacza dwa portfele efektywne:
- **minimalnej wariancji** – najmniejsze możliwe ryzyko,
- **maksymalnego Sharpe'a** – najlepszy stosunek zysku do ryzyka,

oraz granicę efektywną. Wyniki (wagi, parametry portfeli, wykres) trafiają do `wyniki/`.

## Uruchomienie

```bash
pip install -r requirements.txt
python src/portfel_1_wig_markowitz.py
python src/portfel_2_sp500_markowitz.py
python src/portfel_3_etf_markowitz.py
```

## Parametry (na górze każdego skryptu)

`RF` – stopa wolna od ryzyka, `MAX_WAGA` – limit wagi jednego aktywa, `PLIK`, `KOLUMNY_DO_USUNIECIA`.

## Uwagi

- Spółka SPL.WA (Santander) jest pominięta, bo w danych nie ma jej cen.
- Optymalizacja na całej próbie (in-sample) – wyniki są optymistyczne.
- P1 i P2 obejmują 3 lata (2023–2026), P3 ok. 15 lat.
- Brak przeliczenia walut (P1 w PLN, P2 i P3 w USD), brak kosztów transakcyjnych.
