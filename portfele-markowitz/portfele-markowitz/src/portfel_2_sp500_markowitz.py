"""
Portfel 2 – S&P 500 (USD) – optymalizacja Markowitza (long-only)

Co robi ten skrypt:
  1. wczytuje ceny z pliku CSV i liczy dzienne stopy zwrotu,
  2. liczy statystyki każdego aktywa (zwrot, ryzyko, Sharpe, obsunięcie, VaR, beta),
  3. wyznacza 4 portfele: równe wagi, minimalna wariancja, maksymalny Sharpe, maksymalny zwrot,
  4. wyznacza granicę efektywną,
  5. zapisuje wyniki do Excela i wykres do PNG oraz drukuje podsumowanie.

Uruchomienie (z katalogu głównego repo):  python src/src/portfel_2_sp500_markowitz.py
Wymagane biblioteki: numpy, pandas, scipy, matplotlib, openpyxl
"""
import os
import numpy as np
import pandas as pd
from scipy.optimize import minimize, linprog
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ============================== PARAMETRY ==============================
PLIK = "data/portfel_2_SP500_20261013_1548.csv"                      # ścieżka do pliku z cenami
KOLUMNY_DO_USUNIECIA = ["^GSPC"]  # indeks jest benchmarkiem, nie składnikiem        # kolumny, które NIE są składnikami portfela
BENCHMARK = "^GSPC"                  # kolumna z benchmarkiem (None = brak)
RF = 0.0                               # roczna stopa wolna od ryzyka (0.04 = 4%)
MAX_WAGA = 1.0                         # limit wagi jednego aktywa (1.0 = bez limitu, 0.2 = max 20%)
DNI = 252                              # dni sesyjne w roku (annualizacja)
NAZWA = "P2_SP500"                    # przedrostek plików wynikowych
WYJSCIE = "wyniki/"    # katalog na wyniki
# =======================================================================


def wczytaj():
    px = pd.read_csv(PLIK, index_col=0, parse_dates=True)
    bench = px[BENCHMARK].pct_change().dropna() if BENCHMARK else None
    px = px.drop(columns=KOLUMNY_DO_USUNIECIA)
    ret = px.pct_change().dropna()
    print(f"Aktywa: {ret.shape[1]}, obserwacje: {ret.shape[0]}, "
          f"okres: {ret.index[0].date()} – {ret.index[-1].date()}")
    return ret, bench


def statystyki(r, b=None):
    """Statystyki dla szeregu dziennych stóp zwrotu r (b = benchmark do bety)."""
    total = (1 + r).prod() - 1
    lata = (r.index[-1] - r.index[0]).days / 365.25
    cum = (1 + r).cumprod()
    sr = r.mean() * DNI
    vol = r.std() * np.sqrt(DNI)
    return {
        "Całkowita stopa zwrotu": total,
        "CAGR": (1 + total) ** (1 / lata) - 1,
        "Śr. roczna stopa zwrotu": sr,
        "Zmienność roczna": vol,
        "Sharpe": (sr - RF) / vol,
        "Maks. obsunięcie": (cum / cum.cummax() - 1).min(),
        "VaR 95% (dzienny)": np.percentile(r, 5),
        "Beta": np.cov(r, b.loc[r.index])[0, 1] / b.loc[r.index].var() if b is not None else np.nan,
    }


def optymalizuj(mu, cov):
    """Markowitz, long-only, suma wag = 1, waga każdego aktywa w [0, MAX_WAGA]."""
    n = len(mu)
    if MAX_WAGA * n < 1:
        raise ValueError("MAX_WAGA jest za małe: suma wag nie może wynieść 100%.")
    w0 = np.ones(n) / n
    granice = [(0, MAX_WAGA)] * n
    suma1 = {"type": "eq", "fun": lambda w: w.sum() - 1}
    ryzyko = lambda w: np.sqrt(w @ cov @ w)
    opcje = dict(maxiter=1000, ftol=1e-12)

    # (a) minimalna wariancja
    mv = minimize(lambda w: w @ cov @ w, w0, bounds=granice, constraints=[suma1],
                  method="SLSQP", options=opcje).x
    # (b) maksymalny Sharpe
    ms = minimize(lambda w: -(w @ mu - RF) / ryzyko(w), w0, bounds=granice,
                  constraints=[suma1], method="SLSQP", options=opcje).x
    # (c) maksymalny zwrot (programowanie liniowe)
    mr = linprog(-mu, A_eq=np.ones((1, n)), b_eq=[1], bounds=granice).x
    # (d) granica efektywna: min. ryzyko dla rosnącego zwrotu docelowego
    granica, w_prev = [], mv
    for t in np.linspace(mv @ mu, mr @ mu, 40):
        warunki = [suma1, {"type": "eq", "fun": lambda w, t=t: w @ mu - t}]
        res = minimize(lambda w: w @ cov @ w, w_prev, bounds=granice,
                       constraints=warunki, method="SLSQP", options=opcje)
        if res.success:
            w_prev = res.x
            granica.append((ryzyko(res.x), t))

    czysc = lambda w: np.where(w < 1e-6, 0.0, w) / np.where(w < 1e-6, 0.0, w).sum()
    return czysc(mv), czysc(ms), czysc(mr), pd.DataFrame(granica, columns=["Zmienność", "Zwrot"])


def main():
    os.makedirs(WYJSCIE, exist_ok=True)
    ret, bench = wczytaj()
    mu, cov = ret.mean() * DNI, ret.cov() * DNI

    w_ew = np.ones(len(mu)) / len(mu)
    w_mv, w_ms, w_mr, granica = optymalizuj(mu.values, cov.values)
    wagi = pd.DataFrame({"Równe wagi (1/N)": w_ew, "Min. wariancja": w_mv,
                         "Maks. Sharpe": w_ms, "Maks. zwrot": w_mr}, index=mu.index)

    # szeregi dziennych zwrotów portfeli (stałe wagi, rebalansowanie dzienne)
    portfele = {nazwa: ret @ wagi[nazwa] for nazwa in wagi}
    tab_portfele = pd.DataFrame({n: statystyki(s, bench) for n, s in portfele.items()}).T
    tab_portfele["Efektywna liczba aktywów (1/HHI)"] = [1 / (wagi[n] ** 2).sum() for n in wagi]
    if bench is not None:
        tab_portfele.loc[f"Benchmark ({BENCHMARK})"] = statystyki(bench, bench)
    tab_aktywa = pd.DataFrame({t: statystyki(ret[t], bench) for t in ret}).T
    korelacje = ret.corr()

    # --- Excel
    plik_xlsx = f"{WYJSCIE}{NAZWA}_markowitz.xlsx"
    with pd.ExcelWriter(plik_xlsx, engine="openpyxl") as xw:
        tab_portfele.to_excel(xw, sheet_name="Portfele")
        wagi.to_excel(xw, sheet_name="Wagi")
        tab_aktywa.to_excel(xw, sheet_name="Aktywa")
        korelacje.to_excel(xw, sheet_name="Korelacje")
        granica.to_excel(xw, sheet_name="Granica efektywna", index=False)
        pd.DataFrame({"Parametr": ["Rf", "MAX_WAGA", "Dni w roku", "Plik"],
                      "Wartość": [RF, MAX_WAGA, DNI, PLIK]}).to_excel(xw, sheet_name="Parametry", index=False)

    # --- wykres
    fig, ax = plt.subplots(1, 2, figsize=(15, 6))
    ax[0].plot(granica["Zmienność"], granica["Zwrot"], "k-", label="Granica efektywna")
    ax[0].scatter(np.sqrt(np.diag(cov)), mu, s=18, c="grey", label="Aktywa")
    for t in mu.index:
        ax[0].annotate(t, (np.sqrt(cov.loc[t, t]), mu[t]), fontsize=7, alpha=0.7)
    for n, m in zip(wagi, ["o", "s", "D", "^"]):
        s = tab_portfele.loc[n]
        ax[0].scatter(s["Zmienność roczna"], s["Śr. roczna stopa zwrotu"], s=90, marker=m, label=n, zorder=5)
    ax[0].set_xlabel("Zmienność roczna"); ax[0].set_ylabel("Śr. roczna stopa zwrotu")
    ax[0].set_title("Granica efektywna"); ax[0].legend(fontsize=8)
    for n, s in portfele.items():
        ax[1].plot((1 + s).cumprod() * 100, label=n)
    if bench is not None:
        ax[1].plot((1 + bench.loc[ret.index]).cumprod() * 100, "k--", label=f"Benchmark ({BENCHMARK})")
    ax[1].set_title("Wzrost wartości (start = 100)"); ax[1].legend(fontsize=8)
    fig.suptitle("Portfel 2 – S&P 500 (USD)")
    fig.tight_layout()
    fig.savefig(f"{WYJSCIE}{NAZWA}_markowitz.png", dpi=130)

    # --- podsumowanie w konsoli
    pd.options.display.float_format = "{:.3f}".format
    print("\n=== PORTFELE ===")
    print(tab_portfele[["CAGR", "Zmienność roczna", "Sharpe", "Maks. obsunięcie"]].to_string())
    for n in wagi:
        w = wagi[n][wagi[n] > 0.005].sort_values(ascending=False)
        print(f"\nWagi – {n}:", {k: round(v, 3) for k, v in w.items()})
    print(f"\nZapisano: {plik_xlsx}")


if __name__ == "__main__":
    main()
