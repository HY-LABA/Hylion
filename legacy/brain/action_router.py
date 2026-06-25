import json
import time
from typing import Any, Dict, Optional


class ActionRouter:
    """ROS2 publisher wrapper for /hylion/action_json."""

    def __init__(self, topic: str = "/hylion/action_json") -> None:
        self._topic = topic
        self._node: Optional[Any] = None
        self._publisher = None
        self._rclpy = None
        self._string_msg_cls = None

    def start(self) -> None:
        try:
            import rclpy
            from rclpy.node import Node
            from std_msgs.msg import String
        except Exception as exc:
            raise RuntimeError(
                "ROS2 Python environment is not available. "
                "Please source your ROS2 setup and install rclpy/std_msgs."
            ) from exc

        self._rclpy = rclpy
        self._string_msg_cls = String

        if not self._rclpy.ok():
            self._rclpy.init()

        self._node = Node("brain_action_router")
        self._publisher = self._node.create_publisher(String, self._topic, 10)

    def publish_action(self, payload: Dict[str, Any]) -> None:
        if self._node is None or self._publisher is None:
            raise RuntimeError("ActionRouter is not started")

        # Give DDS discovery a short window so first messages are less likely to be dropped.
        time.sleep(0.2)

        msg = self._string_msg_cls()
        msg.data = json.dumps(payload, ensure_ascii=False)
        self._publisher.publish(msg)
        # Let ROS executor process outgoing events.
        self._rclpy.spin_once(self._node, timeout_sec=0.1)

    def close(self) -> None:
        if self._node is not None:
            self._node.destroy_node()
            self._node = None

        if self._rclpy is not None and self._rclpy.ok():
            self._rclpy.shutdown()
