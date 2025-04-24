#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Two-Up Martingale simulator / analyser.

This module drives three Monte-Carlo studies:

1. **Time-boxed Martingale** – player quits after *N* resolved tosses  
   (`N = 10 … 150`, step 5).

2. **Unlimited play – single cap (150 rounds)** – player continues until
   the bankroll can’t cover the next stake (or the cap is hit); records
   peak bankroll and bust statistics.

3. **Unlimited play – cap sweep (10 … 150, step 5)** – repeats the
   unlimited simulation for a range of safety caps to examine how peak
   profit and bust risk vary with session length.

All figures (`.png`) and optional CSV files are written to the directory
given by `--outdir` (default `results/`).
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, Sequence

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# =============================================================================
# 1.  Core simulators
# =============================================================================
def simulate_time_boxed_session(
    bankroll: float,
    base_bet: float,
    max_rounds: int,
    *,
    p_win: float = 0.5,
    loss_mult: float = 2.0,
) -> float:
    """Play one Martingale session with a hard stop after *max_rounds*.

    Args:
        bankroll: Initial player capital in dollars.
        base_bet: Stake placed after every winning turn (the reset amount).
        max_rounds: Maximum resolved turns before the player walks away.
        p_win: Probability of winning a single toss. Defaults to ``0.5``.
        loss_mult: Multiplier applied to the stake after each loss.
            ``2.0`` implements the classic Martingale.

    Returns:
        The final bankroll when the session ends. May be ``0`` if the
        player goes bust before reaching *max_rounds*.
    """
    bal, stake = bankroll, base_bet
    for _ in range(max_rounds):
        if bal < stake:  # Bust: cannot cover next wager.
            break
        if np.random.rand() < p_win:  # Win → collect stake, reset.
            bal += stake
            stake = base_bet
        else:  # Loss → deduct stake, double.
            bal -= stake
            stake *= loss_mult
    return bal


def simulate_until_bust(
    bankroll: float,
    base_bet: float,
    *,
    p_win: float = 0.5,
    loss_mult: float = 2.0,
    safety_round_cap: int = 150,
) -> tuple[float, float]:
    """Play until bust or a safety-round cap is reached.

    Args:
        bankroll: Initial capital (dollars).
        base_bet: Stake placed after each winning turn.
        p_win: Probability of winning a single toss.
        loss_mult: Multiplier applied after each loss.
        safety_round_cap: Hard stop to avoid infinite loops.

    Returns:
        A tuple ``(peak_profit, bust_round)``:

        * **peak_profit** – Highest bankroll reached minus *bankroll*.
        * **bust_round**  – 1-based round index at which bust occurred,
          or ``numpy.nan`` if the safety cap ended the run first.
    """
    bal, stake, peak, rnd = bankroll, base_bet, bankroll, 0
    while rnd < safety_round_cap and bal >= stake:
        rnd += 1
        if np.random.rand() < p_win:          # Win
            bal += stake
            stake = base_bet
        else:                                 # Loss
            bal -= stake
            stake *= loss_mult
        peak = max(peak, bal)

    bust_round = float(rnd) if bal < stake else float("nan")
    return peak - bankroll, bust_round


# =============================================================================
# 2.  Time-boxed parameter sweep
# =============================================================================
def run_grid(
    base_bets: Sequence[int | float],
    round_grid: Iterable[int],
    *,
    bankroll: float = 1_000,
    n_sims: int = 20_000,
    seed: int | None = 42,
) -> pd.DataFrame:
    """Sweep *base_bets × round_grid* and aggregate statistics.

    Returns:
        A ``DataFrame`` with one row per ``(base_bet, box_round)`` and
        columns ``mean_final``, ``pct_profitable``, ``bust_rate``, etc.
    """
    if seed is not None:
        np.random.seed(seed)

    rows: list[dict[str, float]] = []
    for base in base_bets:
        for box in round_grid:
            finals = np.fromiter(
                (simulate_time_boxed_session(bankroll, base, box)
                 for _ in range(n_sims)),
                dtype=float,
                count=n_sims,
            )
            prof_mask, loss_mask = finals > bankroll, finals < bankroll
            rows.append(
                {
                    "base_bet": base,
                    "box_rounds": box,
                    "mean_final": finals.mean(),
                    "median_final": np.median(finals),
                    "bust_rate": (finals == 0).mean(),
                    "pct_profitable": prof_mask.mean(),
                    "avg_profit_given_profit":
                        (finals[prof_mask] - bankroll).mean()
                        if prof_mask.any() else 0.0,
                    "avg_loss_given_loss":
                        (bankroll - finals[loss_mask]).mean()
                        if loss_mask.any() else 0.0,
                }
            )
    return pd.DataFrame(rows)


# =============================================================================
# 3-A.  Unlimited play (single cap = 150)
# =============================================================================
def run_peak_stats(
    base_bets: Sequence[int | float],
    *,
    bankroll: float = 1_000,
    n_sims: int = 100_000,
    seed: int | None = 123,
) -> pd.DataFrame:
    """Compute average peak profit & bust-round statistics for each stake."""
    if seed is not None:
        np.random.seed(seed)

    rows = []
    for base in base_bets:
        peaks, busts = zip(*(simulate_until_bust(bankroll, base)
                             for _ in range(n_sims)))
        rows.append(
            {
                "base_bet": base,
                "avg_peak_profit": np.mean(peaks),
                "median_peak_profit": np.median(peaks),
                "avg_bust_round": np.nanmean(busts),
                "bust_rate": np.isfinite(busts).mean(),
            }
        )
    return pd.DataFrame(rows)


# =============================================================================
# 3-B.  Unlimited play – safety-cap sweep
# =============================================================================
def explore_caps(
    base_bets: Sequence[int | float],
    caps: Iterable[int],
    *,
    bankroll: float = 1_000,
    n_sims: int = 20_000,
    seed: int | None = 321,
) -> pd.DataFrame:
    """Return peak/bust statistics for every *cap × base_bet* combination."""
    if seed is not None:
        np.random.seed(seed)

    rows = []
    for cap in caps:
        for base in base_bets:
            peaks, busts = zip(
                *(simulate_until_bust(bankroll, base, safety_round_cap=cap)
                  for _ in range(n_sims))
            )
            rows.append(
                {
                    "cap_rounds": cap,
                    "base_bet": base,
                    "avg_peak_profit": np.mean(peaks),
                    "avg_bust_round": np.nanmean(busts),
                    "bust_rate": np.isfinite(busts).mean(),
                }
            )
    return pd.DataFrame(rows)


def plot_cap_sweep(df: pd.DataFrame, out_path: Path) -> None:
    """Plot peak profit, bust round and bust-rate vs. safety cap.

    The colour palette adapts to any number of stakes in *df*.

    Args:
        df: Output of :func:`explore_caps`.
        out_path: Destination for the saved PNG.
    """
    # Dynamically assign colours.
    palette = plt.cm.get_cmap("tab20").colors  # 20 categorical colours
    unique_bets = sorted(df.base_bet.unique())
    bet_colour = {bet: palette[i % len(palette)]
                  for i, bet in enumerate(unique_bets)}

    fig, axes = plt.subplots(3, 1, figsize=(7, 9), sharex=True)
    metrics = [
        ("avg_peak_profit", "Avg peak profit ($)"),
        ("avg_bust_round", "Avg bust round"),
        ("bust_rate", "Bust rate (%)"),
    ]

    for ax, (metric, ylabel) in zip(axes, metrics):
        for bet in unique_bets:
            sub = df[df.base_bet == bet]
            y = sub[metric] * (100 if metric == "bust_rate" else 1)
            ax.plot(
                sub.cap_rounds,
                y,
                marker="o",
                label=f"B=${bet}",
                color=bet_colour[bet],
            )
        ax.set_ylabel(ylabel)
        ax.grid(alpha=0.3)
        if metric == "bust_rate":
            ax.set_ylim(0, 100)

    axes[-1].set_xlabel("Safety cap (max resolved rounds)")
    axes[0].set_title("Unlimited play – effect of round cap")
    axes[0].legend(ncol=min(5, len(unique_bets)), fontsize="small")
    fig.tight_layout()
    fig.savefig(out_path, dpi=300)
    plt.show()


# =============================================================================
# 4.  DataFrame display helper
# =============================================================================
def show_dataframe(title: str, df: pd.DataFrame) -> None:
    """Pretty-print *df*, using ace_tools for interactive view if available."""
    try:
        import ace_tools as tools
        tools.display_dataframe_to_user(title, df)
    except Exception:  # noqa: BLE001
        print(f"\n{title}\n{'-' * len(title)}")
        print(df.to_string(index=False))


# =============================================================================
# 5.  Main driver
# =============================================================================
def main() -> None:
    """Run simulations, save artefacts, print headline statistics."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--csv",
        action="store_true",
        help="Save coarse grid & cap sweep data to CSV",
    )
    parser.add_argument(
        "--no-plot",
        action="store_true",
        help="Skip all plots (useful for headless runs)",
    )
    parser.add_argument(
        "--outdir",
        default="results",
        help="Directory for PNG / CSV output",
    )
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(exist_ok=True)
    stakes = [5, 10, 20]

    # Time-boxed study ---------------------------------------------------------
    coarse_df = run_grid(stakes, range(10, 151, 5))
    show_dataframe("Time-boxed coarse grid", coarse_df)

    winners_mean = coarse_df.loc[coarse_df.groupby("base_bet")["mean_final"].idxmax()]
    winners_pct = coarse_df.loc[coarse_df.groupby("base_bet")["pct_profitable"].idxmax()]

    print("\nBest by MEAN bankroll\n", winners_mean.to_string(index=False))
    print("\nBest by % PROFITABLE\n", winners_pct.to_string(index=False))

    if not args.no_plot:
        # Probability-of-profit curve
        fig, ax = plt.subplots(figsize=(8, 5))
        palette = plt.cm.get_cmap("tab10").colors
        for idx, bet in enumerate(stakes):
            sub = coarse_df[coarse_df.base_bet == bet]
            ax.plot(
                sub.box_rounds,
                sub.pct_profitable * 100,
                marker="o",
                color=palette[idx % len(palette)],
                label=f"B=${bet}",
            )
        ax.set_xlabel("Box length (max resolved rounds)")
        ax.set_ylabel("% profitable")
        ax.set_title("Probability of Walking Away Ahead")
        ax.legend()
        plt.tight_layout()
        plt.savefig(outdir / "probability_curve.png", dpi=300)
        plt.show()

    # Unlimited play – cap = 150 ----------------------------------------------
    peak_df = run_peak_stats(stakes)
    show_dataframe("Unlimited play – cap 150 summary", peak_df)

    # Unlimited play – cap sweep ----------------------------------------------
    caps_df = explore_caps(stakes, caps=range(10, 151, 5))
    show_dataframe("Cap sweep (10–150)", caps_df)
    if not args.no_plot:
        plot_cap_sweep(caps_df, outdir / "cap_sweep.png")

    # Optional CSV export ------------------------------------------------------
    if args.csv:
        coarse_df.assign(grid="coarse").to_csv(outdir / "coarse_grid.csv", index=False)
        caps_df.to_csv(outdir / "cap_sweep.csv", index=False)
        print(f"CSV files written to {outdir.resolve()}")


if __name__ == "__main__":
    main()
