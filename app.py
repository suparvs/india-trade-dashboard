import streamlit as st
import pandas as pd
import plotly.express as px
import pycountry

st.set_page_config(page_title="India Trade Dashboard", layout="wide")

# =========================
# COUNTRY CODE FUNCTION
# =========================
def get_country_code(name):
    try:
        return pycountry.countries.lookup(name).alpha_3
    except:
        return None

# =========================
# LOAD DATA
# =========================
@st.cache_data
def load_data():
    exports = pd.read_excel("India Export Data.xlsx")
    imports = pd.read_excel("India Import Data.xlsx")

    exports["Partner Name"] = exports["Partner Name"].str.strip()
    imports["Partner Name"] = imports["Partner Name"].str.strip()

    year_columns = exports.columns[5:]
    return exports, imports, year_columns

exports, imports, year_columns = load_data()
years = sorted([int(y) for y in year_columns])

# =========================
# SIDEBAR
# =========================
st.sidebar.title("🔍 Filters")

countries = sorted(exports["Partner Name"].dropna().unique())

selected_countries = st.sidebar.multiselect(
    "🌍 Select Countries",
    countries,
    default=["World"]
)

year_range = st.sidebar.slider(
    "📅 Year Range",
    years[0],
    years[-1],
    (2000, 2021)
)

# =========================
# DATA PREP
# =========================
all_data = []

for country in selected_countries:
    exp = exports[exports["Partner Name"].str.lower() == country.lower()]
    imp = imports[imports["Partner Name"].str.lower() == country.lower()]

    if exp.empty or imp.empty:
        continue

    exports_values = exp.iloc[0][year_columns].values / 1_000_000
    imports_values = imp.iloc[0][year_columns].values / 1_000_000

    temp_df = pd.DataFrame({
        "Year": years,
        "Exports": exports_values,
        "Imports": imports_values
    })

    temp_df["Trade Balance"] = temp_df["Exports"] - temp_df["Imports"]
    temp_df["Country"] = country

    all_data.append(temp_df)

df = pd.concat(all_data)

# Filter by year
df = df[(df["Year"] >= year_range[0]) & (df["Year"] <= year_range[1])]

# =========================
# HEADER
# =========================
st.markdown("# 📊 India Trade Dashboard")
st.markdown("### Analyze exports, imports, and global trade patterns")

# =========================
# TABS
# =========================
tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📈 Insights", "📋 Data"])

# =========================
# TAB 1: DASHBOARD
# =========================
with tab1:

    # KPIs
    world_df = df[df["Country"] == "World"]

    if not world_df.empty:
        col1, col2, col3 = st.columns(3)

        col1.metric("💰 Exports", f"{world_df['Exports'].sum():,.2f} B$")
        col2.metric("📥 Imports", f"{world_df['Imports'].sum():,.2f} B$")
        col3.metric("⚖️ Balance", f"{world_df['Trade Balance'].sum():,.2f} B$")

    st.markdown("---")

    # 📈 Trade Trend
    fig = px.line(
        df,
        x="Year",
        y=["Exports", "Imports"],
        color="Country",
        title="Exports vs Imports",
        template="plotly_dark"
    )
    st.plotly_chart(fig, use_container_width=True, key="trend")

    # 📉 Trade Balance
    fig2 = px.line(
        df,
        x="Year",
        y="Trade Balance",
        color="Country",
        title="Trade Balance Trend",
        template="plotly_dark"
    )
    fig2.add_hline(y=0, line_dash="dash", line_color="white")
    st.plotly_chart(fig2, use_container_width=True, key="balance")

    # 📊 Growth
    df["Export Growth %"] = df.groupby("Country")["Exports"].pct_change() * 100
    df["Import Growth %"] = df.groupby("Country")["Imports"].pct_change() * 100

    fig3 = px.line(
        df,
        x="Year",
        y=["Export Growth %", "Import Growth %"],
        color="Country",
        title="Growth Rate",
        template="plotly_dark"
    )
    st.plotly_chart(fig3, use_container_width=True, key="growth")

    # 🌍 Top Partners
    latest_year = years[-1]

    top_exports = exports[["Partner Name", latest_year]].sort_values(
        by=latest_year, ascending=False
    ).head(10)

    fig4 = px.bar(
        top_exports,
        x="Partner Name",
        y=latest_year,
        title=f"Top Export Partners ({latest_year})",
        template="plotly_dark"
    )
    st.plotly_chart(fig4, use_container_width=True, key="top")

    # 🌍 MAP VISUALIZATION
    st.subheader("🌍 Global Export Distribution")

    map_df = exports[["Partner Name", latest_year]].copy()
    map_df.columns = ["Country", "Exports"]

    map_df["Exports"] = map_df["Exports"] / 1_000_000

    # Remove "World"
    map_df = map_df[map_df["Country"] != "World"]

    map_df["iso_alpha"] = map_df["Country"].apply(get_country_code)
    map_df = map_df.dropna()

    fig_map = px.choropleth(
        map_df,
        locations="iso_alpha",
        color="Exports",
        hover_name="Country",
        color_continuous_scale="Viridis",
        title=f"Global Export Distribution ({latest_year})"
    )

    st.plotly_chart(fig_map, use_container_width=True, key="map")

# =========================
# TAB 2: INSIGHTS
# =========================
with tab2:
    st.subheader("🔍 Key Insights")

    st.write("• Trade deficit occurs when imports exceed exports")
    st.write("• Growth trends indicate economic expansion or slowdown")
    st.write("• Trade balance helps evaluate national economic health")
    st.write("• Geographic patterns reveal major trade partners")

# =========================
# TAB 3: DATA
# =========================
with tab3:
    st.dataframe(df, use_container_width=True)