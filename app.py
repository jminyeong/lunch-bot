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

# --- 3. 상단 대시보드 ---
st.subheader("현재 정보")
c1, c2 = st.columns([1, 1.2])
with c1:
    st.write("**위치 정보**")
    st.info("📍 위치 확인됨 (구로 TP타워)")
with c2:
    st.write("**구로동 현재 날씨**")
    st.markdown(f"<div style='line-height:1.1;'><span style='font-size:45px; font-weight:800;'>{temp}℃</span> <span style='font-size:20px; color:#666;'>(체감 {feels_like}℃)</span></div>", unsafe_allow_html=True)
st.caption(f"습도 {humidity}% | 강수 {rain}mm | 하늘: {condition}")

# --- 4. [업데이트] 참여 독려 메시지 & 시트 링크 ---
st.write("")
with st.expander("📢 여러분의 참여로 더 좋아집니다! (후기/별점 남기기)", expanded=True):
    st.markdown(f"""
    직접 다녀오신 맛집의 **실제 후기**와 **점수**를 남겨주세요! 
    동료분들의 소중한 의견이 모여 구디 최고의 맛집 지도가 완성됩니다. ✨
    
    👉 [**맛집 리스트 참여 및 후기 남기러 가기 (클릭)**](https://docs.google.com/spreadsheets/d/1PP1HV-NWs3c_QjwuIVBu4H5gLl_A78JbPBLcTrVaz4A/edit?usp=sharing)
    """)

# --- 5. 데이터 연결 및 상세 정보 출력 함수 (별점 반영) ---
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
    elif '별점' in c or 'score' in c: col_mapping[col] = '별점'
    elif '후기' in c or 'review' in c: col_mapping[col] = '후기'
df.rename(columns=col_mapping, inplace=True)

# 가격 숫자 변환 (가성비 검색용)
df['숫자가격'] = pd.to_numeric(df['가격'].astype(str).str.replace(',', '').str.replace('원', ''), errors='coerce').fillna(999999)

# [별점 변환 함수] 4.5 -> ⭐⭐⭐⭐✫
def get_stars(rating):
    try:
        r = float(rating)
        full_stars = int(r)
        half_star = 1 if (r - full_stars) >= 0.5 else 0
        return "⭐" * full_stars + "✫" * half_star + f" ({r})"
    except:
        return "평가 없음"

# 상세 정보 카드 함수
def show_restaurant_card(row, ai_reason="동료들이 직접 검증한 맛집입니다!"):
    st.write(f"🤖 **AI 추천 포인트:** {ai_reason}")
    if row['사진'] != "":
        st.image(row['사진'], use_container_width=True)
    
    # 별점 표시
    stars = get_stars(row.get('별점', 0))
    st.success(f"**[{row['상호명']}]** {stars}")
    
    cc1, cc2 = st.columns(2)
    with cc1:
        st.write(f"🍴 **대표메뉴:** {row['메뉴']}")
        st.write(f"💰 **가격:** {row['가격']}원")
    with cc2:
        st.write(f"📍 **도보 거리:** {row['거리']}")
        st.write(f"🗓️ **예약:** {row['예약']}")
    
    # 실제 후기 표시
    review = row.get('후기', '')
    if review != "":
        st.warning(f"💬 **동료의 찐 후기:** {review}")
    else:
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
    show_restaurant_card(filtered_df.sample(n=1).iloc[0], f"현재 날씨({temp}℃)와 동료들의 별점을 분석했어요!")

# --- 7. 💬 지능형 챗봇 (가성비+별점 포함) ---
st.write("")
if prompt := st.chat_input("예: 가성비 맛집, 별점 높은 부대찌개, 추운데 뭐 먹지?"):
    with st.chat_message("user"):
        st.write(prompt)
    
    with st.chat_message("assistant"):
        res = df.copy()
        ai_msg = "분석 완료! 동료들이 선정한 맛집 리스트를 확인해 보세요."
        
        prompt_nospace = prompt.replace(" ", "")
        
        # 💡 [필터] 가성비
        if any(w in prompt_nospace for w in ["만원이하", "가성비", "저렴", "싼"]):
            res = res[res['숫자가격'] <= 10000]
            ai_msg = "10,000원 이하로 즐기는 가성비 찐 맛집입니다! 💸"
        
        # 💡 [필터] 별점 높은 순 (사용자가 '별점 높은', '평점 좋은' 등 언급 시)
        if any(w in prompt_nospace for w in ["별점", "평점", "인기"]):
            # 별점을 숫자로 변환 후 내림차순 정렬
            res['tmp_score'] = pd.to_numeric(res['별점'], errors='coerce').fillna(0)
            res = res.sort_values(by='tmp_score', ascending=False)
            ai_msg = "동료들의 만족도가 가장 높은 곳들 위주로 골랐어요! ⭐"

        # 💡 [필터] 핵심 키워드 추출 검색
        safe_to_remove = ["추천", "알려줘", "맛집", "식당", "메뉴", "음식", "오늘", "점심", "집", "곳"]
        clean_kw = prompt
        for word in safe_to_remove: clean_kw = clean_kw.replace(word, " ")
        clean_kw = re.sub(r'[^\w\s]', '', clean_kw)
        words = clean_kw.split()
        
        for kw in words:
            if len(kw) > 1:
                res = res[res['카테고리'].str.contains(kw) | res['상호명'].str.contains(kw) | res['메뉴'].str.contains(kw) | res['특징'].str.contains(kw)]

        if not res.empty:
            choice = res.iloc[0] # 정렬된 경우 최상단 출력
            show_restaurant_card(choice, ai_msg)
            if len(res) > 1:
                with st.expander(f"조건에 맞는 다른 후보지 {len(res)-1}곳 더 보기"):
                    st.dataframe(res[['카테고리', '상호명', '메뉴', '별점', '가격']], hide_index=True)
        else:
            st.error("앗, 조건에 맞는 곳이 아직 없네요. 시트에 직접 추가해 보시는 건 어떨까요?")

# --- 8. 사이드바 ---
with st.sidebar:
    st.header("🗂️ 맛집 데이터베이스")
    st.caption("동료들의 참여로 업데이트 중!")
    st.dataframe(df[['카테고리', '상호명', '별점', '메뉴']], hide_index=True, use_container_width=True, height=700)
