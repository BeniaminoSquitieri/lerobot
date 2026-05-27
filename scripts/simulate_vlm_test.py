#!/usr/bin/env python3
"""
Simula la comunicazione BT → VLM senza robot fisico.

Pubblica UNA richiesta su /lerobot_bt/vlm_request e aspetta
la risposta su /lerobot_bt/vlm_result. Stampa tutto ciò che arriva.

Uso:
  python3 scripts/simulate_vlm_test.py
"""

import json
import sys
import threading
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


REQUEST_TOPIC = "/lerobot_bt/vlm_request"
RESULT_TOPIC = "/lerobot_bt/vlm_result"
TIMEOUT_S = 60.0


class VlmTester(Node):
    def __init__(self):
        super().__init__("vlm_protocol_tester")
        self.pub = self.create_publisher(String, REQUEST_TOPIC, 10)
        self.sub = self.create_subscription(String, RESULT_TOPIC, self._on_result, 10)
        self.received: list[dict] = []
        self.done = threading.Event()

    def _on_result(self, msg: String):
        try:
            payload = json.loads(msg.data)
        except json.JSONDecodeError:
            print(f"⚠  JSON non valido: {msg.data[:200]}")
            return
        self.received.append(payload)
        status = payload.get("status", "?")
        skill = payload.get("skill_name", "?")
        attempt = payload.get("attempt_id", "?")
        print(f"  ← RISPOSTA: skill={skill}, attempt={attempt}, status={status}")
        msg_text = payload.get("message", "")
        if msg_text:
            print(f"     message: {msg_text[:150]}")

        if status in ("SUCCESS", "FAILURE"):
            self.done.set()

    def publish_request(self, payload: dict):
        msg = String()
        msg.data = json.dumps(payload)
        self.pub.publish(msg)
        skill = payload["skill_name"]
        attempt = payload["attempt_id"]
        task = payload.get("task", "")
        print(f"  → INVIO richiesta: skill={skill}, attempt={attempt}, task='{task}'")


def main():
    rclpy.init()

    # Payload di test — skill con descrizione task
    request = {
        "event": "vlm_check_requested",
        "skill_name": "place_first_toast",
        "attempt_id": 42,
        "status": "PENDING",
        "message": "Awaiting VLM result.",
        "task": "Pick the toast upon the table.",
        "allowed_statuses": [
            "PENDING", "RUNNING", "WAIT_HUMAN",
            "MANUAL_INTERVENTION_REQUIRED", "SUCCESS", "FAILURE",
        ],
        "allowed_next_actions": [
            "CONTINUE", "RETRY_SKILL", "WAIT_HUMAN", "REQUEST_MANUAL_INTERVENTION",
        ],
    }

    tester = VlmTester()
    print("=" * 50)
    print("  TEST COMUNICAZIONE BT → VLM (simulato)")
    print(f"  Request topic: {REQUEST_TOPIC}")
    print(f"  Result topic:  {RESULT_TOPIC}")
    print(f"  Timeout:       {TIMEOUT_S}s")
    print("=" * 50)
    print()

    # Invia la richiesta
    tester.publish_request(request)

    # Aspetta risposte (spin in un thread separato)
    start = time.monotonic()

    def spin():
        while rclpy.ok() and not tester.done.is_set():
            rclpy.spin_once(tester, timeout_sec=0.1)

    spin_thread = threading.Thread(target=spin, daemon=True)
    spin_thread.start()

    # Aspetta fino a SUCCESS/FAILURE o timeout
    if tester.done.wait(timeout=TIMEOUT_S):
        print(f"\n✓ Risposta terminale ricevuta. {len(tester.received)} messaggi totali.")
    else:
        print(f"\n⚠ Timeout ({TIMEOUT_S}s). Ricevuti {len(tester.received)} messaggi:")
        for r in tester.received:
            print(f"     status={r.get('status')}")

    tester.destroy_node()
    rclpy.shutdown()

    if tester.received and any(r.get("status") in ("SUCCESS",) for r in tester.received):
        print("✓ TEST PASSATO")
        return 0
    elif tester.received:
        print("⚠ TEST PARZIALE — il VLM ha risposto ma senza SUCCESS")
        return 0
    else:
        print("✗ TEST FALLITO — nessuna risposta dal VLM")
        return 1


if __name__ == "__main__":
    sys.exit(main())
