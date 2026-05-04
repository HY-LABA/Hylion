"""
스피커 음성 출력 모듈
- TTS 음성 생성 및 재생
- 입 서보와 동기화
"""

import os
import subprocess
import time
import logging
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# Optional imports
try:
    from gtts import gTTS
    HAS_GTTS = True
except ImportError:
    HAS_GTTS = False

try:
    from mutagen.mp3 import MP3
    HAS_MUTAGEN = True
except ImportError:
    HAS_MUTAGEN = False

logger = logging.getLogger(__name__)

# 저장 디렉토리 설정
def _get_reply_dir():
    """사용 가능한 reply 디렉토리 찾기"""
    candidates = [
        Path("/tmp/hylion_reply"),
        Path(__file__).parent.parent.parent / "data" / "reply",
    ]
    
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            test_file = candidate / ".write_test"
            test_file.touch()
            test_file.unlink()
            return candidate
        except Exception as e:
            logger.debug(f"Cannot use {candidate}: {e}")
            continue
    
    fallback = Path("/tmp/hylion_reply")
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback

REPLY_DIR = _get_reply_dir()
# DEFAULT_CLOVA_SPEAKER: Clova Premium TTS 화자명.
# 감정(emotion) 파라미터 지원 화자 예시 (Clova Premium 기준):
# nara | vara | vmikyung | vdain | vyuna | vgoeun | vdaeseong
# emotion 미지원 화자(예: 현재 기본값 nhajun)는 emotion 값을 보내도 무시됨.
# 정확한 지원 목록과 emotion index(0=중립, 1=슬픔, 2=기쁨, 3=분노 등)는
# 화자별로 다르므로 Clova Premium TTS 공식 문서를 참고해 변경할 것.
DEFAULT_CLOVA_SPEAKER = "nhajun"
DEFAULT_TTS_PROVIDER = "auto"


@dataclass(frozen=True)
class TTSParams:
    """런타임 TTS 파라미터 스냅샷"""

    voice: str = DEFAULT_CLOVA_SPEAKER
    pitch: int = 0
    rate: Optional[int] = None
    speed: int = 0
    volume: int = 0
    audio_format: str = "mp3"
    emotion: int = 0
    emotion_strength: int = 1


def _read_env_file() -> dict:
    """.env 파일을 읽어 key-value 맵 반환"""
    env_path = Path(__file__).parent.parent.parent / ".env"
    env_map = {}

    if not env_path.exists():
        return env_map

    try:
        with env_path.open("r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                env_map[key.strip()] = value.strip().strip('"').strip("'")
    except Exception as e:
        logger.debug(f"Failed to read .env file: {e}")

    return env_map


_DOTENV_CACHE = _read_env_file()


def _get_env_value(key: str, default: str = "") -> str:
    """환경변수 우선, 없으면 .env 캐시 조회"""
    value = os.getenv(key, "").strip().strip('"').strip("'")
    if value:
        return value
    return _DOTENV_CACHE.get(key, default)


class ClovaTTSClient:
    """Naver Clova Premium TTS HTTP 클라이언트"""

    def __init__(self):
        self.client_id = _get_env_value("Naver_Clova_Speech_Client_ID")
        self.client_secret = _get_env_value("Naver_Clova_Speech_Client_Secret")
        self.endpoint = _get_env_value(
            "HYLION_CLOVA_TTS_URL",
            "https://naveropenapi.apigw.ntruss.com/tts-premium/v1/tts",
        )

    @property
    def is_available(self) -> bool:
        return bool(self.client_id and self.client_secret)

    def synthesize(
        self,
        text: str,
        output_file: str,
        voice: str = DEFAULT_CLOVA_SPEAKER,
        pitch: int = 0,
        rate: Optional[int] = None,
        speed: int = -3,
        volume: int = 0,
        audio_format: str = "mp3",
        emotion: int = 0,
        emotion_strength: int = 1,
    ) -> bool:
        if not self.is_available:
            logger.warning("Clova credentials not found. Skip Clova synthesis.")
            return False

        actual_speed = speed if rate is None else rate

        payload = {
            "speaker": voice,
            "text": text,
            "pitch": str(pitch),
            "speed": str(actual_speed),
            "volume": str(volume),
            "format": audio_format,
            "emotion": str(emotion),
            "emotion-strength": str(emotion_strength),
        }
        data = urllib.parse.urlencode(payload).encode("utf-8")
        req = urllib.request.Request(self.endpoint, data=data, method="POST")
        req.add_header("X-NCP-APIGW-API-KEY-ID", self.client_id)
        req.add_header("X-NCP-APIGW-API-KEY", self.client_secret)
        req.add_header("Content-Type", "application/x-www-form-urlencoded")

        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                content = resp.read()
                if not content:
                    logger.error("Clova TTS returned empty audio")
                    return False
                with open(output_file, "wb") as f:
                    f.write(content)
                logger.info("✅ Clova TTS 생성 완료")
                return True
        except Exception as e:
            logger.error(f"❌ Clova TTS 요청 실패: {e}")
            return False


def _find_usb_audio_sink():
    """USB 오디오 출력 장치 자동 감지"""
    try:
        result = subprocess.run(
            ["pactl", "list", "short", "sinks"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            logger.warning("Failed to list audio sinks")
            return None
        
        # USB 관련 싱크 찾기
        for line in result.stdout.strip().split('\n'):
            if not line.strip():
                continue
            
            parts = line.split('\t')
            if len(parts) >= 2:
                sink_name = parts[1]
                # USB 스피커 식별
                if 'usb' in sink_name.lower():
                    logger.info(f"✅ USB 오디오 싱크 감지: {sink_name}")
                    return sink_name
        
        logger.warning("No USB audio sink found")
        return None
        
    except Exception as e:
        logger.warning(f"Error finding USB audio sink: {e}")
        return None


class Speaker:
    """실제 스피커 제어"""
    
    def __init__(
        self,
        device: str = "default",
        enable_lipsync: bool = True,
        tts_provider: str = DEFAULT_TTS_PROVIDER,
        voice: str = DEFAULT_CLOVA_SPEAKER,
        pitch: int = 0,
        rate: Optional[int] = None,
        speed: int = -3,
        volume: int = 0,
        audio_format: str = "mp3",
        emotion: int = 0,
        emotion_strength: int = 1,
    ):
        self.enable_lipsync = enable_lipsync
        self.last_audio_file = None
        self.clova_client = ClovaTTSClient()

        self.tts_provider = self._normalize_tts_provider(tts_provider)
        self.tts_defaults = TTSParams(
            voice=voice,
            pitch=pitch,
            rate=rate,
            speed=speed,
            volume=volume,
            audio_format=audio_format,
            emotion=emotion,
            emotion_strength=emotion_strength,
        )

        if self.tts_provider == "auto":
            self.tts_provider = "clova" if self.clova_client.is_available else "gtts"

        logger.info(
            f"TTS provider: {self.tts_provider} "
            f"(voice={self.tts_defaults.voice}, pitch={self.tts_defaults.pitch}, "
            f"rate={self.tts_defaults.rate}, speed={self.tts_defaults.speed}, "
            f"emotion={self.tts_defaults.emotion}, emotion_strength={self.tts_defaults.emotion_strength})"
        )
        
        # USB 스피커 자동 감지
        usb_sink = _find_usb_audio_sink()
        if usb_sink:
            self.device = usb_sink
            logger.info(f"Using USB audio sink: {usb_sink}")
        else:
            self.device = device
            logger.info(f"Using default audio device: {device}")

    def _normalize_tts_provider(self, tts_provider: str) -> str:
        provider = str(tts_provider or DEFAULT_TTS_PROVIDER).strip().lower()
        if provider in {"auto", "clova", "gtts"}:
            return provider
        logger.warning(f"Unknown tts_provider '{tts_provider}', fallback to '{DEFAULT_TTS_PROVIDER}'")
        return DEFAULT_TTS_PROVIDER

    def _build_output_file(self) -> Path:
        import time as time_module

        timestamp = int(time_module.time() * 1000)
        return REPLY_DIR / f"reply_{timestamp}.mp3"

    def _resolve_tts_params(
        self,
        speaker: str,
        voice: Optional[str],
        pitch: Optional[int],
        rate: Optional[int],
        speed: Optional[int],
        volume: Optional[int],
        audio_format: Optional[str],
        emotion: Optional[int],
        emotion_strength: Optional[int],
    ) -> TTSParams:
        return TTSParams(
            voice=voice or speaker or self.tts_defaults.voice,
            pitch=self.tts_defaults.pitch if pitch is None else pitch,
            rate=self.tts_defaults.rate if rate is None else rate,
            speed=self.tts_defaults.speed if speed is None else speed,
            volume=self.tts_defaults.volume if volume is None else volume,
            audio_format=self.tts_defaults.audio_format if audio_format is None else audio_format,
            emotion=self.tts_defaults.emotion if emotion is None else emotion,
            emotion_strength=self.tts_defaults.emotion_strength if emotion_strength is None else emotion_strength,
        )
        
    def _synthesize_with_gtts(self, reply_text: str, output_file: str) -> bool:
        """gTTS fallback 음성 생성"""
        if not HAS_GTTS:
            logger.error("gTTS not installed")
            return False

        try:
            tts = gTTS(text=reply_text, lang="ko", slow=False)
            tts.save(str(output_file))
            return True
        except Exception as e:
            logger.error(f"❌ gTTS 생성 실패: {e}")
            return False

    def synthesize_reply_audio(
        self,
        reply_text: str,
        speaker: str = DEFAULT_CLOVA_SPEAKER,
        voice: Optional[str] = None,
        pitch: Optional[int] = None,
        rate: Optional[int] = None,
        speed: Optional[int] = None,
        volume: Optional[int] = None,
        audio_format: Optional[str] = None,
        emotion: Optional[int] = None,
        emotion_strength: Optional[int] = None,
    ) -> Optional[str]:
        """TTS 음성 MP3 생성 (Clova 우선, 실패 시 gTTS fallback)"""
        if not reply_text or not reply_text.strip():
            logger.warning("Empty reply text")
            return None

        try:
            REPLY_DIR.mkdir(parents=True, exist_ok=True)

            output_file = self._build_output_file()
            params = self._resolve_tts_params(
                speaker=speaker,
                voice=voice,
                pitch=pitch,
                rate=rate,
                speed=speed,
                volume=volume,
                audio_format=audio_format,
                emotion=emotion,
                emotion_strength=emotion_strength,
            )

            synthesized = False
            if self.tts_provider == "clova":
                synthesized = self.clova_client.synthesize(
                    text=reply_text,
                    output_file=str(output_file),
                    voice=params.voice,
                    pitch=params.pitch,
                    rate=params.rate,
                    speed=params.speed,
                    volume=params.volume,
                    audio_format=params.audio_format,
                    emotion=params.emotion,
                    emotion_strength=params.emotion_strength,
                )
                if not synthesized:
                    logger.warning("Clova TTS 실패, gTTS fallback 시도")

            if not synthesized:
                synthesized = self._synthesize_with_gtts(reply_text, str(output_file))

            if not synthesized:
                return None
            
            self.last_audio_file = str(output_file)
            logger.info(f"✅ TTS 생성 완료: {output_file}")
            return str(output_file)
            
        except Exception as e:
            logger.error(f"❌ TTS 생성 실패: {e}")
            return None
    
    def get_audio_duration_sec(self, audio_file: str) -> float:
        """MP3 파일의 재생 시간(초) 추출"""
        if not HAS_MUTAGEN:
            return 0.0
        
        try:
            audio = MP3(audio_file)
            duration = audio.info.length
            logger.debug(f"Audio duration: {duration:.2f}s")
            return duration
        except Exception as e:
            logger.error(f"Failed to get audio duration: {e}")
            return 0.0
    
    def play_audio_blocking(self, audio_file: str) -> bool:
        """mpg123으로 MP3 재생 (블로킹)"""
        if not os.path.exists(audio_file):
            logger.error(f"Audio file not found: {audio_file}")
            return False
        
        try:
            # PulseAudio 싱크 환경 변수 설정
            env = os.environ.copy()
            if self.device != "default":
                env["PULSE_SINK"] = self.device
                logger.debug(f"Using PulseAudio sink: {self.device}")
            
            result = subprocess.run(
                ["mpg123", "-q", audio_file],
                capture_output=True,
                timeout=300,
                env=env
            )
            
            if result.returncode == 0:
                logger.info(f"✅ 재생 완료: {audio_file}")
                return True
            else:
                logger.error(f"mpg123 failed: {result.stderr.decode()}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("Audio playback timeout")
            return False
        except Exception as e:
            logger.error(f"Play audio error: {e}")
            return False
    
    def speak_with_lipsync(
        self,
        reply_text: str,
        mouth_servo=None,
        speaker: str = DEFAULT_CLOVA_SPEAKER,
        voice: Optional[str] = None,
        pitch: Optional[int] = None,
        rate: Optional[int] = None,
        speed: Optional[int] = None,
        volume: Optional[int] = None,
        audio_format: Optional[str] = None,
        emotion: Optional[int] = None,
        emotion_strength: Optional[int] = None,
    ) -> float:
        """
        음성 합성 → 재생 → 입 서보 동기화

        Returns:
            경과 시간 (초)
        """
        if not reply_text or not reply_text.strip():
            return 0.0

        start_time = time.time()

        # 1. 음성 합성
        audio_file = self.synthesize_reply_audio(
            reply_text=reply_text,
            speaker=speaker,
            voice=voice,
            pitch=pitch,
            rate=rate,
            speed=speed,
            volume=volume,
            audio_format=audio_format,
            emotion=emotion,
            emotion_strength=emotion_strength,
        )
        if not audio_file:
            duration = len(reply_text) / 10.0
            time.sleep(duration)
            return time.time() - start_time
        
        # 2. 재생 시간 추출
        duration = self.get_audio_duration_sec(audio_file)
        if duration <= 0:
            duration = len(reply_text) / 10.0
        
        # 3. 입 서보 시작 (lip-sync 스레드)
        lipsync_thread = None
        if self.enable_lipsync and mouth_servo:
            try:
                import threading
                stop_event = threading.Event()
                lipsync_thread = threading.Thread(
                    target=mouth_servo.run_lipsync_for_duration,
                    args=(duration, stop_event),
                    daemon=True
                )
                lipsync_thread.start()
                logger.debug("Lip-sync thread started")
            except Exception as e:
                logger.warning(f"Failed to start lip-sync: {e}")
                lipsync_thread = None
        
        # 4. 음성 재생 (블로킹)
        self.play_audio_blocking(audio_file)
        
        # 5. 입 서보 스레드 종료 대기
        if lipsync_thread and lipsync_thread.is_alive():
            try:
                lipsync_thread.join(timeout=duration + 1.0)
                logger.debug("Lip-sync thread finished")
            except Exception as e:
                logger.warning(f"Lip-sync thread join failed: {e}")
        
        return time.time() - start_time


class MockSpeaker:
    """테스트용 Mock 스피커"""
    
    def __init__(self, device: str = "mock", enable_lipsync: bool = True):
        self.enable_lipsync = enable_lipsync
        self.last_text = None
        self.tts_defaults = TTSParams()
        self.device = device
        logger.info(f"Mock speaker initialized with device: {device}")
        
    def synthesize_reply_audio(
        self,
        reply_text: str,
        speaker: str = DEFAULT_CLOVA_SPEAKER,
        voice: Optional[str] = None,
        pitch: Optional[int] = None,
        rate: Optional[int] = None,
        speed: Optional[int] = None,
        volume: Optional[int] = None,
        audio_format: Optional[str] = None,
        emotion: Optional[int] = None,
        emotion_strength: Optional[int] = None,
    ) -> Optional[str]:
        self.last_text = reply_text
        logger.info(f"[MOCK] TTS: {reply_text}")
        return f"mock://{len(reply_text)}"
    
    def get_audio_duration_sec(self, audio_file: str) -> float:
        if audio_file.startswith("mock://"):
            length = int(audio_file.split("://")[1])
            return length / 10.0
        return 0.0
    
    def play_audio_blocking(self, audio_file: str) -> bool:
        duration = self.get_audio_duration_sec(audio_file)
        logger.info(f"[MOCK] Playing for {duration:.2f}s: {audio_file}")
        time.sleep(duration)
        return True
    
    def speak_with_lipsync(
        self,
        reply_text: str,
        mouth_servo=None,
        speaker: str = DEFAULT_CLOVA_SPEAKER,
        voice: Optional[str] = None,
        pitch: Optional[int] = None,
        rate: Optional[int] = None,
        speed: Optional[int] = None,
        volume: Optional[int] = None,
        audio_format: Optional[str] = None,
        emotion: Optional[int] = None,
        emotion_strength: Optional[int] = None,
    ) -> float:
        """Mock: 텍스트 출력 및 대기"""
        if not reply_text or not reply_text.strip():
            return 0.0

        start_time = time.time()

        audio_file = self.synthesize_reply_audio(
            reply_text=reply_text,
            speaker=speaker,
            voice=voice,
            pitch=pitch,
            rate=rate,
            speed=speed,
            volume=volume,
            audio_format=audio_format,
            emotion=emotion,
            emotion_strength=emotion_strength,
        )
        duration = self.get_audio_duration_sec(audio_file)
        
        if self.enable_lipsync and mouth_servo:
            try:
                mouth_servo.speak(duration=duration)
            except Exception as e:
                logger.warning(f"[MOCK] Mouth servo failed: {e}")
        
        self.play_audio_blocking(audio_file)
        
        if self.enable_lipsync and mouth_servo:
            try:
                mouth_servo.stop()
            except Exception as e:
                logger.warning(f"[MOCK] Mouth servo stop failed: {e}")
        
        return time.time() - start_time


def build_tts_backend(
    is_online: bool = True,
    speaker: str = DEFAULT_CLOVA_SPEAKER,
    use_mock: bool = False,
    tts_provider: str = DEFAULT_TTS_PROVIDER,
    device: str = "default",
    enable_lipsync: bool = True,
    voice: Optional[str] = None,
    pitch: int = 0,
    rate: Optional[int] = None,
    speed: int = 0,
    volume: int = 0,
    audio_format: str = "mp3",
    emotion: int = 0,
    emotion_strength: int = 1,
):
    """
    TTS 백엔드 생성
    
    Args:
        is_online: 온라인 모드 여부
        speaker: 화자명 (ClovaTTS 사용 시)
        use_mock: Mock 모드 여부
        tts_provider: auto/clova/gtts
        device: 오디오 출력 장치명
        enable_lipsync: 입 서보 동기화 사용 여부
    
    Returns:
        Speaker 또는 MockSpeaker 인스턴스
    """
    if use_mock:
        logger.info("✅ MockSpeaker 생성")
        return MockSpeaker(device=device, enable_lipsync=enable_lipsync)
    else:
        logger.info(f"✅ Speaker 생성 (device: {device}, tts_provider: {tts_provider})")
        return Speaker(
            device=device,
            enable_lipsync=enable_lipsync,
            tts_provider=tts_provider,
            voice=voice or speaker,
            pitch=pitch,
            rate=rate,
            speed=speed,
            volume=volume,
            audio_format=audio_format,
            emotion=emotion,
            emotion_strength=emotion_strength,
        )
