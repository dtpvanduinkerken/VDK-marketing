import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(layout="wide")

# -------------------------
# 🔹 ENTERPRISE STYLING
# -------------------------
st.markdown("""
<style>
body {background:#f4f6f9;}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #084422 0%, #0b5a2f 100%);
    color:white;
}

.kpi {
    background:white;
    padding:18px;
    border-radius:16px;
    box-shadow:0 6px 20px rgba(0,0,0,0.05);
}

.panel {
    background:white;
    padding:20px;
    border-radius:16px;
    box-shadow:0 6px 20px rgba(0,0,0,0.05);
    margin-bottom:20px;
}

h1,h2,h3 {color:#084422;}
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
# 🔹 MEMBERS GROEI (FIX)
# -------------------------
members_growth = pd.DataFrame()

if not members.empty:
    df = members.copy()
    df[['year','week']] = df['created_at'].astype(str).str.extract(r'(\d{4}).*?(\d+)')
    df = df.dropna()

    members_growth = df.groupby(['year','week']).size().reset_index(name='new_members')

    members_growth['sort'] = pd.to_datetime(
        members_growth['year'].astype(str) + members_growth['week'].astype(str) + '1',
        format='%G%V%u'
    )

    members_growth = members_growth.sort_values('sort')

# -------------------------
# 🔹 KPI DATA
# -------------------------
reach = int(social['views'].sum()) if 'views' in social.columns else 0
members_total = len(members)
followers = int(social['followers'].max()) if 'followers' in social.columns else 0

open_rate = 0
if newsletter['sent'].sum() > 0:
    open_rate = (newsletter['opens'].sum() / newsletter['sent'].sum()) * 100

# trend members
member_delta = 0
if len(members_growth) > 1:
    member_delta = members_growth.iloc[-1]['new_members'] - members_growth.iloc[-2]['new_members']

# -------------------------
# 🔥 DASHBOARD
# -------------------------
if page == "Dashboard":

    st.title("📊 Marketing Dashboard")

    # -------------------------
    # 🔹 KPI ROW MET TREND
    # -------------------------
    col1, col2, col3, col4 = st.columns(4)

    def kpi_card(title, value, delta, data=None):
        st.markdown("<div class='kpi'>", unsafe_allow_html=True)
        st.markdown(f"<small>{title}</small>", unsafe_allow_html=True)
        st.markdown(f"<h2>{value}</h2>", unsafe_allow_html=True)

        if delta is not None:
            color = "green" if delta >= 0 else "red"
            st.markdown(f"<span style='color:{color}'>{delta:+}</span>", unsafe_allow_html=True)

        if data is not None and len(data) > 1:
            fig = go.Figure()
            fig.add_trace(go.Scatter(y=data, mode='lines'))
            fig.update_layout(height=60, margin=dict(l=0,r=0,t=0,b=0))
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)

    with col1:
        kpi_card("Bereik", f"{reach:,}", None)

    with col2:
        kpi_card("Members", members_total, member_delta, members_growth['new_members'] if not members_growth.empty else None)

    with col3:
        kpi_card("Open rate", f"{open_rate:.1f}%", None)

    with col4:
        kpi_card("Instagram", followers, None)

    # -------------------------
    # 🔹 MAIN GRID
    # -------------------------
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.subheader("Members groei")
        if not members_growth.empty:
            fig = px.line(members_growth, x='sort', y='new_members')
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
    # 🔹 BOTTOM GRID
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
        st.subheader("Top post")
        if not social.empty:
            top = social.sort_values("views", ascending=False).head(1)
            st.write(top[['platform','type','views']])
        st.markdown("</div>", unsafe_allow_html=True)
