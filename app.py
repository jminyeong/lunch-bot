import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests
import re

# 1. 앱 설정 (레이아웃 및 디자인 절대 고정)
st.set_page_config(page_title="오점뭐?!", page_icon="🍜", layout="centered")

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

# --- 3. [대시보드] 현재 정보 (디자인 복구 완료) ---
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

# --- 4. AI 규칙 박스 (디자인 복구 완료) ---
st.markdown(f"""
<div style="background-color: #f0f2f6; padding: 20px; border-radius: 12px; border-left: 5px solid #ff4b4b;">
    <div style="display: flex; align-items: center; margin-bottom: 15px;">
        <div style="background-color: #ff4b4b; border-radius: 50%; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; margin-right: 10px;">
            <span style="color: white; font-size: 14px;">🤖</span>
        </div>
        <b style="font-size: 16px;">너는 한국 음식 문화와 직장인 점심/저녁 동선에 매우 익숙한 추천 AI다. 날씨와 체감 환경을 고려하여 음식을 추천하되, 아래 "출력 제약"을 반드시 지켜야 한다.</b>
    </div>
    <h3 style="font-size: 18px; margin-bottom: 5px;">입력 정보</h3>
    <ul style="margin-bottom: 15px;"><li>온도: "{temp}℃" | 하늘: "{condition}"</li></ul>
    <h3 style="font-size: 18px; margin-bottom: 5px;">한국 음식 문화 규칙</h3>
    <ol style="font-size: 14px; line-height: 1.6;">
        <li>비가 오면 전, 칼국수, 수제비, 국물 요리 선호</li>
        <li>더우면 냉면이나 샐러드, 추우면 찌개나 뜨거운 국물 선호</li>
        <li>회식 다음 날은 무조건 해장 키워드 반영</li>
    </ol>
</div>
""", unsafe_allow_html=True)

st.write("")
st.info("📢 **여러분의 참여로 더 좋아집니다!** 직접 다녀오신 맛집의 실제 후기와 별점을 남겨주세요. \n\n👉 [**맛집 리스트 참여 및 별점 남기러 가기 (클릭)**](https://docs.google.com/spreadsheets/d/1PP1HV-NWs3c_QjwuIVBu4H5gLl_A78JbPBLcTrVaz4A/edit?usp=sharing)")
st.write("")

# --- 5. 데이터 연결 및 전처리 (💡 실시간 반영 ttl=0 적용) ---
url = "https://docs.google.com/spreadsheets/d/1PP1HV-NWs3c_QjwuIVBu4H5gLl_A78JbPBLcTrVaz4A/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(spreadsheet=url, ttl=0).dropna(how='all', axis=1).fillna("")

col_mapping = {}
for col in df.columns:
    c = str(col).lower().replace(" ", "")
    if '카테고리' in c: col_mapping[col] = '카테고리'
    elif '상호' in c: col_mapping[col] = '상호명'
    elif '메뉴' in c: col_mapping[col] = '메뉴'
    elif '가격' in c: col_mapping[col] = '가격'
    elif '거리' in c: col_mapping[col] = '거리'
    elif '예약' in c: col_mapping[col] = '예약'
    elif '특징' in c or '태그' in c: col_mapping[col] = '특징'
    elif '지도' in c: col_mapping[col] = '지도'
    elif '사진' in c: col_mapping[col] = '사진'
    elif '평균' in c: col_mapping[col] = '평균별점'
df.rename(columns=col_mapping, inplace=True)

for c in ['카테고리', '상호명', '메뉴', '가격', '거리', '예약', '특징', '지도', '사진', '평균별점']:
    if c not in df.columns: df[c] = ""

def get_stars(rating):
    try:
        if rating == "" or pd.isna(rating): return "평가 없음"
        r = float(rating)
        if r <= 0: return "평가 없음"
        return f"{'⭐' * int(r)}{'✫' if (r % 1) >= 0.5 else ''} ({round(r, 1)}점)"
    except: return "평가 없음"

# 상세 정보 카드 함수 (해시태그 깔끔 정리 복구 완료)
def show_restaurant_card(row, ai_reason="민영님이 선정한 맛집입니다!"):
    st.write(f"🤖 **AI 추천 포인트:** {ai_reason}")
    if str(row.get('사진', '')) != "": 
        st.image(row['사진'], use_container_width=True)
    
    star_display = get_stars(row.get('평균별점', 0))
    st.success(f"**[{row['상호명']}]** \n\n {star_display}")
    
    cc1, cc2 = st.columns(2)
    with cc1:
        st.write(f"🍴 **대표메뉴:** {row.get('메뉴', '정보 없음')}")
        st.write(f"💰 **가격:** {row.get('가격', '정보 없음')}원")
    with cc2:
        st.write(f"📍 **도보 거리:** {row.get('거리', '정보 없음')}")
        st.write(f"🗓️ **예약:** {row.get('예약', 'X')}")
    
    char_text = str(row.get('특징', '')).strip()
    if char_text != "" and char_text != "nan":
        raw_tags = re.split(r'[ ,#]+', char_text)
        tags = [f"#{t.strip()}" for t in raw_tags if t.strip()]
        if tags:
            st.markdown(f"<div style='color: #007bff; font-weight: bold; font-size: 1.1em; margin-bottom: 10px;'>{' '.join(tags)}</div>", unsafe_allow_html=True)
    
    if str(row.get('지도', '')) != "":
        st.markdown(f"[🗺️ 네이버 지도 바로보기]({row['지도']})")

# --- 6. 랜덤 추천 버튼 ---
st.write("---")
if st.button("🎲 오늘 날씨에 딱 맞는 메뉴 랜덤 추천!", use_container_width=True):
    kw = []
    if condition in ["비", "눈"]: kw = ["국물", "전", "칼", "수제비", "짬뽕"]
    elif temp >= 25: kw = ["냉면", "소바", "국수", "샐러드", "시원"]
    elif temp <= 5: kw = ["찌개", "탕", "국밥", "샤브", "고기"]
    pattern = '|'.join(kw) if kw else ".*"
    filtered_df = df[df['메뉴'].str.contains(pattern, na=False) | df['특징'].str.contains(pattern, na=False)]
    if filtered_df.empty: filtered_df = df
    st.balloons()
    choice = filtered_df.sample(n=1).iloc[0]
    show_restaurant_card(choice, f"현재 날씨({temp}℃)를 고려한 추천입니다!")

# --- 7. 지능형 챗봇 (💡 해장하기 좋은 곳 검색 + 랜덤 추출 로직) ---
if prompt := st.chat_input("가성비 맛집, 해장하기 좋은 곳, 추울 때 뭐 먹지?"):
    with st.chat_message("user"): st.write(prompt)
    with st.chat_message("assistant"):
        res = df.copy()
        ai_msg, condition_applied = "분석 완료!", False
        p_ns = prompt.replace(" ", "")

        if any(w in p_ns for w in ["안고파", "배불", "가볍", "간단"]):
            res = res[res['메뉴'].str.contains("샐러드|포케|샌드위치|김밥|국수|우동") | res['특징'].str.contains("가벼운|가볍|다이어트|간단")]
            ai_msg, condition_applied = "배가 많이 안 고프실 땐 가벼운 메뉴가 최고죠! 🥗", True

        if any(w in p_ns for w in ["만원", "가성비", "저렴"]):
            res['num_p'] = pd.to_numeric(res['가격'].astype(str).str.replace(',', '').str.replace('원', ''), errors='coerce').fillna(999999)
            res = res[res['num_p'] <= 10000]
            ai_msg, condition_applied = "10,000원 이하 가성비 맛집입니다! 💸", True
        
        if "예약" in prompt:
            res = res[res['예약'].astype(str).str.upper().str.contains("O", na=False)]
            ai_msg, condition_applied = "예약 가능한 식당으로 찾았습니다! 🗓️", True

        # 💡 "해장하기 좋은 곳" -> "해장"만 남도록 조사 및 방해 단어 강력 필터링!
        clean = prompt
        stop_words = ["추천", "알려줘", "맛집", "식당", "메뉴", "음식", "오늘", "점심", "저녁", "집", "곳", "뭐먹지", "어디야", "있는", "곳은", "하기", "좋은", "어때"]
        for w in stop_words: clean = clean.replace(w, " ")
        words = re.sub(r'[^\w\s]', '', clean).split()
        
        final_kws = [w for w in words if w not in ["은", "는", "이", "가", "을", "를", "좀", "데", "거", "요", "때"]]
        
        backup = res.copy()
        for kw in final_kws:
            res = res[
                res['카테고리'].str.contains(kw, na=False) | 
                res['상호명'].str.contains(kw, na=False) | 
                res['메뉴'].str.contains(kw, na=False) | 
                res['특징'].str.contains(kw, na=False)
            ]
        
        if res.empty and condition_applied and not backup.empty: res = backup
        
        if not res.empty:
            # 🚨 챗봇 결과도 항상 랜덤(sample)으로 하나를 보여주도록 복구!
            random_choice = res.sample(n=1).iloc[0]
            show_restaurant_card(random_choice, ai_msg)
            if len(res) > 1:
                with st.expander(f"다른 {len(res)-1}곳의 후보지가 더 있어요! (클릭)"):
                    st.dataframe(res[['카테고리', '상호명', '메뉴', '평균별점']], hide_index=True)
        else: 
            st.error("조건에 맞는 맛집을 찾지 못했어요. 다른 키워드로 검색해 보세요!")

# --- 8. 사이드바 (디자인 복구 완료) ---
with st.sidebar:
    st.header("🗂️ 맛집 데이터베이스")
    st.caption("동료들의 참여로 실시간 업데이트 중!")
    valid_cols = [c for c in ['카테고리', '상호명', '평균별점', '메뉴'] if c in df.columns]
    st.dataframe(df[valid_cols], hide_index=True, use_container_width=True, height=700)
