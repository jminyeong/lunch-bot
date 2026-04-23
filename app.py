import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests

# 1. 앱 기본 설정 (모바일 최적화 레이아웃)
st.set_page_config(page_title="오점뭐?!", page_icon="🍜")

# [수정 1] 타이틀 및 캡션 변경
st.title("🍜 오점뭐?!")
st.caption("'오늘은 뭐 먹지?' 직장인 최대 고민 해결✨")
st.divider()

# --- 2. 상세 날씨 정보 가져오기 ---
@st.cache_data(ttl=600)
def get_detailed_weather():
    url = "https://api.open-meteo.com/v1/forecast?latitude=37.483&longitude=126.897&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,wind_speed_10m,weather_code"
    try:
        data = requests.get(url).json()['current']
        temp = data['temperature_2m']
        feels_like = data['apparent_temperature']
        humidity = data['relative_humidity_2m']
        wind = data['wind_speed_10m']
        rain = data['precipitation']
        code = data['weather_code']
        # 기상 조건 판단
        if code in [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82, 95, 96, 99]: cond, sky = "비", "비/흐림"
        elif code in [71, 73, 75, 77, 85, 86]: cond, sky = "눈", "추움"
        elif code in [1, 2, 3, 45, 48]: cond, sky = "흐림", "무관"
        else: cond, sky = "맑음", "맑음"
        return temp, feels_like, humidity, wind, rain, cond, sky
    except:
        return 20.0, 20.0, 50, 1.0, 0.0, "알수없음", "무관"

temp, feels_like, humidity, wind, rain, condition, weather_tag = get_detailed_weather()

# --- 3. [대시보드] 현재 정보 (이미지 2번째 부분 복구) ---
st.subheader("현재 정보")
col1, col2 = st.columns(2)
with col1:
    st.write("**위치 정보**")
    st.info("📍 위치 확인됨 (구로 TP타워)")
with col2:
    st.write("**구로동 현재 날씨**")
    st.markdown(f"## {temp}℃ <span style='font-size:18px; color:gray;'> (체감 {feels_like}℃)</span>", unsafe_allow_html=True)
st.caption(f"습도 {humidity}% | 강수량 {rain}mm | 풍속 {wind}m/s | **하늘: {condition}**")

st.write("")
st.divider()

# --- 4. [AI 규칙 박스] (이미지 3번째 부분 복구 + 코딩내용 숨김) ---
st.info(f"""
**🤖 안녕하세요! 구디 직장인들의 점심 동선에 매우 익숙한 AI입니다.**

날씨와 체감 환경을 고려하여 구로 TP타워 인근 음식을 추천하되, 아래 **직장인 음식 문화 규칙**을 우선 반영합니다.

**입력 정보**
* 하늘: {condition}
* 기온: {temp}℃

**구디 직장인 음식 문화 규칙**
1. 비가 오면 전, 칼국수, 수제비, 국물 요리 선호
2. 매우 강한 비나 외출이 힘들면 배달 음식 또는 건물 내 식당 선호
3. 추우면 뜨겁고 진한 국물, 고기, 찌개 선호
4. 더우면 냉면, 소바, 국수, 샐러드 선호
5. 회식 다음 날은 무조건 해장 키워드 우선순위 반영
""")

# --- 5. 구글 시트 연결 및 데이터 전처리 (KeyError 완벽 방어) ---
url = "https://docs.google.com/spreadsheets/d/1PP1HV-NWs3c_QjwuIVBu4H5gLl_A78JbPBLcTrVaz4A/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(spreadsheet=url).dropna(how='all', axis=1).fillna("")

# 열 이름 표준화 로직
col_mapping = {}
for col in df.columns:
    c = str(col).lower().replace(" ", "")
    if '상호' in c or 'name' in c: col_mapping[col] = '상호명'
    elif '메뉴' in c or 'menu' in c: col_mapping[col] = '메뉴'
    elif '날씨' in c or 'weather' in c: col_mapping[col] = '날씨'
    elif '거리' in c or 'distance' in c: col_mapping[col] = '거리'
    elif '예약' in c or 'reservation' in c: col_mapping[col] = '예약'
    elif '특징' in c or '태그' in c: col_mapping[col] = '특징'
    elif '가격' in c or 'price' in c: col_mapping[col] = '가격'
    elif '지도' in c or 'url' in c: col_mapping[col] = '지도'
    elif '사진' in c or 'image' in c: col_mapping[col] = '사진'
df.rename(columns=col_mapping, inplace=True)

# 필수 열이 없을 경우 자동 생성 (에러 방지)
for col in ['상호명', '메뉴', '날씨', '거리', '예약', '특징', '가격', '지도', '사진']:
    if col not in df.columns: df[col] = ""

# --- 6. 🎲 문화 규칙 반영 랜덤 추천 버튼 ---
st.write("---")
st.subheader("🎲 도저히 못 고르겠다면?")
if st.button("오늘 날씨에 딱 맞는 메뉴 랜덤 추천!", use_container_width=True):
    # 날씨 규칙 기반 키워드 필터링
    kw = []
    if condition in ["비", "눈"]: kw = ["국물", "전", "칼", "수제비", "짬뽕"]
    elif temp >= 25: kw = ["냉면", "소바", "국수", "샐러드", "시원"]
    elif temp <= 5: kw = ["찌개", "탕", "국밥", "샤브", "고기"]
    
    if kw:
        pattern = '|'.join(kw)
        filtered_df = df[df['메뉴'].str.contains(pattern) | df['특징'].str.contains(pattern)]
    else: filtered_df = df
    if filtered_df.empty: filtered_df = df
    
    choice = filtered_df.sample(n=1).iloc[0]
    st.balloons()
    st.success(f"🎯 오늘의 당첨! **[{choice['상호명']}]**의 **{choice['메뉴']}**")
    if choice['사진'] != "": st.image(choice['사진'], width=300)
    st.write(f"💰 가격: {choice['가격']}원 | 🗓️ 예약: {choice['예약']} | 📍 거리: {choice['거리']}")
    if choice['지도'] != "": st.markdown(f"[🗺️ 지도 보기]({choice['지도']})")

# --- 7. 💬 지능형 챗봇 (예약+키워드+날씨 통합) ---
st.write("")
if prompt := st.chat_input("예: 예약가능한 부대찌개, 비오는데 뭐먹지?, 돈까스"):
    with st.chat_message("user"): st.write(prompt)
    with st.chat_message("assistant"):
        res = df.copy()
        # 예약 필터링
        if "예약" in prompt: res = res[res['예약'].astype(str).str.upper().str.contains("O", na=False)]
        # 날씨 규칙 필터링
        if "비" in prompt or "눈" in prompt: res = res[res['메뉴'].str.contains("국물|전|칼|수제비") | res['특징'].str.contains("국물|전|칼|수제비")]
        
        # 키워드 검색
        clean_kw = prompt.replace("예약", "").replace("추천", "").replace("해줘", "").strip()
        if len(clean_kw) > 1:
            res = res[res['상호명'].str.contains(clean_kw) | res['메뉴'].str.contains(clean_kw) | res['특징'].str.contains(clean_kw)]
        
        if not res.empty:
            choice = res.sample(n=1).iloc[0]
            st.success(f"**{choice['상호명']}** ({choice['메뉴']})")
            if choice['사진'] != "": st.image(choice['사진'], width=250)
            if len(res) > 1:
                with st.expander("다른 후보지 보기"):
                    st.dataframe(res[['상호명', '메뉴', '가격', '예약']], hide_index=True)
        else: st.error("조건에 맞는 식당이 없어요 ㅠㅠ")

# --- 8. [사이드바] 맛집 리스트 (이미지 1번째 부분 복구) ---
with st.sidebar:
    st.header("🗂️ 맛집 DB")
    st.caption("전체 리스트 (상호, 메뉴, 가격)")
    # [수정 사항 반영] 가격 추가, 순번 숨김, 높이 700
    display_cols = ['상호명', '메뉴', '가격']
    st.dataframe(df[display_cols], hide_index=True, use_container_width=True, height=700)
