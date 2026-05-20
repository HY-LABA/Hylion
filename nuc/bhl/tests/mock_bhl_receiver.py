#!/usr/bin/env python3
"""mock_bhl_receiver.py - bridge.py 가 보내는 UDP 패킷을 받아 디코드/출력.

C 컨트롤러 대용. NUC 에서 bridge 를 띄우고 별도 터미널에서 실행.
주의: 진짜 C 컨트롤러와 동시에 띄우면 포트 충돌. 검증용으로만 사용.
"""

import socket
import struct
import time

UDP_PORT = 10011
PACKET_FMT = "<Bfff"
PACKET_SIZE = 13


def main() -> None:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("0.0.0.0", UDP_PORT))
    print(f"listening on UDP 0.0.0.0:{UDP_PORT}")

    last_print = time.time()
    count = 0
    prev_key = None  # (mode, vx_quantized, vy_q, vyaw_q) 로 변화 감지
    while True:
        data, addr = s.recvfrom(64)
        count += 1
        if len(data) != PACKET_SIZE:
            print(f"BAD size {len(data)} from {addr}", flush=True)
            continue
        mode, vx, vy, vyaw = struct.unpack(PACKET_FMT, data)
        now = time.time()
        # 0.05 단위로 양자화해서 같은 명령이면 침묵, 바뀌면 즉시 출력. 1초에 한 번은 heartbeat.
        key = (mode, round(vx, 2), round(vy, 2), round(vyaw, 2))
        if key != prev_key or (now - last_print) >= 1.0:
            label = "CHANGE" if key != prev_key else "tick"
            print(f"[{now:.3f}] {label:6} mode={mode} vx={vx:+.3f} vy={vy:+.3f} vyaw={vyaw:+.3f} pkts/s~{count}", flush=True)
            last_print = now
            count = 0
            prev_key = key


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nstopped")
