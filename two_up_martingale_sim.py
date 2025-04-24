#!/usr/bin/env python3
"""Two-Up Martingale simulator and analyser.

This script provides two complementary Monte-Carlo studies for ANZAC-Day
*Two-Up*:

1. **Time-boxed Martingale** – the player quits after *N* resolved tosses.
2. **Unlimited play**        – the player continues until ruin
   (or a safety cap) so we can examine the *peak bankroll* they could have
   walked away with and the *round on which bust occurs*.

Outputs include:

* Best time-box (by mean bankroll and by % profitable)
* Probability-of-profit curve
* Average peak profit, median peak profit, average bust round, bust rate
  for unlimited play
* Optional CSV export of the coarse grid
"""
from __future__ import annotations

import argparse
from typing import Iterable, Sequence

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

###############################################################################
# 1-A.  Time-boxed simulator
###############################################################################
def simulate_time_boxed_session(
    bankroll: float,
    base_bet: float,
    max_rounds: int,
    *,
    p_win: float = 0.50,
    loss_mult: float = 2.0,
) -> float:
    """Play a Martingale that **stops after ``max_rounds`` turns**.

    Args:
        bankroll: Initial capital.
        base_bet: Stake after every win (the reset amount).
        max_rounds: Maximum resolved turns before quitting.
        p_win: Probability of winning a single turn (default 0.5).
        loss_mult: Factor applied to the stake after each loss
            (2.0 → classic Martingale).

    Returns:
        Final bankroll when the session ends (may be zero if bust).
    """
    bal: float = bankroll
    stake: float = base_bet

    for _ in range(max_rounds):
        if bal < stake:                # cannot cover next stake → bust
            break
        if np.random.rand() < p_win:   # win
            bal += stake
            stake = base_bet
        else:                          # loss
            bal -= stake
            stake *= loss_mult
    return bal


###############################################################################
# 1-B.  Unlimited-run simulator  →  peak-profit & bust-round tracking
###############################################################################
def simulate_until_bust(
    bankroll: float,
    base_bet: float,
    *,
    p_win: float = 0.50,
    loss_mult: float = 2.0,
    safety_round_cap: int = 150,
) -> tuple[float, float]:
    """Play until bankroll < next stake *or* safety cap reached.

    Args:
        bankroll: Initial capital.
        base_bet: Stake after every win.
        p_win: Win probability per turn.
        loss_mult: Stake multiplier after a loss.
        safety_round_cap: Hard stop to avoid infinite loops.

    Returns:
        A tuple ``(peak_profit, bust_round)`` where

        * ``peak_profit`` – Highest bankroll achieved minus ``bankroll``.
        * ``bust_round``  – 1-based index of the turn on which bust occurred,
          ``numpy.nan`` if the safety cap ended the run first.
    """
    bal: float = bankroll
    stake: float = base_bet
    peak: float = bal
    rnd: int = 0

    while rnd < safety_round_cap and bal >= stake:
        rnd += 1
        if np.random.rand() < p_win:      # win
            bal += stake
            stake = base_bet
        else:                             # loss
            bal -= stake
            stake *= loss_mult
        peak = max(peak, bal)

    bust_round: float = float(rnd) if bal < stake else float("nan")
    peak_profit: float = peak - bankroll
    return peak_profit, bust_round


###############################################################################
# 2.  Time-boxed parameter sweep
###############################################################################
def run_grid(
    base_bets: Sequence[int | float],
    round_grid: Iterable[int],
    *,
    bankroll: float = 1_000,
    n_sims: int = 20_000,
    seed: int | None = 42,
) -> pd.DataFrame:
    """Sweep *base_bets × round_grid* and return summary statistics.

    Args:
        base_bets: Collection of starting stakes to test.
        round_grid: Iterable of box lengths to test.
        bankroll: Initial bankroll for every simulation.
        n_sims: Number of Monte-Carlo trials per parameter pair.
        seed: RNG seed; ``None`` to leave RNG unchanged.

    Returns:
        ``pandas.DataFrame`` with one row per (base_bet, box_length) containing:
        mean_final, median_final, bust_rate, pct_profitable, etc.
    """
    if seed is not None:
        np.random.seed(seed)

    rows: list[dict[str, float]] = []
    for B in base_bets:
        for R in round_grid:
            finals = np.fromiter(
                (simulate_time_boxed_session(bankroll, B, R) for _ in range(n_sims)),
                dtype=float,
                count=n_sims,
            )

            prof_mask = finals > bankroll
            loss_mask = finals < bankroll

            rows.append(
                {
                    "base_bet": B,
                    "box_rounds": R,
                    "mean_final": finals.mean(),
                    "median_final": np.median(finals),
                    "bust_rate": (finals == 0).mean(),
                    "pct_profitable": prof_mask.mean(),
                    "avg_profit_given_profit": (
                        (finals[prof_mask] - bankroll).mean()
                        if prof_mask.any()
                        else 0.0
                    ),
                    "avg_loss_given_loss": (
                        (bankroll - finals[loss_mask]).mean()
                        if loss_mask.any()
                        else 0.0
                    ),
                }
            )

    return pd.DataFrame(rows)


###############################################################################
# 3.  Unlimited-play peak / bust statistics
###############################################################################
def run_peak_stats(
    base_bets: Sequence[int | float],
    *,
    bankroll: float = 1_000,
    n_sims: int = 100_000,
    seed: int | None = 123,
) -> pd.DataFrame:
    """Compute average peak profit & bust round for each stake.

    Args:
        base_bets: Stakes to test.
        bankroll: Initial capital per trial.
        n_sims: Monte-Carlo trials per stake.
        seed: RNG seed.

    Returns:
        ``DataFrame`` with columns:

        * ``avg_peak_profit``
        * ``median_peak_profit``
        * ``avg_bust_round``  (NaN ignored)
        * ``bust_rate``       (fraction of trials that bust)
    """
    if seed is not None:
        np.random.seed(seed)

    rows = []
    for B in base_bets:
        peaks, busts = zip(*(simulate_until_bust(bankroll, B) for _ in range(n_sims)))
        peaks_arr = np.array(peaks, dtype=float)
        busts_arr = np.array(busts, dtype=float)

        rows.append(
            {
                "base_bet": B,
                "avg_peak_profit": peaks_arr.mean(),
                "median_peak_profit": np.median(peaks_arr),
                "avg_bust_round": np.nanmean(busts_arr),
                "bust_rate": np.isfinite(busts_arr).mean(),
            }
        )
    return pd.DataFrame(rows)


###############################################################################
# 4.  Convenience: show a DataFrame nicely
###############################################################################
def show_dataframe(name: str, df: pd.DataFrame) -> None:
    """Print a DataFrame or show as an interactive table when available.

    Args:
        name: Title displayed above the table.
        df: The DataFrame to display.
    """
    try:
        import ace_tools as tools  # Only available inside ChatGPT’s environment.
        tools.display_dataframe_to_user(name, df)
    except Exception:  # noqa: BLE001  (broad except fine for graceful fallback)
        print(f"\n{name}\n{'-' * len(name)}")
        print(df.to_string(index=False))


###############################################################################
# 5.  CLI entry-point
###############################################################################
def main() -> None:
    """Run the simulations, plot results, optionally export CSV."""
    parser = argparse.ArgumentParser(
        description="Two-Up time-boxed Martingale study + unlimited peak stats"
    )
    parser.add_argument(
        "--csv", metavar="FILE", help="Write the coarse grid to CSV"
    )
    parser.add_argument(
        "--no-plot", action="store_true", help="Skip probability curve (headless)"
    )
    args = parser.parse_args()

    # 5-A.  Time-boxed coarse grid
    coarse_df = run_grid(base_bets=[5, 10, 20], round_grid=range(10, 151, 5))

    winners_mean = coarse_df.loc[coarse_df.groupby("base_bet")["mean_final"].idxmax()]
    winners_pct = coarse_df.loc[
        coarse_df.groupby("base_bet")["pct_profitable"].idxmax()
    ]

    print("\n===  Best by MEAN bankroll  ===")
    print(winners_mean.to_string(index=False, float_format="{:,.2f}".format))
    print("\n===  Best by % PROFITABLE  ===")
    print(winners_pct.to_string(index=False, float_format="{:,.2f}".format))

    # 5-B.  Probability-of-profit curve
    if not args.no_plot:
        fig, ax = plt.subplots(figsize=(8, 5))
        colours = {5: "tab:blue", 10: "tab:orange", 20: "tab:green"}

        for B in [5, 10, 20]:
            sub = coarse_df[coarse_df.base_bet == B]
            ax.plot(
                sub.box_rounds,
                sub.pct_profitable * 100,  # convert to percentage
                marker="o",
                label=f"B=${B}",
                color=colours[B],
            )

        ax.set_xlabel("Box length (max resolved rounds)")
        ax.set_ylabel("% of profitable sessions")
        ax.set_title("Probability of Walking Away Ahead")
        ax.legend()
        plt.tight_layout()
        plt.show()

    # 5-C.  Unlimited-play statistics
    peak_df = run_peak_stats(base_bets=[5, 10, 20])
    show_dataframe("Unlimited play – average peak profit & bust round", peak_df)

    # 5-D.  Optional CSV export
    if args.csv:
        coarse_df.assign(grid="coarse").to_csv(args.csv, index=False)
        print(f"\nCoarse grid written to {args.csv}")


if __name__ == "__main__":
    main()
