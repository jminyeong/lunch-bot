import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests
import re

# 1. 앱 설정
st.set_page_config(page_title="오점뭐?!", page_icon="🍜")

st.title("🍜 오점뭐?!")
st.caption("'오늘은 뭐 먹지?' 직장인 최대 고민 해결✨")
st.divider()

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

# --- 3. [대시보드] 현재 정보 디자인 ---
st.subheader("현재 정보")
c1, c2 = st.columns([1, 1.2])
with c1:
    st.write("**위치 정보**")
    st.info("📍 위치 확인됨 (구로 TP타워)")
with c2:
    st.write("**구로동 현재 날씨**")
    st.markdown(f"<div style='line-height:1.1;'><span style='font-size:45px; font-weight:800;'>{temp}℃</span> <span style='font-size:20px; color:#666;'>(체감 {feels_like}℃)</span></div>", unsafe_allow_html=True)
st.caption(f"습도 {humidity}% | 강수 {rain}mm | 풍속 {wind}m/s | 하늘: {condition}")

st.write("")

# --- 4. [AI 규칙 박스] ---
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
    <h3 style="font-size: 18px; margin-bottom: 5px;">한국 음식 문화 규칙</h3>
    <ol style="font-size: 14px; line-height: 1.6;">
        <li>비가 오면 국물, 전, 칼국수, 수제비 선호</li>
        <li>더우면 냉면이나 샐러드, 추우면 찌개나 뜨거운 국물 선호</li>
        <li>회식 다음 날은 무조건 해장 키워드 반영</li>
    </ol>
</div>
""", unsafe_allow_html=True)

# --- 5. 데이터 연결 및 상세 정보 출력 함수 ---
url = "https://docs.google.com/spreadsheets/d/1PP1HV-NWs3c_QjwuIVBu4H5gLl_A78JbPBLcTrVaz4A/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(spreadsheet=url).dropna(how='all', axis=1).fillna("")

# 열 이름 자동 매칭
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

for c in ['카테고리', '상호명', '메뉴', '가격', '거리', '예약', '특징', '지도', '사진']:
    if c not in df.columns: df[c] = ""

# 상세 정보 카드 함수
def show_restaurant_card(row, ai_reason="취향을 저격할 맛집입니다!"):
    st.write(f"🤖 **AI 추천 포인트:** {ai_reason}")
    if row['사진'] != "":
        st.image(row['사진'], use_container_width=True)
    st.success(f"**[{row['상호명']}]** ({row['카테고리']})")
    cc1, cc2 = st.columns(2)
    with cc1:
        st.write(f"🍴 **대표메뉴:** {row['메뉴']}")
        st.write(f"💰 **가격:** {row['가격']}원")
    with cc2:
        st.write(f"📍 **도보 거리:** {row['거리']}")
        st.write(f"🗓️ **예약:** {row['예약']}")
    st.info(f"💬 **특징:** {row['특징']}")
    if row['지도'] != "":
        st.markdown(f"[🗺️ 네이버 지도에서 바로보기]({row['지도']})")

# --- 6. 🎲 랜덤 추천 버튼 ---
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
    show_restaurant_card(filtered_df.sample(n=1).iloc[0], f"오늘 같은 {condition} 날씨에 완벽한 메뉴를 골라봤어요!")

# --- 7. 💬 완전 지능형 챗봇 (불필요한 단어 완벽 필터링) ---
st.write("")
if prompt := st.chat_input("예: 예약가능한 부대찌개집, 해장 메뉴, 배 안 고파"):
    with st.chat_message("user"):
        st.write(prompt)
    
    with st.chat_message("assistant"):
        res = df.copy()
        ai_msg = "분석을 완료했습니다! 이 집은 어떠신가요?"
        
        # 💡 [필터 1] 감성 및 상태 파악
        prompt_nospace = prompt.replace(" ", "")
        if any(w in prompt_nospace for w in ["안고파", "안고픈", "배불", "가볍", "간단", "다이어트"]):
            res = res[res['메뉴'].str.contains("샐러드|포케|샌드위치|김밥|국수|우동") | res['특징'].str.contains("가벼운|가볍|다이어트|간단")]
            ai_msg = "배가 많이 안 고프실 땐 무겁지 않고 가벼운 이 메뉴를 추천해 드려요!"
        
        # 💡 [필터 2] 예약 여부 파악
        if "예약" in prompt:
            res = res[res['예약'].astype(str).str.upper().str.contains("O", na=False)]
            ai_msg = "요청하신 예약 가능한 식당으로 찾았습니다!"
            
        # 💡 [필터 3] 강력한 금지어 사전 (메뉴, 음식 등 추가)
        safe_to_remove = [
            "예약 가능한", "예약가능한", "예약되는", "예약",
            "추천해줘", "추천해주세요", "추천해", "추천", "알려줘", "찾아줘", "골라줘",
            "배 많이 안 고픈데", "배 많이 안고픈데", "배 안 고픈데", "배 안고픈데", "배가 안 고파", "배 안 고파",
            "가벼운 거", "간단한 거",
            "뭐 먹을까", "뭐 먹지", "뭐먹지", "뭐먹을까", "먹을까", "먹지", "어때", "어디가", "좋지", "어디야",
            "맛집", "음식점", "식당", "메뉴", "음식", "점심", "저녁", "오늘", "내일"
        ]
        
        clean_kw = prompt
        for word in safe_to_remove:
            clean_kw = clean_kw.replace(word, " ")
        
        # 특수문자(?, ! 등) 지우고 띄어쓰기 기준으로 쪼개기
        clean_kw = re.sub(r'[^\w\s]', '', clean_kw)
        words = clean_kw.split()
        
        # 은, 는, 이, 가 같은 조사와 꼬리표 단어 한 번 더 걸러내기
        final_keywords = [w for w in words if w not in ["집", "곳", "뭐", "좀", "데", "거", "요", "은", "는", "이", "가", "을", "를"]]

        # 💡 [필터 4] 최종 남은 알짜배기 단어로 다중 검색
        for kw in final_keywords:
            res = res[res['카테고리'].str.contains(kw) | res['상호명'].str.contains(kw) | res['메뉴'].str.contains(kw) | res['특징'].str.contains(kw)]

        # 결과 도출
        if not res.empty:
            choice = res.sample(n=1).iloc[0]
            show_restaurant_card(choice, ai_msg)
            
            if len(res) > 1:
                with st.expander(f"조건에 맞는 다른 후보지 {len(res)-1}곳 더 보기"):
                    st.dataframe(res[['카테고리', '상호명', '메뉴', '가격', '예약']], hide_index=True)
        else:
            st.error(f"앗, 데이터베이스에 조건에 맞는 곳이 아직 없네요 ㅠㅠ 다른 메뉴를 말씀해 주시겠어요?")

# --- 8. 사이드바 ---
with st.sidebar:
    st.header("🗂️ 맛집 데이터베이스")
    st.caption("카테고리별 전체 리스트")
    st.dataframe(df[['카테고리', '상호명', '메뉴', '가격']], hide_index=True, use_container_width=True, height=700)
