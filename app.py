import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests

# 앱 기본 설정
st.set_page_config(page_title="오점뭐?!", page_icon="🍜")

st.title("🍜 오점뭐?!")
st.caption("'오늘은 뭐 먹지?' 직장인 최대 고민 해결✨")
st.divider()

# --- 1. 상세 날씨 정보 가져오기 ---
@st.cache_data(ttl=600)
def get_detailed_weather():
    latitude = 37.483
    longitude = 126.897
    url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,wind_speed_10m,weather_code"
    try:
        data = requests.get(url).json()['current']
        temp = data['temperature_2m']
        feels_like = data['apparent_temperature']
        condition_code = data['weather_code']
        
        # 날씨 상태 정의
        is_rainy = condition_code in [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82, 95, 96, 99]
        is_snowy = condition_code in [71, 73, 75, 77, 85, 86]
        
        status = "맑음"
        if is_rainy: status = "비"
        elif is_snowy: status = "눈"
        elif condition_code in [1, 2, 3, 45, 48]: status = "흐림"
        
        return temp, feels_like, status
    except: return 20.0, 20.0, "맑음"

temp, feels_like, condition = get_detailed_weather()

# --- 2. 상단 대시보드 및 규칙 안내 ---
st.subheader("현재 정보")
c1, c2 = st.columns(2)
with c1:
    st.info("📍 위치: 구로 TP타워")
with c2:
    st.success(f"🌡️ {temp}℃ ({condition})")

st.info(f"""
**🤖 AI의 점심 추천 가이드 (직장인 문화 규칙 반영)**
* **비/눈:** 국물, 전, 칼국수, 수제비 우선 추천
* **더위(25℃↑):** 냉면, 소바, 콩국수, 샐러드 우선 추천
* **추위(5℃↓):** 찌개, 고기, 뜨거운 국물 우선 추천
""")

# --- 3. 데이터 연결 및 전처리 ---
url = "https://docs.google.com/spreadsheets/d/1PP1HV-NWs3c_QjwuIVBu4H5gLl_A78JbPBLcTrVaz4A/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(spreadsheet=url).dropna(how='all', axis=1).fillna("")

# 열 이름 매칭 (예약, 메뉴, 특징 등)
col_map = {col: col.replace(" ", "") for col in df.columns}
df.rename(columns=col_map, inplace=True)

# --- 4. 🎲 랜덤 추천 로직 (문화 규칙 반영) ---
st.write("---")
if st.button("오늘 날씨에 딱 맞는 메뉴 랜덤 추천!", use_container_width=True):
    # 규칙 기반 필터링 키워드 설정
    keywords = []
    if condition in ["비", "눈"]: keywords = ["국물", "전", "칼국수", "수제비", "짬뽕", "우동"]
    elif temp >= 25: keywords = ["냉면", "소바", "국수", "샐러드", "시원"]
    elif temp <= 5: keywords = ["찌개", "탕", "국밥", "샤브", "고기"]
    
    # 키워드에 맞는 식당 찾기
    if keywords:
        pattern = '|'.join(keywords)
        filtered_df = df[df['메뉴'].str.contains(pattern) | df['특징'].str.contains(pattern)]
    else:
        filtered_df = df
        
    if filtered_df.empty: filtered_df = df # 맞는게 없으면 전체에서
    
    choice = filtered_df.sample(n=1).iloc[0]
    st.balloons()
    st.success(f"🎯 날씨와 규칙을 고려한 추천: **[{choice['상호명']}]**")
    st.write(f"🍴 **메뉴:** {choice['메뉴']} | 💰 {choice['가격']}원 | 🗓️ 예약: {choice['예약']}")
    st.caption(f"💬 {choice['특징']}")

# --- 5. 💬 똑똑한 챗봇 (예약 + 키워드 + 규칙) ---
st.write("")
if prompt := st.chat_input("예: 예약가능한 부대찌개, 비오는데 뭐먹지?, 돈까스"):
    with st.chat_message("user"): st.write(prompt)
    with st.chat_message("assistant"):
        res = df.copy()
        
        # 1. 예약 필터링
        if "예약" in prompt:
            res = res[res['예약'].astype(str).str.upper().str.contains("O", na=False)]
        
        # 2. 날씨/문화 규칙 필터링 (예: "비오는데", "더운데")
        if "비" in prompt or "눈" in prompt:
            res = res[res['메뉴'].str.contains("국물|전|칼|수제비") | res['특징'].str.contains("국물|전|칼|수제비")]
        elif "더워" in prompt or "덥다" in prompt:
            res = res[res['메뉴'].str.contains("냉면|소바|국수|샐러드") | res['특징'].str.contains("냉면|소바|국수|샐러드")]

        # 3. 특정 메뉴 키워드 검색
        clean_kw = prompt.replace("예약", "").replace("가능한", "").replace("추천", "").replace("해줘", "").strip()
        if clean_kw and len(clean_kw) > 1:
            res = res[res['상호명'].str.contains(clean_kw) | res['메뉴'].str.contains(clean_kw) | res['특징'].str.contains(clean_kw)]
        
        if not res.empty:
            choice = res.sample(n=1).iloc[0]
            st.write(f"조건에 맞는 식당을 {len(res)}곳 찾았습니다!")
            st.success(f"**{choice['상호명']}** ({choice['메뉴']})")
            st.write(f"📍 거리: {choice['거리']} | 🗓️ 예약: {choice['예약']}")
            if len(res) > 1:
                with st.expander("다른 후보지 보기"):
                    st.dataframe(res[['상호명', '메뉴', '가격', '예약']], hide_index=True)
        else:
            st.error("조건에 맞는 식당을 찾지 못했어요. 키워드를 바꿔보시겠어요?")

# --- 6. 사이드바 ---
with st.sidebar:
    st.header("🗂️ 맛집 DB")
    st.dataframe(df[['상호명', '메뉴', '가격']], hide_index=True, height=600)
