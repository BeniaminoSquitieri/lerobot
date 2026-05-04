**Sandwich BT - Test Guide**

Questa guida e divisa in due parti:
- **Guida 1:** tutto il testabile in simulazione.
- **Guida 2:** tutto il testabile con robot reale, con VLM simulato e con VLM reale.

---

## Guida 1 - Test in simulazione (tutto il testabile)

Prerequisiti
- Python env pronto (consigliato `uv sync`).
- Se usi ROS2 service o VLM stub: sorgente ROS2 + workspace e build delle interfacce.

```bash
source /opt/ros/<distro>/setup.bash
colcon build --packages-select sandwich_bt_interfaces --symlink-install
source install/local_setup.bash
```

### 1) Simulazione locale (senza ROS2)
Testa il flusso mock, transizioni e recoveries senza ROS2.

```bash
python3 src/sandwich_bt_python/simulation.py --command skill:place_first_toast
python3 src/sandwich_bt_python/simulation.py --command skill:place_first_toast --command recovery:recover_place_first_toast
```

### 2) Simulazione come servizio ROS2
Testa il confine ROS2 e la compatibilita con il BT runtime.

```bash
python3 src/sandwich_bt_python/simulation.py --ros2-service
```

Servizi esposti:
- `/sandwich_bt/run_command`
- `/sandwich_bt/get_skill_verification`
- `/sandwich_bt/report_skill_verification`

### 3) Verifica manuale via service call
Testa la pipeline di verifica senza VLM.

```bash
ros2 service call /sandwich_bt/run_command sandwich_bt_interfaces/srv/RunNamedCommand "{kind: 'skill', name: 'place_first_toast', timeout_s: 0.0}"
ros2 service call /sandwich_bt/get_skill_verification sandwich_bt_interfaces/srv/GetSkillVerification "{skill_name: 'place_first_toast'}"
ros2 service call /sandwich_bt/report_skill_verification sandwich_bt_interfaces/srv/ReportSkillVerification "{skill_name: 'place_first_toast', attempt_id: 0, status: 'SUCCESS', message: 'ok', confidence: 0.92}"
```

Note:
- `attempt_id=0` applica il verdetto all’ultimo tentativo pendente.

### 4) VLM simulato (topic)
Testa il percorso topic -> report senza VLM reale.

```bash
python3 src/sandwich_bt_python/vlm_stub.py
ros2 topic pub /sandwich_bt/vlm_sim std_msgs/msg/String "{data: '{\"skill_name\":\"place_first_toast\",\"status\":\"SUCCESS\",\"confidence\":0.95,\"message\":\"ok\"}'}" -1
```

### 5) Test automatici

```bash
uv run pytest tests/sandwich_bt -q
```

Cosa valida questa guida:
- Orchestrazione BT/mock, protocolli ROS2, chiamate di servizio.
- Regole di SUCCESS/FAILURE, recoveries e verification flow.
- **Non** valida hardware, sensori, policy reali, camera/gripper.

---

## Guida 2 - Test con robot reale

Prerequisiti
- Robot connesso e driver avviati.
- ROS2 + workspace sorgente e interfacce buildate.

```bash
source /opt/ros/<distro>/setup.bash
colcon build --packages-select sandwich_bt_interfaces --symlink-install
source install/local_setup.bash
```

### 1) Avvio server reale

```bash
python3 src/sandwich_bt_python/server.py
```

Config di default:
- `src/sandwich_bt_python/sandwich_bt_executor.yaml`

### 2) Test skill/recovery su robot reale

```bash
ros2 service call /sandwich_bt/run_command sandwich_bt_interfaces/srv/RunNamedCommand "{kind: 'skill', name: 'place_first_toast', timeout_s: 0.0}"
```

### 3) Robot reale + VLM simulato
Usa lo stub topic per simulare il verdetto di verifica.

```bash
python3 src/sandwich_bt_python/vlm_stub.py
ros2 topic pub /sandwich_bt/vlm_sim std_msgs/msg/String "{data: '{\"skill_name\":\"place_first_toast\",\"status\":\"SUCCESS\",\"confidence\":0.95,\"message\":\"ok\"}'}" -1
```

### 4) Robot reale + VLM reale
Il VLM reale deve chiamare `ReportSkillVerification` con skill e attempt_id.

```bash
ros2 service call /sandwich_bt/report_skill_verification sandwich_bt_interfaces/srv/ReportSkillVerification "{skill_name: 'place_first_toast', attempt_id: 0, status: 'SUCCESS', message: 'vlm ok', confidence: 0.92}"
```

### 5) Query stato verifica

```bash
ros2 service call /sandwich_bt/get_skill_verification sandwich_bt_interfaces/srv/GetSkillVerification "{skill_name: 'place_first_toast'}"
```

Cosa valida questa guida:
- Esecuzione reale della policy e I/O hardware (robot, gripper, sensori).
- Boundary ROS2 e verification flow con VLM simulato o reale.
- Non valida la qualita del VLM se usi lo stub; con VLM reale valida anche la pipeline di verifica esterna.
