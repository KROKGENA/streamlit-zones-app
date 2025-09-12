# app_yandex_map.py
import json
import re
import pandas as pd
import streamlit as st
from collections import defaultdict
from streamlit.components.v1 import html as st_html

st.set_page_config(page_title="Интерактивная карта (Яндекс)", layout="wide")
st.title("🗺️ Интерактивная карта по зонам, дням и месяцам (Яндекс.Карты)")

# ---- настройки столбцов/путей ----
EXCEL_PATH = "../data/Сводка_с_зонами.xlsx"   # пусть поменян
WEIGHT_SRC_COL = "Вес, кг"                 # как в вашей таблице
WEIGHT_STD_COL = "Вес_кг"                  # нормализованный float

def to_float(val):
    if pd.isna(val):
        return None
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).replace("\u00a0"," ").replace(" ","")
    s = s.replace(",", ".")
    s = re.sub(r"[^0-9\.\-]", "", s)
    try:
        return float(s) if s not in ("", ".", "-") else None
    except:
        return None

@st.cache_data
def load_data():
    df = pd.read_excel(EXCEL_PATH)
    df["Дата документа"] = pd.to_datetime(df["Дата документа"])
    MONTHS_RU = {1:"Январь",2:"Февраль",3:"Март",4:"Апрель",5:"Май",6:"Июнь",
                 7:"Июль",8:"Август",9:"Сентябрь",10:"Октябрь",11:"Ноябрь",12:"Декабрь"}
    df["Месяц"] = df["Дата документа"].dt.month.map(MONTHS_RU)
    # нормализуем вес в float
    if WEIGHT_SRC_COL in df.columns:
        df[WEIGHT_STD_COL] = df[WEIGHT_SRC_COL].map(to_float)
    else:
        df[WEIGHT_STD_COL] = pd.NA
    return df

df = load_data()

# --- ФИЛЬТРЫ ---
col1, col2, col3, col4, col5 = st.columns([3, 3, 2, 2, 2])
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
with col5:
    max_weight = st.number_input(
        "⚖️ Заказы менее, кг:",
        min_value=0.0, step=0.1, value=0.0,
        help="Показывать только документы с весом меньше указанного. 0 — без фильтра."
    )

st.markdown("---")

# --- ФИЛЬТРАЦИЯ ---
filtered_df = df.copy()
if selected_day != "Все дни":
    filtered_df = filtered_df[filtered_df["День недели"] == selected_day]
if selected_zone != "Все зоны":
    filtered_df = filtered_df[filtered_df["Зона"] == selected_zone]
if selected_month != "Все месяцы":
    filtered_df = filtered_df[filtered_df["Месяц"] == selected_month]
if max_weight and max_weight > 0:
    filtered_df = filtered_df[
        filtered_df[WEIGHT_STD_COL].notna() & (filtered_df[WEIGHT_STD_COL] < float(max_weight))
    ]

# --- КАРТА ЯНДЕКС ---
if filtered_df.empty:
    st.warning("Нет данных по выбранным фильтрам.")
else:
    center_lat = float(filtered_df["lat"].mean())
    center_lon = float(filtered_df["lon"].mean())

    # группируем по точным координатам => один маркер = одна координата
    groups = defaultdict(list)
    for _, r in filtered_df.iterrows():
        groups[(float(r["lat"]), float(r["lon"]))].append(r)

    points = []
    for (lat, lon), rows in groups.items():
        rows = sorted(rows, key=lambda x: pd.to_datetime(x["Дата документа"]), reverse=True)

        if len(rows) == 1:
            r = rows[0]
            wtxt = f"{float(r[WEIGHT_STD_COL]):,.2f} кг" if pd.notna(r[WEIGHT_STD_COL]) else "—"
            hint = f"🧾 {r['Холдинг, контрагент']}<br>📅 {r['Месяц']} | {r['День недели']}"
            balloon = f"""
                <b>Документ:</b> {r['Номер документа']}<br>
                <b>Дата:</b> {pd.to_datetime(r['Дата документа']).date()}<br>
                <b>Сумма с НДС:</b> {float(r['Сумма с НДС']):,.2f} ₽<br>
                <b>Вес:</b> {wtxt}<br>
                <b>Группа:</b> {r['группа']}<br>
                <b>Холдинг:</b> {r['Холдинг, контрагент']}<br>
                <b>Зона:</b> {r['Зона']}
            """
        else:
            weights = [float(x[WEIGHT_STD_COL]) for x in rows if pd.notna(x[WEIGHT_STD_COL])]
            avg_w = (sum(weights) / len(weights)) if weights else None
            avg_w_txt = f"{avg_w:,.2f} кг" if avg_w is not None else "—"
            hint = f"📍 Повторные визиты: {len(rows)} (ср. вес: {avg_w_txt})"

            rows_html = []
            for r in rows:
                wtxt = f"{float(r[WEIGHT_STD_COL]):,.2f} кг" if pd.notna(r[WEIGHT_STD_COL]) else "—"
                rows_html.append(f"""
                    <tr>
                      <td>{pd.to_datetime(r['Дата документа']).date()}</td>
                      <td>{r['Номер документа']}</td>
                      <td style="text-align:right">{float(r['Сумма с НДС']):,.2f} ₽</td>
                      <td style="text-align:right">{wtxt}</td>
                      <td>{r['группа']}</td>
                      <td>{r['Холдинг, контрагент']}</td>
                      <td>{r['Зона']}</td>
                    </tr>
                """)
            balloon = f"""
                <div style="font-weight:600;margin-bottom:6px">
                  Визиты в эту точку: {len(rows)} | Средний вес: {avg_w_txt}
                </div>
                <div style="max-height:260px;overflow:auto;border:1px solid #eee;border-radius:8px">
                  <table style="border-collapse:collapse;width:100%;font-size:13px">
                    <thead>
                      <tr style="background:#f7f7f7">
                        <th style="text-align:left;padding:6px 8px">Дата</th>
                        <th style="text-align:left;padding:6px 8px">Документ</th>
                        <th style="text-align:right;padding:6px 8px">Сумма</th>
                        <th style="text-align:right;padding:6px 8px">Вес</th>
                        <th style="text-align:left;padding:6px 8px">Группа</th>
                        <th style="text-align:left;padding:6px 8px">Холдинг</th>
                        <th style="text-align:left;padding:6px 8px">Зона</th>
                      </tr>
                    </thead>
                    <tbody>
                      {''.join(rows_html)}
                    </tbody>
                  </table>
                </div>
            """

        points.append({"lat": lat, "lon": lon, "hint": hint, "balloon": balloon})

    st_html(f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<script src="https://api-maps.yandex.ru/2.1/?apikey=a181d434-9dec-492b-8838-73ec5df31ebb&lang=ru_RU"></script>
<style>html,body,#map{{width:100%;height:600px;margin:0;padding:0;}}</style>
</head>
<body>
<div id="map"></div>
<script>
  const CENTER = [{filtered_df["lat"].mean()}, {filtered_df["lon"].mean()}];
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
        clusterOpenBalloonOnClick: true,
        clusterBalloonContentLayout: 'cluster#balloonCarousel'
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
    if filtered_df[WEIGHT_STD_COL].notna().any():
        total_weight = float(filtered_df[WEIGHT_STD_COL].sum(skipna=True))
        avg_weight = float(filtered_df[WEIGHT_STD_COL].mean(skipna=True))
        st.info(
            f"**Всего документов:** {total_docs}  \n"
            f"**Сумма с НДС:** {total_sum:,.2f} ₽  \n"
            f"**Суммарный вес:** {total_weight:,.2f} кг | **Средний вес:** {avg_weight:,.2f} кг"
        )
    else:
        st.info(f"**Всего документов:** {total_docs}  \n**Сумма с НДС:** {total_sum:,.2f} ₽")

    # --- ТАБЛИЦА ---
    st.subheader("📋 Отфильтрованные данные")
    cols = list(filtered_df.columns)
    if WEIGHT_STD_COL in cols:
        # показываем «Вес, кг» (оригинал) и нормализованный столбец
        if WEIGHT_SRC_COL in cols:
            display_cols = cols  # уже есть оба
        else:
            display_cols = cols + [WEIGHT_STD_COL]
    else:
        display_cols = cols
    sorted_df = filtered_df.sort_values(by="Сумма с НДС", ascending=False)
    st.dataframe(sorted_df[display_cols], use_container_width=True)
