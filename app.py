import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests

# 앱 제목 및 설정
st.set_page_config(page_title="구디 점심 대장", page_icon="🍜")
st.title("🍜 구로 TP타워 점심 대장")
st.caption("인사팀 민영님이 엄선한 구디 직장인 찐 맛집 리스트!")

# --- 실시간 구로동 날씨 가져오기 (Open-Meteo 무료 API) ---
def get_current_weather():
    # 구로디지털단지 근처 위도/경도
    url = "https://api.open-meteo.com/v1/forecast?latitude=37.483&longitude=126.897&current_weather=true"
    try:
        response = requests.get(url).json()
        temp = response['current_weather']['temperature']
        code = response['current_weather']['weathercode']
        
        # 날씨 코드 해석
        if code in [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82, 95, 96, 99]:
            condition = "비"
        elif code in [71, 73, 75, 77, 85, 86]:
            condition = "눈"
        elif code in [1, 2, 3, 45, 48]:
            condition = "흐림"
        else:
            condition = "맑음"
            
        # 시트에 있는 날씨 태그와 매칭
        if temp < 5 or condition == "눈":
            tag = "추움"
        elif condition == "비":
            tag = "비"
        elif temp > 25:
            tag = "더움"
        elif condition == "맑음":
            tag = "맑음"
        else:
            tag = "흐림"
            
        return temp, condition, tag
    except:
        return 20.0, "알수없음", "무관"

current_temp, current_condition, weather_tag = get_current_weather()

# 화면에 현재 날씨 띄우기
st.info(f"📍 실시간 구로동 날씨: **{current_condition}** ({current_temp}℃) \n\n 👉 현재 날씨인 **'{weather_tag}'** 키워드(또는 무관)가 포함된 메뉴를 찾아볼게요!")

# --- 1. 구글 시트 연결 ---
url = "https://docs.google.com/spreadsheets/d/1PP1HV-NWs3c_QjwuIVBu4H5gLl_A78JbPBLcTrVaz4A/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(spreadsheet=url)
df = df.fillna("")

# 🚨 [에러 해결 핵심] 구글 시트 헤더 강제 덮어쓰기
df.columns = ['카테고리', '상호명', '메뉴', '날씨', '거리', '특징', '가격', '지도']

# --- 2. 필터링 로직 ---
# 실시간 날씨 태그가 포함되어 있거나, '무관'인 식당만 필터링
filtered_df = df[df['날씨'].str.contains(weather_tag, na=False) | df['날씨'].str.contains("무관", na=False)]

# 혹시 조건에 맞는 식당이 하나도 없으면 '무관' 식당이라도 보여주기
if filtered_df.empty:
    filtered_df = df[df['날씨'].str.contains("무관", na=False)]

# --- 3. 추천 버튼 ---
if st.button("오늘 뭐 먹지? 랜덤 추천받기!"):
    if not filtered_df.empty:
        choice = filtered_df.sample(n=1).iloc[0]
        st.balloons()
        st.success(f"오늘의 추천 메뉴는? **[{choice['상호명']}]**의 **{choice['메뉴']}**!")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"📍 거리: {choice['거리']}")
            st.write(f"💰 가격: {choice['가격']}원")
        with col2:
            st.write(f"💬 특징: {choice['특징']}")
            if choice['지도'] != "":
                st.markdown(f"[🗺️ 네이버 지도 보기]({choice['지도']})")
    else:
        st.warning("앗, 시트에 데이터가 부족해요!")

# --- 4. 전체 리스트 보기 ---
with st.expander("전체 맛집 리스트 보기"):
    st.dataframe(df)
