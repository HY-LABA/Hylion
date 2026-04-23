from __future__ import annotations

import random
import threading
import time
from typing import Optional

try:
	import Jetson.GPIO as GPIO  # type: ignore[import-not-found]
except Exception:  # pragma: no cover - Jetson hardware optional on dev machines
	GPIO = None


class MouthServoController:
	"""Software-PWM controller for MG90S mouth (jaw) servo on Jetson Pin 33."""

	# parameters: MG90S defaults on Jetson 40-pin header (physical Pin 33)
	def __init__(
		self,
		pin: int = 33,
		pwm_hz: int = 50,
		servo_model: str = "MG90S",
		min_pulse_ms: float = 0.5,
		max_pulse_ms: float = 2.5,
		closed_angle: float = 0.0,
		open_angle_min: float = 8.0,
		open_angle_max: float = 30.0,
		move_interval_sec: float = 0.07,
	) -> None:
		self.pin = pin
		self.pwm_hz = pwm_hz
		self.servo_model = servo_model
		self.min_pulse_ms = min_pulse_ms
		self.max_pulse_ms = max_pulse_ms
		self.closed_angle = closed_angle
		self.open_angle_min = open_angle_min
		self.open_angle_max = open_angle_max
		self.move_interval_sec = move_interval_sec

		self._lock = threading.Lock()
		self._initialized = False
		self._available = GPIO is not None

	@property
	def is_available(self) -> bool:
		return self._available

	def _angle_to_duty(self, angle: float) -> float:
		angle = max(0.0, min(180.0, angle))
		# Convert angle -> duty using configurable pulse range (MG90S calibration).
		pulse_ms = self.min_pulse_ms + (angle / 180.0) * (self.max_pulse_ms - self.min_pulse_ms)
		period_ms = 1000.0 / float(self.pwm_hz)
		return (pulse_ms / period_ms) * 100.0

	def initialize(self) -> None:
		if not self._available or self._initialized:
			return

		# Pin 33 is controlled with direct output pulses, matching the working test script.
		GPIO.setwarnings(False)
		GPIO.setmode(GPIO.BOARD)
		GPIO.setup(self.pin, GPIO.OUT)
		self._initialized = True
		time.sleep(0.15)

	def _pulse_once(self, pulse_ms: float) -> None:
		GPIO.output(self.pin, GPIO.HIGH)
		time.sleep(max(0.0, pulse_ms) / 1000.0)
		GPIO.output(self.pin, GPIO.LOW)
		time.sleep(max(0.0, 1000.0 / float(self.pwm_hz) - pulse_ms) / 1000.0)

	def _drive_angle_for_duration(self, angle: float, duration_sec: float) -> None:
		if duration_sec <= 0:
			return

		pulse_ms = self.min_pulse_ms + (max(0.0, min(180.0, angle)) / 180.0) * (self.max_pulse_ms - self.min_pulse_ms)
		cycles = max(1, int(duration_sec * float(self.pwm_hz)))
		for _ in range(cycles):
			self._pulse_once(pulse_ms)

	def move_to_angle(self, angle: float) -> None:
		if not self._available:
			return
		if not self._initialized:
			self.initialize()
		with self._lock:
			self._drive_angle_for_duration(angle, self.move_interval_sec)

	def run_lipsync_for_duration(self, duration_sec: float, stop_event: threading.Event) -> None:
		if duration_sec <= 0:
			return
		if not self._available:
			time.sleep(duration_sec)
			return

		self.initialize()
		end_ts = time.monotonic() + duration_sec

		while time.monotonic() < end_ts and not stop_event.is_set():
			angle = random.uniform(self.open_angle_min, self.open_angle_max)
			remaining = end_ts - time.monotonic()
			self._drive_angle_for_duration(angle, min(self.move_interval_sec, max(0.0, remaining)))

		self._drive_angle_for_duration(self.closed_angle, min(self.move_interval_sec, max(0.0, end_ts - time.monotonic())))

	def cleanup(self) -> None:
		if not self._available:
			return
		if not self._initialized:
			return

		try:
			self._drive_angle_for_duration(self.closed_angle, 0.08)
		finally:
			# Do cleanup only for this pin to avoid side effects on other GPIO users.
			GPIO.cleanup(self.pin)
			self._initialized = False


def cleanup_gpio(pin: Optional[int] = None) -> None:
	"""Best-effort GPIO cleanup used by the coordinator shutdown path."""
	if GPIO is None:
		return

	try:
		if pin is None:
			GPIO.cleanup()
		else:
			GPIO.cleanup(pin)
	except Exception:
		pass
