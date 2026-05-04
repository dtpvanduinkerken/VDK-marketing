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
# 🔹 SHEET ID (JOUW SHEET)
# -------------------------
SHEET_ID = "188PcnFIPrcazZ5o2JmoBJ52RuUo-acqkhIWRQyntuI0"

def load(sheet):
    try:
        return pd.read_csv(f"https://opensheet.elk.sh/{SHEET_ID}/{sheet}")
    except:
        st.error(f"Fout bij laden van tab: {sheet}")
        return pd.DataFrame()

# -------------------------
# 🔹 DATA LADEN
# -------------------------
social = load("social")
newsletter = load("newsletter")
members = load("members")
products = load("product_data")

# -------------------------
# 🔹 DATA PREP (veilig)
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
# 🔹 KPI'S
# -------------------------
col1, col2, col3, col4 = st.columns(4)

# Social KPI
total_reach = social['views'].sum() if 'views' in social.columns else 0

# Nieuwsbrief KPI
if 'opens' in newsletter.columns and 'sent' in newsletter.columns and newsletter['sent'].sum() > 0:
    open_rate = (newsletter['opens'].sum() / newsletter['sent'].sum()) * 100
else:
    open_rate = 0

# Members KPI
new_members = len(members)

# -------------------------
# 🔹 PRODUCT BEREKENING (BELANGRIJKSTE)
# -------------------------
if not products.empty and 'brand' in products.columns:

    grouped = products.groupby('brand').agg(
        totaal=('totaal_producten', 'max') if 'totaal_producten' in products.columns else ('brand', 'count'),
        online=('online', 'sum') if 'online' in products.columns else ('brand', 'count')
    ).reset_index()

    grouped['nog_te_doen'] = grouped['totaal'] - grouped['online']
    grouped['percentage'] = (grouped['online'] / grouped['totaal']) * 100

    totaal_nog = grouped['nog_te_doen'].sum()

else:
    grouped = pd.DataFrame()
    totaal_nog = 0

# KPI rendering
col1.markdown(f"<div class='kpi'><h3>Social bereik</h3><h2>{int(total_reach):,}</h2></div>", unsafe_allow_html=True)
col2.markdown(f"<div class='kpi'><h3>Open rate</h3><h2>{open_rate:.1f}%</h2></div>", unsafe_allow_html=True)
col3.markdown(f"<div class='kpi'><h3>Nieuwe members</h3><h2>{new_members}</h2></div>", unsafe_allow_html=True)
col4.markdown(f"<div class='kpi'><h3>Nog te doen</h3><h2>{int(totaal_nog)}</h2></div>", unsafe_allow_html=True)

# -------------------------
# 🔹 SOCIAL
# -------------------------
st.subheader("📱 Social media")

if not social.empty and 'date' in social.columns and 'views' in social.columns:
    fig1 = px.line(social, x='date', y='views', color='platform' if 'platform' in social.columns else None)
    st.plotly_chart(fig1, use_container_width=True)
else:
    st.info("Geen social data beschikbaar")

# -------------------------
# 🔹 NIEUWSBRIEF
# -------------------------
st.subheader("📩 Nieuwsbrief")

if not newsletter.empty and 'campaign' in newsletter.columns:
    if 'opens' in newsletter.columns and 'sent' in newsletter.columns:
        newsletter['open_rate'] = (newsletter['opens'] / newsletter['sent']) * 100

    fig2 = px.bar(newsletter, x='campaign', y='open_rate' if 'open_rate' in newsletter.columns else 'opens')
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.info("Geen nieuwsbrief data beschikbaar")

# -------------------------
# 🔹 MEMBERS
# -------------------------
st.subheader("👥 Members groei")

if not members.empty and 'created_at' in members.columns:
    members_per_day = members.groupby(members['created_at'].dt.date).size()
    fig3 = px.line(x=members_per_day.index, y=members_per_day.values)
    st.plotly_chart(fig3, use_container_width=True)
else:
    st.info("Geen members data beschikbaar")

# -------------------------
# 🔹 PRODUCT DATA
# -------------------------
st.subheader("📦 Product voortgang per merk")

if not grouped.empty:

    grouped = grouped.sort_values("nog_te_doen", ascending=False)

    fig4 = px.bar(
        grouped,
        x='brand',
        y='nog_te_doen',
        title="Nog online te zetten producten per merk"
    )

    st.plotly_chart(fig4, use_container_width=True)

    st.dataframe(grouped[['brand', 'totaal', 'online', 'nog_te_doen', 'percentage']])

else:
    st.info("Geen product data beschikbaar")

# -------------------------
# 🔹 VOORSPELLING
# -------------------------
st.subheader("⏱ Verwachting")

per_week = st.number_input("Hoeveel producten zetten jullie per week online?", value=100)

if per_week > 0:
    weeks_needed = totaal_nog / per_week
    st.info(f"Geschatte tijd tot afronding: {weeks_needed:.1f} weken")

# -------------------------
# 🔹 INSIGHTS
# -------------------------
st.subheader("🧠 Belangrijkste inzichten")

if open_rate > 35:
    st.success("Nieuwsbrief presteert sterk")
else:
    st.warning("Nieuwsbrief kan beter")

if not social.empty and 'views' in social.columns:
    top_post = social.sort_values("views", ascending=False).iloc[0]
    st.write(f"Beste social post: {top_post.get('platform', '')} met {top_post['views']} views")

if not grouped.empty:
    top_backlog = grouped.iloc[0]
    st.write(f"Grootste achterstand: {top_backlog['brand']} ({int(top_backlog['nog_te_doen'])} producten)")
