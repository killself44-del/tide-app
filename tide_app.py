import streamlit as st
import requests
import math
from datetime import datetime
import os
from dotenv import load_dotenv

# 1. 환경설정 및 키 로드
st.set_page_config(page_title="전국 물때 알리미", page_icon="🌊")
load_dotenv()

def get_secret(key_name):
    try:
        if key_name in st.secrets:
            return st.secrets[key_name]
    except:
        pass
    return os.getenv(key_name)

# 🔑 키 가져오기
KAKAO_KEY = get_secret("KAKAO_API_KEY")
KHOA_KEY = get_secret("KHOA_API_KEY")

# 2. 전국 조위관측소 데이터 (사용자 제공)
STATIONS = [
    {"code": "IE_0060", "name": "이어도", "lat": 32.12277778, "lon": 125.182222},
    {"code": "IE_0062", "name": "옹진소청초", "lat": 37.423056, "lon": 124.738056},
    {"code": "IE_0061", "name": "신안가거초", "lat": 33.941944, "lon": 124.592778},
    {"code": "DT_0001", "name": "인천", "lat": 37.451944, "lon": 126.592222},
    {"code": "DT_0002", "name": "평택", "lat": 36.966944, "lon": 126.822778},
    {"code": "DT_0003", "name": "영광", "lat": 35.426111, "lon": 126.420556},
    {"code": "DT_0004", "name": "제주", "lat": 33.5275, "lon": 126.543056},
    {"code": "DT_0005", "name": "부산", "lat": 35.096389, "lon": 129.035278},
    {"code": "DT_0006", "name": "묵호", "lat": 37.550278, "lon": 129.116389},
    {"code": "DT_0007", "name": "목포", "lat": 34.779722, "lon": 126.375556},
    {"code": "DT_0008", "name": "안산", "lat": 37.192222, "lon": 126.647222},
    {"code": "DT_0010", "name": "서귀포", "lat": 33.24, "lon": 126.561667},
    {"code": "DT_0011", "name": "후포", "lat": 36.6775, "lon": 129.453056},
    {"code": "DT_0012", "name": "속초", "lat": 38.207222, "lon": 128.594167},
    {"code": "DT_0013", "name": "울릉도", "lat": 37.491389, "lon": 130.913611},
    {"code": "DT_0014", "name": "통영", "lat": 34.827778, "lon": 128.434722},
    {"code": "DT_0016", "name": "여수", "lat": 34.747222, "lon": 127.765556},
    {"code": "DT_0017", "name": "대산", "lat": 37.0075, "lon": 126.352778},
    {"code": "DT_0018", "name": "군산", "lat": 35.975556, "lon": 126.563056},
    {"code": "DT_0020", "name": "울산", "lat": 35.501944, "lon": 129.387222},
    {"code": "DT_0021", "name": "추자도", "lat": 33.961944, "lon": 126.300278},
    {"code": "DT_0022", "name": "성산포", "lat": 33.474722, "lon": 126.927778},
    {"code": "DT_0023", "name": "모슬포", "lat": 33.214444, "lon": 126.251111},
    {"code": "DT_0024", "name": "장항", "lat": 36.006944, "lon": 126.6875},
    {"code": "DT_0025", "name": "보령", "lat": 36.406389, "lon": 126.486111},
    {"code": "DT_0026", "name": "고흥발포", "lat": 34.481111, "lon": 127.342778},
    {"code": "DT_0027", "name": "완도", "lat": 34.315556, "lon": 126.759722},
    {"code": "DT_0028", "name": "진도", "lat": 34.377778, "lon": 126.308611},
    {"code": "DT_0029", "name": "거제도", "lat": 34.801389, "lon": 128.699167},
    {"code": "DT_0030", "name": "위도", "lat": 35.618056, "lon": 126.301667},
    {"code": "DT_0031", "name": "거문도", "lat": 34.028333, "lon": 127.308889},
    {"code": "DT_0032", "name": "강화대교", "lat": 37.731944, "lon": 126.522222},
    {"code": "DT_0035", "name": "흑산도", "lat": 34.684167, "lon": 125.435556},
    {"code": "DT_0037", "name": "어청도", "lat": 36.117222, "lon": 125.984722},
    {"code": "DT_0038", "name": "굴업도", "lat": 37.194444, "lon": 125.995},
    {"code": "DT_0043", "name": "영흥도", "lat": 37.23861111, "lon": 126.4286111},
    {"code": "DT_0044", "name": "영종대교", "lat": 37.545556, "lon": 126.584444},
    {"code": "DT_0049", "name": "광양", "lat": 34.903672, "lon": 127.754836},
    {"code": "DT_0050", "name": "태안", "lat": 36.91305556, "lon": 126.2388889},
    {"code": "DT_0051", "name": "서천마량", "lat": 36.12888889, "lon": 126.4952778},
    {"code": "DT_0052", "name": "인천송도", "lat": 37.33805556, "lon": 126.5861111},
    {"code": "DT_0055", "name": "순천만", "lat": 34.88411111, "lon": 127.5125556},
    {"code": "DT_0056", "name": "부산항신항", "lat": 35.0775, "lon": 128.786944},
    {"code": "DT_0057", "name": "동해항", "lat": 37.494722, "lon": 129.143889},
    {"code": "DT_0058", "name": "경인항", "lat": 37.560833, "lon": 126.601111},
    {"code": "DT_0061", "name": "삼천포", "lat": 34.924167, "lon": 128.069722},
    {"code": "DT_0062", "name": "마산", "lat": 35.1975, "lon": 128.576389},
    {"code": "DT_0063", "name": "가덕도", "lat": 35.024178, "lon": 128.810933},
    {"code": "DT_0065", "name": "덕적도", "lat": 37.226333, "lon": 126.156556},
    {"code": "DT_0066", "name": "향화도", "lat": 35.167667, "lon": 126.359556},
    {"code": "DT_0067", "name": "안흥", "lat": 36.67463889, "lon": 126.1295556},
    {"code": "DT_0091", "name": "포항", "lat": 36.047128, "lon": 129.383806},
    {"code": "DT_0092", "name": "여호항", "lat": 34.661944, "lon": 127.469167},
    {"code": "DT_0093", "name": "소무의도", "lat": 37.373069, "lon": 126.440066},
    {"code": "DT_0094", "name": "서거차도", "lat": 34.25142222, "lon": 125.91545}
]

# 3. ⭐️ [카카오맵 API 사용] 정확도 100%
def get_coordinates(place_name):
    if not KAKAO_KEY:
        return None, None
        
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_KEY}"}
    params = {"query": place_name}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=5)
        data = response.json()
        
        if data.get('documents'):
            # 첫 번째 검색 결과 가져오기
            result = data['documents'][0]
            return float(result['y']), float(result['x']) # Lat, Lon
            
    except Exception as e:
        pass
        
    return None, None

def find_nearest_station(lat, lon):
    min_dist = float('inf')
    nearest = None
    for station in STATIONS:
        dist = math.sqrt((station['lat'] - lat)**2 + (station['lon'] - lon)**2)
        if dist < min_dist:
            min_dist = dist
            nearest = station
    return nearest

def get_tide_data(station_code, date_str):
    if not KHOA_KEY:
        return None
    url = "https://www.khoa.go.kr/api/oceangrid/tideObsPreTab/search.do"
    params = {
        "ServiceKey": KHOA_KEY,
        "ObsCode": station_code,
        "Date": date_str,
        "ResultType": "json"
    }
    try:
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        if "result" in data and "data" in data["result"]:
            return data["result"]["data"]
    except:
        pass
    return None

# 4. 화면 구성
st.title("🌊 전국 물때 알리미")
st.markdown("여행 갈 **장소 이름**을 입력하세요. (예: 을왕리, 방아머리, 우리집)")

if not KAKAO_KEY or not KHOA_KEY:
    st.error("🚨 API 키가 설정되지 않았습니다. [Secrets]에 KAKAO_API_KEY와 KHOA_API_KEY를 넣어주세요.")
    st.stop()

col1, col2 = st.columns([2, 1])
with col1:
    place = st.text_input("장소 입력", placeholder="예: 방아머리 해수욕장, 을왕리, 속초")
with col2:
    target_date = st.date_input("날짜 선택", datetime.now())

if st.button("물때 검색하기", type="primary"):
    if not place:
        st.warning("장소를 입력해주세요.")
    else:
        with st.spinner(f"🔍 '{place}' 위치를 찾는 중..."):
            lat, lon = get_coordinates(place)
            
            if lat and lon:
                station = find_nearest_station(lat, lon)
                tide_data = get_tide_data(station['code'], target_date.strftime("%Y%m%d"))
                
                st.divider()
                st.success(f"📍 **'{place}'** 위치 발견! (가까운 관측소: {station['name']})")
                
                if tide_data:
                    st.subheader(f"📅 {target_date.strftime('%Y년 %m월 %d일')} 물때표")
                    
                    cols = st.columns(len(tide_data))
                    for idx, item in enumerate(tide_data):
                        time_str = item['tph_time'][11:16]
                        height = item['tph_level']
                        tide_type = item['hl_code']
                        
                        if idx % 4 == 0 and idx != 0:
                            st.write("")
                            
                        if tide_type == "고조":
                            st.error(f"🔴 **만조**\n\n⏰ {time_str}\n\n🌊 {height}cm")
                        else:
                            st.info(f"🔵 **간조**\n\n⏰ {time_str}\n\n📉 {height}cm")
                            
                    st.caption("자료제공: 국립해양조사원 / 위치검색: Kakao Map")
                else:
                    st.warning("해당 날짜의 조석 예보가 없습니다.")
            else:
                st.error("장소를 찾을 수 없습니다. (카카오맵에서도 못 찾는 곳입니다 😭)")
