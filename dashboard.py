import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

# -------------------------
# 🔹 STYLING (MATCH VOORBEELD)
# -------------------------
st.markdown("""
<style>

/* ACHTERGROND */
body {
    background:#f4f6f9;
}

/* SIDEBAR */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #084422 0%, #0b5a2f 100%);
    color:white;
}

/* KPI CARDS */
.kpi {
    background:white;
    padding:20px;
    border-radius:18px;
    box-shadow:0 8px 20px rgba(0,0,0,0.05);
    text-align:left;
}

/* PANELEN */
.panel {
    background:white;
    padding:20px;
    border-radius:18px;
    box-shadow:0 8px 20px rgba(0,0,0,0.05);
    margin-bottom:20px;
}

/* SOCIAL CARD */
.card {
    background:white;
    padding:15px;
    border-radius:16px;
    box-shadow:0 5px 15px rgba(0,0,0,0.05);
}

/* TITELS */
h1,h2,h3 { color:#084422; }

</style>
""", unsafe_allow_html=True)

# -------------------------
# 🔹 SIDEBAR
# -------------------------
st.sidebar.title("VDK Dashboard")
page = st.sidebar.radio("Navigatie", [
    "Dashboard",
    "Members",
    "Nieuwsbrief",
    "Social",
    "Producten"
])

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
# 🔹 OPSCHONEN
# -------------------------
if 'date' in social.columns:
    social['date'] = pd.to_datetime(social['date'], errors='coerce')

for col in ['views','likes','comments','shares','followers']:
    if col in social.columns:
        social[col] = pd.to_numeric(social[col], errors='coerce')

for col in ['sent','opens','clicks']:
    if col in newsletter.columns:
        newsletter[col] = pd.to_numeric(newsletter[col], errors='coerce')

# -------------------------
# 🔹 MEMBERS GROEI FIX (JUIST)
# -------------------------
members_growth = pd.DataFrame()

if not members.empty and 'created_at' in members.columns:
    df = members.copy()

    df[['year','week']] = df['created_at'].astype(str).str.extract(r'(\d{4}).*?(\d+)')

    df['year'] = pd.to_numeric(df['year'], errors='coerce')
    df['week'] = pd.to_numeric(df['week'], errors='coerce')

    df = df.dropna(subset=['year','week'])

    members_growth = df.groupby(['year','week']).size().reset_index(name='new_members')

    members_growth['label'] = members_growth['year'].astype(int).astype(str) + " - week " + members_growth['week'].astype(int).astype(str)

    members_growth['sort'] = pd.to_datetime(
        members_growth['year'].astype(str) + members_growth['week'].astype(str) + '1',
        format='%G%V%u'
    )

    members_growth = members_growth.sort_values('sort')

# -------------------------
# 🔹 KPI BEREKENING
# -------------------------
reach = int(social['views'].sum()) if 'views' in social.columns else 0
members_total = len(members)

open_rate = 0
if 'sent' in newsletter.columns and newsletter['sent'].sum() > 0:
    open_rate = (newsletter['opens'].sum() / newsletter['sent'].sum()) * 100

followers = int(social['followers'].max()) if 'followers' in social.columns else 0

# -------------------------
# 🔥 DASHBOARD (HOOFDPAGINA)
# -------------------------
if page == "Dashboard":

    st.title("📊 Marketing Dashboard")

    # KPI ROW
    col1, col2, col3, col4 = st.columns(4)

    col1.markdown(f"<div class='kpi'><h3>Bereik</h3><h2>{reach:,}</h2></div>", unsafe_allow_html=True)
    col2.markdown(f"<div class='kpi'><h3>Members</h3><h2>{members_total}</h2></div>", unsafe_allow_html=True)
    col3.markdown(f"<div class='kpi'><h3>Open rate</h3><h2>{open_rate:.1f}%</h2></div>", unsafe_allow_html=True)
    col4.markdown(f"<div class='kpi'><h3>Instagram</h3><h2>{followers}</h2></div>", unsafe_allow_html=True)

    # -------------------------
    # 🔹 GRAFIEKEN (2 KOLOMMEN)
    # -------------------------
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.subheader("Members groei")

        if not members_growth.empty:
            fig = px.line(members_growth, x='label', y='new_members', markers=True)
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.subheader("Social bereik")

        if not social.empty:
            fig = px.line(social, x='date', y='views')
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # -------------------------
    # 🔹 ONDERSTE BLOKKEN
    # -------------------------
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.subheader("Nieuwsbrief")

        if not newsletter.empty:
            st.metric("Verzonden", int(newsletter['sent'].sum()))
            st.metric("Opens", int(newsletter['opens'].sum()))

        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.subheader("Top social post")

        if not social.empty:
            top = social.sort_values("views", ascending=False).head(1)
            st.write(top[['platform','type','views']])

        st.markdown("</div>", unsafe_allow_html=True)

# -------------------------
# 🔹 OVERIGE PAGINA'S (ONGEWIJZIGD)
# -------------------------
if page == "Members":
    st.title("Members")
    if not members_growth.empty:
        fig = px.line(members_growth, x='label', y='new_members')
        st.plotly_chart(fig)

if page == "Nieuwsbrief":
    st.title("Nieuwsbrief")
    st.dataframe(newsletter)

if page == "Social":
    st.title("Social")
    st.dataframe(social)

if page == "Producten":
    st.title("Producten")
    st.dataframe(products)
