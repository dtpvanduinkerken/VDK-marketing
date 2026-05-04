import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

# -------------------------
# 🔹 STYLING (VDK STYLE)
# -------------------------
st.markdown("""
<style>
body {background-color:#f9f3e9;}
.block-container {padding-top:2rem;}

.kpi {
    background:white;
    padding:20px;
    border-radius:20px;
    text-align:center;
    box-shadow:0 6px 20px rgba(0,0,0,0.05);
}

h1, h2, h3 {color:#084422;}
</style>
""", unsafe_allow_html=True)

st.title("📊 Van Duinkerken – Marketing Dashboard")

# -------------------------
# 🔹 DATA LADEN
# -------------------------
def load(sheet):
    return pd.read_csv(f"https://opensheet.elk.sh/YOUR_SHEET_ID/{sheet}")

social = load("social")
newsletter = load("newsletter")
members = load("members")
products = load("product_data")

# -------------------------
# 🔹 DATA PREP
# -------------------------
social['date'] = pd.to_datetime(social['date'])
newsletter['date'] = pd.to_datetime(newsletter['date'])
members['created_at'] = pd.to_datetime(members['created_at'])
products['date_online'] = pd.to_datetime(products['date_online'])

# -------------------------
# 🔹 KPI'S
# -------------------------
col1, col2, col3, col4 = st.columns(4)

total_reach = social['views'].sum()
open_rate = (newsletter['opens'].sum() / newsletter['sent'].sum()) * 100
new_members = len(members)

# Product voortgang berekening
grouped = products.groupby('brand').agg(
    totaal=('totaal_producten', 'max'),
    online=('online', 'sum')
).reset_index()

grouped['nog_te_doen'] = grouped['totaal'] - grouped['online']
grouped['percentage'] = (grouped['online'] / grouped['totaal']) * 100

totaal_nog = grouped['nog_te_doen'].sum()

col1.markdown(f"<div class='kpi'><h3>Social bereik</h3><h2>{int(total_reach):,}</h2></div>", unsafe_allow_html=True)
col2.markdown(f"<div class='kpi'><h3>Open rate</h3><h2>{open_rate:.1f}%</h2></div>", unsafe_allow_html=True)
col3.markdown(f"<div class='kpi'><h3>Nieuwe members</h3><h2>{new_members}</h2></div>", unsafe_allow_html=True)
col4.markdown(f"<div class='kpi'><h3>Nog te doen</h3><h2>{int(totaal_nog)}</h2></div>", unsafe_allow_html=True)

# -------------------------
# 🔹 SOCIAL
# -------------------------
st.subheader("📱 Social media")

fig1 = px.line(
    social,
    x='date',
    y='views',
    color='platform',
    title="Bereik over tijd"
)

st.plotly_chart(fig1, use_container_width=True)

# -------------------------
# 🔹 NIEUWSBRIEF
# -------------------------
st.subheader("📩 Nieuwsbrief")

newsletter['open_rate'] = newsletter['opens'] / newsletter['sent'] * 100

fig2 = px.bar(
    newsletter,
    x='campaign',
    y='open_rate',
    title="Open rate per campagne"
)

st.plotly_chart(fig2, use_container_width=True)

# -------------------------
# 🔹 MEMBERS
# -------------------------
st.subheader("👥 Members groei")

members_per_day = members.groupby(members['created_at'].dt.date).size()

fig3 = px.line(
    x=members_per_day.index,
    y=members_per_day.values,
    title="Nieuwe members per dag"
)

st.plotly_chart(fig3, use_container_width=True)

# -------------------------
# 🔹 PRODUCT DATA (BELANGRIJKSTE BLOK)
# -------------------------
st.subheader("📦 Product voortgang per merk")

grouped = grouped.sort_values("nog_te_doen", ascending=False)

fig4 = px.bar(
    grouped,
    x='brand',
    y='nog_te_doen',
    title="Nog online te zetten producten per merk"
)

st.plotly_chart(fig4, use_container_width=True)

st.dataframe(
    grouped[['brand', 'totaal', 'online', 'nog_te_doen', 'percentage']]
)

# -------------------------
# 🔹 VOORSPELLING
# -------------------------
st.subheader("⏱ Verwachting")

per_week = st.number_input("Hoeveel producten zetten jullie per week online?", value=100)

if per_week > 0:
    weeks_needed = totaal_nog / per_week
    st.info(f"Geschatte tijd tot afronding: {weeks_needed:.1f} weken")

# -------------------------
# 🔹 INSIGHTS (MT WAARDE)
# -------------------------
st.subheader("🧠 Belangrijkste inzichten")

# Nieuwsbrief insight
if open_rate > 35:
    st.success("Nieuwsbrief presteert sterk")
else:
    st.warning("Nieuwsbrief kan beter")

# Beste social post
top_post = social.sort_values("views", ascending=False).iloc[0]
st.write(f"Beste social post: {top_post['platform']} met {top_post['views']} views")

# Grootste achterstand merk
top_backlog = grouped.iloc[0]
st.write(f"Grootste achterstand: {top_backlog['brand']} ({int(top_backlog['nog_te_doen'])} producten)")

# Bijna klaar merk
almost_done = grouped.sort_values("percentage", ascending=False).iloc[0]
st.write(f"Bijna klaar: {almost_done['brand']} ({almost_done['percentage']:.0f}%)")