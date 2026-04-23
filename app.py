import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests

# 1. 앱 설정
st.set_page_config(page_title="오점뭐?!", page_icon="🍜")

st.title("🍜 오점뭐?!")
st.caption("'오늘은 뭐 먹지?' 직장인 최대 고민 해결✨")
st.write("")

# --- 2. 실시간 날씨 정보 가져오기 ---
@st.cache_data(ttl=600)
def get_detailed_weather():
    url = "https://api.open-meteo.com/v1/forecast?latitude=37.483&longitude=126.897&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,wind_speed_10m,weather_code"
    try:
        data = requests.get(url).json()['current']
        temp, feels_like = data['temperature_2m'], data['apparent_temperature']
        humidity, wind, rain = data['relative_humidity_2m'], data['wind_speed_10m'], data['precipitation']
        code = data['weather_code']
        if code in [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82, 95, 96, 99]: cond, sky = "비", "비/흐림"
        elif code in [71, 73, 75, 77, 85, 86]: cond, sky = "눈", "추움"
        elif code in [1, 2, 3, 45, 48]: cond, sky = "흐림", "무관"
        else: cond, sky = "맑음", "맑음"
        return temp, feels_like, humidity, wind, rain, cond, sky
    except: return 20.0, 20.0, 17, 1.5, 0.0, "맑음", "맑음"

temp, feels_like, humidity, wind, rain, condition, weather_tag = get_detailed_weather()

# --- 3. [현재 정보] 디자인 복구 (큰 온도 글씨) ---
st.subheader("현재 정보")
c1, c2 = st.columns([1, 1.2])
with c1:
    st.write("**위치 정보**")
    st.info("📍 위치 확인됨 (구로 TP타워)")
with c2:
    st.write("**구로동 현재 날씨**")
    st.markdown(f"<div style='line-height:1.1;'><span style='font-size:45px; font-weight:800;'>{temp}℃</span> <span style='font-size:20px; color:#666;'>(체감 {feels_like}℃)</span></div>", unsafe_allow_html=True)
st.caption(f"습도 {humidity}% | 강수 {rain}mm | 풍속 {wind}m/s | 하늘: {condition}")

# --- 4. [AI 규칙 박스] 디자인 복구 (빨간 아이콘/테두리) ---
st.markdown(f"""
<div style="background-color: #f0f2f6; padding: 20px; border-radius: 12px; border-left: 5px solid #ff4b4b;">
    <div style="display: flex; align-items: center; margin-bottom: 15px;">
        <div style="background-color: #ff4b4b; border-radius: 50%; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; margin-right: 10px;">
            <span style="color: white; font-size: 14px;">🤖</span>
        </div>
        <b style="font-size: 16px;">너는 한국 음식 문화와 직장인 동선에 매우 익숙한 추천 AI다. 날씨와 체감 환경을 고려하여 음식을 추천하되, 아래 "출력 제약"을 반드시 지켜야 한다.</b>
    </div>
    <h3 style="font-size: 18px; margin-bottom: 5px;">입력 정보</h3>
    <ul style="margin-bottom: 15px;"><li>온도: "{temp}℃" | 하늘: "{condition}"</li></ul>
    <h3 style="font-size: 18px; margin-bottom: 5px;">음식 문화 규칙</h3>
    <ol style="font-size: 14px; line-height: 1.6;">
        <li>비가 오면 국물, 전, 칼국수, 수제비 선호</li>
        <li>추우면 뜨끈한 찌개, 더우면 시원한 면류나 샐러드 선호</li>
        <li>회식 다음 날은 무조건 해장 키워드 반영</li>
    </ol>
</div>
""", unsafe_allow_html=True)

# --- 5. 데이터 연결 및 상세 정보 출력 함수 ---
url = "https://docs.google.com/spreadsheets/d/1PP1HV-NWs3c_QjwuIVBu4H5gLl_A78JbPBLcTrVaz4A/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(spreadsheet=url).dropna(how='all', axis=1).fillna("")

# 열 이름 자동 매칭 (카테고리 포함)
col_mapping = {}
for col in df.columns:
    c = str(col).lower().replace(" ", "")
    if '카테고리' in c or '종류' in c: col_mapping[col] = '카테고리'
    elif '상호' in c or 'name' in c: col_mapping[col] = '상호명'
    elif '메뉴' in c or 'menu' in c: col_mapping[col] = '메뉴'
    elif '가격' in c or 'price' in c: col_mapping[col] = '가격'
    elif '거리' in c or 'distance' in c: col_mapping[col] = '거리'
    elif '예약' in c or 'reservation' in c: col_mapping[col] = '예약'
    elif '특징' in c or '태그' in c: col_mapping[col] = '특징'
    elif '지도' in c or 'url' in c: col_mapping[col] = '지도'
    elif '사진' in c or 'image' in c: col_mapping[col] = '사진'
df.rename(columns=col_mapping, inplace=True)

# 필수 열 안전장치
for c in ['카테고리', '상호명', '메뉴', '가격', '거리', '예약', '특징', '지도', '사진']:
    if c not in df.columns: df[c] = ""

def show_result_detail(choice, reason="AI가 추천하는 오늘의 맛집입니다!"):
    st.write(f"🤖 **추천 사유:** {reason}")
    if choice['사진'] != "": st.image(choice['사진'], use_container_width=True)
    st.success(f"**[{choice['상호명']}]** ({choice['카테고리']})")
    cc1, cc2 = st.columns(2)
    with cc1:
        st.write(f"🍴 **메뉴:** {choice['메뉴']}")
        st.write(f"💰 **가격:** {choice['가격']}원")
    with cc2:
        st.write(f"📍 **거리:** {choice['거리']}")
        st.write(f"🗓️ **예약:** {choice['예약']}")
    st.info(f"💬 **특징:** {choice['특징']}")
    if choice['지도'] != "": st.markdown(f"[🗺️ 네이버 지도 보기]({choice['지도']})")

# --- 6. 추천 버튼 ---
st.write("---")
if st.button("🎲 오늘 날씨에 딱 맞는 메뉴 랜덤 추천!", use_container_width=True):
    kw = []
    if condition in ["비", "눈"]: kw = ["국물", "전", "칼", "수제비", "짬뽕"]
    elif temp >= 25: kw = ["냉면", "소바", "국수", "샐러드", "시원"]
    elif temp <= 5: kw = ["찌개", "탕", "국밥", "샤브", "고기"]
    pattern = '|'.join(kw) if kw else ".*"
    filtered_df = df[df['메뉴'].str.contains(pattern) | df['특징'].str.contains(pattern)]
    if filtered_df.empty: filtered_df = df
    st.balloons()
    show_result_detail(filtered_df.sample(n=1).iloc[0], "현재 날씨와 직장인 규칙을 분석해 골라봤어요!")

# --- 7. 💬 지능형 챗봇 (이미지 속 모든 상황 대응!) ---
if prompt := st.chat_input("예: 예약 가능한 부대찌개집, 쌀국수 추천해줘, 배 안 고파"):
    with st.chat_message("user"): st.write(prompt)
    with st.chat_message("assistant"):
        res = df.copy()
        reason = "사용자님의 취향에 딱 맞는 곳을 찾았습니다!"
        
        # 💡 지능형 필터링 (키워드 분해 검색)
        # 1. 상태/일상어 이해
        if "배 안 고파" in prompt or "가볍" in prompt or "다이어트" in prompt:
            res = res[res['메뉴'].str.contains("샐러드|포케|샌드위치|우동") | res['특징'].str.contains("가벼운|샐러드")]
            reason = "입맛이 없으실 땐 가벼운 샐러드나 면 요리가 부담 없죠!"
        
        # 2. 예약 여부
        if "예약" in prompt:
            res = res[res['예약'].astype(str).str.upper().str.contains("O", na=False)]
        
        # 3. 카테고리 감지
        for cat in ["한식", "일식", "중식", "양식", "아시안"]:
            if cat in prompt: res = res[res['카테고리'].str.contains(cat)]

        # 4. 핵심 메뉴 키워드 추출 (조사/접미사 제거)
        clean_kw = prompt
        for word in ["추천해줘", "추천", "알려줘", "집", "식당", "맛집", "뭐가", "좋지", "있어"]:
            clean_kw = clean_kw.replace(word, "")
        clean_kw = clean_kw.strip()
        
        if len(clean_kw) >= 1:
            res = res[res['상호명'].str.contains(clean_kw) | res['메뉴'].str.contains(clean_kw) | res['특징'].str.contains(clean_kw)]

        # 결과 출력
        if not res.empty:
            choice = res.sample(n=1).iloc[0]
            show_result_detail(choice, reason)
            if len(res) > 1:
                with st.expander(f"다른 {clean_kw} 후보지 더 보기"):
                    st.dataframe(res[['카테고리', '상호명', '메뉴', '가격', '거리']], hide_index=True)
        else:
            st.error(f"앗, 데이터베이스에 '{clean_kw}'와(과) 관련된 정보가 아직 없네요 ㅠㅠ")

# --- 8. 사이드바 (카테고리 추가!) ---
with st.sidebar:
    st.header("🗂️ 맛집 데이터베이스")
    st.caption("카테고리별 전체 리스트")
    st.dataframe(df[['카테고리', '상호명', '메뉴', '가격']], hide_index=True, use_container_width=True, height=700)
