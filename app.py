import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests

# 앱 기본 설정
st.set_page_config(page_title="오점뭐?!", page_icon="🍜")

# 🚀 [요청 1 반영] 인사팀 민영님 멘트 삭제 및 직관적인 캡션으로 변경
st.title("🍜 오점뭐?!")
st.caption("'오늘은 뭐 먹지?' 직장인 최대 고민 해결✨")

st.divider()

# --- 1. 상세 날씨 정보 가져오기 (Open-Meteo API) ---
@st.cache_data(ttl=600)
def get_detailed_weather():
    latitude = 37.483 # 구로 TP타워 근처
    longitude = 126.897
    url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,wind_speed_10m,weather_code"
    try:
        data = requests.get(url).json()['current']
        temp = data['temperature_2m']
        feels_like = data['apparent_temperature']
        humidity = data['relative_humidity_2m']
        wind = data['wind_speed_10m']
        rain = data['precipitation']
        code = data['weather_code']
        if code in [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82, 95, 96, 99]: condition, sky = "비", "비/흐림"
        elif code in [71, 73, 75, 77, 85, 86]: condition, sky = "눈", "추움"
        elif code in [1, 2, 3, 45, 48]: condition, sky = "흐림", "무관"
        else: condition, sky = "맑음", "맑음"
        return temp, feels_like, humidity, wind, rain, condition, sky
    except: return 20.0, 20.0, 50, 1.0, 0.0, "알수없음", "무관"

temp, feels_like, humidity, wind, rain, condition, weather_tag = get_detailed_weather()

# --- 2. 상단 대시보드 UI (위치 & 날씨) ---
st.subheader("현재 정보")
c1, c2 = st.columns(2)
with c1:
    st.write("**위치 정보**")
    st.info("📍 위치 확인됨 (구로 TP타워)")
with c2:
    st.write("**구로동 현재 날씨**")
    st.markdown(f"## {temp}℃ <span style='font-size:18px; color:gray;'> (체감 {feels_like}℃)</span>", unsafe_allow_html=True)
st.caption(f"습도 {humidity}% | 강수량 {rain}mm | 풍속 {wind}m/s | **하늘: {condition}**")

st.write("")
st.divider()

# 🚀 [요청 4 반영] 코딩 태그(HTML) 제거하고 깔끔한 마크다운 박스로 교체!
st.info(f"""
**🤖 안녕하세요! 구디 직장인들의 점심 동선에 매우 익숙한 AI입니다.**

날씨와 체감 환경을 고려하여 구로 TP타워 인근 음식을 추천하되, 아래 **직장인 음식 문화 규칙**을 우선 반영합니다.

**입력 정보**
* 하늘: {condition}
* 기온: {temp}℃

**구디 직장인 음식 문화 규칙**
1. 비가 오면 전, 칼국수, 수제비, 국물 요리 선호 (TP타워 지하 등 가까운 곳 우대)
2. 매우 강한 비나 외출이 힘들면 배달 음식 또는 건물 내 식당 선호
3. 추우면 뜨겁고 진한 국물, 고기, 찌개 선호
4. 더우면 냉면, 콩국수, 비빔국수, 샐러드 선호
5. 회식 다음 날은 무조건 해장 키워드 우선순위 반영
""")

st.write("")
st.write("")

# --- 4. 구글 시트 데이터 연결 ---
url = "https://docs.google.com/spreadsheets/d/1PP1HV-NWs3c_QjwuIVBu4H5gLl_A78JbPBLcTrVaz4A/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(spreadsheet=url).dropna(how='all', axis=1).fillna("")

# 열 이름 자동 매칭
col_mapping = {}
for col in df.columns:
    col_str = str(col).lower().replace(" ", "")
    if '상호' in col_str or 'name' in col_str: col_mapping[col] = '상호명'
    elif '메뉴' in col_str or 'menu' in col_str: col_mapping[col] = '메뉴'
    elif '날씨' in col_str or 'weather' in col_str: col_mapping[col] = '날씨'
    elif '거리' in col_str or 'distance' in col_str: col_mapping[col] = '거리'
    elif '예약' in col_str or 'reservation' in col_str: col_mapping[col] = '예약'
    elif '특징' in col_str or '태그' in col_str: col_mapping[col] = '특징'
    elif '가격' in col_str or 'price' in col_str: col_mapping[col] = '가격'
    elif '지도' in col_str or 'url' in col_str: col_mapping[col] = '지도'
    elif '사진' in col_str or 'image' in col_str: col_mapping[col] = '사진'
df.rename(columns=col_mapping, inplace=True)

# --- 5. 💬 챗봇 UI (하단 대화창) ---
st.write("---")
# 아래 여백 추가 (스크롤 방지)
st.write("")
st.write("")
st.write("")
st.write("")

if prompt := st.chat_input("구디 맛집에 관련된 궁금한 내용들을 말씀해주세요! (예: 부대찌개, 해장, 더움)"):
    
    with st.chat_message("user"): st.write(prompt)
    with st.chat_message("assistant"):
        if "추천" in prompt or "아무거나" in prompt:
            res = df[df['날씨'].str.contains(weather_tag, na=False) | df['날씨'].str.contains("무관", na=False)]
            if res.empty: res = df
            choice = res.sample(n=1).iloc[0]
            st.write(f"오늘 같은 **{condition}** 날씨에는 이 메뉴를 추천해 드려요! 🥘")
        else:
            res = df[df['상호명'].str.contains(prompt) | df['메뉴'].str.contains(prompt) | df['특징'].str.contains(prompt)]
            if not res.empty:
                choice = res.sample(n=1).iloc[0] 
                st.write(f"요청하신 '{prompt}' 키워드에 딱 맞는 곳을 찾았어요! ✨ (총 {len(res)}곳 중 추천)")
            else:
                choice = None
                st.write(f"앗, 아직 제 데이터베이스에 '{prompt}'에 해당하는 식당이 없네요. 다른 메뉴는 어떠세요?")
        if choice is not None:
            if '사진' in choice and choice['사진'] != "":
                st.image(choice['사진'], width=300)
            st.success(f"**{choice['상호명']}** ({choice['메뉴']})")
            st.write(f"📍 **거리:** {choice['거리']} | 💰 **가격:** {choice['가격']}원 | 🗓️ **예약:** {choice['예약']}")
            st.info(f"💬 **특징:** {choice['특징']}")
            if choice['지도'] != "":
                st.markdown(f"[🗺️ 네이버 지도에서 바로보기]({choice['지도']})")
            if "추천" not in prompt and len(res) > 1:
                with st.expander(f"'{prompt}' 관련 다른 식당 리스트 모두 보기"):
                    st.dataframe(res[['상호명', '메뉴', '거리', '특징']], hide_index=True)

# --- 6. 사이드바 (전체 데이터 보기) ---
with st.sidebar:
    st.header("🗂️ 맛집 데이터베이스")
    st.caption("현재 등록된 식당 리스트입니다.")
    
    # 🚀 [요청 3 반영] 데이터베이스에 '가격' 열 추가
    df_display = df[['상호명', '메뉴', '가격']].copy()
    
    # 🚀 [요청 2 반영] 표의 높이(height)를 700으로 대폭 늘려 리스트가 더 길게 보이도록 수정!
    st.dataframe(df_display, hide_index=True, use_container_width=True, height=700)
