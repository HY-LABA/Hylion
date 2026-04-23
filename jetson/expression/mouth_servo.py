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
		self._pwm: Optional[object] = None

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

		# Jetson.GPIO GPIO.PWM is software PWM and Pin 33 uses BOARD numbering.
		GPIO.setwarnings(False)
		GPIO.setmode(GPIO.BOARD)
		GPIO.setup(self.pin, GPIO.OUT)

		self._pwm = GPIO.PWM(self.pin, self.pwm_hz)
		self._pwm.start(self._angle_to_duty(self.closed_angle))
		self._initialized = True
		time.sleep(0.15)

	def move_to_angle(self, angle: float) -> None:
		if not self._available:
			return
		if not self._initialized:
			self.initialize()
		if not self._pwm:
			return

		duty = self._angle_to_duty(angle)
		with self._lock:
			self._pwm.ChangeDutyCycle(duty)

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
			self.move_to_angle(angle)
			time.sleep(self.move_interval_sec)

		self.move_to_angle(self.closed_angle)

	def cleanup(self) -> None:
		if not self._available:
			return
		if not self._initialized:
			return

		try:
			if self._pwm:
				self._pwm.ChangeDutyCycle(self._angle_to_duty(self.closed_angle))
				time.sleep(0.05)
				self._pwm.stop()
		finally:
			# Do cleanup only for this pin to avoid side effects on other GPIO users.
			GPIO.cleanup(self.pin)
			self._initialized = False
			self._pwm = None
