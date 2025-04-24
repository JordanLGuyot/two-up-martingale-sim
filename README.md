# Two-Up - Time-Boxed Martingale Study

> *“The only fair game in town … unless you double after every loss.”*  
> - Typical ANZAC-Day punter

This repository contains a small Monte-Carlo study that asks:

*Does quitting a Martingale after a fixed number of Two-Up tosses give you a real edge, or just change how the risk shows up?*

The answer is explored for three common stakes (\$5, \$10, \$20) and a wide range of **box lengths** (the quit-after-N-tosses rule).

---

## 1  Background

Two-Up is a 50-50 coin game played in Australia each ANZAC Day:

1. A “kip” (paddle) is flicked to toss two pennies.  
2. **Two Heads ⇢ Win**, **Two Tails ⇢ Lose**, **Odds (one each) ⇢ re-toss**.

A **Martingale** doubles the wager after every loss and resets to the base stake after a win.  
Because bankrolls and table limits are finite, sooner or later the system hits a streak it cannot cover and goes bust.

**Time-boxing** (e.g. “leave after 75 resolved tosses”) shuts the game down early.  
The trade-off becomes:

| Short box | Long box |
|-----------|----------|
| High probability of a small win | Low probability of a huge win |
| Tiny bust risk | Larger bust risk |

---

## 2  Methodology

The analysis is now split into **three** Monte-Carlo experiments.

|                        | Time-boxed sweep | Unlimited (fixed cap) | Unlimited (cap sweep) |
|------------------------|------------------|-----------------------|-----------------------|
| Goal                   | How does a fixed “quit after *N* tosses” rule alter profit, bust risk, and hit-rate? | How big can the bankroll get before ruin under one generous cap? | How do peak profit and bust risk evolve as the cap lengthens? |
| Box length / Safety cap| `N = 10 → 150` (step 5) | Hard cap = **150** rounds | Caps = **10 → 150** (step 5) |
| Base stake **B**       | \$5, \$10, \$20 | same | same |
| Initial bankroll       | \$1 000         | same | same |
| Coin bias              | Fair (p = 0.5)  | same | same |
| Loss multiplier        | 2.0 (classic Martingale) | same | same |
| Trials per setting     | 20 000 per (B, N) | 100 000 per stake | 20 000 per (B, cap) |
| Recorded metrics       | • mean / median bankroll<br>• % profitable<br>• bust-rate<br>• avg win / loss | • avg / median **peak profit**<br>• avg bust round<br>• bust-rate | • avg peak profit<br>• avg bust round<br>• bust-rate |

> **Peak profit** answers “What could I have walked away with if I’d quit at the perfect moment?”  
> **Bust round** shows how fast the Martingale collapses once you stop quitting.

---

## 3  Results

### 3 .1  Probability of walking away ahead (coarse grid)

![Probability curve](results/probability_curve.png "Probability of Walking Away Ahead")

*Short boxes give a high hit-rate but the curve decays rapidly as you allow more tosses.*

### 3 .2  Fine-grid table (B = $5)

| Box length | % ahead | Typical profit (if ahead) | Bust-rate % |
|-----------:|-------:|---------------------------:|------------:|
| 10  | **83.71** | 23.41 | 0.000 |
| 15  | 86.61 | 34.91 | 0.000 |
| 20  | 87.92 | 46.47 | 0.000 |
| 25  | 87.40 | 58.81 | 0.000 |
| 30  | 86.08 | 71.31 | 0.000 |
| 35  | 85.42 | 82.73 | 0.000 |
| 40  | 84.58 | 94.71 | 0.000 |
| 45  | 83.37 | 107.74 | 0.000 |
| 50  | 81.01 | 120.15 | 0.000 |
| 55  | 80.04 | 132.64 | 0.000 |
| 60  | 78.21 | 145.34 | 0.000 |
| 65  | 77.50 | 157.31 | 0.000 |
| 70  | 75.91 | 169.67 | 0.000 |
| 75  | 75.01 | 181.95 | 0.000 |
| 80  | 73.29 | 194.92 | 0.000 |
| 85  | 72.08 | 207.31 | 0.000 |
| 90  | 69.97 | 220.45 | 0.000 |
| 95  | 69.23 | 232.45 | 0.010 |
| 100 | 67.68 | 245.44 | 0.010 |
| 105 | 65.63 | 257.84 | 0.045 |
| 110 | 65.42 | 270.14 | 0.065 |
| 115 | 64.44 | 283.72 | 0.135 |
| 120 | 63.60 | 296.88 | 0.185 |
| 125 | 62.44 | 321.44 | 0.230 |
| 130 | 62.07 | 333.99 | 0.230 |
| 135 | 62.87 | 345.90 | 0.240 |
| 140 | 60.64 | 356.98 | 0.280 |
| 145 | 60.02 | 357.54 | 0.230 |
| 150 | 59.80 | 370.57 | 0.265 |


### 3 .3  Fine-grid table (B = $10)

| Box length | % ahead | Typical profit (if ahead) | Bust-rate % |
|-----------:|-------:|---------------------------:|------------:|
| 10  | **81.86** | 47.51 | 0.000 |
| 15  | 82.72 | 70.90 | 0.000 |
| 20  | 82.98 | 94.53 | 0.000 |
| 25  | 79.97 | 119.09 | 0.000 |
| 30  | 77.37 | 144.48 | 0.000 |
| 35  | 75.41 | 168.18 | 0.000 |
| 40  | 72.78 | 193.18 | 0.000 |
| 45  | 70.40 | 218.40 | 0.010 |
| 50  | 67.63 | 244.08 | 0.050 |
| 55  | 64.68 | 271.29 | 0.145 |
| 60  | 63.44 | 295.73 | 0.290 |
| 65  | 61.33 | 321.26 | 0.365 |
| 70  | 59.23 | 345.24 | 0.430 |
| 75  | 60.23 | 369.58 | 0.490 |
| 80  | 57.97 | 394.74 | 0.540 |
| 85  | 57.72 | 421.15 | 0.535 |
| 90  | 56.66 | 446.96 | 0.520 |
| 95  | 55.53 | 472.34 | 0.475 |
| 100 | 54.32 | 496.46 | 0.500 |
| 105 | 53.28 | 521.98 | 0.515 |
| 110 | 52.34 | 548.07 | 0.540 |
| 115 | 51.34 | 572.86 | 0.540 |
| 120 | 50.39 | 598.98 | 0.520 |
| 125 | 50.06 | 622.81 | 0.485 |
| 130 | 48.16 | 647.78 | 0.465 |
| 135 | 47.48 | 672.99 | 0.490 |
| 140 | 47.12 | 698.60 | 0.460 |
| 145 | 46.08 | 724.12 | 0.525 |
| 150 | 44.59 | 748.94 | 0.455 |

### 3 .4  Fine-grid table (B = $20)

| Box length | % ahead | Typical profit (if ahead) | Bust-rate % |
|-----------:|-------:|---------------------------:|------------:|
| 10  | **78.54** | 95.99  | 0.000 |
| 15  | 75.31 | 144.57 | 0.000 |
| 20  | 71.55 | 192.57 | 0.000 |
| 25  | 66.94 | 244.25 | 0.125 |
| 30  | 62.86 | 295.92 | 0.535 |
| 35  | 61.02 | 344.50 | 0.860 |
| 40  | 58.87 | 394.01 | 1.045 |
| 45  | 56.28 | 445.34 | 1.015 |
| 50  | 54.56 | 498.51 | 1.000 |
| 55  | 52.66 | 550.50 | 1.010 |
| 60  | 49.24 | 600.22 | 1.060 |
| 65  | 49.24 | 648.18 | 0.870 |
| 70  | 46.50 | 697.03 | 1.000 |
| 75  | 44.65 | 751.47 | 1.035 |
| 80  | 43.64 | 804.64 | 0.805 |
| 85  | 41.78 | 852.57 | 0.970 |
| 90  | 39.17 | 904.58 | 1.085 |
| 95  | 38.09 | 956.83 | 0.995 |
| 100 | 36.42 | 1 009.79 | 1.025 |
| 105 | 35.02 | 1 058.98 | 1.010 |
| 110 | 33.54 | 1 111.37 | 0.970 |
| 115 | 32.40 | 1 161.16 | 1.095 |
| 120 | 31.32 | 1 205.92 | 1.045 |
| 125 | 31.24 | 1 239.78 | 1.195 |
| 130 | 30.01 | 1 258.64 | 1.080 |
| 135 | 29.84 | 1 276.83 | 1.090 |
| 140 | 30.03 | 1 285.43 | 1.065 |
| 145 | 29.82 | 1 287.77 | 1.040 |
| 150 | 29.02 | 1 298.33 | 1.155 |


### 3.5  Unlimited play - peak profit & bust statistics

When the player *never* time-boxes and simply plays until the bankroll can no longer cover the next doubled stake, the picture changes dramatically.

| Base stake | Avg peak profit | Median peak profit | Avg bust round | Bust-rate |
|-----------:|---------------:|-------------------:|--------------:|----------:|
| \$5  | \$ 290.35 | \$ 360 | 64.4 rounds | 39.5 % |
| \$10 | \$ 488.84 | \$ 600 | 55.2 rounds | 55.1 % |
| \$20 | \$ 749.41 | \$ 600 | 50.4 rounds | 75.3 % |

* **Avg peak profit** – the best bankroll you *could* have walked away with if you’d stopped at exactly the right moment.  
* **Avg bust round** – how long the strategy survives (on average) before ruin.  
* **Bust-rate** – fraction of sessions that end in complete ruin under the 150-round safety cap.

### 3.6  Unlimited play - safety-cap sweep

![Cap sweep](results/cap_sweep.png "Peak profit / bust-round / bust-rate vs. cap")

*Top panel - average peak profit rises with a longer cap.*  
*Middle panel - average bust round lengthens steadily.*  
*Bottom panel - bust-rate soars once the cap exceeds ~60 rounds, especially for the \$20 stake.*

---

## 4  Discussion

### Time-boxed play

* **Short boxes (≤ 50 tosses)** - 70 – 85 % of sessions end ahead but the
  typical win is small (< \$50).  
* **Middle boxes (~75 – 100 tosses)** - hit-rate drifts down to 60 – 70 %;
  median wins climb toward \$250; bust-risk is still below 1 %.  
* **Long boxes (≥ 135 tosses)** - upside exceeds \$300, yet chance of profit
  drops below 60 % and bust-risk starts to matter.

### Unlimited play

The cap-sweep plot shows three clear trends as the safety cap lengthens:

| Cap ≈ 60 rounds | Cap = 150 rounds |
|-----------------|------------------|
| Avg peak profit | \$200 / \$350 / \$550 (B =\$5/10/20) | \$280 / \$480 / \$730 |
| Avg bust round  | ~30 / 26 / 23     | ~66 / 56 / 50 |
| Bust-rate       | **30 % / 45 % / 60 %** | **38 % / 55 % / 75 %** |

* Peak profit rises roughly linearly with the cap, but **risk rises
  faster**-especially for the \$20 stake.  
* Bust-round growth flattens: every extra 10 allowed tosses buys only a few
  additional rounds before ruin on average.  
* Once the cap exceeds ~60 rounds the bust-rate curve becomes almost
  vertical for higher stakes (bottom panel of the figure).

In other words, every extra shot at a bigger payday costs an outsized jump
in the probability of total ruin.

---

## 5  Conclusion

* A **time-boxed Martingale** can deliver frequent, modest wins-as long as
  you quit soon (≤ 50 tosses) and keep the base stake small.  
* Extending the session past ~60 tosses **rapidly erodes that comfort**:
  bust-risk climbs into double-digits for \$5 stakes and breaches 50 % for
  \$20 stakes by the time you reach the 150-round cap.  
* Unlimited play exposes the strategy’s fatal flaw: the rare long losing
  streak eventually wipes out any series of small victories, and the
  escalation is faster than the upside grows.

> **Practical takeaway** – If you insist on playing a Martingale in
> Two-Up, cap both the number of throws and the base stake. Treat anything
> else as pure entertainment and budget for going bust.