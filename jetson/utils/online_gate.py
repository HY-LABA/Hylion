"""Sticky online/offline state machine for the coordinator.

Original behaviour called :func:`is_online` once per wake activation, which
on a disconnected wifi paid the 4-target × 1.5 s timeout cost (~6 s) inside
every "Hey Hyleon" → response path. :class:`OnlineGate` collapses that into a
single probe whose result is reused until either the caller reports a failure
(``report_online_failure``) or the cached state has been ``False`` for long
enough that we should retry — both knobs share the same cooldown value so the
retry cadence and the post-failure mute cadence stay symmetric.

The gate intentionally probes lazily (only when :meth:`is_active` is called)
to avoid a background thread; coordinator drives it from the main loop, which
is invoked exactly when an answer is needed, so freshness is naturally bounded
to the cooldown window.
"""

from __future__ import annotations

import time
from typing import Callable

from jetson.utils.network import is_online as _default_probe


class OnlineGate:
	def __init__(
		self,
		cooldown_sec: float = 60.0,
		probe_fn: Callable[[], bool] = _default_probe,
	) -> None:
		self._cooldown_sec = cooldown_sec
		self._probe_fn = probe_fn
		self._cached_state = probe_fn()
		self._last_check = time.monotonic()
		self._failure_latched_until = 0.0

	def is_active(self) -> bool:
		"""Whether the online path should be tried right now.

		``True`` means callers should construct online backends; ``False``
		means offline. The freshness contract: returned state was either probed
		within the last ``cooldown_sec`` or is being held False explicitly via
		:meth:`report_online_failure`.
		"""
		now = time.monotonic()
		if now < self._failure_latched_until:
			return False
		cooldown_just_expired = self._failure_latched_until > 0.0
		age_expired = (now - self._last_check) >= self._cooldown_sec
		if cooldown_just_expired or age_expired:
			self._cached_state = self._probe_fn()
			self._last_check = now
			if cooldown_just_expired:
				self._failure_latched_until = 0.0
		return self._cached_state

	def report_online_failure(self) -> None:
		"""Tell the gate that an online attempt just failed, so subsequent
		:meth:`is_active` calls return False for one cooldown window."""
		self._failure_latched_until = time.monotonic() + self._cooldown_sec
		self._cached_state = False
