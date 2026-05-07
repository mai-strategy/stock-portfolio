import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import json
import os

PORTFOLIO_FILE    = os.path.join(os.path.dirname(__file__), "../data/portfolio.json")
TRANSACTIONS_FILE = os.path.join(os.path.dirname(__file__), "../data/transactions.json")

PERIODS = {
    "Daily":   {"period": "5d",  "label": "1D"},
    "Monthly": {"period": "1mo", "label": "1M"},
    "YTD":     {"period": "ytd", "label": "YTD"},
    "1 Year":  {"period": "1y",  "label": "1Y"},
    "2 Year":  {"period": "2y",  "label": "2Y"},
    "3 Year":  {"period": "3y",  "label": "3Y"},
    "Total":   {"period": None,  "label": "Total"},
}

st.set_page_config(page_title="Stock Portfolio Tracker", layout="wide", page_icon="📈")
st.title("📈 Stock Portfolio Tracker")
st.caption("Synced with: https://savvytrader.com/mushhood_sheikh89/new-portfolio")


def load_portfolio():
    if os.path.exists(PORTFOLIO_FILE):
        with open(PORTFOLIO_FILE) as f:
            return json.load(f)
    return []


def save_portfolio(data):
    os.makedirs(os.path.dirname(PORTFOLIO_FILE), exist_ok=True)
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(data, f, indent=2)


def load_transactions():
    if os.path.exists(TRANSACTIONS_FILE):
        with open(TRANSACTIONS_FILE) as f:
            return json.load(f)
    return []


def save_transactions(data):
    with open(TRANSACTIONS_FILE, "w") as f:
        json.dump(data, f, indent=2)


@st.cache_data(ttl=300)
def fetch_history(tickers, period):
    data = yf.download(tickers, period=period, auto_adjust=True, progress=False)["Close"]
    if isinstance(data, pd.Series):
        data = data.to_frame(name=tickers[0] if isinstance(tickers, list) else tickers)
    return data


@st.cache_data(ttl=300)
def fetch_all_period_returns(holdings_tuple, period_key):
    """Fetch returns for all holdings for a given period. Cached per period."""
    holdings = list(holdings_tuple)
    period_cfg = PERIODS[period_key]["period"]
    tickers = [h["ticker"].upper() for h in holdings]
    buy_prices = {h["ticker"].upper(): h["buy_price"] for h in holdings}
    shares_map = {h["ticker"].upper(): h["shares"] for h in holdings}

    results = []
    try:
        if period_key == "Total":
            info_data = {t: yf.Ticker(t).fast_info.last_price for t in tickers}
            for t in tickers:
                now = round(info_data[t], 2)
                bp = buy_prices[t]
                pct = round((now - bp) / bp * 100, 2)
                gain_dollar = round((now - bp) * shares_map[t], 2)
                results.append({"Ticker": t, "Return %": pct, "Return $": gain_dollar, "Current Price": now})
        else:
            hist = yf.download(tickers, period=period_cfg, auto_adjust=True, progress=False)["Close"]
            if isinstance(hist, pd.Series):
                hist = hist.to_frame(name=tickers[0])
            for t in tickers:
                if t not in hist.columns:
                    continue
                col = hist[t].dropna()
                if len(col) < 2:
                    continue
                start = round(col.iloc[0], 2)
                now = round(col.iloc[-1], 2)
                pct = round((now - start) / start * 100, 2)
                gain_dollar = round((now - start) * shares_map[t], 2)
                results.append({"Ticker": t, "Return %": pct, "Return $": gain_dollar, "Current Price": now})
    except Exception:
        pass
    return results


def get_period_return(ticker, period_key, buy_price):
    """Return (pct_change, price_start, price_now) for the given period."""
    try:
        t = yf.Ticker(ticker)
        now = round(t.fast_info.last_price, 2)

        if period_key == "Total":
            pct = round((now - buy_price) / buy_price * 100, 2)
            return pct, buy_price, now

        period = PERIODS[period_key]["period"]
        hist = t.history(period=period, auto_adjust=True)
        if hist.empty:
            return None, None, now
        start_price = round(hist["Close"].iloc[0], 2)
        pct = round((now - start_price) / start_price * 100, 2)
        return pct, start_price, now
    except Exception:
        return None, None, None


def fetch_prices(holdings):
    rows = []
    for h in holdings:
        ticker = h["ticker"].upper()
        shares = h["shares"]
        buy_price = h["buy_price"]
        try:
            info = yf.Ticker(ticker).fast_info
            current_price = round(info.last_price, 2)
            current_value = round(current_price * shares, 2)
            cost_basis = round(buy_price * shares, 2)
            gain_loss = round(current_value - cost_basis, 2)
            gain_loss_pct = round((gain_loss / cost_basis) * 100, 2) if cost_basis else 0
            rows.append({
                "Ticker": ticker,
                "Shares": shares,
                "Buy Price": f"${buy_price:.2f}",
                "Current Price": f"${current_price:.2f}",
                "Cost Basis": f"${cost_basis:.2f}",
                "Current Value": f"${current_value:.2f}",
                "Gain/Loss ($)": gain_loss,
                "Gain/Loss (%)": gain_loss_pct,
                "_current_price": current_price,
                "_current_value": current_value,
                "_cost_basis": cost_basis,
                "_buy_price": buy_price,
            })
        except Exception:
            rows.append({
                "Ticker": ticker,
                "Shares": shares,
                "Buy Price": f"${buy_price:.2f}",
                "Current Price": "N/A",
                "Cost Basis": f"${buy_price * shares:.2f}",
                "Current Value": "N/A",
                "Gain/Loss ($)": 0,
                "Gain/Loss (%)": 0,
                "_current_price": None,
                "_current_value": 0,
                "_cost_basis": buy_price * shares,
                "_buy_price": buy_price,
            })
    return rows


def color_val(val):
    if isinstance(val, (int, float)):
        return f"color: {'green' if val >= 0 else 'red'}"
    return ""


# Sidebar — manage holdings
st.sidebar.header("Manage Holdings")
portfolio = load_portfolio()

with st.sidebar.form("add_stock"):
    st.subheader("Add / Update Stock")
    ticker_input = st.text_input("Ticker Symbol", placeholder="e.g. AAPL").upper()
    shares_input = st.number_input("Number of Shares", min_value=0.01, step=0.01)
    buy_price_input = st.number_input("Buy Price per Share ($)", min_value=0.01, step=0.01)
    submitted = st.form_submit_button("Add to Portfolio")

    if submitted and ticker_input:
        existing = next((h for h in portfolio if h["ticker"] == ticker_input), None)
        if existing:
            existing["shares"] = shares_input
            existing["buy_price"] = buy_price_input
        else:
            portfolio.append({"ticker": ticker_input, "shares": shares_input, "buy_price": buy_price_input})
        save_portfolio(portfolio)
        st.success(f"{ticker_input} saved!")

if portfolio:
    remove_ticker = st.sidebar.selectbox("Remove a Stock", [""] + [h["ticker"] for h in portfolio])
    if st.sidebar.button("Remove") and remove_ticker:
        portfolio = [h for h in portfolio if h["ticker"] != remove_ticker]
        save_portfolio(portfolio)
        st.rerun()

# Main dashboard
if not portfolio:
    st.info("Add your stock holdings in the sidebar to get started.")
else:
    with st.spinner("Fetching live prices..."):
        rows = fetch_prices(portfolio)

    total_value = sum(r["_current_value"] for r in rows)
    total_cost = sum(r["_cost_basis"] for r in rows)
    total_gain = total_value - total_cost
    total_pct = (total_gain / total_cost * 100) if total_cost else 0

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Portfolio Value", f"${total_value:,.2f}")
    col2.metric("Total Cost Basis", f"${total_cost:,.2f}")
    col3.metric("Total Gain / Loss", f"${total_gain:,.2f}", f"{total_pct:.2f}%")
    col4.metric("Holdings", len(portfolio))

    st.divider()

    # ── Top & Bottom 3 Performers ─────────────────────────────────────────────
    st.subheader("Top & Bottom 3 Performers")
    perf_period = st.radio(
        "Period",
        ["Daily", "Monthly", "1 Year", "Total"],
        horizontal=True,
        key="perf_period",
    )

    with st.spinner(f"Loading {perf_period} performers..."):
        all_returns = fetch_all_period_returns(
            tuple({"ticker": h["ticker"], "buy_price": h["buy_price"], "shares": h["shares"]} for h in portfolio),
            perf_period,
        )

    if all_returns:
        perf_df = pd.DataFrame(all_returns).sort_values("Return %", ascending=False)
        top3 = perf_df.head(3).copy()
        bot3 = perf_df.tail(3).sort_values("Return %").copy()

        def fmt_pct(v):
            arrow = "▲" if v >= 0 else "▼"
            return f"{arrow} {v:+.2f}%"

        def fmt_dollar(v):
            arrow = "▲" if v >= 0 else "▼"
            return f"{arrow} ${v:+,.2f}"

        for df in (top3, bot3):
            df["Return %"] = df["Return %"].apply(fmt_pct)
            df["Return $"] = df["Return $"].apply(fmt_dollar)
            df["Current Price"] = df["Current Price"].apply(lambda v: f"${v:,.2f}")

        col_top, col_bot = st.columns(2)

        with col_top:
            st.markdown("##### 🟢 Top 3")
            st.dataframe(
                top3[["Ticker", "Current Price", "Return %", "Return $"]],
                use_container_width=True,
                hide_index=True,
            )

        with col_bot:
            st.markdown("##### 🔴 Bottom 3")
            st.dataframe(
                bot3[["Ticker", "Current Price", "Return %", "Return $"]],
                use_container_width=True,
                hide_index=True,
            )

    st.divider()

    # ── Returns by Period ─────────────────────────────────────────────────────
    st.subheader("Returns by Period")
    selected_period = st.radio(
        "Select period",
        list(PERIODS.keys()),
        horizontal=True,
        index=0,
    )

    with st.spinner(f"Loading {selected_period} returns..."):
        period_rows = []
        for r in rows:
            ticker = r["Ticker"]
            buy_price = r["_buy_price"]
            pct, price_start, price_now = get_period_return(ticker, selected_period, buy_price)
            shares = r["Shares"]
            gain_dollar = round((price_now - price_start) * shares, 2) if price_start and price_now else None
            period_rows.append({
                "Ticker": ticker,
                "Shares": shares,
                "Start Price": f"${price_start:.2f}" if price_start else "N/A",
                "Current Price": f"${price_now:.2f}" if price_now else "N/A",
                f"Return ({selected_period}) $": gain_dollar,
                f"Return ({selected_period}) %": pct,
            })

    period_df = pd.DataFrame(period_rows)
    ret_dollar_col = f"Return ({selected_period}) $"
    ret_pct_col = f"Return ({selected_period}) %"

    styled_period = period_df.style.applymap(color_val, subset=[ret_dollar_col, ret_pct_col])
    st.dataframe(styled_period, use_container_width=True, hide_index=True)

    # Period summary bar
    valid = period_df[period_df[ret_pct_col].notna()]
    if not valid.empty:
        colors = ["green" if v >= 0 else "red" for v in valid[ret_pct_col]]
        fig_period = go.Figure(go.Bar(
            x=valid["Ticker"],
            y=valid[ret_pct_col],
            marker_color=colors,
            text=[f"{v:.1f}%" for v in valid[ret_pct_col]],
            textposition="outside",
        ))
        fig_period.update_layout(
            yaxis_title=f"Return % ({selected_period})",
            xaxis_title="Ticker",
            height=400,
        )
        st.plotly_chart(fig_period, use_container_width=True)

    st.divider()

    # ── Holdings table ────────────────────────────────────────────────────────
    st.subheader("All Holdings (Total Return)")
    display_df = pd.DataFrame(rows).drop(columns=["_current_value", "_cost_basis", "_current_price", "_buy_price"])
    styled = display_df.style.applymap(color_val, subset=["Gain/Loss ($)", "Gain/Loss (%)"])
    st.dataframe(styled, use_container_width=True, hide_index=True)

    st.divider()

    # ── Charts ────────────────────────────────────────────────────────────────
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Portfolio Allocation")
        pie_df = pd.DataFrame({
            "Ticker": [r["Ticker"] for r in rows],
            "Value": [r["_current_value"] for r in rows],
        })
        fig_pie = px.pie(pie_df, names="Ticker", values="Value", hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_b:
        st.subheader("Total Gain / Loss by Stock")
        bar_df = pd.DataFrame({
            "Ticker": [r["Ticker"] for r in rows],
            "Gain/Loss (%)": [r["Gain/Loss (%)"] for r in rows],
        })
        colors = ["green" if v >= 0 else "red" for v in bar_df["Gain/Loss (%)"]]
        fig_bar = go.Figure(go.Bar(
            x=bar_df["Ticker"],
            y=bar_df["Gain/Loss (%)"],
            marker_color=colors,
        ))
        fig_bar.update_layout(yaxis_title="Gain/Loss (%)", xaxis_title="Ticker")
        st.plotly_chart(fig_bar, use_container_width=True)

    # ── Price history chart ───────────────────────────────────────────────────
    st.subheader("Price History vs Benchmarks")
    hist_period = st.select_slider(
        "Chart period",
        options=["1W", "1M", "3M", "6M", "YTD", "1Y", "2Y", "3Y", "Max"],
        value="3M",
    )
    period_map = {"1W": "5d", "1M": "1mo", "3M": "3mo", "6M": "6mo",
                  "YTD": "ytd", "1Y": "1y", "2Y": "2y", "3Y": "3y", "Max": "max"}

    col_tickers, col_bench = st.columns([3, 1])
    with col_tickers:
        selected_tickers = st.multiselect(
            "Select holdings to compare",
            [h["ticker"] for h in portfolio],
            default=[h["ticker"] for h in portfolio[:5]],
        )
    with col_bench:
        show_spy = st.checkbox("SPY (S&P 500)", value=True)
        show_qqq = st.checkbox("QQQ (Nasdaq 100)", value=True)

    all_tickers = list(selected_tickers) + (["SPY"] if show_spy else []) + (["QQQ"] if show_qqq else [])

    if all_tickers:
        raw = fetch_history(tuple(all_tickers), period_map[hist_period])
        # Normalize to % return from start so all tickers are comparable
        normalized = (raw / raw.iloc[0] - 1) * 100
        normalized.index.name = "Date"

        fig_line = go.Figure()
        for col in normalized.columns:
            is_benchmark = col in ("SPY", "QQQ")
            fig_line.add_trace(go.Scatter(
                x=normalized.index,
                y=normalized[col],
                name=col,
                line=dict(
                    dash="dash" if is_benchmark else "solid",
                    width=2.5 if is_benchmark else 1.5,
                    color="#FFD700" if col == "SPY" else ("#00BFFF" if col == "QQQ" else None),
                ),
            ))
        fig_line.update_layout(
            yaxis_title="Return (%)",
            xaxis_title="Date",
            legend_title="Ticker",
            hovermode="x unified",
            height=500,
        )
        fig_line.add_hline(y=0, line_dash="dot", line_color="gray", opacity=0.5)
        st.plotly_chart(fig_line, use_container_width=True)
        st.caption("Chart shows % return from start of selected period. SPY = S&P 500, QQQ = Nasdaq 100 (dashed).")

    st.divider()

    # ── Transaction History ───────────────────────────────────────────────────
    st.subheader("Transaction History")

    transactions = load_transactions()

    # Add new transaction form
    with st.expander("+ Log New Transaction"):
        with st.form("add_transaction"):
            tc1, tc2, tc3, tc4, tc5 = st.columns([2, 1, 1, 1, 1])
            with tc1:
                t_ticker = st.text_input("Ticker").upper()
            with tc2:
                t_action = st.selectbox("Action", ["Buy", "Sell"])
            with tc3:
                t_shares = st.number_input("Shares", min_value=0.01, step=0.01)
            with tc4:
                t_price = st.number_input("Price ($)", min_value=0.01, step=0.01)
            with tc5:
                t_date = st.date_input("Date", value=date.today())
            t_submitted = st.form_submit_button("Add Transaction")
            if t_submitted and t_ticker:
                transactions.insert(0, {
                    "date": str(t_date),
                    "ticker": t_ticker,
                    "action": t_action,
                    "shares": t_shares,
                    "price": t_price,
                })
                save_transactions(transactions)
                st.success(f"Transaction logged: {t_action} {t_shares} {t_ticker} @ ${t_price}")
                st.rerun()

    if transactions:
        tx_df = pd.DataFrame(transactions)
        tx_df["date"] = pd.to_datetime(tx_df["date"])
        tx_df["Total Value"] = (tx_df["shares"] * tx_df["price"]).round(2)
        tx_df = tx_df.sort_values("date", ascending=False)

        today = pd.Timestamp(date.today())
        week_ago  = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)

        tab_daily, tab_weekly, tab_monthly, tab_all = st.tabs(["Today", "This Week", "This Month", "All Time"])

        def render_tx(df):
            if df.empty:
                st.info("No transactions in this period.")
                return
            display = df.copy()
            display["date"] = display["date"].dt.strftime("%b %d, %Y")
            display["price"] = display["price"].apply(lambda x: f"${x:,.2f}")
            display["Total Value"] = display["Total Value"].apply(lambda x: f"${x:,.2f}")
            display.columns = ["Date", "Ticker", "Action", "Shares", "Price", "Total Value"]

            def highlight_action(row):
                color = "background-color: #d4edda" if row["Action"] == "Buy" else "background-color: #f8d7da"
                return [color] * len(row)

            st.dataframe(
                display.style.apply(highlight_action, axis=1),
                use_container_width=True,
                hide_index=True,
            )
            buys  = df[df["action"] == "Buy"]["Total Value"].sum()
            sells = df[df["action"] == "Sell"]["Total Value"].sum()
            sc1, sc2, sc3 = st.columns(3)
            sc1.metric("Transactions", len(df))
            sc2.metric("Total Bought", f"${buys:,.2f}")
            if sells > 0:
                sc3.metric("Total Sold", f"${sells:,.2f}")

        with tab_daily:
            render_tx(tx_df[tx_df["date"].dt.date == date.today()])

        with tab_weekly:
            render_tx(tx_df[tx_df["date"] >= week_ago])

        with tab_monthly:
            render_tx(tx_df[tx_df["date"] >= month_ago])

        with tab_all:
            render_tx(tx_df)

    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
