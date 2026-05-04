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
members['created_at'] = pd.to_datetime(members.get('created_at'), errors='coerce')
newsletter['date'] = pd.to_datetime(newsletter.get('date'), errors='coerce')

# -------------------------
# 🔹 INSTAGRAM VOLGERS
# -------------------------
if 'followers' in social.columns:
    followers_data = social.dropna(subset=['followers']).sort_values('date')

    if len(followers_data) > 1:
        latest = followers_data.iloc[-1]['followers']
        previous = followers_data.iloc[-2]['followers']
        follower_growth = latest - previous
    else:
        latest = followers_data.iloc[-1]['followers'] if len(followers_data) > 0 else 0
        follower_growth = 0
else:
    latest = 0
    follower_growth = 0

# -------------------------
# 🔹 KPI’S
# -------------------------
col1, col2, col3, col4 = st.columns(4)

reach = social['views'].sum() if 'views' in social.columns else 0
members_count = len(members)

open_rate = (newsletter['opens'].sum() / newsletter['sent'].sum()) * 100 if 'opens' in newsletter.columns else 0

# product voortgang
grouped = products.groupby('brand').agg(
    totaal=('totaal_producten','max'),
    online=('online','sum')
).reset_index()

grouped['nog_te_doen'] = grouped['totaal'] - grouped['online']
totaal_nog = grouped['nog_te_doen'].sum()

col1.markdown(f"<div class='kpi'><h3>Bereik</h3><h2>{int(reach):,}</h2></div>", unsafe_allow_html=True)
col2.markdown(f"<div class='kpi'><h3>Open rate</h3><h2>{open_rate:.1f}%</h2></div>", unsafe_allow_html=True)
col3.markdown(f"<div class='kpi'><h3>Members</h3><h2>{members_count}</h2></div>", unsafe_allow_html=True)
col4.markdown(f"<div class='kpi'><h3>Instagram</h3><h2>{int(latest)}</h2><p>+{follower_growth}</p></div>", unsafe_allow_html=True)

# -------------------------
# 🔹 MT SAMENVATTING
# -------------------------
st.subheader("📌 Week samenvatting")

if open_rate > 35:
    st.write("✔ Nieuwsbrief presteert sterk")
else:
    st.write("⚠ Nieuwsbrief onder benchmark")

st.write(f"📈 Instagram groei: +{follower_growth}")
st.write(f"📦 Nog te doen: {int(totaal_nog)} producten")

# -------------------------
# 🔹 SOCIAL TREND
# -------------------------
st.subheader("📱 Social trend")

if 'views' in social.columns:
    fig = px.line(social, x='date', y='views')
    st.plotly_chart(fig, use_container_width=True)

# -------------------------
# 🔹 INSTAGRAM VOLGERS TREND
# -------------------------
if 'followers' in social.columns:
    fig_follow = px.line(followers_data, x='date', y='followers', title="Instagram volgers groei")
    st.plotly_chart(fig_follow, use_container_width=True)

# -------------------------
# 🔹 MEMBERS GROEI
# -------------------------
st.subheader("👥 Members groei")

members_per_day = members.groupby(members['created_at'].dt.date).size().reset_index()
members_per_day.columns = ['date','new_members']

fig_members = px.line(members_per_day, x='date', y='new_members')
st.plotly_chart(fig_members, use_container_width=True)

# -------------------------
# 🔹 PRODUCT VOORTGANG
# -------------------------
st.subheader("📦 Product voortgang")

grouped = grouped.sort_values("nog_te_doen", ascending=False)

fig_products = px.bar(grouped, x='brand', y='nog_te_doen')
st.plotly_chart(fig_products, use_container_width=True)

st.dataframe(grouped.head(5))

# -------------------------
# 🔹 INSIGHTS
# -------------------------
st.subheader("🧠 Insights")

top_brand = grouped.iloc[0]
st.write(f"Grootste achterstand: {top_brand['brand']} ({int(top_brand['nog_te_doen'])})")

top_post = social.sort_values("views", ascending=False).iloc[0]
st.write(f"Beste post: {top_post['views']} views")
