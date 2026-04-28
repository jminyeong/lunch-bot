import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests
import re

# 1. 앱 설정
st.set_page_config(page_title="오점뭐?!", page_icon="🍜", layout="centered")

st.title("🍜 오점뭐?!")
st.caption("'오늘은 뭐 먹지?' 직장인 최대 고민 해결✨")
st.divider()

# --- 2. 날씨 정보 (이건 API 부하 방지를 위해 10분 유지) ---
@st.cache_data(ttl=600)
def get_detailed_weather():
    url = "https://api.open-meteo.com/v1/forecast?latitude=37.483&longitude=126.897&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,wind_speed_10m,weather_code"
    try:
        data = requests.get(url).json()['current']
        return data['temperature_2m'], data['apparent_temperature'], data['relative_humidity_2m'], data['weather_code'], "맑음"
    except: return 20.0, 20.0, 50, 0, "맑음"

temp, feels_like, humidity, code, condition = get_detailed_weather()

# [대시보드 및 AI 규칙 박스 디자인은 기존과 동일하게 유지됩니다]
st.subheader("현재 정보")
c1, c2 = st.columns([1, 1.2])
with c1:
    st.info("📍 위치: 구로 TP타워")
with c2:
    st.markdown(f"### {temp}℃ (체감 {feels_like}℃)")

st.markdown("""
<div style="background-color: #f0f2f6; padding: 20px; border-radius: 12px; border-left: 5px solid #ff4b4b; margin-bottom: 20px;">
    <b style="font-size: 16px;">🤖 AI 추천 가이드</b><br>
    날씨와 여러분의 해시태그를 분석하여 최적의 메뉴를 랜덤하게 골라드립니다.
</div>
""", unsafe_allow_html=True)

# --- 3. 데이터 연결 (💡 실시간 반영을 위해 캐시 TTL을 0으로 설정!) ---
url = "https://docs.google.com/spreadsheets/d/1PP1HV-NWs3c_QjwuIVBu4H5gLl_A78JbPBLcTrVaz4A/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

# 여기서 ttl=0 설정이 핵심입니다! 시트 수정 후 앱 새로고침하면 바로 반영돼요.
df = conn.read(spreadsheet=url, ttl=0).dropna(how='all', axis=1).fillna("")

# [컬럼 매핑 로직 동일]
col_mapping = {'카테고리':'카테고리', '상호명':'상호명', '메뉴':'메뉴', '가격':'가격', '거리':'거리', '예약':'예약', '특징':'특징', '태그':'특징', '지도':'지도', '사진':'사진', '평균':'평균별점'}
df.rename(columns=lambda x: col_mapping.get(next((k for k in col_mapping if k in x), x), x), inplace=True)

def show_restaurant_card(row, ai_reason="추천 맛집입니다!"):
    st.write(f"🤖 **AI 추천 포인트:** {ai_reason}")
    if row.get('사진'): st.image(row['사진'], use_container_width=True)
    st.success(f"**[{row['상호명']}]**")
    
    char_text = str(row.get('특징', '')).strip()
    if char_text:
        tags = [f"#{t.strip()}" for t in re.split(r'[ ,#]+', char_text) if t.strip()]
        st.markdown(f"<div style='color: #007bff; font-weight: bold;'>{' '.join(tags)}</div>", unsafe_allow_html=True)
    
    if row.get('지도'): st.markdown(f"[🗺️ 지도 보기]({row['지도']})")

# --- 4. 검색 로직 (💡 "해장하기 좋은 곳" 대응) ---
if prompt := st.chat_input("해장하기 좋은 곳, 친절한 식당, 가벼운 메뉴..."):
    with st.chat_message("user"): st.write(prompt)
    with st.chat_message("assistant"):
        # 검색어 정제: "좋은", "곳", "추천" 등을 빼고 핵심만 추출
        clean_prompt = re.sub(r'좋은|곳|추천|맛집|알려줘|어디야|있어|뭐먹지|식당|메뉴', ' ', prompt).strip()
        # "해장하기" -> "해장"만 남기기 위해 짧은 단어로 분리
        keywords = [k for k in clean_prompt.split() if len(k) >= 2] or [clean_prompt]
        
        res = df.copy()
        # 모든 키워드가 포함된 식당 찾기
        for kw in keywords:
            # 단어의 일부만 포함되어도 검색되도록 (예: '해장하기' 입력 시 '해장' 포함된 행 검색)
            res = res[res.apply(lambda row: row.astype(str).str.contains(kw[:2]).any(), axis=1)]
        
        if not res.empty:
            # 🚨 결과 중 무조건 랜덤으로 하나 추출!
            choice = res.sample(n=1).iloc[0]
            show_restaurant_card(choice, f"'{prompt}' 검색 결과 중 엄선했습니다!")
            if len(res) > 1:
                with st.expander(f"다른 {len(res)-1}개의 후보 더 보기"):
                    st.table(res[['상호명', '메뉴', '특징']].head(5))
        else:
            st.error("앗, 그런 곳은 아직 리스트에 없어요. 직접 추가해 보시겠어요?")

# [사이드바 및 나머지 기능 동일]
