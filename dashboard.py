import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

# -------------------------
# 🔹 VDK DASHBOARD STYLING
# -------------------------
st.markdown("""
<style>

body {
    background:#f9f3e9;
}

/* SIDEBAR */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #084422 0%, #0b5a2f 100%);
    color:white;
}

/* TITELS */
h1 {
    font-size:30px;
    font-weight:800;
    color:#084422;
}

h2 {
    margin-top:40px;
    font-size:22px;
    font-weight:700;
    color:#084422;
}

/* KPI CARDS */
.kpi {
    background:#ffffff;
    padding:22px;
    border-radius:22px;
    text-align:left;
    box-shadow:0 10px 25px rgba(0,0,0,0.05);
    border-left:6px solid #8cbe26;
}

.kpi h3 {
    font-size:14px;
    color:#7a8f85;
}

.kpi h2 {
    font-size:26px;
    margin:0;
}

/* SOCIAL CARDS */
.card {
    background:white;
    padding:18px;
    border-radius:20px;
    box-shadow:0 8px 20px rgba(0,0,0,0.05);
}

/* GRAFIEKEN */
.plotly-chart {
    background:white;
    border-radius:20px;
    padding:10px;
}

.block-container {
    max-width:1400px;
}

</style>
""", unsafe_allow_html=True)

st.title("📊 Marketing Dashboard")

# -------------------------
# 🔹 DATA LADEN
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
# 🔹 KPI BEREKENING
# -------------------------
reach = int(social['views'].sum()) if 'views' in social.columns else 0

open_rate = 0
if newsletter['sent'].sum() > 0:
    open_rate = (newsletter['opens'].sum() / newsletter['sent'].sum()) * 100

# -------------------------
# 🔹 MEMBERS GROEI
# -------------------------
members_growth = pd.DataFrame()

if not members.empty:
    df = members.copy()
    df[['year','week']] = df['created_at'].astype(str).str.extract(r'(\d{4}).*?(\d+)')
    df = df.dropna()

    members_growth = df.groupby(['year','week']).size().reset_index(name='new_members')
    members_growth['label'] = members_growth['year'].astype(str) + " - week " + members_growth['week'].astype(str)

# -------------------------
# 🔹 INSTAGRAM
# -------------------------
latest = 0

if 'followers' in social.columns:
    latest = int(social['followers'].max())

# -------------------------
# 🔹 KPI'S
# -------------------------
st.subheader("📊 KPI overzicht")

col1, col2, col3, col4 = st.columns(4)

col1.markdown(f"<div class='kpi'><h3>Bereik</h3><h2>{reach:,}</h2></div>", unsafe_allow_html=True)
col2.markdown(f"<div class='kpi'><h3>Members</h3><h2>{len(members)}</h2></div>", unsafe_allow_html=True)
col3.markdown(f"<div class='kpi'><h3>Open rate</h3><h2>{open_rate:.1f}%</h2></div>", unsafe_allow_html=True)
col4.markdown(f"<div class='kpi'><h3>Instagram</h3><h2>{latest}</h2></div>", unsafe_allow_html=True)

# -------------------------
# 👥 MEMBERS
# -------------------------
st.subheader("👥 Members groei")

if not members_growth.empty:
    fig = px.line(members_growth, x='label', y='new_members', markers=True)
    st.plotly_chart(fig, use_container_width=True)

# -------------------------
# 📧 NIEUWSBRIEF
# -------------------------
st.subheader("📧 Nieuwsbrief")

if not newsletter.empty:

    col1, col2, col3 = st.columns(3)

    col1.metric("Verzonden", int(newsletter['sent'].sum()))
    col2.metric("Opens", int(newsletter['opens'].sum()))
    col3.metric("Clicks", int(newsletter['clicks'].sum()))

    fig = px.line(newsletter, y='sent')
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 🔥 Beste mailing")
    st.dataframe(newsletter.sort_values("opens", ascending=False).head(5))

# -------------------------
# 📱 SOCIAL
# -------------------------
st.subheader("📱 Social analyse")

df = social.copy()

if all(col in df.columns for col in ['likes','comments','shares']):
    df['engagement'] = df['likes'] + df['comments'] + df['shares']
else:
    df['engagement'] = 0

df = df.sort_values("views", ascending=False)

# VISUELE CARDS
st.markdown("### 🔥 Beste posts visueel")

cols = st.columns(3)

for i, (_, row) in enumerate(df.head(6).iterrows()):
    with cols[i % 3]:
        st.markdown(f"""
        <div class='card'>
            <div style="font-size:13px;color:#8aa39a;">
                {row.get('platform','')} • {row.get('type','')}
            </div>
            <div style="font-size:22px;font-weight:700;">
                {int(row.get('views',0)):,}
            </div>
            <div style="font-size:13px;">
                ❤️ {int(row.get('likes',0))}  
                💬 {int(row.get('comments',0))}  
                🔁 {int(row.get('shares',0))}
            </div>
        </div>
        """, unsafe_allow_html=True)

# TABEL
st.subheader("📊 Alle social posts")

cols = ['date','platform','type','views','likes','comments','shares','engagement']
cols = [c for c in cols if c in df.columns]

st.dataframe(df[cols], use_container_width=True)

# -------------------------
# 📦 PRODUCTEN
# -------------------------
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
