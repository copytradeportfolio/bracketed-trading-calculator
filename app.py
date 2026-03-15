import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import math

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Bracketed Trading Growth Calculator",
    page_icon="📈",
    layout="wide",
)

# ── CSS: dark theme polish ────────────────────────────────────────────────────
st.markdown("""
<style>
  /* body / app background */
  .stApp { background-color: #0d1117; color: #e6edf3; }

  /* sidebar */
  [data-testid="stSidebar"] { background-color: #161b22; }
  [data-testid="stSidebar"] label { color: #c9d1d9 !important; }

  /* metric cards */
  [data-testid="metric-container"] {
      background: linear-gradient(135deg, #1c2333, #21262d);
      border: 1px solid #30363d;
      border-radius: 12px;
      padding: 16px 20px;
  }

  /* metric label */
  [data-testid="metric-container"] label {
      color: #a0b0c8 !important;
      font-size: 0.95rem !important;
      font-weight: 600 !important;
      letter-spacing: 0.03em;
  }

  /* metric value */
  [data-testid="metric-container"] [data-testid="stMetricValue"] {
      color: #ffffff !important;
      font-size: 1.8rem !important;
      font-weight: 700 !important;
  }

  /* metric delta */
  [data-testid="metric-container"] [data-testid="stMetricDelta"] {
      color: #3fb950 !important;
      font-size: 1rem !important;
  }

  /* headers */
  h1, h2, h3 { color: #58a6ff !important; }

  /* dataframe */
  [data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; }

  /* divider accent */
  hr { border-color: #30363d !important; }

  /* number inputs */
  input[type="number"] { background-color: #161b22 !important; color: #e6edf3 !important; }
</style>
""", unsafe_allow_html=True)

# ── Title ─────────────────────────────────────────────────────────────────────
st.title("📈 Bracketed Trading Growth Calculator")
st.markdown("*Simulate compound account growth as you unlock higher lot brackets.*")
st.divider()

# ── Sidebar inputs ────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Settings")
    starting_balance = st.number_input(
        "Starting Balance ($)", min_value=10.0, value=100.0, step=10.0, format="%.2f"
    )
    daily_profit_pct = st.number_input(
        "Net Daily Profit (%)", min_value=0.1, max_value=50.0, value=3.0, step=0.1, format="%.1f"
    )
    bracket_size = st.number_input(
        "Bracket Size ($)", min_value=10.0, value=100.0, step=10.0, format="%.2f",
        help="Every time profit grows by this amount, the lot bracket increases by 1."
    )
    num_days = st.slider("Projection Days", min_value=30, max_value=730, value=60, step=10)
    st.divider()
    st.caption("Built with ❤️ for copy traders")

# ── Calculation ───────────────────────────────────────────────────────────────
rows = []
balance = starting_balance
current_bracket = 1
bracket_base = starting_balance  # lot size is fixed at bracket entry balance

for day in range(1, num_days + 1):
    # Daily profit is FIXED within a bracket (same lot size = same dollar profit)
    profit = bracket_base * (daily_profit_pct / 100)
    balance += profit

    # Check if we've crossed into a new bracket
    new_bracket = math.floor((balance - starting_balance) / bracket_size) + 1
    if new_bracket > current_bracket:
        current_bracket = new_bracket
        bracket_base = starting_balance + (current_bracket - 1) * bracket_size

    rows.append({
        "Day": day,
        "Balance ($)": round(balance, 2),
        "Daily Profit ($)": round(profit, 2),
        "Bracket": int(current_bracket),
    })

df = pd.DataFrame(rows)

# ── Key metrics ───────────────────────────────────────────────────────────────
final_balance = df["Balance ($)"].iloc[-1]
total_gain    = final_balance - starting_balance
max_bracket   = df["Bracket"].iloc[-1]
gain_pct      = (total_gain / starting_balance) * 100

col1, col2, col3, col4 = st.columns(4)

def metric_card(label, value, delta=None):
    delta_html = f'<div style="color:#3fb950;font-size:0.95rem;margin-top:4px;">{delta}</div>' if delta else ""
    return f"""
    <div style="background:linear-gradient(135deg,#1c2333,#21262d);border:1px solid #30363d;
                border-radius:12px;padding:18px 22px;">
      <div style="color:#a8c0d6;font-size:0.9rem;font-weight:600;letter-spacing:0.04em;
                  text-transform:uppercase;margin-bottom:8px;">{label}</div>
      <div style="color:#ffffff;font-size:1.9rem;font-weight:700;line-height:1.1;">{value}</div>
      {delta_html}
    </div>"""

col1.markdown(metric_card("Starting Balance", f"${starting_balance:,.2f}"), unsafe_allow_html=True)
col2.markdown(metric_card("Final Balance", f"${final_balance:,.2f}", delta=f"▲ +${total_gain:,.2f}"), unsafe_allow_html=True)
col3.markdown(metric_card("Total Growth", f"{gain_pct:,.1f}%"), unsafe_allow_html=True)
col4.markdown(metric_card("Max Bracket", f"#{max_bracket}"), unsafe_allow_html=True)

st.divider()

# ── Chart ─────────────────────────────────────────────────────────────────────
fig = go.Figure()

# Balance line
fig.add_trace(go.Scatter(
    x=df["Day"], y=df["Balance ($)"],
    mode="lines",
    name="Balance ($)",
    line=dict(color="#58a6ff", width=2.5),
    fill="tozeroy",
    fillcolor="rgba(88, 166, 255, 0.08)",
    hovertemplate="Day %{x}<br>Balance: $%{y:,.2f}<extra></extra>",
))

# Bracket-change markers
bracket_changes = df[df["Bracket"] != df["Bracket"].shift(1)]
fig.add_trace(go.Scatter(
    x=bracket_changes["Day"],
    y=bracket_changes["Balance ($)"],
    mode="markers",
    name="Bracket Up ▲",
    marker=dict(color="#3fb950", size=9, symbol="triangle-up",
                line=dict(color="#ffffff", width=1)),
    hovertemplate="Day %{x} — Bracket %{customdata}<br>Balance: $%{y:,.2f}<extra></extra>",
    customdata=bracket_changes["Bracket"],
))

fig.update_layout(
    template="plotly_dark",
    paper_bgcolor="#0d1117",
    plot_bgcolor="#0d1117",
    title=dict(text="Account Growth Over Time", font=dict(size=18, color="#58a6ff")),
    xaxis=dict(title="Day", gridcolor="#21262d", zeroline=False),
    yaxis=dict(title="Balance ($)", gridcolor="#21262d", zeroline=False,
               tickformat="$,.2f"),
    legend=dict(bgcolor="#161b22", bordercolor="#30363d", borderwidth=1),
    hovermode="x unified",
    height=480,
    margin=dict(l=10, r=10, t=50, b=10),
)

st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── Table ─────────────────────────────────────────────────────────────────────
st.subheader("📋 Day-by-Day Breakdown")

# Colour bracket column
def bracket_color(val):
    palette = ["#1f3d2e", "#1a3a5c", "#3d2b1f", "#3a1f3d", "#2b3d1f",
               "#3d3a1f", "#1f2b3d", "#3d1f2b", "#1f3d3a", "#2b1f3d"]
    idx = (val - 1) % len(palette)
    return f"background-color: {palette[idx]}; color: #e6edf3"

styled = (
    df.style
    .applymap(bracket_color, subset=["Bracket"])
    .format({"Balance ($)": "${:,.2f}", "Daily Profit ($)": "${:,.2f}"})
    .set_properties(**{"background-color": "#161b22", "color": "#e6edf3"})
)

st.dataframe(styled, use_container_width=True, height=420)

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    f"Projection assumes {daily_profit_pct}% net daily profit, compounding each day. "
    "Bracket increases every $" + f"{bracket_size:,.0f} of cumulative profit."
)
