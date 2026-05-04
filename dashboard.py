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
if 'date' in social.columns:
    social['date'] = pd.to_datetime(social['date'], errors='coerce')

for col in ['views','likes','comments','shares','followers']:
    if col in social.columns:
        social[col] = pd.to_numeric(social[col], errors='coerce')

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
# 🔹 MEMBERS GROEI
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
# 🔹 TARGETS
# -------------------------
TARGET_MEMBERS = 25
TARGET_OPENRATE = 40

open_rate = 0
if 'opens' in newsletter.columns and 'sent' in newsletter.columns:
    if newsletter['sent'].sum() > 0:
        open_rate = (newsletter['opens'].sum() / newsletter['sent'].sum()) * 100

last_members = members_growth.iloc[-1]['new_members'] if len(members_growth)>0 else 0

# -------------------------
# 🔹 INSIGHTS
# -------------------------
st.subheader("📌 Belangrijkste inzichten")

if last_members >= TARGET_MEMBERS:
    st.success(f"Members groei boven target (+{int(last_members)})")
else:
    st.warning(f"Members groei onder target ({int(last_members)} vs {TARGET_MEMBERS})")

if open_rate >= TARGET_OPENRATE:
    st.success("Nieuwsbrief presteert sterk")
else:
    st.warning("Nieuwsbrief onder benchmark")

if growth > 0:
    st.success(f"Instagram groeit (+{growth})")
else:
    st.warning("Instagram groeit niet")

# -------------------------
# 🔹 KPI'S
# -------------------------
col1, col2, col3, col4 = st.columns(4)

reach = int(social['views'].sum()) if 'views' in social.columns else 0

col1.markdown(f"<div class='kpi'><h3>Bereik</h3><h2>{reach:,}</h2></div>", unsafe_allow_html=True)
col2.markdown(f"<div class='kpi'><h3>Members</h3><h2>{int(last_members)}</h2><p>Target: {TARGET_MEMBERS}</p></div>", unsafe_allow_html=True)
col3.markdown(f"<div class='kpi'><h3>Open rate</h3><h2>{open_rate:.1f}%</h2><p>Target: {TARGET_OPENRATE}%</p></div>", unsafe_allow_html=True)
col4.markdown(f"<div class='kpi'><h3>Instagram</h3><h2>{latest}</h2><p>+{growth}</p></div>", unsafe_allow_html=True)

# -------------------------
# 🔹 MEMBERS VISUALS
# -------------------------
st.subheader("👥 Members groei")

if not members_growth.empty:

    fig = px.line(members_growth, x='label', y='new_members', markers=True)
    st.plotly_chart(fig, use_container_width=True)

    members_growth['cumulative'] = members_growth['new_members'].cumsum()

    fig2 = px.line(members_growth, x='label', y='cumulative', title="Totale groei", markers=True)
    st.plotly_chart(fig2, use_container_width=True)

# -------------------------
# 🔹 SOCIAL ANALYSE
# -------------------------
st.subheader("📱 Social analyse")

df = social.copy()

if all(col in df.columns for col in ['likes','comments','shares']):
    df['engagement'] = df['likes'] + df['comments'] + df['shares']
else:
    df['engagement'] = 0

col1, col2 = st.columns(2)

if 'platform' in df.columns:
    platform = col1.selectbox("Platform", ["Alles"] + df['platform'].dropna().unique().tolist())
    if platform != "Alles":
        df = df[df['platform'] == platform]

if 'type' in df.columns:
    t = col2.selectbox("Type", ["Alles"] + df['type'].dropna().unique().tolist())
    if t != "Alles":
        df = df[df['type'] == t]

# -------------------------
# 🔥 VISUELE SOCIAL CARDS (NIEUW)
# -------------------------
st.markdown("### 🔥 Beste posts visueel")

cols = st.columns(3)

for i, (_, row) in enumerate(df.sort_values("views", ascending=False).head(6).iterrows()):
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
# 🔹 TOP POSTS (BESTOND AL)
# -------------------------
st.markdown("### 🔥 Top posts")

for _, row in df.sort_values("views", ascending=False).head(3).iterrows():
    st.write(f"{row.get('type','')} - {int(row.get('views',0))} views")

# -------------------------
# 🔹 CONTENT ADVIES
# -------------------------
st.subheader("🧠 Content advies")

if 'type' in df.columns:
    perf = df.groupby('type')['views'].mean().sort_values(ascending=False)
    if not perf.empty:
        st.success(f"Focus op {perf.index[0]} content")

# -------------------------
# 🔹 VOLLEDIGE TABEL (BESTOND AL)
# -------------------------
st.subheader("📊 Alle social posts")

cols = ['date','platform','type','views','likes','comments','shares','engagement']
cols = [c for c in cols if c in df.columns]

st.dataframe(df[cols], use_container_width=True)

# -------------------------
# 🔹 PRODUCTEN
# -------------------------
st.subheader("📦 Product voortgang")

if not products.empty and 'brand' in products.columns:

    products['online'] = pd.to_numeric(products['online'], errors='coerce').fillna(0)

    grouped = products.groupby('brand').agg(
        totaal=('totaal_producten','max'),
        online=('online','sum')
    ).reset_index()

    grouped['nog'] = grouped['totaal'] - grouped['online']

    fig = px.bar(grouped, x='brand', y='nog')
    st.plotly_chart(fig, use_container_width=True)
