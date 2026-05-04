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
# 🔹 INSTAGRAM
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
# 🔹 KPI’S
# -------------------------
col1, col2, col3, col4 = st.columns(4)

reach = social['views'].sum() if 'views' in social.columns else 0
members_count = len(members)

open_rate = 0
if 'opens' in newsletter.columns and 'sent' in newsletter.columns and newsletter['sent'].sum() > 0:
    open_rate = (newsletter['opens'].sum() / newsletter['sent'].sum()) * 100

# -------------------------
# 🔹 PRODUCT DATA (FIXED)
# -------------------------
grouped = pd.DataFrame()
totaal_nog = 0

if not products.empty and 'brand' in products.columns:

    # FIX: lege online waarden opvullen
    if 'online' in products.columns:
        products['online'] = products['online'].fillna(0)

    if 'totaal_producten' in products.columns:

        grouped = products.groupby('brand').agg(
            totaal=('totaal_producten','max'),
            online=('online','sum')
        ).reset_index()

        grouped['nog_te_doen'] = grouped['totaal'] - grouped['online']
        grouped['percentage'] = (grouped['online'] / grouped['totaal']) * 100

        totaal_nog = grouped['nog_te_doen'].sum()

# KPI rendering
col1.markdown(f"<div class='kpi'><h3>Bereik</h3><h2>{int(reach):,}</h2></div>", unsafe_allow_html=True)
col2.markdown(f"<div class='kpi'><h3>Open rate</h3><h2>{open_rate:.1f}%</h2></div>", unsafe_allow_html=True)
col3.markdown(f"<div class='kpi'><h3>Members</h3><h2>{members_count}</h2></div>", unsafe_allow_html=True)
col4.markdown(f"<div class='kpi'><h3>Instagram</h3><h2>{int(latest)}</h2><p>+{int(growth)}</p></div>", unsafe_allow_html=True)

# -------------------------
# 🔹 MT SAMENVATTING
# -------------------------
st.subheader("📌 Week samenvatting")

if open_rate > 35:
    st.success("Nieuwsbrief presteert sterk")
else:
    st.warning("Nieuwsbrief onder benchmark")

st.write(f"📈 Instagram groei: +{int(growth)}")
st.write(f"📦 Nog te doen: {int(totaal_nog)} producten")

# -------------------------
# 🔹 SOCIAL
# -------------------------
st.subheader("📱 Social trend")

if not social.empty and 'views' in social.columns:
    fig = px.line(social, x='date', y='views')
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Geen social data")

# -------------------------
# 🔹 INSTAGRAM TREND
# -------------------------
if 'followers' in social.columns:
    f = social.dropna(subset=['followers'])
    if not f.empty:
        fig = px.line(f, x='date', y='followers')
        st.plotly_chart(fig, use_container_width=True)

# -------------------------
# 🔹 MEMBERS (FIXED VOOR JOUW DATA)
# -------------------------
st.subheader("👥 Members groei")

if not members.empty:

    # Gebruik last_purchase_date als fallback
    if 'last_purchase_date' in members.columns:
        members['last_purchase_date'] = pd.to_datetime(members['last_purchase_date'], errors='coerce')

        m = members.dropna(subset=['last_purchase_date'])
        m = m.groupby(m['last_purchase_date'].dt.date).size().reset_index()
        m.columns = ['date','new_members']

        fig = px.line(m, x='date', y='new_members')
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.warning("Members data niet bruikbaar")

# -------------------------
# 🔹 PRODUCT VOORTGANG
# -------------------------
st.subheader("📦 Product voortgang")

if not grouped.empty:

    grouped = grouped.sort_values("nog_te_doen", ascending=False)

    fig = px.bar(grouped, x='brand', y='nog_te_doen')
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 🔥 Focus merken")
    st.dataframe(grouped.head(5))

else:
    st.warning("Geen product data beschikbaar")

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
