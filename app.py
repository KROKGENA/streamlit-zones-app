import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

st.set_page_config(page_title="Интерактивная карта", layout="wide")
st.title("🗺️ Интерактивная карта по зонам, дням и месяцам")

@st.cache_data
def load_data():
    df = pd.read_excel("data/Сводка_с_зонами.xlsx")
    df["Месяц"] = df["Дата документа"].dt.strftime("%B")
    return df

df = load_data()

# --- ФИЛЬТРЫ ---
col1, col2, col3, col4 = st.columns([3, 3, 2, 2])

with col1:
    all_days = ["Все дни"] + sorted(df["День недели"].unique())
    selected_day = st.selectbox("📅 День недели:", all_days)

with col2:
    all_zones = ["Все зоны"] + sorted(df["Зона"].unique())
    selected_zone = st.selectbox("📍 Зона:", all_zones)

with col3:
    all_months = ["Все месяцы"] + sorted(df["Месяц"].unique())
    selected_month = st.selectbox("📆 Месяц:", all_months)

with col4:
    use_clusters = st.toggle("🧲 Кластеризация", value=True)
    # --- ССЫЛКА НА КАРТУ МАРШРУТОВ ---
st.markdown("---")
st.subheader("🛣️ Карта маршрутов")

st.markdown(
    """
    <a href="https://krokgena.github.io/streamlit-zones-app/routes.html" target="_blank">
        <button style="
            background-color:#4CAF50;
            color:white;
            padding:10px 20px;
            border:none;
            border-radius:8px;
            font-size:16px;
            cursor:pointer;
        ">
        🚗 Открыть карту маршрутов
        </button>
    </a>
    """,
    unsafe_allow_html=True
)


# --- ФИЛЬТРАЦИЯ ---
filtered_df = df.copy()

if selected_day != "Все дни":
    filtered_df = filtered_df[filtered_df["День недели"] == selected_day]

if selected_zone != "Все зоны":
    filtered_df = filtered_df[filtered_df["Зона"] == selected_zone]

if selected_month != "Все месяцы":
    filtered_df = filtered_df[filtered_df["Месяц"] == selected_month]

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

    # --- ИТОГИ ---
    st.markdown("---")
    st.subheader("📊 Итоги по фильтру:")

    total_docs = len(filtered_df)
    total_sum = filtered_df["Сумма с НДС"].sum()

    st.info(
        f"""
        **Всего документов:** {total_docs}  
        **Сумма с НДС:** {total_sum:,.2f} ₽
        """
    )

    # --- ТАБЛИЦА ---
    st.subheader("📋 Отфильтрованные данные")

    # СОРТИРОВКА по сумме с НДС по убыванию
    sorted_df = filtered_df.sort_values(by="Сумма с НДС", ascending=False)

    st.dataframe(sorted_df)
