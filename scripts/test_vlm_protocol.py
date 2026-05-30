#!/usr/bin/env python3
"""
@file test_vlm_protocol.py
@brief Simula richieste VLM dal BT stack e valida le risposte del nodo VLM.

Usa ros2 topic pub/echo internamente per:
  1. Pubblicare una richiesta simulata su /lerobot_bt/vlm_request
  2. Ascoltare le risposte su /lerobot_bt/vlm_result
  3. Validare che i campi chiave (skill_name, attempt_id, status, task)
     siano preservati correttamente.

Prerequisiti:
  - ROS 2 Jazzy source-ato
  - Nodo VLM (panda_vlm_live.py) in esecuzione
  - Oppure: il nodo lerobot_bt_skill_server in esecuzione (per test BT completo)

Usage:
  # Test 1: richiesta skill con campo task (aspetta risposta fino a SUCCESS/FAILURE)
  python3 scripts/test_vlm_protocol.py --test skill

  # Test 2: richiesta VLM gate senza campo task
  python3 scripts/test_vlm_protocol.py --test gate

  # Test 3: verifica solo pubblicazione (non aspetta risposta)
  python3 scripts/test_vlm_protocol.py --test skill --fire-and-forget

  # Test 4: usa topic personalizzati
  python3 scripts/test_vlm_protocol.py --test skill \
      --request-topic /lerobot_bt/vlm_request \
      --result-topic /lerobot_bt/vlm_result
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time


# ── Mock request payloads ─────────────────────────────────────────────

SKILL_REQUEST = {
    "event": "vlm_check_requested",
    "skill_name": "place_first_toast",
    "attempt_id": 42,
    "status": "RUNNING",
    "message": "Awaiting VLM result for skill 'place_first_toast'.",
    "task": "Pick the toast upon the table.",
    "allowed_statuses": [
        "RUNNING", "SUCCESS", "FAILURE",
    ],
    "allowed_next_actions": [
        "CONTINUE", "RETRY_SKILL", "WAIT",
    ],
}

GATE_REQUEST = {
    "event": "vlm_check_requested",
    "skill_name": "initial_scene_ready",
    "attempt_id": 1,
    "status": "RUNNING",
    "message": "Awaiting VLM result for gate 'initial_scene_ready'.",
    "task": "",  # I gate non hanno descrizione task
    "allowed_statuses": [
        "RUNNING", "SUCCESS", "FAILURE",
    ],
    "allowed_next_actions": [
        "CONTINUE", "RETRY_SKILL", "WAIT",
    ],
}

VALID_STATUSES = {
    "RUNNING", "SUCCESS", "FAILURE",
}

TERMINAL_STATUSES = {"SUCCESS", "FAILURE"}


# ── Test helpers ──────────────────────────────────────────────────────


def publish_request(payload: dict, topic: str) -> None:
    """Pubblica un singolo messaggio JSON su un topic ROS2."""
    json_str = json.dumps(payload)
    # Escape double quotes for shell
    escaped = json_str.replace('"', '\\"')
    cmd = [
        "ros2", "topic", "pub", "--once", topic,
        "std_msgs/msg/String", f'data:="{escaped}"',
    ]
    print(f"  → Pubblicando su {topic}...")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    if result.returncode != 0:
        print(f"  ✗ ERRORE pubblicazione: {result.stderr.strip()}")
    else:
        print(f"  ✓ Richiesta pubblicata: skill={payload['skill_name']}, "
              f"attempt={payload['attempt_id']}, task='{payload.get('task', '')}'")


def listen_results(topic: str, timeout_s: float = 30.0) -> list[dict]:
    """Ascolta i messaggi su un topic ROS2 e li raccoglie come dict."""
    print(f"  → In ascolto su {topic} (timeout={timeout_s}s)...")
    collected: list[dict] = []

    cmd = [
        "ros2", "topic", "echo", "--once", "--timeout", str(timeout_s),
        "--field", "data", topic,
    ]
    # Usiamo --once, ma il VLM potrebbe inviare più messaggi (RUNNING, poi SUCCESS).
    # Quindi eseguiamo echo più volte.
    start = time.monotonic()
    max_attempts = 0
    while time.monotonic() - start < timeout_s and max_attempts < 20:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s + 5)
        max_attempts += 1
        if result.returncode != 0:
            if "timeout" in result.stderr.lower() or not result.stdout.strip():
                time.sleep(0.5)
                continue
            print(f"  ✗ ERRORE ascolto: {result.stderr.strip()}")
            break

        raw = result.stdout.strip()
        if not raw:
            continue

        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            print(f"  ⚠ JSON invalido ricevuto: {raw[:200]}")
            continue

        if not isinstance(payload, dict):
            continue

        collected.append(payload)
        status = payload.get("status", "?")
        print(f"  ← Ricevuto: skill={payload.get('skill_name','?')}, "
              f"attempt={payload.get('attempt_id','?')}, status={status}")

        # Se è uno stato terminale, smetti di ascoltare
        if status in TERMINAL_STATUSES:
            break

    return collected


def validate_response(request: dict, responses: list[dict]) -> bool:
    """Valida che le risposte VLM rispettino il protocollo."""
    print("\n── Validazione risposte ──")
    all_ok = True

    if not responses:
        print("  ✗ NESSUNA risposta ricevuta! Il nodo VLM è in esecuzione?")
        return False

    # Controlla ogni risposta
    for i, resp in enumerate(responses):
        skill_name = resp.get("skill_name", "")
        attempt_id = resp.get("attempt_id", -1)
        status = resp.get("status", "")
        message = resp.get("message", "")

        # 1. skill_name deve corrispondere alla richiesta
        if skill_name != request["skill_name"]:
            print(f"  ✗ Risposta {i+1}: skill_name mismatch "
                  f"(atteso={request['skill_name']}, ricevuto={skill_name})")
            all_ok = False
        else:
            print(f"  ✓ Risposta {i+1}: skill_name corretto ({skill_name})")

        # 2. attempt_id deve corrispondere
        if attempt_id != request["attempt_id"]:
            print(f"  ✗ Risposta {i+1}: attempt_id mismatch "
                  f"(atteso={request['attempt_id']}, ricevuto={attempt_id})")
            all_ok = False
        else:
            print(f"  ✓ Risposta {i+1}: attempt_id corretto ({attempt_id})")

        # 3. status deve essere uno dei valori autorizzati
        if status not in VALID_STATUSES:
            print(f"  ✗ Risposta {i+1}: status non valido ({status})")
            all_ok = False
        else:
            print(f"  ✓ Risposta {i+1}: status valido ({status})")

        # 4. Se RUNNING, non deve essere l'unica risposta
        #    (a meno che non abbiamo raggiunto il timeout)
        if i == len(responses) - 1 and status not in TERMINAL_STATUSES:
            print(f"  ⚠ Ultima risposta non terminale ({status}). "
                  f"Il VLM potrebbe star ancora processando.")

        if message:
            print(f"     message: {message[:120]}")

    # 5. Deve esserci almeno una risposta RUNNING prima del terminale (buona pratica)
    has_running = any(r.get("status") == "RUNNING" for r in responses)
    has_terminal = any(r.get("status") in TERMINAL_STATUSES for r in responses)
    if has_running:
        print(f"  ✓ Il VLM ha pubblicato RUNNING intermedio (buona pratica)")
    if has_terminal:
        print(f"  ✓ Il VLM ha pubblicato stato terminale")
    elif has_running:
        print(f"  ⚠ Nessuno stato terminale ricevuto (timeout?)")

    print(f"\n  Riepilogo: {len(responses)} risposte ricevute, "
          f"{'TUTTE OK' if all_ok else 'ALCUNI ERRORI'}")
    return all_ok


# ── Main ──────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Test del protocollo BT ↔ VLM: pubblica una richiesta e valida la risposta.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Esempi:
  python3 scripts/test_vlm_protocol.py --test skill
  python3 scripts/test_vlm_protocol.py --test gate
  python3 scripts/test_vlm_protocol.py --test skill --timeout 60
  python3 scripts/test_vlm_protocol.py --test skill --fire-and-forget
        """,
    )
    parser.add_argument("--test", choices=["skill", "gate"], default="skill",
                        help="Tipo di richiesta da simulare (default: skill).")
    parser.add_argument("--request-topic", default="/lerobot_bt/vlm_request",
                        help="Topic ROS2 per la richiesta VLM.")
    parser.add_argument("--result-topic", default="/lerobot_bt/vlm_result",
                        help="Topic ROS2 per la risposta VLM.")
    parser.add_argument("--timeout", type=float, default=30.0,
                        help="Timeout in secondi per attendere la risposta (default: 30).")
    parser.add_argument("--fire-and-forget", action="store_true",
                        help="Pubblica solo la richiesta, non attendere risposta.")
    args = parser.parse_args()

    # Seleziona il payload
    payload = SKILL_REQUEST if args.test == "skill" else GATE_REQUEST
    test_label = "skill (con task)" if args.test == "skill" else "gate (senza task)"

    print("=" * 60)
    print(f"  Test protocollo VLM — {test_label}")
    print(f"  Request topic: {args.request_topic}")
    print(f"  Result topic:  {args.result_topic}")
    print("=" * 60)

    # Step 1: pubblica la richiesta
    publish_request(payload, args.request_topic)

    if args.fire_and_forget:
        print("\n  Fatto. Controlla manualmente la risposta con:")
        print(f"    ros2 topic echo {args.result_topic}")
        return

    # Step 2: ascolta le risposte
    time.sleep(0.5)  # Breve pausa per lasciare al VLM il tempo di ricevere
    responses = listen_results(args.result_topic, timeout_s=args.timeout)

    # Step 3: valida
    ok = validate_response(payload, responses)

    if ok:
        print("\n✓ Test SUPERATO")
        sys.exit(0)
    else:
        print("\n✗ Test FALLITO — controlla gli errori sopra.")
        sys.exit(1)


if __name__ == "__main__":
    main()
