#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genera un PDF in italiano che documenta nel dettaglio il lavoro svolto oggi.

Uso:
    conda activate lerobot
    python scripts/genera_report_oggi.py [percorso_output.pdf]

Il PDF copre tutte le modifiche, i problemi affrontati e risolti, le variabili e
i modelli usati e come si integrano nella pipeline finale del task "make coffee".
"""
from __future__ import annotations

import sys
from datetime import date

from fpdf import FPDF

# --------------------------------------------------------------------------- #
# Contenuto del documento.
#
# Ogni blocco e' una tupla (tipo, testo). I tipi sono renderizzati con stili
# diversi (titoli, corpo, elenco puntato, codice, ecc.).
# --------------------------------------------------------------------------- #
BLOCKS: list[tuple[str, str]] = [
    ("title", "Report tecnico del lavoro svolto"),
    ("subtitle", f"Pipeline finale 'make coffee': percezione, spatial-prior gate, "
                 f"VLM e integrazione CycloneDDS - {date.today().isoformat()}"),

    ("h1", "0. Come leggere questo documento"),
    ("body",
     "Questo report e' pensato per essere riletto a distanza di tempo e capire "
     "OGNI dettaglio di cio' che e' stato affrontato e risolto. Per ogni "
     "argomento trovi: (1) il problema concreto, (2) la causa tecnica, (3) la "
     "soluzione applicata, (4) le variabili e i file coinvolti, (5) i modelli "
     "usati e il perche', (6) come il pezzo si incastra nella pipeline finale."),
    ("body",
     "Convenzioni: 'mu' indica il vettore medio del prior gaussiano, 'sigma' la "
     "matrice di covarianza, '->' indica un flusso o una trasformazione. I "
     "percorsi file sono relativi alla radice del repo indicato."),

    ("h1", "1. Contesto e obiettivo della pipeline finale"),
    ("body",
     "Obiettivo: eseguire in sicurezza il task 'make coffee' sul robot Panda "
     "combinando quattro componenti che si controllano a vicenda invece di "
     "fidarsi ciecamente di una sola fonte:"),
    ("bullet", "Percezione RGB-D (nodo ROS 2): rileva gli oggetti e ne stima la "
               "posa 3D nel frame base_link. E' l'UNICA fonte di verita' sulla "
               "posizione degli oggetti."),
    ("bullet", "Spatial-prior gate (deterministico): PRIMA di lanciare una skill, "
               "verifica che la posa osservata dell'oggetto sia compatibile con la "
               "distribuzione delle pose viste in addestramento. Se non lo e', "
               "blocca o segnala."),
    ("bullet", "Skill ACT (policy neurale): esegue il gesto vero e proprio "
               "(prendere la capsula e inserirla, chiudere la macchina)."),
    ("bullet", "VLM verifier (Qwen3-VL): DOPO l'esecuzione valuta semanticamente "
               "la scena per dire se lo stato finale e' corretto."),
    ("body",
     "Il principio di sicurezza e' un fail-safe ASIMMETRICO: il gate, in caso di "
     "dubbio, si astiene/blocca (conservativo, non muove il robot a rischio); il "
     "VLM, in caso di dubbio, lascia proseguire (RUNNING) per non interrompere "
     "inutilmente. Le due barriere coprono errori diversi (geometrico vs "
     "semantico)."),

    ("h1", "2. Problema #1 (il piu' critico): il gate si astiene SEMPRE"),
    ("h2", "2.1 Sintomo"),
    ("body",
     "Con la percezione reale collegata, lo spatial-prior gate restituiva sempre "
     "ABSTAIN con reason=no_translation. In pratica la barriera geometrica era "
     "morta: non passava (PASS) ne' bloccava (FAIL), si limitava ad astenersi, "
     "quindi non proteggeva nulla."),
    ("h2", "2.2 Causa tecnica"),
    ("body",
     "Il nodo di percezione serializza la posa dell'oggetto con la traslazione "
     "come DIZIONARIO {x, y, z} (vedi build_object_pose_fact). La funzione "
     "parse_object_pose_json in spatial_prior_gate.py, invece, accettava la "
     "traslazione SOLO come LISTA [x, y, z]. Ricevendo un dict, non trovava una "
     "lista valida -> translation=None -> ObservedPose con error='no_translation' "
     "-> il gate non aveva una posa da valutare -> ABSTAIN permanente."),
    ("h2", "2.3 Soluzione"),
    ("body",
     "Ho reso il parser tollerante a ENTRAMBI i formati. File: "
     "src/lerobot_bt_python/spatial_prior_gate.py (repo lerobot)."),
    ("code",
     "raw = pose.get(\"translation\")\n"
     "if isinstance(raw, Mapping):            # formato percezione reale {x,y,z}\n"
     "    translation = [float(raw[\"x\"]), float(raw[\"y\"]), float(raw[\"z\"])]\n"
     "elif isinstance(raw, (list, tuple)):     # formato legacy [x, y, z]\n"
     "    translation = [float(v) for v in raw]\n"
     "else:\n"
     "    translation = None"),
    ("body",
     "Ho aggiunto 'Mapping' agli import di typing. Risultato: con la percezione "
     "reale il gate ora estrae correttamente la posa e produce PASS/FAIL invece "
     "di astenersi."),
    ("h2", "2.4 Test aggiunti"),
    ("body",
     "File: src/lerobot_bt_python/test_spatial_prior.py. Tre nuovi test: "
     "(a) il parser accetta la traslazione come dict; (b) il gate da PASS su un "
     "payload reale in base_link vicino a mu; (c) il gate si astiene se il payload "
     "e' in frame camera (non base_link). Totale suite: 30 test, tutti verdi."),

    ("h1", "3. Lo spatial-prior gate in dettaglio"),
    ("h2", "3.1 Modello statistico"),
    ("body",
     "Il prior e' una gaussiana 3D sulla posizione dell'oggetto al momento della "
     "presa. Si verifica la compatibilita' con la distanza di Mahalanobis:"),
    ("formula",
     "d(x) = sqrt( (x - mu)^T * Sigma^-1 * (x - mu) )"),
    ("body",
     "Se d(x) <= soglia -> PASS (la posa e' plausibile). Se d(x) > soglia -> FAIL "
     "(posa anomala). Se manca la posa o il frame non e' confrontabile -> ABSTAIN."),
    ("h2", "3.2 Variabili del prior 'put_coffee.json' (oggetto: coffee_capsule)"),
    ("bullet", "frame_id = base_link (le pose vanno confrontate in questo frame)."),
    ("bullet", "mu = [0.68432, -0.26041, 0.15019] m (media della posizione "
               "end-effector all'istante di presa, usata come PROXY della posa "
               "oggetto)."),
    ("bullet", "mahalanobis_threshold = 3.36821 (soglia a confidence_level 0.99 su "
               "3 gradi di liberta')."),
    ("bullet", "sigma = matrice 3x3 di covarianza; translation_std_m ~ [0.026, "
               "0.028, 0.005] m (la profondita' z e' molto piu' stretta)."),
    ("bullet", "n_demos = 50, proxy = grasp_ee_position, min_pose_confidence = 0.0."),
    ("body",
     "Nota importante: mu/sigma sono fittati sulla posizione dell'end-effector, "
     "NON direttamente sul centroide dell'oggetto visto dalla percezione. Esiste "
     "quindi un offset fisso di presa; per questo il gate parte in modalita' "
     "SHADOW e va calibrato prima di passare a ENFORCE."),
    ("h2", "3.3 Modalita' operative e logging"),
    ("bullet", "shadow: il gate calcola e logga il verdetto ma NON blocca la skill "
               "(serve a raccogliere dati e calibrare). E' la modalita' attuale in "
               "make_coffee_executor.yaml."),
    ("bullet", "enforce: il gate blocca davvero la skill su FAIL."),
    ("body",
     "Ogni decisione emette una riga di log greppabile, ad esempio:"),
    ("code",
     "event=spatial_prior_gate mode=shadow skill=pick_and_insert_capsule \\\n"
     "  object=coffee_capsule status=PASS reason=within_threshold \\\n"
     "  distance=1.83 threshold=3.368 frame=base_link n_demos=50"),

    ("h1", "4. Problema #2: calibrazione camera->base (camera_static_tf_map)"),
    ("h2", "4.1 Perche' serve"),
    ("body",
     "La percezione vede gli oggetti nel frame della camera. Per confrontarli col "
     "prior (in base_link) serve la trasformazione statica camera->base. Senza una "
     "calibrazione reale, qualunque posa risulterebbe sistematicamente sbagliata."),
    ("h2", "4.2 Cosa ho aggiunto nel config"),
    ("body",
     "In src/lerobot_bt_python/make_coffee_executor.yaml ho aggiunto, accanto a "
     "camera_frame_id_map (wrist->panda_wrist_camera, left->panda_front_camera), "
     "un blocco placeholder COMMENTATO 'camera_static_tf_map' con valori a zero e "
     "il commento '# REPLACE WITH REAL CALIBRATION', cosi' la procedura e' "
     "evidente e non si rischia di lasciare valori finti attivi."),
    ("h2", "4.3 Helper di calibrazione (nuovo script)"),
    ("body",
     "File nuovo: scripts/calibrate_camera_extrinsics.py (repo panda_live_viewer). "
     "Risolve la trasformazione rigida camera->base da una lista di corrispondenze "
     "punto-punto."),
    ("bullet", "solve_rigid_transform(camera, base): algoritmo di Kabsch/Umeyama; "
               "restituisce R (rotazione 3x3), t (traslazione) e rms (errore "
               "residuo)."),
    ("bullet", "rotation_matrix_to_quaternion_xyzw(matrix): converte R in "
               "quaternione [x, y, z, w] (formato usato dal TF)."),
    ("bullet", "_format_yaml_block(...): stampa direttamente il blocco "
               "'camera_static_tf_map:' pronto da incollare nel config."),
    ("bullet", "main(): legge un JSON {camera_name, parent_frame_id, "
               "child_frame_id, correspondences:[{camera:[x,y,z], base:[X,Y,Z]}]}, "
               "stampa l'RMS e avvisa se supera 20 mm (calibrazione poco "
               "affidabile). Output opzionale con --output."),
    ("body",
     "Verifica: su una trasformazione rigida esatta il solver restituisce RMS=0 e "
     "recupera R, t e quaternione esattamente."),

    ("h1", "5. Problema #3: doppia sorgente delle estrinseche (TF ridondante)"),
    ("body",
     "Il nodo di percezione aveva un proprio broadcaster delle estrinseche "
     "(_init_static_extrinsics + parametro camera_extrinsics_json). Coesistendo "
     "con camera_static_tf_map del config lerobot, c'erano DUE fonti per la stessa "
     "trasformazione base->camera, con rischio di conflitto."),
    ("body",
     "Soluzione: ho rimosso da perception/node.py la chiamata e il metodo "
     "_init_static_extrinsics e il parametro camera_extrinsics_json. Ora la "
     "SINGOLA fonte di verita' per l'estrinseca base->camera e' "
     "camera_static_tf_map nel config lerobot."),

    ("h1", "6. Problema #4: arricchire il VLM con le scene-facts (one-way)"),
    ("h2", "6.1 Obiettivo"),
    ("body",
     "Dare al VLM verifier il contesto numerico della percezione (oggetti "
     "presenti e relative pose) per giudizi piu' informati, MANTENENDO il flusso "
     "a senso unico: la percezione informa il VLM, ma il VLM non modifica mai la "
     "percezione (nessun anello di retroazione che falsi la fonte di verita')."),
    ("h2", "6.2 Implementazione"),
    ("bullet", "vlm_live/prompt.py: nuova format_scene_context(scene_facts_json) che "
               "rende gli oggetti presenti come, ad es., '- coffee_capsule: "
               "[0.684, -0.260, 0.150] m in base_link, confidence 0.62'. "
               "Restituisce stringa vuota se non ci sono fatti utili."),
    ("bullet", "build_prompt aggiunge il blocco 'Perception scene facts (...)' SOLO "
               "se request contiene 'scene_context'; senza, nessuna regressione."),
    ("bullet", "vlm_live/node.py: importa format_scene_context; in _run_vlm calcola "
               "scene_context dai fatti piu' recenti e lo inietta nella request "
               "prima di build_prompt (solo se non gia' presente). _on_scene_facts "
               "fa da cache dell'ultimo JSON, _get_latest_scene_facts_json lo "
               "espone."),
    ("body",
     "Test: tests/test_vlm_status_protocol.py, classe SceneContextEnrichmentTests "
     "(5 test). Totale suite: 15 test verdi."),

    ("h1", "7. Smoke test offline dello spatial-prior gate"),
    ("body",
     "File nuovo: scripts/smoke_spatial_prior_gate.py (repo lerobot). Costruisce un "
     "vero SpatialPriorGate da put_coffee.json in modalita' ENFORCE e gli passa "
     "tre payload sintetici con traslazione in formato dict (come la percezione "
     "reale):"),
    ("bullet", "PASS: oggetto in base_link vicino a mu ([0.684, -0.260, 0.150])."),
    ("bullet", "FAIL: oggetto in base_link lontano ([1.50, 0.90, 0.80])."),
    ("bullet", "ABSTAIN: oggetto nel frame panda_front_camera (non confrontabile)."),
    ("body",
     "Stampa righe greppabili 'event=spatial_prior_gate ...' e infine 'SMOKE TEST "
     "PASSED/FAILED' con exit 0/1. Eseguito: i tre verdetti escono corretti. "
     "ATTENZIONE: va lanciato con l'ambiente conda 'lerobot' attivo (vedi sez. 11)."),

    ("h1", "8. Modelli usati e perche'"),
    ("bullet", "Skill ACT 'pick_and_insert_capsule' -> HSP-IIT/act_put_coffee. "
               "Policy neurale ACT (action chunking) addestrata per prendere la "
               "capsula e inserirla. Skill 'close_machine' -> Squitieri/"
               "act_close_machine."),
    ("bullet", "Percezione (segmentazione zero-shot) -> OWL-ViT "
               "(google/owlvit-base-patch32) come backend di default; rileva "
               "oggetti da alias in linguaggio naturale (es. 'coffee capsule') e "
               "li converte in maschere. Lo strumento diagnostico wrist_snapshot "
               "usa OWLv2 (google/owlv2-base-patch16-ensemble), piu' accurato per "
               "le ispezioni puntuali."),
    ("bullet", "VLM verifier -> Qwen3-VL-32B-Instruct. Modello vision-language che "
               "valuta semanticamente la scena dopo l'esecuzione. Scelto per la "
               "capacita' di ragionamento multimodale; in caso di incertezza "
               "lascia proseguire (RUNNING) per non bloccare inutilmente."),
    ("bullet", "Prior spaziale gaussiano (mu, sigma) fittato da 50 dimostrazioni "
               "con fit_spatial_prior.py. Non e' una rete neurale: e' un modello "
               "statistico leggero e interpretabile, ideale come barriera "
               "deterministica pre-skill."),

    ("h1", "9. Come tutto si integra nella pipeline finale"),
    ("body", "Flusso end-to-end del task 'make coffee':"),
    ("code",
     "Percezione RGB-D\n"
     "   -> posa oggetto in base_link (UNICA fonte di verita')\n"
     "        |                                   \\\n"
     "        v                                    v (one-way, sola lettura)\n"
     "Spatial-prior gate (deterministico)     VLM scene-facts context\n"
     "   PASS/FAIL/ABSTAIN  (pre-skill)             |\n"
     "        |                                     |\n"
     "        v                                     |\n"
     "Skill ACT (act_put_coffee / close_machine)    |\n"
     "        |                                     v\n"
     "        +-----------------------------> VLM verifier (Qwen3-VL)\n"
     "                                          giudizio semantico (post-skill)"),
    ("body",
     "Punti chiave dell'integrazione: (1) la percezione e' l'unica fonte di posa; "
     "(2) il gate e' una barriera geometrica PRIMA della skill; (3) la skill ACT "
     "esegue; (4) il VLM giudica DOPO. Le scene-facts viaggiano solo dalla "
     "percezione al VLM, mai all'indietro. Il fail-safe e' asimmetrico: il gate "
     "si astiene/blocca nel dubbio, il VLM lascia proseguire nel dubbio."),

    ("h1", "10. Integrazione automatica di CycloneDDS (locale + server)"),
    ("h2", "10.1 Problema"),
    ("body",
     "Ad ogni avvio bisognava esportare a mano quattro impostazioni ROS 2: "
     "ROS_DOMAIN_ID, RMW_IMPLEMENTATION, CYCLONEDDS_URI e fare 'unset "
     "ROS_LOCALHOST_ONLY'. Operazione ripetitiva e facile da dimenticare, sia in "
     "locale sia sul server."),
    ("h2", "10.2 Soluzione: un unico file sorgenziabile per repo"),
    ("body",
     "Ho creato 'ros_env.sh' nella radice di ENTRAMBI i repo (lerobot e "
     "panda_live_viewer). E' idempotente, rispetta eventuali valori gia' impostati "
     "(usa la sintassi ${VAR:-default}) ed e' indipendente dalla macchina:"),
    ("code",
     "export ROS_DOMAIN_ID=\"${ROS_DOMAIN_ID:-0}\"\n"
     "export RMW_IMPLEMENTATION=\"${RMW_IMPLEMENTATION:-rmw_cyclonedds_cpp}\"\n"
     "if [ -z \"${CYCLONEDDS_URI:-}\" ] && [ -f \"$HOME/.ros/cyclonedds.xml\" ]; then\n"
     "    export CYCLONEDDS_URI=\"file://$HOME/.ros/cyclonedds.xml\"\n"
     "fi\n"
     "unset ROS_LOCALHOST_ONLY"),
    ("body",
     "Perche' cosi': il file cyclonedds.xml e' SPECIFICO della macchina (contiene "
     "l'interfaccia di rete e i peer, IP diversi tra laptop e server). Quindi "
     "ros_env.sh non lo sovrascrive mai: punta semplicemente a "
     "$HOME/.ros/cyclonedds.xml e lo usa solo se esiste. Lo stesso script "
     "funziona su ogni macchina dopo un 'git pull'."),
    ("h2", "10.3 Dove viene agganciato"),
    ("bullet", "panda_live_viewer/run.sh: il vecchio blocco di export inline e' "
               "stato sostituito da 'source \"$SCRIPT_DIR/ros_env.sh\"' (DRY)."),
    ("bullet", "lerobot/scripts/run_demo_bt_trial.sh: aggiunto 'source "
               "\"$REPO_ROOT/ros_env.sh\"' subito dopo il calcolo di REPO_ROOT."),
    ("bullet", "~/.bashrc (locale): aggiunto un blocco delimitato '>>> "
               "lerobot/panda ROS 2 + CycloneDDS env >>>' con gli stessi default, "
               "cosi' anche i terminali interattivi sono gia' configurati. Ho "
               "anche ripulito una riga malformata preesistente del blocco "
               "LEAP_Hand_tests."),
    ("h2", "10.4 Sul server"),
    ("body",
     "Gli script (run.sh, run_demo_bt_trial.sh) configurano l'ambiente in "
     "automatico anche sul server, perche' 'ros_env.sh' viaggia con il repo via "
     "git pull. Per i terminali interattivi sul server (dove non posso editare il "
     "suo .bashrc da qui) basta aggiungere UNA volta in fondo a ~/.bashrc:"),
    ("code",
     "source ~/lerobot/ros_env.sh        # oppure il percorso del repo sul server"),
    ("body",
     "Da quel momento ogni nuova shell sul server e' configurata, senza piu' "
     "export manuali."),

    ("h1", "11. Documentazione aggiornata e nota sull'ambiente Python"),
    ("bullet", "docs/spatial_prior_gating.md: conteggio test 27->30; nuove sezioni "
               "10 (calibrazione hand-eye / camera_static_tf_map), 11 "
               "(arricchimento scene-facts VLM one-way), 12 (smoke test offline)."),
    ("bullet", "docs/DEMO_FINALE_COMMANDS.md: aggiornati i passi 11c.2 (smoke "
               "script + 30 test + avviso conda), 11c.5 (calibrazione hand-eye), "
               "11b.8 (nota scene_facts del VLM)."),
    ("bullet", "panda_live_viewer/README.md: note su arricchimento scene_facts in "
               "sola lettura, camera_static_tf_map come fonte unica e helper di "
               "calibrazione."),
    ("body",
     "Nota ambiente: gli script Python di questo lavoro vanno eseguiti con l'env "
     "conda 'lerobot' attivo (source di conda.sh + 'conda activate lerobot'). Il "
     "python nudo dell'env da' un errore CXXABI_1.3.15/libstdc++ nella catena di "
     "import (config.py -> transformers/scipy); l'attivazione conda sistema "
     "LD_LIBRARY_PATH."),

    ("h1", "12. Riepilogo file creati/modificati"),
    ("h2", "12.1 Repo lerobot"),
    ("bullet", "Modificato: src/lerobot_bt_python/spatial_prior_gate.py (parser "
               "dict+list)."),
    ("bullet", "Modificato: src/lerobot_bt_python/test_spatial_prior.py (+3 test, "
               "30 totali)."),
    ("bullet", "Modificato: src/lerobot_bt_python/make_coffee_executor.yaml "
               "(placeholder camera_static_tf_map commentato)."),
    ("bullet", "Nuovo: scripts/smoke_spatial_prior_gate.py (smoke test offline)."),
    ("bullet", "Nuovo: ros_env.sh (env ROS 2/CycloneDDS centralizzato)."),
    ("bullet", "Modificato: scripts/run_demo_bt_trial.sh (source ros_env.sh)."),
    ("bullet", "Modificato: docs/spatial_prior_gating.md, "
               "docs/DEMO_FINALE_COMMANDS.md."),
    ("bullet", "Nuovo: scripts/genera_report_oggi.py (questo report)."),
    ("h2", "12.2 Repo panda_live_viewer"),
    ("bullet", "Nuovo: scripts/calibrate_camera_extrinsics.py (Kabsch/Umeyama)."),
    ("bullet", "Modificato: vlm_live/prompt.py (format_scene_context, build_prompt)."),
    ("bullet", "Modificato: vlm_live/node.py (iniezione scene_context one-way)."),
    ("bullet", "Modificato: perception/node.py (rimosso TF estrinseco ridondante)."),
    ("bullet", "Modificato: tests/test_vlm_status_protocol.py (+5 test, 15 totali)."),
    ("bullet", "Modificato: README.md."),
    ("bullet", "Nuovo: ros_env.sh (env ROS 2/CycloneDDS centralizzato)."),
    ("bullet", "Modificato: run.sh (source ros_env.sh)."),

    ("h1", "13. Stato dei test"),
    ("body",
     "lerobot/test_spatial_prior.py: 30 test PASS. "
     "panda_live_viewer/test_vlm_status_protocol.py: 15 test PASS. "
     "smoke_spatial_prior_gate.py: PASS/FAIL/ABSTAIN tutti corretti. "
     "calibrate_camera_extrinsics.py: solver verificato con RMS=0 su trasformazione "
     "rigida esatta."),
    ("body",
     "Falle preesistenti (NON causate da questo lavoro, confermate su HEAD pulito "
     "via git stash): test_perception_segmenters.py "
     "(test_labels_from_registry_uses_canonical_object_names) e "
     "test_vlm_node_static.py (2 test). Vanno trattate separatamente."),
]


class ReportPDF(FPDF):
    def header(self) -> None:  # pragma: no cover - rendering
        if self.page_no() == 1:
            return
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(130, 130, 130)
        self.cell(0, 6, "Report tecnico - pipeline make coffee", align="L")
        self.cell(0, 6, f"pag. {self.page_no()}", align="R")
        self.ln(8)
        self.set_text_color(0, 0, 0)

    def footer(self) -> None:  # pragma: no cover - rendering
        self.set_y(-12)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 6, "Generato da scripts/genera_report_oggi.py", align="C")
        self.set_text_color(0, 0, 0)


def _latin1(text: str) -> str:
    """Sostituisce i caratteri non rappresentabili dai font core (latin-1)."""
    replacements = {
        "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
        "\u2013": "-", "\u2014": "-", "\u2026": "...", "\u2192": "->",
        "\u2265": ">=", "\u2264": "<=", "\u00d7": "x", "\u2022": "-",
        "\u00b5": "mu", "\u03bc": "mu", "\u03c3": "sigma", "\u03a3": "Sigma",
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    return text.encode("latin-1", "replace").decode("latin-1")


def build(output_path: str) -> None:
    pdf = ReportPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_margins(18, 16, 18)
    pdf.add_page()

    for kind, text in BLOCKS:
        text = _latin1(text)
        if kind == "title":
            pdf.set_font("Helvetica", "B", 20)
            pdf.set_text_color(20, 20, 60)
            pdf.multi_cell(0, 9, text)
            pdf.ln(1)
        elif kind == "subtitle":
            pdf.set_font("Helvetica", "I", 11)
            pdf.set_text_color(90, 90, 90)
            pdf.multi_cell(0, 6, text)
            pdf.set_text_color(0, 0, 0)
            pdf.ln(4)
        elif kind == "h1":
            pdf.ln(2)
            pdf.set_font("Helvetica", "B", 14)
            pdf.set_text_color(20, 20, 90)
            pdf.multi_cell(0, 7, text)
            pdf.set_draw_color(180, 180, 200)
            pdf.set_line_width(0.3)
            y = pdf.get_y()
            pdf.line(pdf.l_margin, y, pdf.w - pdf.r_margin, y)
            pdf.ln(2)
            pdf.set_text_color(0, 0, 0)
        elif kind == "h2":
            pdf.ln(1)
            pdf.set_font("Helvetica", "B", 11.5)
            pdf.set_text_color(40, 40, 70)
            pdf.multi_cell(0, 6, text)
            pdf.set_text_color(0, 0, 0)
            pdf.ln(0.5)
        elif kind == "body":
            pdf.set_font("Helvetica", "", 10.5)
            pdf.multi_cell(0, 5.4, text)
            pdf.ln(1.5)
        elif kind == "bullet":
            pdf.set_font("Helvetica", "", 10.5)
            x0 = pdf.get_x()
            pdf.cell(5, 5.4, "-")
            pdf.set_x(x0 + 5)
            pdf.multi_cell(0, 5.4, text)
            pdf.ln(0.8)
        elif kind in ("code", "formula"):
            pdf.ln(0.5)
            pdf.set_font("Courier", "", 9 if kind == "code" else 10)
            pdf.set_fill_color(244, 244, 248)
            pdf.set_text_color(20, 20, 20)
            pdf.multi_cell(0, 5, text, border=0, fill=True)
            pdf.set_text_color(0, 0, 0)
            pdf.ln(1.5)

    pdf.output(output_path)


def main() -> int:
    output = sys.argv[1] if len(sys.argv) > 1 else "/home/panda-admin/users/sben/report_pipeline_oggi.pdf"
    build(output)
    print(f"PDF generato: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
