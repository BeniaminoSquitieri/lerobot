# Comandi robot day

Usa questo file dall'alto verso il basso. Copia/incolla i comandi così come sono.

## 0. Prerequisiti

Controlla repo, branch e ROS:

```bash
cd /home/bsquitieri/lerobot
git branch --show-current

cd /home/bsquitieri/panda_live_viewer
git branch --show-current

source /opt/ros/jazzy/setup.bash
echo $ROS_DISTRO
```

Atteso:

- `runtime-bt-generation-mvp-c` in `/home/bsquitieri/lerobot`
- `after_lorenzo_meeting` in `/home/bsquitieri/panda_live_viewer`
- `jazzy` come ROS distro

## 1. Build e source workspace lerobot

```bash
cd /home/bsquitieri/lerobot
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
```

Controlli rapidi:

```bash
ros2 interface show lerobot_bt_interfaces/srv/GenerateTaskPlan
ros2 interface show lerobot_bt_interfaces/srv/RunNamedCommand
```

## 2. Terminale A — VLM / Panda server

Apri un terminale dedicato e lascialo aperto.

### A1. Dry-run planner mode, consigliato per primo

Questo deve essere il primo modo usato sul robot day.

```bash
conda activate lerobot
cd /home/bsquitieri/panda_live_viewer

source /opt/ros/jazzy/setup.bash
source /home/bsquitieri/lerobot/install/setup.bash
export PYTHONPATH=/opt/ros/jazzy/lib/python3.12/site-packages:/home/bsquitieri/lerobot/src:$PWD:$PYTHONPATH

python3 -u -m vlm_live.cli \
  --ros-args \
  -p planner_dry_run:=true \
  -p lazy_load_model:=true \
  -p require_generate_plan_service:=true \
  -p verifier_experiment_log_path:=/home/bsquitieri/lerobot/generated_bt/experiments/verifier_events.jsonl
```

Atteso:

- il processo resta attivo;
- compare `/lerobot_bt/generate_plan`;
- Qwen o il modello non devono caricarsi.

### A2. Live VLM planner mode, solo dopo che il dry-run funziona

```bash
conda activate lerobot
cd /home/bsquitieri/panda_live_viewer

source /opt/ros/jazzy/setup.bash
source /home/bsquitieri/lerobot/install/setup.bash
export PYTHONPATH=/opt/ros/jazzy/lib/python3.12/site-packages:/home/bsquitieri/lerobot/src:$PWD:$PYTHONPATH

python3 -u -m vlm_live.cli \
  --ros-args \
  -p planner_dry_run:=false \
  -p lazy_load_model:=true \
  -p require_generate_plan_service:=true \
  -p verifier_experiment_log_path:=/home/bsquitieri/lerobot/generated_bt/experiments/verifier_events.jsonl
```

Usalo solo dopo questi tre passaggi:

- service dry-run OK;
- BT generation dry-run OK;
- `robot_live` con planner dry-run OK.

## 3. Terminale B — Skill server reale

Apri un secondo terminale dedicato e lascialo aperto.

Comando per `make_sandwich`:

```bash
conda activate lerobot
cd /home/bsquitieri/lerobot

source /opt/ros/jazzy/setup.bash
source install/setup.bash
export PYTHONPATH=/opt/ros/jazzy/lib/python3.12/site-packages:$PWD/src:$PYTHONPATH

uv run lerobot-bt-skill-server \
  --config_path=src/lerobot_bt_python/make_sandwich_executor.yaml
```

Fallback senza `uv`:

Usalo solo se `uv` non è disponibile e l'ambiente Python ha già tutte le dipendenze richieste.

```bash
conda activate lerobot
cd /home/bsquitieri/lerobot

source /opt/ros/jazzy/setup.bash
source install/setup.bash
export PYTHONPATH=/opt/ros/jazzy/lib/python3.12/site-packages:$PWD/src:$PYTHONPATH

PYTHONPATH=src python3 -m lerobot_bt_python.server \
  --config_path=src/lerobot_bt_python/make_sandwich_executor.yaml
```

Altri task:

```bash
uv run lerobot-bt-skill-server --config_path=src/lerobot_bt_python/make_coffee_executor.yaml
uv run lerobot-bt-skill-server --config_path=src/lerobot_bt_python/set_breakfast_table_executor.yaml
uv run lerobot-bt-skill-server --config_path=src/lerobot_bt_python/prepare_picnic_bag_executor.yaml
uv run lerobot-bt-skill-server --config_path=src/lerobot_bt_python/items_in_drawer_executor.yaml
```

## 4. Terminale C — Check servizi ROS

Apri un terzo terminale. Userai questo terminale per tutti i test BT.

```bash
conda activate lerobot
cd /home/bsquitieri/lerobot

source /opt/ros/jazzy/setup.bash
source install/setup.bash

ros2 service list | grep /lerobot_bt
ros2 service type /lerobot_bt/generate_plan
ros2 service type /lerobot_bt/run
```

Servizi attesi:

```text
/lerobot_bt/generate_plan
/lerobot_bt/run
```

Tipi attesi:

```text
lerobot_bt_interfaces/srv/GenerateTaskPlan
lerobot_bt_interfaces/srv/RunNamedCommand
```

## 5. Terminale C — Primo test: genera senza eseguire

Questo è il primo trial da lanciare.

```bash
conda activate lerobot
cd /home/bsquitieri/lerobot

source /opt/ros/jazzy/setup.bash
source install/setup.bash
export PYTHONPATH=/opt/ros/jazzy/lib/python3.12/site-packages:$PWD/src:$PYTHONPATH

PYTHON_BIN=python3 scripts/run_icra_runtime_bt_trial.sh make_sandwich dry_run_no_run
```

Atteso:

- chiama Panda `/lerobot_bt/generate_plan`;
- scrive XML, YAML e manifest;
- non avvia il runner;
- stampa un `trial_id`.

## 6. Terminale C — Secondo test: esegui BT sul robot

Solo dopo che la sezione 5 passa e lo skill server è attivo.

```bash
conda activate lerobot
cd /home/bsquitieri/lerobot

source /opt/ros/jazzy/setup.bash
source install/setup.bash
export PYTHONPATH=/opt/ros/jazzy/lib/python3.12/site-packages:$PWD/src:$PYTHONPATH

PYTHON_BIN=python3 scripts/run_icra_runtime_bt_trial.sh make_sandwich robot_live
```

Atteso:

- genera il piano;
- valida;
- scrive XML e YAML;
- lancia il runner C++;
- il BT esegue:

```text
AwaitScene(initial_scene_ready)
DoSkill(place_first_toast)
AwaitScene(pour_ingredient)
AwaitScene(ingredient_poured)
AwaitScene(second_toast_ready)
DoSkill(place_second_toast)
AwaitScene(make_sandwich.task_complete)
```

## 7. Annotare il trial

Il comando precedente stampa un `trial_id` reale, per esempio:

```text
trial_id: make_sandwich__ros-service__20260601T160013__8f93444d
```

Non copiare la parola `trial_id:`. Copia il valore reale dopo `trial_id:`.

Esempio successo:

```bash
cd /home/bsquitieri/lerobot

TRIAL_ID=make_sandwich__ros-service__20260601T160013__8f93444d

python3 scripts/annotate_runtime_bt_trial.py \
  --jsonl generated_bt/experiments/trials.jsonl \
  --trial-id "$TRIAL_ID" \
  --task-success success \
  --outcome-label completed \
  --failure-category none \
  --notes "robot_live completed"
```

Esempio fallimento: service unavailable.

Sostituisci `replace_with_real_trial_id` con il valore reale appena stampato.

```bash
cd /home/bsquitieri/lerobot

TRIAL_ID=replace_with_real_trial_id

python3 scripts/annotate_runtime_bt_trial.py \
  --jsonl generated_bt/experiments/trials.jsonl \
  --trial-id "$TRIAL_ID" \
  --task-success failure \
  --outcome-label aborted \
  --failure-category service_unavailable \
  --notes "panda generate_plan service was not available"
```

Esempio fallimento: skill failed.

Sostituisci `replace_with_real_trial_id` con il valore reale appena stampato.

```bash
cd /home/bsquitieri/lerobot

TRIAL_ID=replace_with_real_trial_id

python3 scripts/annotate_runtime_bt_trial.py \
  --jsonl generated_bt/experiments/trials.jsonl \
  --trial-id "$TRIAL_ID" \
  --task-success failure \
  --outcome-label partial \
  --failure-category skill_failed \
  --notes "robot skill failed during execution"
```

Esempio fallimento: verifier false negative.

Sostituisci `replace_with_real_trial_id` con il valore reale appena stampato.

```bash
cd /home/bsquitieri/lerobot

TRIAL_ID=replace_with_real_trial_id

python3 scripts/annotate_runtime_bt_trial.py \
  --jsonl generated_bt/experiments/trials.jsonl \
  --trial-id "$TRIAL_ID" \
  --task-success failure \
  --outcome-label aborted \
  --failure-category verifier_false_negative \
  --notes "verifier stayed RUNNING although scene appeared ready"
```

## 8. Report e bundle

Report:

```bash
cd /home/bsquitieri/lerobot

python3 scripts/summarize_runtime_bt_experiments.py

python3 scripts/make_icra_runtime_bt_report.py \
  --experiments-dir generated_bt/experiments \
  --out-md generated_bt/experiments/icra_report.md
```

Bundle:

Sostituisci `replace_with_real_trial_id` con il valore reale appena stampato.

```bash
cd /home/bsquitieri/lerobot

TRIAL_ID=replace_with_real_trial_id

python3 scripts/bundle_runtime_bt_trial.py \
  --output-dir generated_bt \
  --trial-id "$TRIAL_ID" \
  --out generated_bt/experiments/bundles/"$TRIAL_ID".tar.gz
```

## 9. Comandi equivalenti per altri task

```bash
cd /home/bsquitieri/lerobot

PYTHON_BIN=python3 scripts/run_icra_runtime_bt_trial.sh make_coffee dry_run_no_run
PYTHON_BIN=python3 scripts/run_icra_runtime_bt_trial.sh make_coffee robot_live

PYTHON_BIN=python3 scripts/run_icra_runtime_bt_trial.sh set_breakfast_table dry_run_no_run
PYTHON_BIN=python3 scripts/run_icra_runtime_bt_trial.sh set_breakfast_table robot_live

PYTHON_BIN=python3 scripts/run_icra_runtime_bt_trial.sh prepare_picnic_bag dry_run_no_run
PYTHON_BIN=python3 scripts/run_icra_runtime_bt_trial.sh prepare_picnic_bag robot_live

PYTHON_BIN=python3 scripts/run_icra_runtime_bt_trial.sh items_in_drawer dry_run_no_run
PYTHON_BIN=python3 scripts/run_icra_runtime_bt_trial.sh items_in_drawer robot_live
```

## 10. Errori comuni

### `/lerobot_bt/generate_plan` mancante

Causa:

- Panda VLM server non attivo;
- oppure Terminale A non ha fatto `source /home/bsquitieri/lerobot/install/setup.bash`.

Fix:

```bash
ros2 service list | grep generate_plan
```

Se manca, riavvia Terminale A in dry-run.

### `/lerobot_bt/run` mancante

Causa:

- skill server non attivo.

Fix:

- avvia Terminale B.

### `qwen_vl_utils` mancante

Causa:

- dipendenze del planner live non disponibili.

Fix:

- usa prima `planner_dry_run:=true`;
- la modalità live richiede le dipendenze VLM.

### `rclpy` mancante nel conda env

Fix:

```bash
export PYTHONPATH=/opt/ros/jazzy/lib/python3.12/site-packages:$PYTHONPATH
```

### errore RetryNode `num_attempts`

Atteso: XML con interi letterali.

```bash
grep -n "RetryUntilSuccessful" generated_bt/trees/make_sandwich.xml
```

Non deve comparire:

```text
num_attempts="{...}"
```

## 11. Ordine sicuro sul robot day

1. Build e source di `lerobot`.
2. Avvia Panda con `planner_dry_run:=true`.
3. Avvia lo skill server reale.
4. Controlla i servizi ROS.
5. Lancia `dry_run_no_run`.
6. Annota il trial.
7. Lancia `robot_live` con planner dry-run.
8. Annota il trial.
9. Genera il report.
10. Solo dopo, riavvia Panda con `planner_dry_run:=false`.