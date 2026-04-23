import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests

# 앱 제목 및 설정
st.set_page_config(page_title="구디 점심 대장", page_icon="🍜")
st.title("🍜 구로 TP타워 점심 대장")
st.caption("인사팀 민영님이 엄선한 구디 직장인 찐 맛집 리스트!")

# --- 실시간 구로동 날씨 가져오기 ---
def get_current_weather():
    url = "https://api.open-meteo.com/v1/forecast?latitude=37.483&longitude=126.897&current_weather=true"
    try:
        response = requests.get(url).json()
        temp = response['current_weather']['temperature']
        code = response['current_weather']['weathercode']
        
        if code in [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82, 95, 96, 99]:
            condition = "비"
        elif code in [71, 73, 75, 77, 85, 86]:
            condition = "눈"
        elif code in [1, 2, 3, 45, 48]:
            condition = "흐림"
        else:
            condition = "맑음"
            
        if temp < 5 or condition == "눈":
            tag = "추움"
        elif condition == "비":
            tag = "비/흐림"
        elif temp > 25:
            tag = "더움"
        elif condition == "맑음":
            tag = "맑음"
        else:
            tag = "비/흐림"
            
        return temp, condition, tag
    except:
        return 20.0, "알수없음", "무관"

current_temp, current_condition, weather_tag = get_current_weather()

st.info(f"📍 실시간 구로동 날씨: **{current_condition}** ({current_temp}℃) \n\n 👉 현재 날씨인 **'{weather_tag}'** 키워드(또는 무관)가 포함된 메뉴를 찾아볼게요!")

# --- 1. 구글 시트 연결 ---
url = "https://docs.google.com/spreadsheets/d/1PP1HV-NWs3c_QjwuIVBu4H5gLl_A78JbPBLcTrVaz4A/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(spreadsheet=url)

df = df.dropna(how='all', axis=1) 
df = df.fillna("")

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

df.rename(columns=col_mapping, inplace=True)

for required_col in ['상호명', '메뉴', '날씨', '거리', '예약', '특징', '가격', '지도']:
    if required_col not in df.columns:
        df[required_col] = ""

# --- 2. 날씨 기반 추천 (기존 기능) ---
st.subheader("🎲 오늘의 날씨 맞춤 추천")
filtered_df = df[df['날씨'].str.contains(weather_tag, na=False) | df['날씨'].str.contains("무관", na=False)]

if filtered_df.empty:
    filtered_df = df[df['날씨'].str.contains("무관", na=False)]

if st.button("아무거나 추천해줘!"):
    if not filtered_df.empty:
        choice = filtered_df.sample(n=1).iloc[0]
        st.balloons()
        st.success(f"오늘의 추천 메뉴는? **[{choice['상호명']}]**의 **{choice['메뉴']}**!")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"📍 거리: {choice['거리']}")
            st.write(f"💰 가격: {choice['가격']}원")
            st.write(f"🗓️ 예약: {choice['예약']}")
        with col2:
            st.write(f"💬 특징: {choice['특징']}")
            if choice['지도'] != "":
                st.markdown(f"[🗺️ 네이버 지도 보기]({choice['지도']})")
    else:
        st.warning("앗, 시트에 데이터가 부족해요!")

st.divider() # 화면에 예쁜 가로선 긋기

# --- 3. 💬 내 맘대로 키워드 검색 (신규 기능!) ---
st.subheader("🔎 먹고 싶은 메뉴나 기분으로 찾기")
user_query = st.text_input("예: 부대찌개, 매콤, 해장, 가성비, 웨이팅")

if st.button("검색어로 찾기"):
    if user_query:
        # 상호명, 메뉴, 특징 열에서 검색어가 하나라도 포함된 것 찾기
        search_result = df[
            df['상호명'].str.contains(user_query, na=False) |
            df['메뉴'].str.contains(user_query, na=False) |
            df['특징'].str.contains(user_query, na=False)
        ]
        
        if not search_result.empty:
            st.success(f"오! '{user_query}'에 딱 맞는 맛집을 {len(search_result)}개 찾았어요! 👇")
            # 검색 결과를 표(Dataframe)로 깔끔하게 보여줌
            st.dataframe(search_result[['상호명', '메뉴', '거리', '가격', '특징', '예약']])
        else:
            st.warning(f"앗, '{user_query}'에 대한 식당은 아직 리스트에 없네요. 다른 단어로 검색해보세요!")
    else:
        st.error("검색어를 입력해주세요!")

st.divider()

# --- 4. 전체 리스트 보기 ---
with st.expander("전체 맛집 리스트 보기"):
    st.dataframe(df)
