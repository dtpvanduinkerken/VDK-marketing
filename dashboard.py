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

for col in ['views','likes','comments','shares','followers']:
    if col in social.columns:
        social[col] = pd.to_numeric(social[col], errors='coerce')

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
members_full = members.merge(members_insights, on='member_id', how='left')

# -------------------------
# 🔥 INSTAGRAM VOLGERS
# -------------------------
latest = 0
growth = 0
followers_data = pd.DataFrame()

if not social.empty and 'followers' in social.columns:

    df = social.copy()

    if 'platform' in df.columns:
        df = df[df['platform'].astype(str).str.lower() == 'instagram']

    df = df.dropna(subset=['followers','date'])
    df = df.sort_values('date')
    df = df.groupby(df['date'].dt.date).tail(1)

    if not df.empty:
        followers_data = df
        latest = int(df.iloc[-1]['followers'])

        if len(df) > 1:
            growth = latest - int(df.iloc[-2]['followers'])

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

col1.markdown(f"<div class='kpi'><h3>Bereik</h3><h2>{reach:,}</h2></div>", unsafe_allow_html=True)
col2.markdown(f"<div class='kpi'><h3>Open rate</h3><h2>{open_rate:.1f}%</h2></div>", unsafe_allow_html=True)
col3.markdown(f"<div class='kpi'><h3>Nieuwe members</h3><h2>{members_count}</h2></div>", unsafe_allow_html=True)
col4.markdown(f"<div class='kpi'><h3>Instagram</h3><h2>{latest}</h2><p>+{growth}</p></div>", unsafe_allow_html=True)

# -------------------------
# 🔥 MEMBERS GROEI (VERBETERD)
# -------------------------
st.subheader("👥 Members groei")

if not members.empty and 'created_at' in members.columns:

    df = members.copy()

    df[['year', 'week']] = df['created_at'].astype(str).str.extract(r'(\d{4}).*?(\d+)')

    df['year'] = pd.to_numeric(df['year'], errors='coerce')
    df['week'] = pd.to_numeric(df['week'], errors='coerce')

    df = df.dropna(subset=['year','week'])

    weekly = df.groupby(['year','week']).size().reset_index(name='new_members')

    weekly['label'] = weekly['year'].astype(int).astype(str) + " - week " + weekly['week'].astype(int).astype(str)

    weekly['sort'] = pd.to_datetime(
        weekly['year'].astype(str) + weekly['week'].astype(str) + '1',
        format='%G%V%u',
        errors='coerce'
    )

    weekly = weekly.sort_values('sort')

    # KPI boven grafiek
    if len(weekly) > 1:
        last = weekly.iloc[-1]['new_members']
        prev = weekly.iloc[-2]['new_members']
        delta = last - prev

        colA, colB = st.columns(2)
        colA.metric("Nieuwe members deze week", int(last), delta=int(delta))
        colB.metric("Totale members", int(weekly['new_members'].sum()))

    fig = px.line(weekly, x='label', y='new_members', markers=True)
    st.plotly_chart(fig, use_container_width=True)

    weekly['cumulative'] = weekly['new_members'].cumsum()

    fig2 = px.line(weekly, x='label', y='cumulative', title="Totale groei", markers=True)
    st.plotly_chart(fig2, use_container_width=True)

# -------------------------
# 🔹 MEMBERS INSIGHTS
# -------------------------
st.subheader("👥 Members waarde & gedrag")

if not members_full.empty:

    if 'total_spent' in members_full.columns:
        st.metric("Gemiddelde besteding", f"€ {members_full['total_spent'].mean():.2f}")

    if 'last_purchase_date' in members_full.columns:
        recent = members_full[
            members_full['last_purchase_date'] >= (pd.Timestamp.today() - pd.Timedelta(days=90))
        ]
        pct = (len(recent) / len(members_full)) * 100
        st.metric("Actieve members", f"{pct:.1f}%")

    members_full['segment'] = "Overig"
    members_full.loc[members_full['total_spent'] > 200, 'segment'] = "VIP"
    members_full.loc[members_full['total_spent'] < 50, 'segment'] = "Laag waarde"

    st.dataframe(members_full['segment'].value_counts())

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

st.dataframe(df[['date','platform','type','views','likes','comments','shares','engagement']], use_container_width=True)

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

if not products.empty and 'brand' in products.columns:

    if 'online' in products.columns:
        products['online'] = pd.to_numeric(products['online'], errors='coerce').fillna(0)

    if 'totaal_producten' in products.columns:

        grouped = products.groupby('brand').agg(
            totaal=('totaal_producten','max'),
            online=('online','sum')
        ).reset_index()

        grouped['nog_te_doen'] = grouped['totaal'] - grouped['online']

        fig = px.bar(grouped, x='brand', y='nog_te_doen')
        st.plotly_chart(fig, use_container_width=True)
