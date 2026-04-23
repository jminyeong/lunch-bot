import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 앱 제목 및 설정
st.set_page_config(page_title="구디 점심 대장", page_icon="🍜")
st.title("🍜 구로 TP타워 점심 대장")
st.caption("인사팀 민영님이 엄선한 구디 직장인 찐 맛집 리스트!")

# 1. 구글 시트 연결
url = "https://docs.google.com/spreadsheets/d/1PP1HV-NWs3c_QjwuIVBu4H5gLl_A78JbPBLcTrVaz4A/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(spreadsheet=url)

# 결측치(빈칸) 처리
df = df.fillna("")

# 2. 오늘 날씨 선택
weather = st.selectbox("☀️ 오늘 날씨가 어떤가요?", ["맑음", "비", "흐림", "추움", "더움", "무관"])

# 3. 필터링 로직 (선택한 날씨 키워드가 시트의 날씨 태그에 포함되어 있거나, 무관인 경우)
filtered_df = df[df['weather_tag (날씨)'].str.contains(weather, na=False) | (df['weather_tag (날씨)'] == "무관")]

# 4. 추천 버튼
if st.button("오늘 뭐 먹지? 랜덤 추천받기!"):
    if not filtered_df.empty:
        choice = filtered_df.sample(n=1).iloc[0]
        st.balloons()
        st.success(f"오늘의 추천 메뉴는? **[{choice['name (식당명)']}]**의 **{choice['menu(주요메뉴)']}**!")
        
        # 상세 정보 표시
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"📍 거리: {choice['distance (거리)']}")
            st.write(f"💰 가격: {choice['price (가격대)']}원")
        with col2:
            st.write(f"💬 특징: {choice['특징/태그']}")
            # 지도 링크가 비어있지 않으면 링크 버튼 표시
            if choice['map_url (지도)'] != "":
                st.markdown(f"[🗺️ 네이버 지도 보기]({choice['map_url (지도)']})")
    else:
        st.warning("앗, 해당 조건에 맞는 식당이 없어요. 다른 날씨를 선택해 볼까요?")

# 5. 전체 리스트 보기
with st.expander("전체 맛집 리스트 보기"):
    st.dataframe(df)
