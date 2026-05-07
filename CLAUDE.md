# Stock Portfolio Tracker

## Project Overview
This project tracks stock portfolio performance sourced from SavvyTrader.

- **Portfolio URL:** https://savvytrader.com/mushhood_sheikh89/new-portfolio
- **Owner:** Mai-strategy (mairasarwar@mai-strategy.com)
- **GitHub Repo:** https://github.com/mai-strategy/stock-portfolio
- **Goal:** Monitor and analyze stock holdings, track performance, gains/losses, and portfolio value over time.

---

## Project Structure
```
Stock Portfolio/
├── CLAUDE.md                  # Project documentation (this file)
├── requirements.txt           # Python dependencies
├── Start Dashboard.command    # Double-click to launch dashboard on Mac
├── data/
│   └── portfolio.json         # Holdings data (ticker, shares, avg buy price)
├── reports/                   # Performance reports and summaries
└── scripts/
    └── dashboard.py           # Streamlit dashboard app
```

---

## Tech Stack
- **Python 3.9**
- **Streamlit** — dashboard UI
- **yfinance** — live stock prices and historical data
- **Plotly** — interactive charts
- **pandas** — data processing

---

## Setup & Installation

### First-time setup
```bash
pip3 install streamlit pandas yfinance plotly
```

### Launch Dashboard
**Option 1 — Double-click:**
Open Finder → `/Users/mairasarwar/Stock Portfolio` → double-click `Start Dashboard.command`

**Option 2 — Terminal:**
```bash
/Users/mairasarwar/Library/Python/3.9/bin/streamlit run "/Users/mairasarwar/Stock Portfolio/scripts/dashboard.py"
```

Dashboard runs at: **http://localhost:8501**

---

## Dashboard Features

### 1. Summary Metrics (top of page)
- Total Portfolio Value
- Total Cost Basis
- Total Gain / Loss ($) and (%)
- Number of Holdings

### 2. Top & Bottom 3 Performers
- Shown at top of page below summary metrics
- Period selector: **Daily | Monthly | 1 Year | Total**
- 🟢 Top 3 table — best performers with ▲ arrows
- 🔴 Bottom 3 table — worst performers with ▼ arrows
- Shows: Ticker, Current Price, Return %, Return $

### 3. Returns by Period
- Period selector: **Daily | Monthly | YTD | 1 Year | 2 Year | 3 Year | Total**
- Full table: Start Price, Current Price, Return $, Return %
- Color-coded bar chart per stock for selected period

### 4. All Holdings Table (Total Return)
- All 28 positions with: Shares, Buy Price, Current Price, Cost Basis, Current Value, Gain/Loss
- Color-coded green (gain) / red (loss)

### 5. Portfolio Allocation Chart
- Donut pie chart showing % weight of each holding by current value

### 6. Total Gain/Loss by Stock
- Bar chart showing total % gain/loss per stock

### 7. Price History vs Benchmarks
- Period slider: 1W | 1M | 3M | 6M | YTD | 1Y | 2Y | 3Y | Max
- Select any holdings to compare
- **SPY** (S&P 500) overlay — gold dashed line
- **QQQ** (Nasdaq 100) overlay — blue dashed line
- Normalized to % return so all stocks are directly comparable

### 8. Manage Holdings (Sidebar)
- Add or update a stock (ticker, shares, buy price)
- Remove a stock from portfolio

---

## Portfolio Holdings (30 positions as of May 7, 2026)

| Ticker | Company | Shares | Avg Buy Price |
|--------|---------|--------|---------------|
| TSLA | Tesla Inc | 250 | $199.95 |
| RKLB | Rocket Lab USA | 720 | $15.99 |
| AMZN | Amazon.com | 180 | $142.23 |
| NBIS | Nebius Group | 235 | $55.43 |
| CRWD | CrowdStrike Holdings | 65 | $244.67 |
| MSFT | Microsoft | 73 | $347.74 |
| NVDA | NVIDIA | 100 | $131.53 |
| SOFI | SoFi Technologies | 1,135 | $6.75 |
| META | Meta Platforms | 26 | $557.95 |
| ASTS | AST SpaceMobile | 225 | $31.76 |
| ABCL | AbCellera Biologics | 3,000 | $3.70 |
| HOOD | Robinhood Markets | 120 | $53.80 |
| CRWV | CoreWeave | 55 | $96.57 |
| AMKR | Amkor Technology | 75 | $33.54 |
| RDDT | Reddit | 30 | $183.33 |
| LUNR | Intuitive Machines | 200 | $18.92 *(updated: +40 shares)* |
| GRAB | Grab Holdings | 1,100 | $5.13 |
| ZETA | Zeta Global | 200 | $18.41 |
| BMNR | BitMine Immersion | 108 | $44.49 |
| CIFR | Cipher Mining | 100 | $18.78 |
| CRDO | Credo Technology | 10 | $120.27 |
| ONDS | Ondas Holdings | 200 | $11.98 |
| MITK | Mitek Systems | 100 | $14.56 |
| VG | Venture Global | 100 | $6.95 |
| NOW | ServiceNow | 10 | $92.29 |
| MU | Micron Technology | 1 | $634.88 |
| DGXX | Digi Power X | 200 | $5.96 *(updated: +100 shares)* |
| RBRK | Rubrik | 10 | $71.88 |
| FPS | Forgent Power Solutions | 10 | $42.79 *(new)* |

---

## Portfolio Snapshot (May 7, 2026)
- **Total Value:** $455.86K
- **1 Day Return:** -1.09%
- **1 Month Return:** +20.11%
- **YTD Return:** +4.84%
- **1 Year Return:** +58.62%
- **Total Return:** +207.79%
- **CAGR:** 45.57%

---

## Git & GitHub
- **Repo:** https://github.com/mai-strategy/stock-portfolio
- **Branch:** main
- **Commit history:** all changes tracked and pushed

### Push changes
```bash
cd "/Users/mairasarwar/Stock Portfolio"
git add .
git commit -m "your message"
git push
```

---

## Notes
- Live prices are pulled from Yahoo Finance (refreshed every 5 minutes via cache)
- Portfolio data is stored locally in `data/portfolio.json`
- Dashboard is for monitoring purposes — sourced from SavvyTrader virtual/paper trading portfolio
