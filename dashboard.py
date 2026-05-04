import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

# -------------------------
# 🔹 STYLING (VDK)
# -------------------------
st.markdown("""
<style>
body {background-color:#f9f3e9;}

.kpi {
    background:white;
    padding:20px;
    border-radius:20px;
    text-align:center;
    border-top:4px solid #8cbe26;
    box-shadow:0 5px 15px rgba(0,0,0,0.05);
}

.card {
    background:white;
    padding:15px;
    border-radius:18px;
    box-shadow:0 5px 15px rgba(0,0,0,0.05);
    margin-bottom:15px;
}

h1,h2,h3{color:#084422;}
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
members_insights = load("members_insights")
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
click_rate = 0

if 'sent' in newsletter.columns and newsletter['sent'].sum() > 0:
    open_rate = (newsletter['opens'].sum() / newsletter['sent'].sum()) * 100
    click_rate = (newsletter['clicks'].sum() / newsletter['sent'].sum()) * 100

# -------------------------
# 🔹 MEMBERS GROEI
# -------------------------
members_growth = pd.DataFrame()

if not members.empty and 'created_at' in members.columns:
    df = members.copy()
    df[['year','week']] = df['created_at'].astype(str).str.extract(r'(\d{4}).*?(\d+)')
    df = df.dropna()

    members_growth = df.groupby(['year','week']).size().reset_index(name='new_members')
    members_growth['label'] = members_growth['year'].astype(str) + " - week " + members_growth['week'].astype(str)

last_members = members_growth.iloc[-1]['new_members'] if len(members_growth)>0 else 0

# -------------------------
# 🔹 INSTAGRAM
# -------------------------
latest = 0
growth = 0

if 'followers' in social.columns:
    df = social.copy()
    if 'platform' in df.columns:
        df = df[df['platform'].astype(str).str.lower() == 'instagram']

    df = df.dropna(subset=['followers','date']).sort_values('date')
    df = df.groupby(df['date'].dt.date).tail(1)

    if not df.empty:
        latest = int(df.iloc[-1]['followers'])
        if len(df) > 1:
            growth = latest - int(df.iloc[-2]['followers'])

# -------------------------
# 🔹 KPI'S
# -------------------------
st.subheader("📊 KPI overzicht")

col1, col2, col3, col4 = st.columns(4)

col1.markdown(f"<div class='kpi'><h3>Bereik</h3><h2>{reach:,}</h2></div>", unsafe_allow_html=True)
col2.markdown(f"<div class='kpi'><h3>Members</h3><h2>{last_members}</h2></div>", unsafe_allow_html=True)
col3.markdown(f"<div class='kpi'><h3>Open rate</h3><h2>{open_rate:.1f}%</h2></div>", unsafe_allow_html=True)
col4.markdown(f"<div class='kpi'><h3>Instagram</h3><h2>{latest}</h2><p>+{growth}</p></div>", unsafe_allow_html=True)

# -------------------------
# 👥 MEMBERS
# -------------------------
st.subheader("👥 Members groei")

if not members_growth.empty:
    fig = px.line(members_growth, x='label', y='new_members')
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
# 📱 SOCIAL ANALYSE
# -------------------------
st.subheader("📱 Social analyse")

df = social.copy()

if all(col in df.columns for col in ['likes','comments','shares']):
    df['engagement'] = df['likes'] + df['comments'] + df['shares']
else:
    df['engagement'] = 0

# filters
col1, col2 = st.columns(2)

if 'platform' in df.columns:
    p = col1.selectbox("Platform", ["Alles"] + df['platform'].dropna().unique().tolist())
    if p != "Alles":
        df = df[df['platform'] == p]

if 'type' in df.columns:
    t = col2.selectbox("Type", ["Alles"] + df['type'].dropna().unique().tolist())
    if t != "Alles":
        df = df[df['type'] == t]

# -------------------------
# 🔥 VISUELE SOCIAL CARDS
# -------------------------
st.markdown("### 🔥 Beste posts visueel")

df = df.sort_values("views", ascending=False)

cols = st.columns(3)

for i, (_, row) in enumerate(df.head(6).iterrows()):
    with cols[i % 3]:
        st.markdown(f"""
        <div class='card'>
            <b>{row.get('platform','')}</b><br>
            {row.get('type','')}<br><br>
            👁 {int(row.get('views',0)):,} views<br>
            ❤️ {int(row.get('likes',0))}<br>
            💬 {int(row.get('comments',0))}<br>
            🔁 {int(row.get('shares',0))}
        </div>
        """, unsafe_allow_html=True)

# -------------------------
# 🔹 SOCIAL TABEL
# -------------------------
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
