import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

# -------------------------
# 🔹 STYLING (ECHTE UPGRADE)
# -------------------------
st.markdown("""
<style>

/* PAGINA */
body {
    background:#f9f3e9;
}

/* SIDEBAR */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #084422 0%, #0b5a2f 100%);
    color:white;
}

/* KPI BLOK */
.kpi {
    background:white;
    padding:20px;
    border-radius:18px;
    box-shadow:0 8px 20px rgba(0,0,0,0.05);
}

/* PANEL */
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

h1,h2,h3 { color:#084422; }

</style>
""", unsafe_allow_html=True)

# -------------------------
# 🔹 SIDEBAR NAVIGATIE
# -------------------------
st.sidebar.title("VDK Dashboard")

page = st.sidebar.radio("Navigatie", [
    "Overzicht",
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

# opschonen
for col in ['views','likes','comments','shares','followers']:
    if col in social.columns:
        social[col] = pd.to_numeric(social[col], errors='coerce')

for col in ['sent','opens','clicks']:
    if col in newsletter.columns:
        newsletter[col] = pd.to_numeric(newsletter[col], errors='coerce')

# -------------------------
# 🔹 OVERZICHT PAGINA
# -------------------------
if page == "Overzicht":

    st.title("📊 Overzicht")

    reach = int(social['views'].sum()) if 'views' in social.columns else 0
    members_count = len(members)
    open_rate = (newsletter['opens'].sum() / newsletter['sent'].sum()) * 100 if newsletter['sent'].sum() > 0 else 0
    followers = int(social['followers'].max()) if 'followers' in social.columns else 0

    col1, col2, col3, col4 = st.columns(4)

    col1.markdown(f"<div class='kpi'><h3>Bereik</h3><h2>{reach:,}</h2></div>", unsafe_allow_html=True)
    col2.markdown(f"<div class='kpi'><h3>Members</h3><h2>{members_count}</h2></div>", unsafe_allow_html=True)
    col3.markdown(f"<div class='kpi'><h3>Open rate</h3><h2>{open_rate:.1f}%</h2></div>", unsafe_allow_html=True)
    col4.markdown(f"<div class='kpi'><h3>Instagram</h3><h2>{followers}</h2></div>", unsafe_allow_html=True)

    # grafieken in 2 kolommen
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.subheader("Members groei")
        if not members.empty:
            df = members.copy()
            df[['year','week']] = df['created_at'].astype(str).str.extract(r'(\d{4}).*?(\d+)')
            df = df.dropna()
            weekly = df.groupby(['year','week']).size().reset_index(name='new_members')
            weekly['label'] = weekly['year'].astype(str) + " - week " + weekly['week'].astype(str)
            fig = px.line(weekly, x='label', y='new_members')
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
# 🔹 MEMBERS PAGINA
# -------------------------
if page == "Members":

    st.title("👥 Members")

    if not members.empty:
        df = members.copy()
        df[['year','week']] = df['created_at'].astype(str).str.extract(r'(\d{4}).*?(\d+)')
        df = df.dropna()

        weekly = df.groupby(['year','week']).size().reset_index(name='new_members')
        weekly['label'] = weekly['year'].astype(str) + " - week " + weekly['week'].astype(str)

        fig = px.line(weekly, x='label', y='new_members')
        st.plotly_chart(fig, use_container_width=True)

# -------------------------
# 🔹 NIEUWSBRIEF PAGINA
# -------------------------
if page == "Nieuwsbrief":

    st.title("📧 Nieuwsbrief")

    if not newsletter.empty:
        st.dataframe(newsletter)

# -------------------------
# 🔹 SOCIAL PAGINA
# -------------------------
if page == "Social":

    st.title("📱 Social")

    df = social.copy()

    if all(col in df.columns for col in ['likes','comments','shares']):
        df['engagement'] = df['likes'] + df['comments'] + df['shares']

    df = df.sort_values("views", ascending=False)

    cols = st.columns(3)

    for i, (_, row) in enumerate(df.head(6).iterrows()):
        with cols[i % 3]:
            st.markdown(f"""
            <div class='card'>
                <b>{row.get('platform','')}</b><br>
                {row.get('type','')}<br><br>
                👁 {int(row.get('views',0)):,}<br>
                ❤️ {int(row.get('likes',0))}<br>
                💬 {int(row.get('comments',0))}<br>
            </div>
            """, unsafe_allow_html=True)

    st.dataframe(df)

# -------------------------
# 🔹 PRODUCTEN PAGINA
# -------------------------
if page == "Producten":

    st.title("📦 Producten")

    if not products.empty:
        products['online'] = pd.to_numeric(products['online'], errors='coerce')

        grouped = products.groupby('brand').agg(
            totaal=('totaal_producten','max'),
            online=('online','sum')
        ).reset_index()

        grouped['nog'] = grouped['totaal'] - grouped['online']

        fig = px.bar(grouped, x='brand', y='nog')
        st.plotly_chart(fig, use_container_width=True)
