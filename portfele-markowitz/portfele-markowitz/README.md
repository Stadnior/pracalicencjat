# Portfele – optymalizacja Markowitza

Trzy niezależne portfele analizowane metodą Markowitza (long-only):

| Skrypt | Portfel | Aktywa | Benchmark |
|---|---|---|---|
| `src/portfel_1_wig_markowitz.py` | GPW (PLN) | 24 spółki | brak (WIG20 niedostępny w danych) |
| `src/portfel_2_sp500_markowitz.py` | S&P 500 (USD) | 25 spółek | ^GSPC |
| `src/portfel_3_etf_markowitz.py` | ETF (USD) | 7 funduszy | SPY |

Każdy skrypt liczy statystyki aktywów (zwrot, CAGR, zmienność, Sharpe, maks. obsunięcie, VaR, beta),
cztery portfele (równe wagi, min. wariancja, maks. Sharpe, maks. zwrot) oraz granicę efektywną.

## Uruchomienie

```bash
pip install -r requirements.txt
# wgraj pliki CSV do katalogu data/
python src/portfel_1_wig_markowitz.py
python src/portfel_2_sp500_markowitz.py
python src/portfel_3_etf_markowitz.py
```

Wyniki (Excel + wykres PNG) trafiają do `wyniki/`.

## Parametry (na górze każdego skryptu)

`RF` – stopa wolna od ryzyka, `MAX_WAGA` – limit wagi jednego aktywa, `PLIK`, `KOLUMNY_DO_USUNIECIA`, `BENCHMARK`.

## Zastrzeżenia

- Optymalizacja in-sample (na całej próbie) – wyniki są optymistyczne.
- P1 i P2 obejmują tylko 3 lata (2023–2026), P3 ok. 15 lat.
- Brak przeliczenia walut (P1 w PLN, P2 i P3 w USD), brak kosztów transakcyjnych, rebalansowanie dzienne.
