#!/usr/bin/env python3
"""Two-up time-boxed Martingale analysis.

Runs Monte-Carlo experiments that model a time-boxed Martingale
strategy for the ANZAC-Day game Two-Up.

High-level flow
---------------
1.  `simulate_time_boxed_session` – simulate one gambling session.
2.  `run_grid`                    – sweep a grid of (base-bet, box-length)
    pairs and collect summary statistics in a ``pandas.DataFrame``.
3.  `main`                        – 
    * coarse grid → “best by mean bankroll / best by % profitable”
    * probability-of-profit line plot
    * fine grid (10-150 rounds, step 5) → interactive tables
    * optional CSV export
"""

from __future__ import annotations

import argparse
import sys
from typing import Iterable, Sequence

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# ────────────────────────────────────────────────────────────────
# 1.  Single-session simulator
# ────────────────────────────────────────────────────────────────
def simulate_time_boxed_session(
    bankroll: float,
    base_bet: float,
    max_rounds: int,
    *,
    p_win: float = 0.50,
    loss_mult: float = 2.0,
) -> float:
    """Run one Martingale session that stops after *max_rounds* turns.

    Args:
        bankroll: Initial capital available to the player.
        base_bet: Stake placed after every winning turn (i.e. the
            “reset” amount).
        max_rounds: Maximum number of resolved turns before the
            player walks away.
        p_win: Probability of winning a single turn. Defaults to 0.5
            (fair game).
        loss_mult: Factor applied to the stake after each loss.
            ``2.0`` = classic Martingale (double after loss).

    Returns:
        Final bankroll at the end of the session. May be zero if the
        player goes bust before reaching *max_rounds*.
    """
    bal: float = bankroll
    stake: float = base_bet

    for _ in range(max_rounds):
        if bal < stake:  # Bust: cannot cover the next wager.
            break

        win: bool = np.random.rand() < p_win
        if win:
            bal += stake
            stake = base_bet  # Reset after a win.
        else:
            bal -= stake
            stake *= loss_mult  # Double after a loss.

    return bal


# ────────────────────────────────────────────────────────────────
# 2.  Parameter-grid runner
# ────────────────────────────────────────────────────────────────
def run_grid(
    base_bets: Sequence[int | float],
    round_grid: Iterable[int],
    *,
    bankroll: float = 1_000,
    n_sims: int = 20_000,
    seed: int | None = 42,
) -> pd.DataFrame:
    """Sweep a grid of Martingale parameters.

    Args:
        base_bets: Collection of starting stakes ``B`` to test.
        round_grid: Iterable of box lengths (max turns) to test.
        bankroll: Initial bankroll for every simulation.
        n_sims: Number of Monte-Carlo trials per (B, box) pair.
        seed: RNG seed. ``None`` → leave NumPy RNG untouched.

    Returns:
        DataFrame with one row per (B, box) pair containing:
            * mean_final, median_final
            * bust_rate
            * pct_profitable
            * avg_profit_given_profit
            * avg_loss_given_loss
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


# ────────────────────────────────────────────────────────────────
# 3.  Data-frame presenter
# ────────────────────────────────────────────────────────────────
def show_dataframe(name: str, df: pd.DataFrame) -> None:
    """Display *df* interactively (ace_tools) or print as fallback.

    Args:
        name: Title shown above the table / printed block.
        df: Data to display.
    """
    try:
        import ace_tools as tools  # Available only inside ChatGPT sessions.

        tools.display_dataframe_to_user(name, df)
    except Exception:  # noqa: BLE001: broad except ok—fallback for any failure
        print(f"\n{name}\n{'-' * len(name)}")
        print(df.to_string(index=False))


# ────────────────────────────────────────────────────────────────
# 4.  Command-line entry-point
# ────────────────────────────────────────────────────────────────
def main() -> None:
    """Run both the coarse and fine parameter sweeps and plot results."""
    parser = argparse.ArgumentParser(description="Time-boxed Martingale study")
    parser.add_argument(
        "--csv",
        metavar="FILE",
        help="Write both grids (coarse+fine) to CSV",
    )
    args = parser.parse_args()

    # 4-A ▸ coarse grid → winners + probability-curve plot
    coarse_df = run_grid(
        base_bets=[5, 10, 20],
        round_grid=range(10, 151, 5),
    )

    winners_mean = coarse_df.loc[
        coarse_df.groupby("base_bet")["mean_final"].idxmax()
    ]
    winners_pct = coarse_df.loc[
        coarse_df.groupby("base_bet")["pct_profitable"].idxmax()
    ]

    print("\n===  Best by MEAN bankroll  ===")
    print(winners_mean.to_string(index=False, float_format="{:,.2f}".format))
    print("\n===  Best by % PROFITABLE  ===")
    print(winners_pct.to_string(index=False, float_format="{:,.2f}".format))

    # Plot probability-of-profit curve.
    fig, ax = plt.subplots(figsize=(8, 5))
    colours = {5: "tab:blue", 10: "tab:orange", 20: "tab:green"}

    for B in [5, 10, 20]:
        sub = coarse_df[coarse_df.base_bet == B]
        ax.plot(
            sub.box_rounds,
            sub.pct_profitable * 100,  # convert to %
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

    # 4-B ▸ fine grid 10-150 step-5 → interactive tables
    fine_df = run_grid(
        base_bets=[5, 10, 20],
        round_grid=range(10, 151, 5),
    )

    for B in [5, 10, 20]:
        subset = (
            fine_df[fine_df.base_bet == B]
            .loc[
                :,
                [
                    "box_rounds",
                    "pct_profitable",
                    "avg_profit_given_profit",
                    "bust_rate",
                ],
            ]
            .rename(
                columns={
                    "box_rounds": "Box length",
                    "pct_profitable": "% ahead",
                    "avg_profit_given_profit": "Typical profit when ahead",
                    "bust_rate": "Bust-rate %",
                }
            )
        )

        # Human-readable formatting.
        subset["% ahead"] = (subset["% ahead"] * 100).round(2)
        subset["Bust-rate %"] = (subset["Bust-rate %"] * 100).round(3)
        subset["Typical profit when ahead"] = subset[
            "Typical profit when ahead"
        ].round(2)

        show_dataframe(f"Base bet ${B}", subset)

    # 4-C ▸ optional CSV export of both grids
    if args.csv:
        (
            pd.concat(
                [coarse_df.assign(grid="coarse"), fine_df.assign(grid="fine")]
            ).to_csv(args.csv, index=False)
        )
        print(f"\nFull results written to {args.csv}")


# ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
