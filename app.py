# app_yandex_map.py
import json
import pandas as pd
import streamlit as st
from datetime import datetime
from streamlit.components.v1 import html as st_html

st.set_page_config(page_title="Интерактивная карта (Яндекс)", layout="wide")
st.title("🗺️ Интерактивная карта по зонам, дням и месяцам (Яндекс.Карты)")

@st.cache_data
def load_data():
    df = pd.read_excel("data/Сводка_с_зонами.xlsx")
    df["Дата документа"] = pd.to_datetime(df["Дата документа"])
    MONTHS_RU = {
        1:"Январь",2:"Февраль",3:"Март",4:"Апрель",5:"Май",6:"Июнь",
        7:"Июль",8:"Август",9:"Сентябрь",10:"Октябрь",11:"Ноябрь",12:"Декабрь"
    }
    df["Месяц"] = df["Дата документа"].dt.month.map(MONTHS_RU)
    return df

df = load_data()

# --- ФИЛЬТРЫ ---
col1, col2, col3, col4 = st.columns([3, 3, 2, 2])
with col1:
    all_days = ["Все дни"] + sorted(df["День недели"].dropna().unique())
    selected_day = st.selectbox("📅 День недели:", all_days)
with col2:
    all_zones = ["Все зоны"] + sorted(df["Зона"].dropna().unique())
    selected_zone = st.selectbox("📍 Зона:", all_zones)
with col3:
    all_months = ["Все месяцы"] + sorted(df["Месяц"].dropna().unique())
    selected_month = st.selectbox("📆 Месяц:", all_months)
with col4:
    use_clusters = st.toggle("🧲 Кластеризация", value=True)

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

# --- КАРТА ЯНДЕКС ---
if filtered_df.empty:
    st.warning("Нет данных по выбранным фильтрам.")
else:
    center_lat = float(filtered_df["lat"].mean())
    center_lon = float(filtered_df["lon"].mean())

    points = []
    for _, row in filtered_df.iterrows():
        tooltip = f"🧾 {row['Холдинг, контрагент']}<br>📅 {row['Месяц']} | {row['День недели']}"
        popup = f"""
        <b>Документ:</b> {row['Номер документа']}<br>
        <b>Дата:</b> {pd.to_datetime(row['Дата документа']).date()}<br>
        <b>Сумма с НДС:</b> {float(row['Сумма с НДС']):,.2f} ₽<br>
        <b>Группа:</b> {row['группа']}<br>
        <b>Холдинг:</b> {row['Холдинг, контрагент']}<br>
        <b>Зона:</b> {row['Зона']}
        """
        points.append({
            "lat": float(row["lat"]),
            "lon": float(row["lon"]),
            "hint": tooltip,
            "balloon": popup
        })

    st_html(f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<script src="https://api-maps.yandex.ru/2.1/?apikey=a181d434-9dec-492b-8838-73ec5df31ebb&lang=ru_RU" type="text/javascript"></script>
<style>
  html, body, #map {{ width: 100%; height: 600px; margin: 0; padding: 0; }}
</style>
</head>
<body>
<div id="map"></div>
<script>
  const CENTER = [{center_lat}, {center_lon}];
  const USE_CLUSTERS = {str(use_clusters).lower()};
  const POINTS = {json.dumps(points, ensure_ascii=False)};

  ymaps.ready(init);
  function init() {{
    const map = new ymaps.Map('map', {{
      center: CENTER,
      zoom: 7,
      controls: ['zoomControl','typeSelector','fullscreenControl']
    }});

    const geoObjects = POINTS.map(p => new ymaps.Placemark(
      [p.lat, p.lon],
      {{ hintContent: p.hint, balloonContent: p.balloon }},
      {{ preset: 'islands#blueIcon' }}
    ));

    if (USE_CLUSTERS) {{
      const clusterer = new ymaps.Clusterer({{
        preset: 'islands#invertedBlueClusterIcons',
        groupByCoordinates: false,
        clusterDisableClickZoom: false,
        clusterOpenBalloonOnClick: true
      }});
      clusterer.add(geoObjects);
      map.geoObjects.add(clusterer);
      if (geoObjects.length) map.setBounds(clusterer.getBounds(), {{checkZoomRange:true, zoomMargin:50}});
    }} else {{
      const collection = new ymaps.GeoObjectCollection();
      geoObjects.forEach(go => collection.add(go));
      map.geoObjects.add(collection);
      if (geoObjects.length) map.setBounds(collection.getBounds(), {{checkZoomRange:true, zoomMargin:50}});
    }}
  }}
</script>
</body>
</html>
    """, height=620)

    # --- ИТОГИ ---
    st.markdown("---")
    st.subheader("📊 Итоги по фильтру:")
    total_docs = len(filtered_df)
    total_sum = float(filtered_df["Сумма с НДС"].sum())
    st.info(f"**Всего документов:** {total_docs}  \n**Сумма с НДС:** {total_sum:,.2f} ₽")

    # --- ТАБЛИЦА ---
    st.subheader("📋 Отфильтрованные данные")
    sorted_df = filtered_df.sort_values(by="Сумма с НДС", ascending=False)
    st.dataframe(sorted_df, use_container_width=True)
