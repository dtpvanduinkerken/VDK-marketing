import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

# -------------------------
# 🔹 STYLING
# -------------------------
st.markdown("""
<style>
body {background-color:#f9f3e9;}
.kpi {
    background:white;
    padding:20px;
    border-radius:20px;
    text-align:center;
    box-shadow:0 6px 20px rgba(0,0,0,0.05);
}
h1,h2,h3{color:#084422;}
</style>
""", unsafe_allow_html=True)

st.title("📊 Marketing Dashboard – MT Overzicht")

# -------------------------
# 🔹 DATA
# -------------------------
SHEET_ID = "188PcnFIPrcazZ5o2JmoBJ52RuUo-acqkhIWRQyntuI0"

def load(sheet):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet}"
    try:
        return pd.read_csv(url)
    except:
        return pd.DataFrame()

social = load("social")
newsletter = load("newsletter")
members = load("members")
products = load("product_data")

# -------------------------
# 🔹 DATA PREP
# -------------------------
social['date'] = pd.to_datetime(social.get('date'), errors='coerce')
newsletter['date'] = pd.to_datetime(newsletter.get('date'), errors='coerce')
members['created_at'] = pd.to_datetime(members.get('created_at'), errors='coerce')

# -------------------------
# 🔹 INSTAGRAM GROEI
# -------------------------
latest = 0
growth = 0

if 'followers' in social.columns:
    f = social.dropna(subset=['followers']).sort_values('date')

    if len(f) > 1:
        latest = f.iloc[-1]['followers']
        growth = latest - f.iloc[-2]['followers']
    elif len(f) == 1:
        latest = f.iloc[-1]['followers']

# -------------------------
# 🔹 KPI BASIS
# -------------------------
reach = social['views'].sum() if 'views' in social.columns else 0
members_count = len(members)

open_rate = 0
if 'opens' in newsletter.columns and 'sent' in newsletter.columns and newsletter['sent'].sum() > 0:
    open_rate = (newsletter['opens'].sum() / newsletter['sent'].sum()) * 100

# -------------------------
# 🔹 PRODUCT DATA
# -------------------------
grouped = pd.DataFrame()
totaal_nog = 0

if not products.empty and 'brand' in products.columns:
    if 'totaal_producten' in products.columns and 'online' in products.columns:
        grouped = products.groupby('brand').agg(
            totaal=('totaal_producten','max'),
            online=('online','sum')
        ).reset_index()

        grouped['nog_te_doen'] = grouped['totaal'] - grouped['online']
        grouped['percentage'] = (grouped['online'] / grouped['totaal']) * 100

        totaal_nog = grouped['nog_te_doen'].sum()

# -------------------------
# 🔹 KPI'S
# -------------------------
col1, col2, col3, col4 = st.columns(4)

col1.markdown(f"<div class='kpi'><h3>Bereik</h3><h2>{int(reach):,}</h2></div>", unsafe_allow_html=True)
col2.markdown(f"<div class='kpi'><h3>Open rate</h3><h2>{open_rate:.1f}%</h2></div>", unsafe_allow_html=True)
col3.markdown(f"<div class='kpi'><h3>Members</h3><h2>{members_count}</h2></div>", unsafe_allow_html=True)
col4.markdown(f"<div class='kpi'><h3>Instagram</h3><h2>{int(latest)}</h2><p>+{int(growth)}</p></div>", unsafe_allow_html=True)

# -------------------------
# 🔥 MT SAMENVATTING
# -------------------------
st.subheader("📌 Week samenvatting")

insights = []
alerts = []

if open_rate > 35:
    insights.append("Nieuwsbrief presteert boven benchmark")
else:
    alerts.append("Nieuwsbrief performance onder benchmark")

if growth > 0:
    insights.append(f"Instagram groeit (+{growth})")
else:
    alerts.append("Instagram groei stagneert")

if totaal_nog > 0:
    alerts.append(f"{int(totaal_nog)} producten nog online te zetten")

for i in insights:
    st.success(i)

for a in alerts:
    st.warning(a)

# -------------------------
# 🔹 SOCIAL TREND
# -------------------------
st.subheader("📱 Social trend")

if not social.empty and 'views' in social.columns:
    fig = px.line(social, x='date', y='views')
    st.plotly_chart(fig, use_container_width=True)

# -------------------------
# 🔹 INSTAGRAM TREND
# -------------------------
if 'followers' in social.columns:
    f = social.dropna(subset=['followers'])
    if not f.empty:
        fig = px.line(f, x='date', y='followers', title="Instagram groei")
        st.plotly_chart(fig, use_container_width=True)

# -------------------------
# 🔹 MEMBERS GROEI
# -------------------------
st.subheader("👥 Members groei")

if not members.empty and 'created_at' in members.columns:
    m = members.groupby(members['created_at'].dt.date).size().reset_index()
    m.columns = ['date','new_members']

    fig = px.line(m, x='date', y='new_members')
    st.plotly_chart(fig, use_container_width=True)

# -------------------------
# 🔹 PRODUCT STURING
# -------------------------
st.subheader("📦 Product voortgang")

if not grouped.empty:

    grouped = grouped.sort_values("nog_te_doen", ascending=False)

    fig = px.bar(grouped, x='brand', y='nog_te_doen')
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 🔥 Focus merken (meeste werk)")
    st.dataframe(grouped.head(5))

# -------------------------
# 🔹 SLIMME INSIGHTS
# -------------------------
st.subheader("🧠 Slimme inzichten")

if not social.empty and 'views' in social.columns:
    best_post = social.sort_values("views", ascending=False).iloc[0]
    st.write(f"Beste content: {best_post['views']} views")

if not grouped.empty:
    risk = grouped.iloc[0]
    st.write(f"Grootste risico: {risk['brand']} ({int(risk['nog_te_doen'])} producten achter)")
