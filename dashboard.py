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
    padding:18px;
    border-radius:18px;
    text-align:center;
    border-top:4px solid #8cbe26;
    box-shadow:0 5px 15px rgba(0,0,0,0.05);
}

.section {
    margin-top:40px;
}

h1,h2,h3{color:#084422;}
</style>
""", unsafe_allow_html=True)

st.title("📊 Marketing Dashboard")

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
members_insights = load("members_insights")
products = load("product_data")

# -------------------------
# 🔹 OPSCHONEN
# -------------------------
for col in ['views','likes','comments','shares','followers']:
    if col in social.columns:
        social[col] = pd.to_numeric(social[col], errors='coerce')

if 'date' in social.columns:
    social['date'] = pd.to_datetime(social['date'], errors='coerce')

# nieuwsbrief
for col in ['sent','opens','clicks']:
    if col in newsletter.columns:
        newsletter[col] = pd.to_numeric(newsletter[col], errors='coerce')

# -------------------------
# 🔹 KPI BEREKENING
# -------------------------
reach = int(social['views'].sum()) if 'views' in social.columns else 0

open_rate = 0
click_rate = 0

if 'opens' in newsletter.columns and 'sent' in newsletter.columns:
    if newsletter['sent'].sum() > 0:
        open_rate = (newsletter['opens'].sum() / newsletter['sent'].sum()) * 100

if 'clicks' in newsletter.columns and 'sent' in newsletter.columns:
    if newsletter['sent'].sum() > 0:
        click_rate = (newsletter['clicks'].sum() / newsletter['sent'].sum()) * 100

# members groei laatste week
members_growth = 0
if not members.empty and 'created_at' in members.columns:
    df = members.copy()
    df[['year','week']] = df['created_at'].astype(str).str.extract(r'(\d{4}).*?(\d+)')
    df = df.dropna()
    weekly = df.groupby(['year','week']).size().reset_index(name='new_members')
    members_growth = weekly.iloc[-1]['new_members'] if len(weekly) > 0 else 0

# -------------------------
# 🔥 INSIGHTS
# -------------------------
st.subheader("📌 Belangrijkste inzichten")

if open_rate > 40:
    st.success("Nieuwsbrief presteert sterk")
else:
    st.warning("Nieuwsbrief onder benchmark")

if members_growth > 25:
    st.success("Members groei goed")
else:
    st.warning("Members groei laag")

# -------------------------
# 🔹 KPI'S
# -------------------------
st.subheader("📊 KPI overzicht")

col1, col2, col3, col4 = st.columns(4)

col1.markdown(f"<div class='kpi'><h3>Bereik</h3><h2>{reach:,}</h2></div>", unsafe_allow_html=True)
col2.markdown(f"<div class='kpi'><h3>Members</h3><h2>{members_growth}</h2></div>", unsafe_allow_html=True)
col3.markdown(f"<div class='kpi'><h3>Open rate</h3><h2>{open_rate:.1f}%</h2></div>", unsafe_allow_html=True)
col4.markdown(f"<div class='kpi'><h3>Click rate</h3><h2>{click_rate:.1f}%</h2></div>", unsafe_allow_html=True)

# -------------------------
# 👥 MEMBERS
# -------------------------
st.markdown("<div class='section'></div>", unsafe_allow_html=True)
st.subheader("👥 Members")

if not members.empty:
    df = members.copy()
    df[['year','week']] = df['created_at'].astype(str).str.extract(r'(\d{4}).*?(\d+)')
    df = df.dropna()

    weekly = df.groupby(['year','week']).size().reset_index(name='new_members')
    weekly['label'] = weekly['year'].astype(str) + " - week " + weekly['week'].astype(str)

    fig = px.line(weekly, x='label', y='new_members')
    st.plotly_chart(fig, use_container_width=True)

# -------------------------
# 📧 NIEUWSBRIEF (NIEUW)
# -------------------------
st.markdown("<div class='section'></div>", unsafe_allow_html=True)
st.subheader("📧 Nieuwsbrief prestaties")

if not newsletter.empty:

    total_sent = newsletter['sent'].sum()
    total_opens = newsletter['opens'].sum()
    total_clicks = newsletter['clicks'].sum()

    col1, col2, col3 = st.columns(3)

    col1.metric("Verzonden", int(total_sent))
    col2.metric("Opens", int(total_opens))
    col3.metric("Clicks", int(total_clicks))

    # grafiek
    if 'sent' in newsletter.columns:
        fig = px.line(newsletter, y='sent', title="Verzonden mails")
        st.plotly_chart(fig, use_container_width=True)

    # beste mailing
    best = newsletter.sort_values("opens", ascending=False).head(1)

    st.markdown("### 🔥 Beste mailing")
    st.dataframe(best)

# -------------------------
# 📱 SOCIAL
# -------------------------
st.markdown("<div class='section'></div>", unsafe_allow_html=True)
st.subheader("📱 Social")

if not social.empty:
    fig = px.line(social, x='date', y='views')
    st.plotly_chart(fig, use_container_width=True)

# -------------------------
# 📦 PRODUCTEN
# -------------------------
st.markdown("<div class='section'></div>", unsafe_allow_html=True)
st.subheader("📦 Product voortgang")

if not products.empty:
    products['online'] = pd.to_numeric(products['online'], errors='coerce')

    grouped = products.groupby('brand').agg(
        totaal=('totaal_producten','max'),
        online=('online','sum')
    ).reset_index()

    grouped['nog'] = grouped['totaal'] - grouped['online']

    fig = px.bar(grouped, x='brand', y='nog')
    st.plotly_chart(fig, use_container_width=True)
