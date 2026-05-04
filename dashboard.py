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
.kpi {
    background:white;
    padding:22px;
    border-radius:22px;
    text-align:center;
    box-shadow:0 10px 25px rgba(0,0,0,0.05);
    border-top:4px solid #8cbe26;
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
products = load("product_data")

# -------------------------
# 🔹 CLEAN NUMBERS (FIX)
# -------------------------
def clean_number(series):
    def parse(x):
        if pd.isna(x):
            return None
        x = str(x)
        x = ''.join(c for c in x if c.isdigit())
        return int(x) if x else None
    return series.apply(parse)

if 'date' in social.columns:
    social['date'] = pd.to_datetime(social['date'], errors='coerce')

for col in ['views','likes','comments','shares','saves','followers']:
    if col in social.columns:
        social[col] = clean_number(social[col])

# -------------------------
# 🔥 INSTAGRAM VOLGERS
# -------------------------
latest = 0
growth = 0
followers_data = pd.DataFrame()

if 'followers' in social.columns:
    df = social.copy()

    if 'platform' in df.columns:
        df = df[df['platform'].astype(str).str.lower() == 'instagram']

    df = df.dropna(subset=['followers','date']).sort_values('date')

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

# KPI CARDS
col1.markdown(f"<div class='kpi'><h3>Bereik</h3><h2>{reach:,}</h2></div>", unsafe_allow_html=True)
col2.markdown(f"<div class='kpi'><h3>Open rate</h3><h2>{open_rate:.1f}%</h2></div>", unsafe_allow_html=True)
col3.markdown(f"<div class='kpi'><h3>Members</h3><h2>{members_count}</h2></div>", unsafe_allow_html=True)
col4.markdown(f"<div class='kpi'><h3>Instagram</h3><h2>{latest}</h2><p>+{growth}</p></div>", unsafe_allow_html=True)

# -------------------------
# 🔹 SOCIAL TREND
# -------------------------
st.subheader("📱 Social")

if 'views' in social.columns:
    fig = px.line(social, x='date', y='views')
    st.plotly_chart(fig, use_container_width=True)

# -------------------------
# 🔹 INSTAGRAM TREND
# -------------------------
if not followers_data.empty:
    fig = px.line(followers_data, x='date', y='followers')
    st.plotly_chart(fig, use_container_width=True)

# -------------------------
# 🔹 SOCIAL OVERZICHT + CONTENT ADVIES
# -------------------------
st.subheader("📱 Social posts overzicht")

df = social.copy()

# engagement
if all(col in df.columns for col in ['likes','comments','shares']):
    df['engagement'] = df['likes'] + df['comments'] + df['shares']
else:
    df['engagement'] = 0

# filters
col1, col2 = st.columns(2)

if 'platform' in df.columns:
    platform = col1.selectbox("Platform", ["Alles"] + df['platform'].dropna().unique().tolist())
    if platform != "Alles":
        df = df[df['platform'] == platform]

if 'type' in df.columns:
    type_filter = col2.selectbox("Type", ["Alles"] + df['type'].dropna().unique().tolist())
    if type_filter != "Alles":
        df = df[df['type'] == type_filter]

# sort
sort = st.selectbox("Sorteer op", ["Views", "Engagement", "Datum"])

if sort == "Views":
    df = df.sort_values("views", ascending=False)
elif sort == "Engagement":
    df = df.sort_values("engagement", ascending=False)
elif sort == "Datum":
    df = df.sort_values("date", ascending=False)

# top posts
st.markdown("### 🔥 Top posts")

top_posts = df.head(3)

for _, row in top_posts.iterrows():
    st.write(f"{row.get('platform','')} | {row.get('type','')} | {int(row.get('views',0))} views")

# -------------------------
# 🔥 CONTENT ADVIES
# -------------------------
st.markdown("### 🧠 Content advies")

advies = []

if 'type' in df.columns and 'views' in df.columns:
    type_perf = df.groupby('type')['views'].mean().sort_values(ascending=False)

    if not type_perf.empty:
        beste_type = type_perf.index[0]
        slechtste_type = type_perf.index[-1]

        advies.append(f"Beste contenttype: {beste_type}")
        advies.append(f"Minder presterend: {slechtste_type}")
        advies.append(f"👉 Focus meer op {beste_type}")

if 'platform' in df.columns:
    platform_perf = df.groupby('platform')['views'].mean().sort_values(ascending=False)
    if not platform_perf.empty:
        beste_platform = platform_perf.index[0]
        advies.append(f"Beste platform: {beste_platform}")

if 'engagement' in df.columns:
    if df['engagement'].mean() < 50:
        advies.append("Engagement laag → stel meer vragen of call-to-actions")

for a in advies:
    st.success(a)

# -------------------------
# 🔹 TABEL
# -------------------------
st.markdown("### 📊 Alle posts")

cols = ['date','platform','type','views','likes','comments','shares','engagement']
cols = [c for c in cols if c in df.columns]

st.dataframe(df[cols], use_container_width=True)
