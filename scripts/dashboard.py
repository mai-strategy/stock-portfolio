import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import json
import os

PORTFOLIO_FILE = os.path.join(os.path.dirname(__file__), "../data/portfolio.json")

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


@st.cache_data(ttl=300)
def fetch_history(tickers, period):
    data = yf.download(tickers, period=period, auto_adjust=True, progress=False)["Close"]
    if isinstance(data, pd.Series):
        data = data.to_frame(name=tickers[0] if isinstance(tickers, list) else tickers)
    return data


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
    st.subheader("Price History")
    hist_period = st.select_slider(
        "Chart period",
        options=["1W", "1M", "3M", "6M", "YTD", "1Y", "2Y", "3Y", "Max"],
        value="3M",
    )
    period_map = {"1W": "5d", "1M": "1mo", "3M": "3mo", "6M": "6mo",
                  "YTD": "ytd", "1Y": "1y", "2Y": "2y", "3Y": "3y", "Max": "max"}
    selected_tickers = st.multiselect(
        "Select tickers",
        [h["ticker"] for h in portfolio],
        default=[h["ticker"] for h in portfolio[:5]],
    )
    if selected_tickers:
        hist_data = fetch_history(tuple(selected_tickers), period_map[hist_period])
        fig_line = px.line(hist_data, labels={"value": "Price ($)", "index": "Date", "variable": "Ticker"})
        st.plotly_chart(fig_line, use_container_width=True)

    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
