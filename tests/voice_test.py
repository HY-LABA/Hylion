import os
import urllib.request
import urllib.parse
from dotenv import load_dotenv

load_dotenv()

client_id = os.getenv("Naver_Clova_Speech_Client_ID", "").strip().replace('"', '')
client_secret = os.getenv("Naver_Clova_Speech_Client_Secret", "").strip().replace('"', '')

# 이번에는 꼭 'gihyo'나 'ara'로 테스트해보세요!
SPEAKER = "ndain" 
TEXT = "안녕! 나는 파란 사자 하이리온이야. 헤더를 추가했으니 이제 목소리가 나올까?"
OUTPUT_FILE = SPEAKER + "_final_test.mp3"

url = "https://naveropenapi.apigw.ntruss.com/tts-premium/v1/tts"

params = {
    "speaker": SPEAKER,
    "volume": "0",
    "speed": "0",
    "pitch": "0",
    "format": "mp3",
    "text": TEXT
}
data = urllib.parse.urlencode(params).encode('utf-8')

request = urllib.request.Request(url, data=data)

# --- 필수 헤더들 ---
request.add_header("X-NCP-APIGW-API-KEY-ID", client_id)
request.add_header("X-NCP-APIGW-API-KEY", client_secret)
# 바로 이 줄이 핵심입니다!
request.add_header("Content-Type", "application/x-www-form-urlencoded") 

try:
    response = urllib.request.urlopen(request)
    print(f"✅ 성공! {SPEAKER} 목소리 생성 완료.")
    with open(OUTPUT_FILE, 'wb') as f:
        f.write(response.read())
    
    if os.name == 'nt':
        os.startfile(OUTPUT_FILE)
    else:
        os.system(f"mpg123 -q {OUTPUT_FILE}")

except Exception as e:
    if hasattr(e, 'read'):
        print(f"❌ 에러 상세: {e.read().decode('utf-8')}")
    else:
        print(f"❌ 일반 에러: {e}")