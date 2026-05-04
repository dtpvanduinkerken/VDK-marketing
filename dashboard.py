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
# 🔹 SHEET ID
# -------------------------
SHEET_ID = "188PcnFIPrcazZ5o2JmoBJ52RuUo-acqkhIWRQyntuI0"

def load(sheet):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet}"
    try:
        return pd.read_csv(url)
    except:
        return pd.DataFrame()

# -------------------------
# 🔹 DATA LADEN
# -------------------------
social = load("social")
newsletter = load("newsletter")
members = load("members")
products = load("product_data")

# -------------------------
# 🔹 DATA PREP
# -------------------------
def safe_date(df, col):
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors='coerce')
    return df

social = safe_date(social, 'date')
newsletter = safe_date(newsletter, 'date')
members = safe_date(members, 'created_at')
products = safe_date(products, 'date_online')

# -------------------------
# 🔹 INSTAGRAM VOLGERS
# -------------------------
latest = 0
follower_growth = 0

if 'followers' in social.columns:
    followers_data = social.dropna(subset=['followers']).sort_values('date')

    if len(followers_data) > 1:
        latest = followers_data.iloc[-1]['followers']
        previous = followers_data.iloc[-2]['followers']
        follower_growth = latest - previous
    elif len(followers_data) == 1:
        latest = followers_data.iloc[-1]['followers']

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
# 🔹 PRODUCT DATA (VEILIG)
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

# KPI rendering
col1.markdown(f"<div class='kpi'><h3>Bereik</h3><h2>{int(reach):,}</h2></div>", unsafe_allow_html=True)
col2.markdown(f"<div class='kpi'><h3>Open rate</h3><h2>{open_rate:.1f}%</h2></div>", unsafe_allow_html=True)
col3.markdown(f"<div class='kpi'><h3>Members</h3><h2>{members_count}</h2></div>", unsafe_allow_html=True)
col4.markdown(f"<div class='kpi'><h3>Instagram</h3><h2>{int(latest)}</h2><p>+{int(follower_growth)}</p></div>", unsafe_allow_html=True)

# -------------------------
# 🔹 MT SAMENVATTING
# -------------------------
st.subheader("📌 Week samenvatting")

if open_rate > 35:
    st.write("✔ Nieuwsbrief presteert sterk")
else:
    st.write("⚠ Nieuwsbrief onder benchmark")

st.write(f"📈 Instagram groei: +{int(follower_growth)}")
st.write(f"📦 Nog te doen: {int(totaal_nog)} producten")

# -------------------------
# 🔹 SOCIAL TREND
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
if 'followers' in social.columns and not social.empty:
    followers_data = social.dropna(subset=['followers'])
    if not followers_data.empty:
        fig_follow = px.line(followers_data, x='date', y='followers')
        st.plotly_chart(fig_follow, use_container_width=True)

# -------------------------
# 🔹 MEMBERS GROEI (FIXED)
# -------------------------
st.subheader("👥 Members groei")

if not members.empty and 'created_at' in members.columns:

    members_per_day = members.groupby(members['created_at'].dt.date).size().reset_index()
    members_per_day.columns = ['date','new_members']

    fig_members = px.line(members_per_day, x='date', y='new_members')
    st.plotly_chart(fig_members, use_container_width=True)

else:
    st.warning("Geen members data")

# -------------------------
# 🔹 PRODUCT VOORTGANG
# -------------------------
st.subheader("📦 Product voortgang")

if not grouped.empty:

    grouped = grouped.sort_values("nog_te_doen", ascending=False)

    fig_products = px.bar(grouped, x='brand', y='nog_te_doen')
    st.plotly_chart(fig_products, use_container_width=True)

    st.dataframe(grouped.head(5))

else:
    st.warning("Geen product data beschikbaar")

# -------------------------
# 🔹 INSIGHTS
# -------------------------
st.subheader("🧠 Insights")

# Product insight (FIX)
if not grouped.empty:
    top_brand = grouped.iloc[0]
    st.write(f"Grootste achterstand: {top_brand['brand']} ({int(top_brand['nog_te_doen'])})")
else:
    st.write("Geen product inzichten beschikbaar")

# Social insight (FIX)
if not social.empty and 'views' in social.columns:
    top_post = social.sort_values("views", ascending=False).iloc[0]
    st.write(f"Beste post: {top_post['views']} views")
else:
    st.write("Geen social inzichten beschikbaar")
