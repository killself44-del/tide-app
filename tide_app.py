import streamlit as st
import requests
import math
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# --- 1. 기본 설정 ---
st.set_page_config(page_title="전국 물때 & 날씨", page_icon="🌊")
load_dotenv()

# 안전한 키 로드
def get_secret(key_name):
    try:
        if key_name in st.secrets: return st.secrets[key_name]
    except: pass
    return os.getenv(key_name)

KAKAO_KEY = get_secret("KAKAO_API_KEY")
KHOA_KEY = get_secret("KHOA_API_KEY")
WEATHER_KEY = get_secret("WEATHER_API_KEY")

# --- 2. 데이터 & 헬퍼 함수 ---

# 기상청 격자 변환 함수 (위경도 -> x,y 좌표)
def dfs_xy_conv(v1, v2):
    RE = 6371.00877; GRID = 5.0; SLAT1 = 30.0; SLAT2 = 60.0; OLON = 126.0; OLAT = 38.0; XO = 43; YO = 136
    DEGRAD = math.pi / 180.0; RADDEG = 180.0 / math.pi
    re = RE / GRID; slat1 = SLAT1 * DEGRAD; slat2 = SLAT2 * DEGRAD; olon = OLON * DEGRAD; olat = OLAT * DEGRAD
    sn = math.tan(math.pi * 0.25 + slat2 * 0.5) / math.tan(math.pi * 0.25 + slat1 * 0.5)
    sn = math.log(math.cos(slat1) / math.cos(slat2)) / math.log(sn)
    sf = math.tan(math.pi * 0.25 + slat1 * 0.5); sf = math.pow(sf, sn) * math.cos(slat1) / sn
    ro = math.tan(math.pi * 0.25 + olat * 0.5); ro = re * sf / math.pow(ro, sn)
    ra = math.tan(math.pi * 0.25 + v1 * DEGRAD * 0.5); ra = re * sf / math.pow(ra, sn)
    theta = v2 * DEGRAD - olon
    if theta > math.pi: theta -= 2.0 * math.pi
    if theta < -math.pi: theta += 2.0 * math.pi
    theta *= sn
    return int(math.floor(ra * math.sin(theta) + XO + 0.5)), int(math.floor(ro - ra * math.cos(theta) + YO + 0.5))

# 바람 세기 시각화
def get_wind_visual(speed_str):
    try:
        speed = float(speed_str)
        if speed <= 4: return "🍃 약함 (잔잔)", "#4CAF50"
        elif speed <= 8: return "🌬️ 약간 강함 (선선)", "#2196F3"
        elif speed <= 13: return "💨 강함 (주의)", "#FF9800"
        else: return "🌪️ 매우 강함 (위험!)", "#F44336"
    except:
        return "정보 없음", "gray"

# 하늘 상태 변환
def get_sky_condition(sky_code, pty_code):
    if pty_code != '0':
        pty_dict = {'1':'비 🌧️', '2':'비/눈 🌧️❄️', '3':'눈 ❄️', '5':'빗방울 💧', '6':'빗방울/눈날림 💧❄️', '7':'눈날림 ❄️'}
        return pty_dict.get(pty_code, "")
    else:
        sky_dict = {'1':'맑음 ☀️', '3':'구름많음 ⛅', '4':'흐림 ☁️'}
        return sky_dict.get(sky_code, "")

# --- 3. 전국 조위관측소 데이터 (전체 포함) ---
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

# --- 4. API 호출 및 검색 함수 ---

# 1. 카카오맵 좌표 찾기
def get_coordinates(place_name):
    if not KAKAO_KEY: return None, None
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_KEY}"}
    try:
        response = requests.get(url, headers=headers, params={"query": place_name}, timeout=5)
        data = response.json()
        if data.get('documents'): return float(data['documents'][0]['y']), float(data['documents'][0]['x'])
    except: pass
    return None, None

# 2. 가장 가까운 관측소 찾기
def find_nearest_station(lat, lon):
    min_dist = float('inf')
    nearest = None
    for station in STATIONS:
        dist = math.sqrt((station['lat'] - lat)**2 + (station['lon'] - lon)**2)
        if dist < min_dist:
            min_dist = dist
            nearest = station
    return nearest

# 3. 기상청 현재 날씨 (초단기실황)
def get_current_weather(lat, lon):
    if not WEATHER_KEY: return None
    nx, ny = dfs_xy_conv(lat, lon)
    
    # 40분 전 기준 (API 데이터 제공 시점 고려)
    now = datetime.now() - timedelta(minutes=40) 
    base_date = now.strftime("%Y%m%d")
    base_time = now.strftime("%H00")

    url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst"
    params = {
        "serviceKey": WEATHER_KEY, "pageNo": "1", "numOfRows": "10", "dataType": "JSON",
        "base_date": base_date, "base_time": base_time, "nx": nx, "ny": ny
    }
    try:
        response = requests.get(url, params=params, timeout=5)
        items = response.json()['response']['body']['items']['item']
        weather_data = {}
        for item in items:
            weather_data[item['category']] = item['obsrValue']
        return weather_data
    except: return None

# 4. KHOA 물때 가져오기
def get_tide_data(station_code, date_str):
    if not KHOA_KEY: return None
    url = "https://www.khoa.go.kr/api/oceangrid/tideObsPreTab/search.do"
    try:
        response = requests.get(url, params={"ServiceKey": KHOA_KEY, "ObsCode": station_code, "Date": date_str, "ResultType": "json"}, timeout=5)
        data = response.json()
        if "result" in data and "data" in data["result"]: return data["result"]["data"]
    except: pass
    return None

# --- 5. 화면 구성 (UI) ---
st.title("🌊 전국 물때 & 날씨 알리미")
st.markdown("여행 갈 **장소(해수욕장, 항구 등)**를 입력하세요. 가장 가까운 바다의 물때와 날씨를 알려드립니다.")

if not KAKAO_KEY or not KHOA_KEY:
    st.error("🚨 필수 API 키가 없습니다! (카카오, 해양조사원 키 확인 필요)")
    st.stop()

col1, col2 = st.columns([2, 1])
with col1: place = st.text_input("장소 입력", placeholder="예: 을왕리, 방아머리, 격포항")
with col2: target_date = st.date_input("날짜 선택", datetime.now())

if st.button("검색하기", type="primary") and place:
    with st.spinner(f"🔍 '{place}' 탐색 중..."):
        # 1. 좌표 찾기
        lat, lon = get_coordinates(place)
        
        if lat and lon:
            # 2. 가장 가까운 관측소 찾기
            station = find_nearest_station(lat, lon)
            
            # 3. 날씨 가져오기
            weather = get_current_weather(lat, lon)
            
            # --- 결과 화면 ---
            st.divider()
            st.success(f"📍 **'{place}'** 위치 발견! (가까운 관측소: **{station['name']}**)")
            
            # [날씨 섹션]
            if weather:
                st.subheader(f"🌤️ 현재 날씨 ({station['name']} 부근)")
                temp = weather.get('T1H', '-')
                wind_spd = weather.get('WSD', '0')
                sky = get_sky_condition(weather.get('SKY', '1'), weather.get('PTY', '0'))
                wind_text, wind_color = get_wind_visual(wind_spd)

                wc1, wc2, wc3 = st.columns(3)
                wc1.metric("기온", f"{temp}℃")
                wc2.metric("하늘 상태", sky)
                with wc3:
                    st.markdown("**바람 세기**")
                    st.markdown(f"<h3 style='color:{wind_color}; margin:0;'>{wind_text}</h3>", unsafe_allow_html=True)
                    st.caption(f"풍속: {wind_spd} m/s")
            elif WEATHER_KEY:
                st.warning("⚠️ 날씨 정보를 가져오는 중입니다. (잠시 후 다시 시도해보세요)")
            
            # [물때 섹션]
            tide_data = get_tide_data(station['code'], target_date.strftime("%Y%m%d"))
            
            st.subheader(f"📅 {target_date.strftime('%m월 %d일')} 물때표")
            if tide_data:
                # 모바일에서도 보기 좋게 3~4개씩 줄바꿈
                cols = st.columns(4)
                for idx, item in enumerate(tide_data):
                    col_idx = idx % 4
                    time_str = item['tph_time'][11:16]
                    height = item['tph_level']
                    tide_type = item['hl_code']
                    
                    if tide_type == "고조":
                        cols[col_idx].error(f"🔴 **만조**\n\n⏰ {time_str}\n\n🌊 {height}cm")
                    else:
                        cols[col_idx].info(f"🔵 **간조**\n\n⏰ {time_str}\n\n📉 {height}cm")
                st.caption("자료제공: 국립해양조사원(KHOA) / 기상청")
            else:
                st.warning("해당 날짜의 조석 예보가 없습니다.")
        else:
            st.error("장소를 찾을 수 없습니다. (카카오맵에서도 못 찾는 곳입니다 😭)")
