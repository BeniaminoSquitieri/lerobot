# Comandi robot day

Usa questo file dall'alto verso il basso. Copia/incolla i comandi così come sono.

## 0. Prerequisiti

Controlla repo, branch e ROS:

```bash
cd /home/panda-admin/users/sben/lerobot
git branch --show-current

cd /home/panda-admin/users/sben/panda_live_viewer
git branch --show-current
```

Atteso:

- `codex/perception-rgbd-publisher` in `/home/panda-admin/users/sben/lerobot`
- `codex/perception-scene-facts-node` in `/home/panda-admin/users/sben/panda_live_viewer`

Nota: ROS Jazzy è embedded nell'ambiente conda `lerobot_ben`, non in `/opt/ros/jazzy`.

## 1. Requisito critico: CycloneDDS su entrambe le macchine

**Panda hardware richiede CycloneDDS.** Se una sola shell resta su FastDDS o
non esporta la configurazione giusta, le due macchine non si scoprono e
topic/servizi ROS 2 non compaiono in rete.

### 1.1 Crea `~/.ros/cyclonedds.xml` su robot e server GPU

```bash
mkdir -p ~/.ros
cat > ~/.ros/cyclonedds.xml << 'EOF'
<?xml version="1.0" encoding="UTF-8" ?>
<CycloneDDS xmlns="https://cdds.io/config">
  <Domain>
    <General>
      <AllowMulticast>true</AllowMulticast>
    </General>
  </Domain>
</CycloneDDS>
EOF
```

### 1.2 Esporta queste variabili in **ogni** terminale usato

```bash
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI=file://$HOME/.ros/cyclonedds.xml
unset ROS_LOCALHOST_ONLY
```

Errore comune:

- dimenticare questi export in un solo terminale;
- rilanciare `panda_live_viewer` o `lerobot-bt-skill-server` senza CycloneDDS;
- controllare i servizi da una shell rimasta su un altro RMW.

## 2. Build e source workspace lerobot

```bash
cd /home/panda-admin/users/sben/lerobot
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI=file://$HOME/.ros/cyclonedds.xml
unset ROS_LOCALHOST_ONLY
colcon build --symlink-install
source install/setup.bash
```

Controlli rapidi:

```bash
ros2 interface show lerobot_bt_interfaces/srv/GenerateTaskPlan
ros2 interface show lerobot_bt_interfaces/srv/RunNamedCommand
```

## 3. Terminale A — VLM / Panda server

Apri un terminale dedicato e lascialo aperto.

### A1. Dry-run planner mode, consigliato per primo

Questo deve essere il primo modo usato sul robot day.

```bash
conda activate lerobot_ben
cd /home/panda-admin/users/sben/panda_live_viewer

source /home/panda-admin/users/sben/lerobot/install/setup.bash
export PYTHONPATH=/home/panda-admin/users/sben/lerobot/src:$PWD:$PYTHONPATH
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI=file://$HOME/.ros/cyclonedds.xml
unset ROS_LOCALHOST_ONLY

python3 -u -m vlm_live.cli \
  --ros-args \
  -p planner_dry_run:=true \
  -p lazy_load_model:=true \
  -p require_generate_plan_service:=true \
  -p verifier_experiment_log_path:=/home/panda-admin/users/sben/lerobot/generated_bt/experiments/verifier_events.jsonl
```

Atteso:

- il processo resta attivo;
- compare `/lerobot_bt/generate_plan`;
- Qwen o il modello non devono caricarsi.

### A2. Live VLM planner mode, solo dopo che il dry-run funziona

```bash
conda activate lerobot_ben
cd /home/panda-admin/users/sben/panda_live_viewer

source /home/panda-admin/users/sben/lerobot/install/setup.bash
export PYTHONPATH=/home/panda-admin/users/sben/lerobot/src:$PWD:$PYTHONPATH
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI=file://$HOME/.ros/cyclonedds.xml
unset ROS_LOCALHOST_ONLY

python3 -u -m vlm_live.cli \
  --ros-args \
  -p planner_dry_run:=false \
  -p lazy_load_model:=true \
  -p require_generate_plan_service:=true \
  -p verifier_experiment_log_path:=/home/panda-admin/users/sben/lerobot/generated_bt/experiments/verifier_events.jsonl
```

Usalo solo dopo questi tre passaggi:

- service dry-run OK;
- BT generation dry-run OK;
- `robot_live` con planner dry-run OK.

## 4. Verifica discovery cross-machine

Prima di avviare i trial, verifica che robot e server GPU si vedano davvero via
ROS 2.

Sul robot:

```bash
ros2 topic list | grep -E "lerobot_bt|panda"
```

Sul server GPU:

```bash
ros2 topic list | grep -E "lerobot_bt|panda"
```

Gli stessi topic principali devono comparire su entrambe le macchine.

Se i topic o servizi non compaiono ma sospetti che la discovery stia comunque
funzionando, riavvia il daemon ROS 2 nella shell di controllo:

```bash
ros2 daemon stop
ros2 daemon start
ros2 service list | grep lerobot_bt
ros2 topic list | grep lerobot_bt
```

### Ping rapido topic robot -> server

Sul robot:

```bash
ros2 topic pub /lerobot_bt/vlm_request std_msgs/msg/String '{"data":"{\"skill_name\":\"ping\"}"}' -1
```

Sul server GPU, apri un altro terminale e controlla:

```bash
ros2 topic echo /lerobot_bt/vlm_request
```

Se il messaggio non compare sul server:

- ricontrolla gli export CycloneDDS in **tutte** le shell;
- riavvia i processi dopo aver cambiato RMW;
- non procedere con `dry_run_no_run` finche' il ping non passa.

### Sanity check del planner service

Prima di lanciare la generazione vera, puoi verificare che il service remoto
risponda davvero a una chiamata ROS 2:

```bash
ros2 service call /lerobot_bt/generate_plan lerobot_bt_interfaces/srv/GenerateTaskPlan \
"{task_name: 'make_coffee', planner_registry_json: '{\"task_name\":\"make_coffee\",\"canonical_task_sequence\":[]}', scene_facts_json: ''}"
```

Atteso:

- il server remoto logga la richiesta;
- la chiamata ritorna un errore applicativo tipo
  `canonical_task_sequence must be a non-empty list.`

Questo errore e' **buono**: significa che il service risponde e che il problema
non e' piu' DDS/discovery ma solo il payload di test volutamente incompleto.

## 5. Terminale B — Skill server reale

Apri un secondo terminale dedicato e lascialo aperto.

Comando per `make_coffee`:

```bash
conda activate lerobot_ben
cd /home/panda-admin/users/sben/lerobot

source install/setup.bash
export PYTHONPATH=$PWD/src:$PYTHONPATH
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI=file://$HOME/.ros/cyclonedds.xml
unset ROS_LOCALHOST_ONLY

  --config_path=src/lerobot_bt_python/make_coffee_executor.yaml
```

Fallback senza `uv`:

Usalo solo se `uv` non è disponibile e l'ambiente Python ha già tutte le dipendenze richieste.

```bash
conda activate lerobot_ben
cd /home/panda-admin/users/sben/lerobot

source install/setup.bash
export PYTHONPATH=$PWD/src:$PYTHONPATH
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI=file://$HOME/.ros/cyclonedds.xml
unset ROS_LOCALHOST_ONLY

export PYTHONPATH=$PWD/src:$PYTHONPATH

python3 -m lerobot_bt_python.server \
  --config_path=src/lerobot_bt_python/make_coffee_executor.yaml
```

**Importante:** non usare `PYTHONPATH=src python3 -m ...`.
Quella forma puo' shadoware `lerobot_bt_interfaces` generato da ROS e far
fallire import come `GenerateTaskPlan`.

Altri task:

```bash
```

## 6. Terminale C — Check servizi ROS

Apri un terzo terminale. Userai questo terminale per tutti i test BT.

```bash
conda activate lerobot_ben
cd /home/panda-admin/users/sben/lerobot

source install/setup.bash
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI=file://$HOME/.ros/cyclonedds.xml
unset ROS_LOCALHOST_ONLY

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

## 7. Terminale C — Primo test: genera senza eseguire

Questo è il primo trial da lanciare.

```bash
conda activate lerobot_ben
cd /home/panda-admin/users/sben/lerobot

source install/setup.bash
export PYTHONPATH=$PWD/src:$PYTHONPATH
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI=file://$HOME/.ros/cyclonedds.xml
unset ROS_LOCALHOST_ONLY

PYTHON_BIN=python3 scripts/run_demo_bt_trial.sh make_coffee dry_run_no_run
```

Atteso:

- chiama Panda `/lerobot_bt/generate_plan`;
- scrive XML, YAML e manifest;
- non avvia il runner;
- stampa un `trial_id`.

I file generati finiscono sotto `generated_bt/`:

- `generated_bt/plans/`
- `generated_bt/trees/`
- `generated_bt/config/`
- `generated_bt/raw_model_responses/`
- `generated_bt/manifests/`

Se vuoi una cartella temporanea e cleanup automatico a fine comando, usa:

```bash
python3 -m lerobot_bt_python.bt_generation.generate_and_run \
  --task make_coffee \
  --planner ros-service \
  --registry src/lerobot_bt_python/bt_generation/skills_registry.yaml \
  --executor-yaml src/lerobot_bt_python/make_coffee_executor.yaml \
  --output-dir /tmp/generated_bt_make_coffee \
  --cleanup-output-dir-on-exit \
  --no-run
```

Se preferisci bypassare lo shell script e chiamare direttamente il modulo:

```bash
cd /home/panda-admin/users/sben/lerobot
source install/setup.bash
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI=file://$HOME/.ros/cyclonedds.xml
unset ROS_LOCALHOST_ONLY

python3 -m lerobot_bt_python.bt_generation.generate_and_run \
  --task make_coffee \
  --planner ros-service \
  --registry src/lerobot_bt_python/bt_generation/skills_registry.yaml \
  --executor-yaml src/lerobot_bt_python/make_coffee_executor.yaml \
  --output-dir generated_bt \
  --no-run
```

Anche qui: non anteporre `PYTHONPATH=src` al comando.

## 8. Terminale C — Secondo test: esegui BT sul robot

Solo dopo che la sezione 7 passa e lo skill server è attivo.

```bash
conda activate lerobot_ben
cd /home/panda-admin/users/sben/lerobot

source install/setup.bash
export PYTHONPATH=$PWD/src:$PYTHONPATH
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI=file://$HOME/.ros/cyclonedds.xml
unset ROS_LOCALHOST_ONLY

PYTHON_BIN=python3 scripts/run_demo_bt_trial.sh make_coffee robot_live
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
AwaitScene(make_coffee.task_complete)
```

## 9. Annotare il trial

Il comando precedente stampa un `trial_id` reale, per esempio:

```text
trial_id: make_coffee__ros-service__20260601T160013__8f93444d
```

Non copiare la parola `trial_id:`. Copia il valore reale dopo `trial_id:`.

Esempio successo:

```bash
cd /home/panda-admin/users/sben/lerobot

TRIAL_ID=make_coffee__ros-service__20260601T160013__8f93444d

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
cd /home/panda-admin/users/sben/lerobot

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
cd /home/panda-admin/users/sben/lerobot

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
cd /home/panda-admin/users/sben/lerobot

TRIAL_ID=replace_with_real_trial_id

python3 scripts/annotate_runtime_bt_trial.py \
  --jsonl generated_bt/experiments/trials.jsonl \
  --trial-id "$TRIAL_ID" \
  --task-success failure \
  --outcome-label aborted \
  --failure-category verifier_false_negative \
  --notes "verifier stayed RUNNING although scene appeared ready"
```

## 10. Report e bundle

Report:

```bash
cd /home/panda-admin/users/sben/lerobot

python3 scripts/summarize_runtime_bt_experiments.py

python3 scripts/make_demo_bt_report.py \
  --experiments-dir generated_bt/experiments \
  --out-md generated_bt/experiments/demo_report.md
```

Bundle:

Sostituisci `replace_with_real_trial_id` con il valore reale appena stampato.

```bash
cd /home/panda-admin/users/sben/lerobot

TRIAL_ID=replace_with_real_trial_id

python3 scripts/bundle_runtime_bt_trial.py \
  --output-dir generated_bt \
  --trial-id "$TRIAL_ID" \
  --out generated_bt/experiments/bundles/"$TRIAL_ID".tar.gz
```

## 11. Comandi equivalenti per altri task

```bash
cd /home/panda-admin/users/sben/lerobot

PYTHON_BIN=python3 scripts/run_demo_bt_trial.sh make_coffee dry_run_no_run
PYTHON_BIN=python3 scripts/run_demo_bt_trial.sh make_coffee robot_live

PYTHON_BIN=python3 scripts/run_demo_bt_trial.sh set_breakfast_table dry_run_no_run
PYTHON_BIN=python3 scripts/run_demo_bt_trial.sh set_breakfast_table robot_live

PYTHON_BIN=python3 scripts/run_demo_bt_trial.sh prepare_picnic_bag dry_run_no_run
PYTHON_BIN=python3 scripts/run_demo_bt_trial.sh prepare_picnic_bag robot_live

PYTHON_BIN=python3 scripts/run_demo_bt_trial.sh items_in_drawer dry_run_no_run
PYTHON_BIN=python3 scripts/run_demo_bt_trial.sh items_in_drawer robot_live
```

## 11b. Percezione RGB-D opzionale (scene facts + pose 6D)

Questa sezione è opzionale e parallela al flusso BT. Serve solo se vuoi pose 6D
degli oggetti e `scene_facts` dalla percezione invece dei soli gate VLM.

**Proprietà delle camere:** le RealSense sono aperte **solo** dallo skill server
(Terminale B). Il server, con `use_depth: true` e i `camera_*_map` valorizzati
nell'executor YAML, ripubblica automaticamente i frame come topic ROS. Non
avviare `panda_live_camera` né altri publisher RealSense: aprire lo stesso
device due volte causa conflitto hardware e frame persi.

### 11b.1 Verifica che lo skill server pubblichi RGB-D

Con Terminale B attivo (sezione 5), da Terminale C:

```bash
ros2 topic hz /panda/camera/front/image_compressed
ros2 topic hz /panda/camera/front/depth
ros2 topic echo --once /panda/camera/front/camera_info
ros2 topic hz /panda/camera/wrist/image_compressed
ros2 topic hz /panda/camera/wrist/depth
ros2 topic echo --once /panda/camera/wrist/camera_info
```

Atteso:

- Hz stabile e non nullo su image/depth;
- `camera_info` con `k` non vuoto (fx/fy/ppx/ppy) e `distortion_model: plumb_bob`;
- depth e color con **stessa width/height** (depth allineata al color). Se le
  risoluzioni differiscono, l'allineamento `rs.align` nel core non sta girando.

### 11b.2 Verifica le TF statiche base_link -> camera

```bash
ros2 run tf2_ros tf2_echo base_link panda_front_camera
ros2 run tf2_ros tf2_echo base_link panda_wrist_camera
```

Atteso: una trasformata stabile. **Attenzione:** se `camera_static_tf_map` non
è popolato con la calibrazione hand-eye reale nell'executor YAML, la TF non
viene pubblicata e la percezione marca le pose come `tf_unavailable`,
rifiutando le query in robot-frame. Popola `camera_static_tf_map` con la
calibrazione reale prima di usare le pose per il grasping.

### 11b.3 Avvia il nodo di percezione (panda_live_viewer)

Apri un terminale dedicato:

```bash
conda activate lerobot_ben
cd /home/panda-admin/users/sben/panda_live_viewer

source /home/panda-admin/users/sben/lerobot/install/setup.bash
export PYTHONPATH=/home/panda-admin/users/sben/lerobot/src:$PWD:$PYTHONPATH
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI=file://$HOME/.ros/cyclonedds.xml
unset ROS_LOCALHOST_ONLY

python3 -m perception.cli \
  --ros-args \
  -p planner_registry_json:='{"objects":[{"canonical_name":"cup","aliases":["mug"]}]}' \
  -p segmenter_backend:=owlvit \
  -p require_query_pose_service:=true
```

Atteso: il nodo logga disponibilità camere/TF e il caricamento del modello
OWL-ViT. Fallisce subito se `QueryObjectPose.srv` non è stato ribuildato e
sourcato (rebuild di `lerobot_bt_interfaces`).

Per i soli dry-run del verifier, senza percezione reale, usa
`-p segmenter_backend:=noop`.

### 11b.4 Verifica gli scene facts

```bash
ros2 topic echo --once /perception/scene_facts
```

Atteso: JSON con, per ogni oggetto, `pose` (traslazione + quaternione),
`covariance`, `pose_confidence`, `pose_residual_m`, `inlier_ratio` e
`warnings`. Senza detection il fact degrada (disponibilità + warning) invece di
inventare una posa.

### 11b.5 Interroga una posa via service

```bash
ros2 service call /perception/query_pose \
  lerobot_bt_interfaces/srv/QueryObjectPose \
  "{object_name: 'cup', require_fresh: true, max_age_s: 1.0}"
```

Atteso: `success: true` con `pose_json`, oppure `success: false` con
`error_message` chiaro (es. dati stantii o `tf_unavailable`) — mai una posa
vuota silenziosa.

### 11b.6 Sanity check metrico

- Posiziona l'oggetto a distanza nota; verifica che `pose.translation` in
  `base_link` coincida con la misura a metro entro pochi centimetri.
- Per una detection pulita `pose_residual_m` deve essere piccolo e
  `inlier_ratio` alto; entrambi degradano con viste parziali/occluse.
- `warnings` deve segnalare le condizioni reali (`insufficient_depth`,
  `orientation_estimated_pca`, RGB-D/TF stantii) invece di restare vuoto quando
  i dati sono scarsi.

### 11b.7 Planner + percezione (end-to-end opzionale)

Invia una richiesta `/lerobot_bt/generate_plan` **senza** `scene_facts_json`: il
planner inietta automaticamente gli ultimi `/perception/scene_facts`. Verifica
che il piano Linear IR referenzi gli oggetti percepiti.

### 11b.8 Arricchimento VLM con scene_facts (sola lettura)

Il verificatore VLM può **opzionalmente** includere nel prompt le pose metriche
degli oggetti misurate dalla percezione, solo come contesto spaziale:

- se `/perception/scene_facts` è attivo, `VlmNode` formatta gli oggetti presenti
  (es. `- coffee_capsule: [0.684, -0.260, 0.150] m in base_link, confidence 0.62`)
  e li inietta nel prompt del verificatore;
- è **a senso unico** percezione → VLM: il VLM *legge* le pose ma **non produce
  mai coordinate**; la percezione resta l'unica sorgente delle pose;
- senza `scene_facts` il prompt è identico a prima (nessuna regressione).

Per verificare: con la percezione attiva, nel log del VLM il prompt mostra il
blocco `Perception scene facts (...)`; spegnendo la percezione il blocco sparisce
e il comportamento torna quello base.

## 11c. Spatial-prior gate (task caffè, shadow mode)

Questa sezione testa il **gate spaziale OOD** per il task caffè
(`make_coffee`, skill `pick_and_insert_capsule`). Il gate confronta la posizione
osservata della capsula con un prior gaussiano addestrato dai 50 episodi del
dataset `Squitieri/put_coffee` e decide PASS / FAIL / ABSTAIN con distanza di
Mahalanobis. È **complementare e indipendente** dal gate VLM.

Documentazione completa: `docs/spatial_prior_gating.md`.

**Default = `shadow`**: il gate logga il verdetto ma **non blocca mai** lo skill.
Serve a misurare la distanza reale osservata-vs-prior prima di abilitare il
blocco. Già configurato in `make_coffee_executor.yaml`.

### 11c.1 Verifica che il prior sia presente e valido

Da un terminale qualsiasi:

```bash
conda activate lerobot_ben
cd /home/panda-admin/users/sben/lerobot/src

cat lerobot_bt_python/spatial_priors/put_coffee.json | python3 -m json.tool | head -20
```

Atteso: JSON con `frame_id: base_link`, `n_demos: 50`,
`mahalanobis_threshold ≈ 3.368`, `mu ≈ [0.684, -0.260, 0.150]`.

### 11c.2 Smoke test del gate (offline, senza robot)

Due modi, entrambi senza robot/GPU. **Importante:** attiva l'env conda
(`conda activate lerobot`) prima di lanciare, altrimenti l'import di `config.py`
fallisce con un errore di `libstdc++`/`CXXABI`.

Script standalone con i tre verdetti e log greppabili:

```bash
conda activate lerobot
cd /home/panda-admin/users/sben/lerobot

python3 scripts/smoke_spatial_prior_gate.py
```

Atteso: tre righe `event=spatial_prior_gate` con `status=PASS` (in-distribution,
base_link), `status=FAIL` (OOD, base_link, blocca in enforce), `status=ABSTAIN`
(`frame_mismatch`, frame camera = nessuna calibrazione), e `SMOKE TEST PASSED`.

Suite pytest completa:

```bash
conda activate lerobot
cd /home/panda-admin/users/sben/lerobot/src

python3 -m pytest lerobot_bt_python/test_spatial_prior.py -q
```

Atteso: `30 passed`. Conferma checker, fitter, parser (formato dict `{x,y,z}`
reale della percezione), modi del gate e i casi end-to-end PASS/ABSTAIN.

### 11c.3 Avvia lo skill server con il gate attivo

Il gate si attiva automaticamente quando avvii lo skill server (Terminale B,
sezione 5) con l'executor del caffè:

```bash
# Terminale B — skill server reale, task caffè
PYTHON_BIN=python3 scripts/run_demo_bt_trial.sh make_coffee robot_live
```

oppure direttamente:

```bash
  --config_path=src/lerobot_bt_python/make_coffee_executor.yaml
```

All'avvio cerca nel log:

```
spatial_prior_gate: loaded prior for skill 'pick_and_insert_capsule' ...
spatial_prior_gate: mode=shadow, querying object poses on '/perception/query_pose'.
```

Serve anche il nodo di percezione attivo (sezione 11b.3) con l'oggetto
`coffee_capsule` nel registry, altrimenti il gate si astiene
(`perception:...`).

### 11c.4 Leggi i verdetti del gate durante l'esecuzione

Quando il BT lancia lo skill `pick_and_insert_capsule`, nel log del Terminale B
compare una riga greppabile:

```bash
# Da un terminale che guarda il log dello skill server:
# (oppure filtra l'output del Terminale B)
grep "event=spatial_prior_gate" <log dello skill server>
```

Formato:

```
event=spatial_prior_gate mode=shadow skill='pick_and_insert_capsule' \
  object='coffee_capsule' status=PASS reason='in_distribution' \
  distance=0.84 threshold=3.368 frame='base_link' n_demos=50
```

Interpretazione:

- `status=PASS` → la capsula è nella regione addestrata.
- `status=FAIL` → capsula fuori distribuzione (in shadow **non** blocca).
- `status=ABSTAIN reason=frame_mismatch:...` → la percezione restituisce pose in
  frame camera: **manca la calibrazione hand-eye**. Popola
  `camera_static_tf_map` nell'executor YAML (vedi 11b.2) per avere pose in
  `base_link`.
- `status=ABSTAIN reason=perception:...` → percezione non disponibile o nessuna
  posa per `coffee_capsule`.

### 11c.5 Calibrazione dell'offset e soglia

Il prior è la posa EE all'istante di presa (proxy della posizione oggetto): ha
un **offset costante** rispetto al centroide oggetto della percezione. In shadow:

1. Posiziona la capsula in una posa "buona" (come nei demo) e annota la
   `distance` loggata.
2. Se in pose valide la `distance` è sistematicamente alta (es. > soglia per via
   dell'offset), correggi una delle due:
   - rifitta/sposta `mu` dell'offset misurato, oppure
   - alza `mahalanobis_threshold` / usa un `confidence_level` più lasco.
3. Ripeti finché pose buone → PASS e pose chiaramente sbagliate → FAIL.

#### Calibrazione hand-eye (`camera_static_tf_map`)

Se vedi `status=ABSTAIN reason=frame_mismatch:...`, manca la trasformata
base→camera. **Non inventare numeri.** Raccogli 4+ corrispondenze (stesso punto
in frame camera da `/perception/query_pose` e in `base_link` dal tool-tip),
salvale in un JSON e genera il blocco YAML pronto da incollare:

```bash
conda activate lerobot
python3 panda_live_viewer/scripts/calibrate_camera_extrinsics.py \
  --input corr.json --output cam_tf.yaml
```

Lo script stampa l'RMS del fit (avvisa se > 20 mm). Incolla il blocco
`camera_static_tf_map` in `make_coffee_executor.yaml` (al posto del placeholder
commentato accanto a `camera_frame_id_map`) e riavvia lo skill server. Dettagli:
`docs/spatial_prior_gating.md` sezione 10.

> Senza calibrazione reale il gate resta in ABSTAIN: è il comportamento corretto
> e sicuro, non un errore.

### 11c.6 Abilita il blocco (solo dopo calibrazione)

Quando le distanze in shadow sono sensate, passa a enforce nell'executor YAML:

```yaml
spatial_prior_gate:
  mode: enforce   # era: shadow
```

In `enforce` un verdetto FAIL blocca lo skill **prima** del movimento; ABSTAIN
non blocca mai. Riavvia lo skill server per applicare.

### 11c.7 Rigenera il prior (se cambi dataset)

```bash
conda activate lerobot_ben
cd /home/panda-admin/users/sben/lerobot/src

python3 -m lerobot_bt_python.fit_spatial_prior \
  --dataset-repo-id Squitieri/put_coffee \
  --skill pick_and_insert_capsule \
  --object coffee_capsule \
  --output lerobot_bt_python/spatial_priors/put_coffee.json
```

Scarica solo i parquet di stato + metadati (mai i video). Stampa demo, `mu`,
std per asse, soglia e tasso di accettazione leave-one-out (un prior unimodale
sano accetta ~99% dei demo held-out).

## 12. Errori comuni


### `/lerobot_bt/generate_plan` mancante

Causa:

- Panda VLM server non attivo;
- oppure Terminale A non ha fatto `source /home/panda-admin/users/sben/lerobot/install/setup.bash`.
- oppure una o piu' shell non stanno usando CycloneDDS.

Fix:

```bash
ros2 service list | grep generate_plan
```

Se manca, riavvia Terminale A in dry-run.

Se il service esiste sul server GPU ma non compare sul robot:

```bash
ros2 daemon stop
ros2 daemon start
ros2 service list | grep lerobot_bt
```

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

```

Nota:

- durante le prove e' emerso che il messaggio
  `rclpy is required for ROS planning but is not installed`
  puo' essere fuorviante;
- spesso il problema reale e' l'import del service ROS generato, non `rclpy`.

Verifica rapida:

```bash
python3 - <<'PY'
import rclpy
from lerobot_bt_interfaces.srv import GenerateTaskPlan
print("OK", rclpy.__file__, GenerateTaskPlan)
PY
```

Se `GenerateTaskPlan` fallisce, rebuilda le interfacce.

### `GenerateTaskPlan` non importabile

Causa:

- `lerobot_bt_interfaces` non buildato correttamente;
- oppure `PYTHONPATH=src python3 ...` ha shadowato il package installato.

Fix:

```bash
cd /home/panda-admin/users/sben/lerobot
rm -rf build/lerobot_bt_interfaces install/lerobot_bt_interfaces log
colcon build --packages-select lerobot_bt_interfaces --symlink-install
source install/setup.bash
```

Verifica:

```bash
python3 - <<'PY'
from lerobot_bt_interfaces.srv import GenerateTaskPlan
print("OK", GenerateTaskPlan)
PY
```

Se passa, rilancia la generazione senza usare `PYTHONPATH=src python3 -m ...`.

### Nessun topic/servizio visibile tra robot e server GPU

Causa:

- `RMW_IMPLEMENTATION` diverso tra le macchine;
- `CYCLONEDDS_URI` non esportato in una shell;
- processo avviato prima degli export corretti.

Fix:

```bash
echo $RMW_IMPLEMENTATION
echo $CYCLONEDDS_URI
ros2 topic list | grep -E "lerobot_bt|panda"
```

Atteso:

```text
rmw_cyclonedds_cpp
file://$HOME/.ros/cyclonedds.xml
```

Se non coincide su tutte le shell, chiudi e riapri i processi.

### errore RetryNode `num_attempts`

Atteso: XML con interi letterali.

```bash
grep -n "RetryUntilSuccessful" generated_bt/trees/make_coffee.xml
```

Non deve comparire:

```text
num_attempts="{...}"
```

### depth assente o pose sempre vuote

Causa:

- `use_depth: true` mancante nell'executor YAML;
- depth e color con risoluzioni diverse (allineamento `rs.align` non attivo).

Fix:

```bash
ros2 topic echo --once /panda/camera/front/camera_info
# confronta width/height di depth e color
ros2 topic hz /panda/camera/front/depth
```

Se le risoluzioni differiscono, ricontrolla `use_depth: true` su ogni camera
nello YAML e ribuilda/riavvia lo skill server.

### `/perception/query_pose` mancante

Causa:

- `QueryObjectPose.srv` non buildato/sourcato.

Fix:

```bash
cd /home/panda-admin/users/sben/lerobot
colcon build --packages-select lerobot_bt_interfaces --symlink-install
source install/setup.bash
```

Poi riavvia il nodo di percezione.

### pose marcate `tf_unavailable`

Causa:

- `camera_static_tf_map` non popolato con la calibrazione hand-eye reale.

Fix:

- popola `camera_static_tf_map` nell'executor YAML con la trasformata
  `base_link`->camera calibrata, ribuilda/riavvia lo skill server e riverifica
  con `tf2_echo` (sezione 11b.2).

### device RealSense occupato / frame persi

Causa:

- più di un publisher apre la stessa camera.

Fix:

- assicurati che solo lo skill server (Terminale B) possieda le RealSense;
- non avviare `panda_live_camera` in parallelo.

### spatial-prior gate sempre ABSTAIN

Causa e fix per `reason`:

- `frame_mismatch:...!=base_link` → manca la calibrazione hand-eye: la
  percezione restituisce pose in frame camera. Popola `camera_static_tf_map`
  (sezione 11b.2) e riavvia lo skill server.
- `perception:no_scene_facts` / `perception:No usable pose...` → nodo di
  percezione spento o oggetto `coffee_capsule` non rilevato/non nel registry.
  Avvia la percezione (11b.3) con l'alias corretto.
- `query_pose_service_unavailable` → il servizio `/perception/query_pose` non è
  attivo; verifica con `ros2 service list | grep query_pose`.
- prior non caricato (nessuna riga `loaded prior...` all'avvio) → controlla che
  `spatial_priors/put_coffee.json` esista e che `mode` non sia `off`.

## 13. Ordine sicuro sul robot day

1. Configura CycloneDDS su entrambe le macchine.
2. Build e source di `lerobot`.
3. Avvia Panda con `planner_dry_run:=true`.
4. Verifica discovery cross-machine e ping topic.
5. Avvia lo skill server reale.
6. Controlla i servizi ROS.
7. Lancia `dry_run_no_run`.
8. Annota il trial.
9. Lancia `robot_live` con planner dry-run.
10. Annota il trial.
11. Genera il report.
12. Solo dopo, riavvia Panda con `planner_dry_run:=false`.
13. (Opzionale) Per le pose 6D: verifica i topic RGB-D e le TF (sezione 11b),
    poi avvia il nodo di percezione e controlla `scene_facts`/`query_pose`.
14. (Opzionale, task caffè) Spatial-prior gate in shadow (sezione 11c): verifica
    il prior, avvia skill server + percezione, leggi i verdetti
    `event=spatial_prior_gate`, calibra offset/soglia e solo dopo passa a
    `enforce`.
