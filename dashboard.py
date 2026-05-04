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
.block-container{ padding-top:2rem; }

.kpi {
    background:white;
    padding:22px;
    border-radius:22px;
    text-align:center;
    box-shadow:0 10px 25px rgba(0,0,0,0.05);
    border-top:4px solid #8cbe26;
}

h1,h2,h3{ color:#084422; }
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
if 'date' in social.columns:
    social['date'] = pd.to_datetime(social['date'], errors='coerce')

for col in ['views','likes','comments','shares','saves','followers']:
    if col in social.columns:
        social[col] = pd.to_numeric(social[col], errors='coerce')

if 'last_purchase_date' in members.columns:
    members['last_purchase_date'] = pd.to_datetime(members['last_purchase_date'], errors='coerce')

if 'created_at' in members.columns:
    members['created_at'] = pd.to_datetime(members['created_at'], errors='coerce')

# -------------------------
# 🔥 INSTAGRAM VOLGERS
# -------------------------
latest = 0
growth = 0
followers_data = pd.DataFrame()

if not social.empty and 'followers' in social.columns:

    df = social.copy()

    if 'platform' in df.columns:
        df['platform'] = df['platform'].astype(str).str.lower()
        df = df[df['platform'] == 'instagram']

    df = df.dropna(subset=['followers', 'date'])
    df = df.sort_values('date')

    # 🔥 PER DAG LAATSTE WAARDE
    df = df.groupby(df['date'].dt.date).tail(1)

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
# 🔹 SOCIAL OVERZICHT
# -------------------------
st.subheader("📱 Social posts overzicht")

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
    type_filter = col2.selectbox("Type", ["Alles"] + df['type'].dropna().unique().tolist())
    if type_filter != "Alles":
        df = df[df['type'] == type_filter]

sort = st.selectbox("Sorteer op", ["Views", "Engagement", "Datum"])

if sort == "Views":
    df = df.sort_values("views", ascending=False)
elif sort == "Engagement":
    df = df.sort_values("engagement", ascending=False)
elif sort == "Datum":
    df = df.sort_values("date", ascending=False)

st.markdown("### 🔥 Top posts")
for _, row in df.head(3).iterrows():
    st.write(f"{row.get('platform','')} | {row.get('type','')} | {int(row.get('views',0))} views")

# -------------------------
# 🔹 CONTENT ADVIES
# -------------------------
st.markdown("### 🧠 Content advies")

advies = []

if 'type' in df.columns and 'views' in df.columns:
    perf = df.groupby('type')['views'].mean().sort_values(ascending=False)
    if not perf.empty:
        advies.append(f"Focus op {perf.index[0]} content")

if df['engagement'].mean() < 50:
    advies.append("Engagement laag → gebruik meer call-to-actions")

for a in advies:
    st.success(a)

# -------------------------
# 🔥 MEMBERS ANALYSE
# -------------------------
st.subheader("👥 Members analyse")

if not members.empty:

    m = members.copy()

    if 'last_purchase_date' in m.columns:
        m['date'] = m['last_purchase_date']
    elif 'created_at' in m.columns:
        m['date'] = m['created_at']

    m = m.dropna(subset=['date'])

    m['week'] = m['date'].dt.to_period('W').apply(lambda r: r.start_time)

    weekly = m.groupby('week').size().reset_index(name='new_members')

    fig = px.line(weekly, x='week', y='new_members')
    st.plotly_chart(fig, use_container_width=True)

    weekly['total'] = weekly['new_members'].cumsum()

    fig2 = px.line(weekly, x='week', y='total')
    st.plotly_chart(fig2, use_container_width=True)

    if 'total_spent' in m.columns:
        m['total_spent'] = pd.to_numeric(m['total_spent'], errors='coerce')
        st.metric("Gemiddelde besteding", f"€ {m['total_spent'].mean():.2f}")
