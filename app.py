import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

st.set_page_config(page_title="Интерактивная карта", layout="wide")
st.title("🗺️ Интерактивная карта по зонам и дням")
tab1, tab2 = st.tabs(["📍 Карта", "📈 Динамика"])
@st.cache_data
def load_data():
    df = pd.read_excel("data/Сводка_с_зонами.xlsx")
    df["Месяц"] = df["Дата документа"].dt.strftime("%B")
    return df

df = load_data()

# --- ФИЛЬТРЫ ---
col1, col2, col3 = st.columns([3, 3, 2])

with col1:
    selected_day = st.selectbox("📅 День недели:", sorted(df["День недели"].unique()))

with col2:
    selected_zone = st.selectbox("📍 Зона:", sorted(df["Зона"].unique()))

with col3:
    use_clusters = st.toggle("🧲 Кластеризация", value=True)

# --- ФИЛЬТРАЦИЯ ---
filtered_df = df[(df["День недели"] == selected_day) & (df["Зона"] == selected_zone)]

# --- КАРТА ---
if filtered_df.empty:
    st.warning("Нет данных по выбранным фильтрам.")
else:
    center = [filtered_df["lat"].mean(), filtered_df["lon"].mean()]
    m = folium.Map(location=center, zoom_start=7)

    if use_clusters:
        marker_group = MarkerCluster().add_to(m)
    else:
        marker_group = m

    for _, row in filtered_df.iterrows():
        tooltip = f"""🧾 {row['Холдинг, контрагент']}  
📅 {row['Месяц']} | {row['День недели']}"""

        popup = f"""
        <b>Документ:</b> {row['Номер документа']}<br>
        <b>Дата:</b> {row['Дата документа'].date()}<br>
        <b>Сумма с НДС:</b> {row['Сумма с НДС']:,} ₽<br>
        <b>Группа:</b> {row['группа']}<br>
        <b>Холдинг:</b> {row['Холдинг, контрагент']}<br>
        <b>Зона:</b> {row['Зона']}
        """

        folium.Marker(
            location=[row["lat"], row["lon"]],
            tooltip=tooltip,
            popup=popup
        ).add_to(marker_group)

    st_folium(m, width=1000, height=600)

    # --- ТАБЛИЦА ---
    st.subheader("📋 Отфильтрованные данные")
    st.dataframe(filtered_df)
