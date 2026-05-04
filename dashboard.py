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
members_insights = load("members_insights")
products = load("product_data")

# -------------------------
# 🔹 DATA OPSCHONEN
# -------------------------
if 'date' in social.columns:
    social['date'] = pd.to_datetime(social['date'], errors='coerce')

for col in ['views','likes','comments','shares','saves','followers']:
    if col in social.columns:
        social[col] = pd.to_numeric(social[col], errors='coerce')

if 'created_at' in members.columns:
    members['created_at'] = pd.to_datetime(members['created_at'], errors='coerce')

if 'last_purchase_date' in members_insights.columns:
    members_insights['last_purchase_date'] = pd.to_datetime(
        members_insights['last_purchase_date'], errors='coerce'
    )

if 'total_spent' in members_insights.columns:
    members_insights['total_spent'] = pd.to_numeric(
        members_insights['total_spent'], errors='coerce'
    )

# -------------------------
# 🔥 MEMBERS MERGE
# -------------------------
members_full = members.merge(
    members_insights,
    on='member_id',
    how='left'
)

# -------------------------
# 🔥 INSTAGRAM VOLGERS FIX
# -------------------------
latest = 0
growth = 0
followers_data = pd.DataFrame()

if not social.empty and 'followers' in social.columns:

    df = social.copy()

    if 'platform' in df.columns:
        df['platform'] = df['platform'].astype(str).str.lower()
        df = df[df['platform'] == 'instagram']

    df = df.dropna(subset=['followers','date'])
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
col3.markdown(f"<div class='kpi'><h3>Nieuwe members</h3><h2>{members_count}</h2></div>", unsafe_allow_html=True)
col4.markdown(f"<div class='kpi'><h3>Instagram</h3><h2>{latest}</h2><p>+{growth}</p></div>", unsafe_allow_html=True)

# -------------------------
# 🔹 MEMBERS GROEI
# -------------------------
st.subheader("👥 Members groei")

if not members.empty:

    weekly = members.groupby(
        members['created_at'].dt.to_period('W')
    ).size().reset_index(name='new_members')

    weekly['week'] = weekly['created_at'].dt.start_time

    fig = px.line(weekly, x='week', y='new_members')
    st.plotly_chart(fig, use_container_width=True)

# -------------------------
# 🔥 MEMBERS INSIGHTS
# -------------------------
st.subheader("👥 Members waarde & gedrag")

if not members_full.empty:

    if 'total_spent' in members_full.columns:
        avg_spent = members_full['total_spent'].mean()
        st.metric("Gemiddelde besteding", f"€ {avg_spent:.2f}")

    if 'last_purchase_date' in members_full.columns:
        recent = members_full[
            members_full['last_purchase_date'] >= (pd.Timestamp.today() - pd.Timedelta(days=90))
        ]

        pct = (len(recent) / len(members_full)) * 100
        st.metric("Actieve members", f"{pct:.1f}%")

    # segmentatie
    members_full['segment'] = "Overig"

    members_full.loc[members_full['total_spent'] > 200, 'segment'] = "VIP"
    members_full.loc[members_full['total_spent'] < 50, 'segment'] = "Laag waarde"

    st.markdown("### 🧠 Segmentatie")
    st.dataframe(members_full['segment'].value_counts())

# -------------------------
# 🔹 SOCIAL OVERZICHT
# -------------------------
st.subheader("📱 Social posts")

df = social.copy()

if all(col in df.columns for col in ['likes','comments','shares']):
    df['engagement'] = df['likes'] + df['comments'] + df['shares']
else:
    df['engagement'] = 0

st.dataframe(df.head(10))

# -------------------------
# 🔹 CONTENT ADVIES
# -------------------------
st.subheader("🧠 Content advies")

if 'type' in df.columns and 'views' in df.columns:
    perf = df.groupby('type')['views'].mean().sort_values(ascending=False)
    if not perf.empty:
        st.success(f"Focus op {perf.index[0]} content")

# -------------------------
# 🔹 PRODUCTEN
# -------------------------
st.subheader("📦 Product voortgang")

if not grouped.empty:
    fig = px.bar(grouped, x='brand', y='nog_te_doen')
    st.plotly_chart(fig, use_container_width=True)
