# Deal Stress Tester

A client-side web app that stress-tests real estate deals before you buy. Plug in your numbers, see where the deal breaks.

**[Live Demo](https://sbc1-code.github.io/deal-stress-tester/)**

## Why This Exists

Lessons from a real 4-plex sale. Most rental calculators show you best-case numbers and hide the ugly stuff: closing costs on both ends, vacancy spikes, rising expenses, partner splits, the hourly value of your time. This tool includes all of it by default.

The stress test grids are the centerpiece. Two heatmaps show exactly which combinations of rate hikes, vacancy increases, rent declines, and expense jumps break the deal. Green means strong. Gold means marginal. Red means you lose money.

## What It Does

- Monthly mortgage payment (standard amortization)
- Net cash flow after vacancy, expenses, and capex reserves
- Cash-on-cash return and annualized ROI
- Exit analysis: projected sale price, mortgage payoff, net proceeds, partner splits
- Effective hourly rate (assumes 5 hrs/mo management)
- Two stress test heatmaps: Interest Rate vs. Vacancy, Rent Decline vs. Expense Increase
- Color-coded cells: green (8%+ CoC, positive CF), gold (positive CF, sub-8% CoC), red (negative CF)

## Privacy

No backend, no database, no analytics, no cookies. Your numbers never leave your browser.

## Stack

Single-file HTML/CSS/JS. No frameworks, no build step, no dependencies.

## Run Locally

```
git clone https://github.com/sbc1-code/deal-stress-tester.git
cd deal-stress-tester
open index.html
```

## License

MIT
