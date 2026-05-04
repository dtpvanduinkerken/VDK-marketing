import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

# -------------------------
# 🔹 VDK STYLING
# -------------------------
st.markdown("""
<style>
body {background-color:#f9f3e9;}

.block-container{
    padding-top:2rem;
}

.kpi {
    background:white;
    padding:22px;
    border-radius:22px;
    text-align:center;
    box-shadow:0 10px 25px rgba(0,0,0,0.05);
    border-top:4px solid #8cbe26;
}

h1,h2,h3{
    color:#084422;
}
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
products = load("product_data")

# -------------------------
# 🔹 DATA OPSCHONEN
# -------------------------
def clean_number(series):
    return pd.to_numeric(
        series.astype(str)
        .str.replace(".", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.replace(" ", "", regex=False),
        errors='coerce'
    )

if 'date' in social.columns:
    social['date'] = pd.to_datetime(social['date'], errors='coerce')

if 'views' in social.columns:
    social['views'] = clean_number(social['views'])

if 'followers' in social.columns:
    social['followers'] = clean_number(social['followers'])

if 'last_purchase_date' in members.columns:
    members['last_purchase_date'] = pd.to_datetime(members['last_purchase_date'], errors='coerce')

# -------------------------
# 🔥 INSTAGRAM VOLGERS (DEFINITIEVE FIX)
# -------------------------
latest = 0
growth = 0
followers_data = pd.DataFrame()

if not social.empty and 'followers' in social.columns:

    df = social.copy()

    # Alleen Instagram
    if 'platform' in df.columns:
        df['platform'] = df['platform'].astype(str).str.lower()
        df = df[df['platform'] == 'instagram']

    # Geldige rijen
    df = df.dropna(subset=['followers', 'date'])

    # Sorteren
    df = df.sort_values('date')

    if not df.empty:
        followers_data = df

        latest = int(df.iloc[-1]['followers'])

        if len(df) > 1:
            previous = int(df.iloc[-2]['followers'])
            growth = latest - previous

# -------------------------
# 🔹 KPI'S
# -------------------------
col1, col2, col3, col4 = st.columns(4)

reach = int(social['views'].sum()) if 'views' in social.columns else 0
members_count = len(members)

open_rate = 0
if 'opens' in newsletter.columns and 'sent' in newsletter.columns:
    if newsletter['sent'].sum() > 0:
        open_rate = (newsletter['opens'].sum() / newsletter['sent'].sum()) * 100

# product data
grouped = pd.DataFrame()
totaal_nog = 0

if not products.empty and 'brand' in products.columns:

    if 'online' in products.columns:
        products['online'] = pd.to_numeric(products['online'], errors='coerce').fillna(0)

    if 'totaal_producten' in products.columns:

        grouped = products.groupby('brand').agg(
            totaal=('totaal_producten','max'),
            online=('online','sum')
        ).reset_index()

        grouped['nog_te_doen'] = grouped['totaal'] - grouped['online']
        totaal_nog = int(grouped['nog_te_doen'].sum())

# KPI cards
col1.markdown(f"<div class='kpi'><h3>Bereik</h3><h2>{reach:,}</h2></div>", unsafe_allow_html=True)
col2.markdown(f"<div class='kpi'><h3>Open rate</h3><h2>{open_rate:.1f}%</h2></div>", unsafe_allow_html=True)
col3.markdown(f"<div class='kpi'><h3>Members</h3><h2>{members_count}</h2></div>", unsafe_allow_html=True)
col4.markdown(f"<div class='kpi'><h3>Instagram</h3><h2>{latest}</h2><p>+{growth}</p></div>", unsafe_allow_html=True)

# -------------------------
# 🔹 SAMENVATTING
# -------------------------
st.subheader("📌 Week samenvatting")

if open_rate > 35:
    st.success("Nieuwsbrief presteert sterk")
else:
    st.warning("Nieuwsbrief kan beter")

if growth > 0:
    st.success(f"Instagram groeit (+{growth})")
else:
    st.warning("Instagram groeit niet")

st.write(f"📦 Nog te doen: {totaal_nog} producten")

# -------------------------
# 🔹 SOCIAL TREND
# -------------------------
st.subheader("📱 Social")

if not social.empty and 'views' in social.columns:
    fig = px.line(social, x='date', y='views')
    fig.update_layout(plot_bgcolor='white')
    st.plotly_chart(fig, use_container_width=True)

# -------------------------
# 🔹 INSTAGRAM TREND
# -------------------------
if not followers_data.empty:
    fig = px.line(followers_data, x='date', y='followers', title="Instagram groei")
    fig.update_layout(plot_bgcolor='white')
    st.plotly_chart(fig, use_container_width=True)

# -------------------------
# 🔹 MEMBERS
# -------------------------
st.subheader("👥 Members")

if not members.empty and 'last_purchase_date' in members.columns:

    m = members.dropna(subset=['last_purchase_date'])
    m = m.groupby(m['last_purchase_date'].dt.date).size().reset_index()
    m.columns = ['date','new_members']

    fig = px.line(m, x='date', y='new_members')
    fig.update_layout(plot_bgcolor='white')
    st.plotly_chart(fig, use_container_width=True)

# -------------------------
# 🔹 PRODUCTEN
# -------------------------
st.subheader("📦 Product voortgang")

if not grouped.empty:

    grouped = grouped.sort_values("nog_te_doen", ascending=False)

    fig = px.bar(grouped, x='brand', y='nog_te_doen')
    fig.update_layout(plot_bgcolor='white')
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 🔥 Focus merken")
    st.dataframe(grouped.head(5))

# -------------------------
# 🔹 INSIGHTS
# -------------------------
st.subheader("🧠 Insights")

if not grouped.empty:
    top_brand = grouped.iloc[0]
    st.write(f"Grootste achterstand: {top_brand['brand']} ({int(top_brand['nog_te_doen'])})")

if not social.empty and 'views' in social.columns:
    top_post = social.sort_values("views", ascending=False).iloc[0]
    st.write(f"Beste post: {top_post['views']} views")
