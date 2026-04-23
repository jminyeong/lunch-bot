import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests

# 1. 앱 설정
st.set_page_config(page_title="오점뭐?!", page_icon="🍜")

st.title("🍜 오점뭐?!")
st.caption("'오늘은 뭐 먹지?' 직장인 최대 고민 해결✨")
st.write("")

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
        if code in [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82, 95, 96, 99]: cond, sky = "비", "비/흐림"
        elif code in [71, 73, 75, 77, 85, 86]: cond, sky = "눈", "추움"
        elif code in [1, 2, 3, 45, 48]: cond, sky = "흐림", "무관"
        else: cond, sky = "맑음", "맑음"
        return temp, feels_like, humidity, wind, rain, cond, sky
    except: return 20.0, 20.0, 17, 1.5, 0.0, "맑음", "맑음"

temp, feels_like, humidity, wind, rain, condition, weather_tag = get_detailed_weather()

# --- 3. [현재 정보] 디자인 ---
st.subheader("현재 정보")
c1, c2 = st.columns([1, 1.2])
with c1:
    st.write("**위치 정보**")
    st.info("위치 확인됨")
    st.caption("구로 TP타워 (37.483, 126.897)")
with c2:
    st.write("**구로동 현재 날씨**")
    st.markdown(f"<div style='line-height:1.1;'><span style='font-size:45px; font-weight:800;'>{temp}℃</span> <span style='font-size:20px; color:#666;'>(체감 {feels_like}℃)</span></div>", unsafe_allow_html=True)
st.caption(f"습도 {humidity}% | 강수 {rain}mm | 하늘: {condition}")

# --- 4. [AI 규칙 박스] 디자인 ---
st.markdown(f"""
<div style="background-color: #f0f2f6; padding: 20px; border-radius: 12px; border-left: 5px solid #ff4b4b;">
    <b style="font-size: 16px;">🤖 한국 음식 문화와 직장인 동선에 익숙한 AI입니다. 아래 규칙을 반영하여 추천합니다.</b>
    <h3 style="font-size: 18px; margin-top: 15px; margin-bottom: 5px;">입력 정보</h3>
    <ul style="margin-bottom: 15px;"><li>온도: "{temp}℃" | 하늘: "{condition}"</li></ul>
    <h3 style="font-size: 18px; margin-bottom: 5px;">음식 문화 규칙</h3>
    <ol style="font-size: 14px; line-height: 1.6;">
        <li>비가 오면 국물, 전, 칼국수, 수제비 선호</li>
        <li>외출이 힘들면 배달 가능 메뉴나 건물 내 식당 추천</li>
        <li>추우면 진한 국물과 찌개, 더우면 냉면과 샐러드 선호</li>
        <li>회식 다음 날은 무조건 해장 키워드 반영</li>
    </ol>
</div>
""", unsafe_allow_html=True)

# --- 5. 데이터 연결 및 공통 출력 함수 ---
url = "https://docs.google.com/spreadsheets/d/1PP1HV-NWs3c_QjwuIVBu4H5gLl_A78JbPBLcTrVaz4A/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(spreadsheet=url).dropna(how='all', axis=1).fillna("")

col_mapping = {str(col): str(col).lower().replace(" ", "") for col in df.columns}
# 구체적인 매칭
final_cols = {}
for real_col, clean_col in col_mapping.items():
    if '상호' in clean_col or 'name' in clean_col: final_cols[real_col] = '상호명'
    elif '메뉴' in clean_col or 'menu' in clean_col: final_cols[real_col] = '메뉴'
    elif '가격' in clean_col or 'price' in clean_col: final_cols[real_col] = '가격'
    elif '거리' in clean_col or 'distance' in clean_col: final_cols[real_col] = '거리'
    elif '예약' in clean_col or 'reservation' in clean_col: final_cols[real_col] = '예약'
    elif '특징' in clean_col or '태그' in clean_col: final_cols[real_col] = '특징'
    elif '지도' in clean_col or 'url' in clean_col: final_cols[real_col] = '지도'
    elif '사진' in clean_col or 'image' in clean_col: final_cols[real_col] = '사진'
df.rename(columns=final_cols, inplace=True)

# 필수 열 안전장치
for c in ['상호명', '메뉴', '가격', '거리', '예약', '특징', '지도', '사진']:
    if c not in df.columns: df[c] = ""

# 공통 상세 출력 함수 (중요!)
def show_restaurant_detail(choice):
    if choice['사진'] != "": st.image(choice['사진'], use_container_width=True)
    st.success(f"오늘의 추천: **[{choice['상호명']}]**의 **{choice['메뉴']}**")
    cc1, cc2 = st.columns(2)
    with cc1:
        st.write(f"💰 **가격:** {choice['가격']}원")
        st.write(f"📍 **거리:** {choice['거리']}")
    with cc2:
        st.write(f"🗓️ **예약:** {choice['예약']}")
        if choice['지도'] != "": st.markdown(f"[🗺️ 네이버 지도 보기]({choice['지도']})")
    st.info(f"💬 **특징:** {choice['특징']}")

# --- 6. 추천 버튼 ---
st.write("---")
if st.button("🎲 오늘 날씨에 딱 맞는 메뉴 랜덤 추천!", use_container_width=True):
    kw = []
    if condition in ["비", "눈"]: kw = ["국물", "전", "칼", "수제비", "짬뽕", "우동", "부대찌개"]
    elif temp >= 25: kw = ["냉면", "소바", "국수", "샐러드", "시원"]
    elif temp <= 5: kw = ["찌개", "탕", "국밥", "샤브", "고기"]
    
    pattern = '|'.join(kw) if kw else ".*"
    filtered_df = df[df['메뉴'].str.contains(pattern) | df['특징'].str.contains(pattern)]
    if filtered_df.empty: filtered_df = df
    
    st.balloons()
    show_restaurant_detail(filtered_df.sample(n=1).iloc[0])

# --- 7. 💬 지능형 챗봇 (이미지 상세정보 완벽 복구) ---
if prompt := st.chat_input("예: 쌀국수집 추천해줘, 비 오는데 뭐 먹지?, 예약 가능한 곳"):
    with st.chat_message("user"): st.write(prompt)
    with st.chat_message("assistant"):
        res = df.copy()
        
        # 1. 날씨 키워드 감지 (비, 눈 등)
        if "비" in prompt or "눈" in prompt:
            res = res[res['메뉴'].str.contains("국물|전|칼|수제비|찌개|짬뽕") | res['특징'].str.contains("국물|전|칼|수제비|찌개|짬뽕")]
            st.write(f"비/눈 오는 날씨에 딱인 뜨끈한 곳들을 찾아봤어요! 🌧️")
        
        # 2. 예약 키워드 감지
        if "예약" in prompt:
            res = res[res['예약'].astype(str).str.upper().str.contains("O", na=False)]

        # 3. 메뉴 키워드 추출 (불필요한 단어 제거)
        clean_kw = prompt
        for word in ["추천해줘", "추천", "알려줘", "어디야", "어때", "뭐가", "좋지", "집", "식당", "음식점"]:
            clean_kw = clean_kw.replace(word, "")
        clean_kw = clean_kw.strip()
        
        # 메뉴 검색 적용
        if len(clean_kw) >= 1:
            res = res[res['상호명'].str.contains(clean_kw) | res['메뉴'].str.contains(clean_kw) | res['특징'].str.contains(clean_kw)]
        
        # 결과 출력
        if not res.empty:
            choice = res.sample(n=1).iloc[0]
            # [핵심] 여기서 예전처럼 상세 정보를 다 보여줍니다!
            show_restaurant_detail(choice)
            
            if len(res) > 1:
                with st.expander(f"'{clean_kw}' 관련 다른 후보지 더 보기"):
                    st.dataframe(res[['상호명', '메뉴', '가격', '거리', '예약']], hide_index=True)
        else:
            st.error(f"앗, 아직 데이터베이스에 '{clean_kw}'(와)과 관련된 정보가 없어요 ㅠㅠ")

# --- 8. 사이드바 ---
with st.sidebar:
    st.header("🗂️ 맛집 DB")
    st.dataframe(df[['상호명', '메뉴', '가격']], hide_index=True, use_container_width=True, height=700)
