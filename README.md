
<!-- ══════════════════════════════════════════════════════════════════════════ -->
<!--                IDENTITY VERIFICATION PLATFORM — REPO REFERENCE               -->
<!-- ══════════════════════════════════════════════════════════════════════════ -->

<div align="center">

![Hero](https://capsule-render.vercel.app/api?type=venom&color=0:0d1117,30:0a0f2c,60:0d2137,100:0a1628&height=240&section=header&text=IDENTITY%20VERIFICATION%20PLATFORM&fontSize=48&fontColor=00d4ff&animation=fadeIn&desc=AI+Identity+%7C+Kiosk+%7C+Training+%7C+Cloud&descSize=14&descColor=7dd3fc&stroke=00d4ff&strokeWidth=1)

<br/>

[![Profile Views](https://komarev.com/ghpvc/?username=Arshath015&label=PROFILE+SCANS&color=00d4ff&style=flat-square)](https://github.com/Arshath015)
&nbsp;![Status](https://img.shields.io/badge/STATUS-DEV_READY-00d4ff?style=flat-square&labelColor=0d1117)
&nbsp;![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat-square&labelColor=0d1117)
&nbsp;![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?style=flat-square&labelColor=0d1117)

</div>

---

<!-- ═══════════════════════════════════════════════════════════════════════════
     QUICK SUMMARY
══════════════════════════════════════════════════════════════════════════════ -->

This repository groups three coordinated projects focused on identity capture, biometric verification, and embedding-based similarity training:

- `ai_native_app/` — on-device Streamlit kiosk + admin dashboard (camera, QR, biometric, Supabase storage and DB integration).
- `cloud_native_app/` — cloud-facing companion for APIs, webhook ingestion, and background tasks.
- `face_similarity_training/` — dataset preprocessing, embedding generation, and threshold analysis utilities.

This README blends a developer profile header with thorough operational details (run, deploy, SQL schema, and a 3D visual snippet).

---

## 👨‍💻 About (Project Owner)

```python
class Owner:
    NAME = "Arshath Farwyz"
    ROLE = "AI Creative Engineer"
    LOCATION = "Chennai / Bangalore, India"
    CORE_STACK = ["Python", "Streamlit", "Supabase", "OpenCV", "FastAPI", "LangChain"]

    def motto(self):
        return "Automate the repetitive. Amplify the creative. Engineer the impossible."

owner = Owner()
print(owner.motto())
```

---

## 🧭 Repo Layout (short)

- `ai_native_app/` — Streamlit app (pages, services, ui, config)
- `cloud_native_app/` — cloud API and integration glue
- `face_similarity_training/` — training scripts, embeddings, results

---

## 🛠️ Tech Stack (high level)

- Languages: Python, SQL
- UI: Streamlit
- Vision: OpenCV (fallback), optional DeepFace/tf for stronger embeddings
- DB & Storage: Supabase (Postgres + Storage)
- Packaging: virtualenv / pip

---

## 🚀 Highlights & How It Works

- Registration flow: camera capture -> optional face embedding -> upload to `id_photos` bucket -> create `id_cards` entry.
- Kiosk flow: QR scan / ID lookup -> live face capture -> embedding -> cosine similarity check against KB -> record `verifications`.
- Training: use `face_similarity_training/scripts` to build embeddings and tune thresholds (outputs in `results/`).

---

## 🎯 Supabase Schema (SQL)

Run this SQL in Supabase SQL editor to create the minimal schema used by the apps.

```sql
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS id_cards (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  full_name text NOT NULL,
  rrn text UNIQUE,
  department text,
  phone text,
  email text UNIQUE,
  photo_path text,
  is_active boolean DEFAULT true,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz
);

CREATE TABLE IF NOT EXISTS verifications (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  card_id uuid REFERENCES id_cards(id) ON DELETE SET NULL,
  result text NOT NULL,
  note text,
  created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_id_cards_email ON id_cards(email);
CREATE INDEX IF NOT EXISTS idx_verifications_card_id ON verifications(card_id);

-- example seed
INSERT INTO id_cards(full_name, rrn, department, phone, email, photo_path)
VALUES ('Alice Example','RRN-001','Engineering','+1234567890','alice@example.com','photos/sample.jpg');
```

---

## 🧪 3D Block Animation (embed)

Save the HTML below as `3d-blocks.html` and open it in a browser or serve via docs. Useful as a visual demo snippet for the admin UI.

```html
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>3D Block Grid</title>
  <style>
    body { background:#081018; display:flex; align-items:center; justify-content:center; height:100vh; margin:0; }
    .scene { perspective:1000px; }
    .grid { width:520px; display:grid; grid-template-columns:repeat(5,100px); grid-gap:8px; transform-style:preserve-3d; }
    .block { width:100px; height:100px; background:linear-gradient(135deg,#002b36,#004e6b); border-radius:8px; box-shadow:0 8px 20px rgba(0,0,0,0.6); transform-origin:center; transition:transform 450ms cubic-bezier(.2,.9,.3,1), box-shadow 450ms; }
    .block:hover { transform:translateZ(40px) rotateX(12deg) rotateY(-8deg); box-shadow:0 30px 40px rgba(0,0,0,0.6); }
    @keyframes floaty { 0%{transform:translateZ(0)} 50%{transform:translateZ(24px)} 100%{transform:translateZ(0)} }
    .block.animated { animation:floaty 3s ease-in-out infinite; }
    .label { font-family:Inter,system-ui; color:#a1dcf1; text-align:center; font-size:12px; padding-top:6px }
  </style>
</head>
<body>
  <div class="scene">
    <div class="grid" id="grid"></div>
  </div>
  <script>
    const grid = document.getElementById('grid');
    for(let i=0;i<20;i++){
      const b = document.createElement('div');
      b.className='block animated';
      const lbl = document.createElement('div'); lbl.className='label'; lbl.textContent='NODE '+(i+1);
      b.appendChild(lbl);
      b.style.animationDelay = (i*120)+'ms';
      grid.appendChild(b);
    }
  </script>
</body>
</html>
```

---

## ▶️ Run locally (quick)

Recommended Python: 3.9–3.11. For full `deepface` support use a separate venv with Python 3.9/3.10 and install `tensorflow`.

```powershell
cd "D:\\....\\project\\app"
python -m pip install -r ai_native_app\requirements.txt
python -m streamlit run ai_native_app\app.py
```

If Supabase is not available, the `ai_native_app` code uses defensive fallbacks and will still run in demo mode.

---

## 📂 Important Files

- `ai_native_app/app.py` — Streamlit entry and tab router
- `ai_native_app/config.py` — env loader (supports optional `python-dotenv`)
- `ai_native_app/services/biometric_service.py` — OpenCV fallback + optional DeepFace
- `face_similarity_training/scripts` — embedding & threshold tools

---

## 👥 Contact & Credits

- Author: Arshath Farwyz — AI Creative Engineer
- Email: arshathfarwyz015@gmail.com
- GitHub: https://github.com/Arshath015

License: MIT

---

**Table of Contents**

- Overview
- Project Structure (high-level)
- ai_native_app — Deep breakdown
- cloud_native_app — Deep breakdown
- face_similarity_training — Deep breakdown
- 3D UI block / Animated showcase (HTML/CSS/JS snippet you can embed)
- Supabase: schema & SQL (complete)
- Running locally (commands)
- Deployment notes
- Troubleshooting & FAQ
- Credits & License

---

## Overview

This workspace demonstrates a full small-stack pipeline for identity verification and related tooling:

- An interactive local kiosk built with Streamlit (`ai_native_app`) — camera-based QR + biometric verification, registration, and an admin dashboard.
- A cloud-native companion (`cloud_native_app`) which can expose APIs for orchestration, worker tasks, or webhook integration.
- A model training area (`face_similarity_training`) containing scripts to create embeddings, evaluate similarity thresholds, and produce datasets and CSV outputs used by the kiosk at runtime.

The repository is intended for research, demo, and PoC deployments. It focuses on modularity: UI logic separated from services (Supabase, biometric, QR, email), and the training code isolated for re-use.

---

## Project Structure (high-level)

- ai_native_app/
  - app.py — entry point (Streamlit router)
  - config.py — environment configuration
  - pages/ — Streamlit page modules (register, dashboard, kiosk)
  - services/ — business logic (supabase, biometric, qr, email, knowledge base)
  - ui/ — theme and small UI helpers

- cloud_native_app/
  - app.py — cloud-facing app (API server or web frontend)

- face_similarity_training/
  - scripts/ — training & preprocessing scripts
  - models/ — saved model artifacts
  - train_embeddings.npy — sample/trained embeddings
  - results/ — CSV of similarity scores and analyses

---

## ai_native_app — Deep breakdown

This is the primary demo application. The code has been modularized into pages and services.

- `app.py`
  - Lightweight router that applies the UI theme and mounts three tabs: Register Person, Command Center, Auto-Scan Kiosk.

- `config.py`
  - Loads environment variables (supports python-dotenv optionally). Exposes constants such as `SUPABASE_URL`, `SUPABASE_KEY`, `STORAGE_BUCKET`, `MODEL_NAME`, and `VERIFICATION_THRESHOLD`.

- `ui/theme.py`
  - Contains CSS injected to achieve the cyber/JARVIS look, plus the `render_terminal_logs()` helper used by the kiosk and dashboard.

- `pages/register_page.py`
  - Handles biometric acquisition via `st.camera_input`, registration form, validation, photo upload to Supabase storage, and QR generation & email dispatch.

- `pages/dashboard_page.py`
  - Admin view that lists users, allows searching, inline updates and deletions, and shows verification logs.

- `pages/kiosk_page.py`
  - Continuous camera loop performing: QR scan -> map QR UUID to known user (embeddings KB) -> run face detection & embedding -> similarity check -> record verification.
  - Uses robust camera handling to recover from hardware locks and throttles the frame loop.

- `services/supabase_service.py`
  - Single place for Supabase client initialization and table/storage methods. The code is defensive — returns defaults when the network or credentials are missing.

- `services/biometric_service.py`
  - Provides `BiometricEngine.extract_and_embed()` which returns a normalized vector embedding and bounding box. The implementation uses a lightweight OpenCV fallback for environments where the TensorFlow-based `DeepFace` stack is unavailable. If `DeepFace` is present and compatible, it will be used automatically.

- `services/qr_service.py`, `services/email_service.py`, `services/knowledge_service.py`
  - Utilities for QR encode/decode, sending emails with attachments, and building the in-memory knowledge base (id -> embedding map).

Notes & Tips
- Keep `.env` secrets out of source control. Use `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` for Supabase.
- If your environment cannot install heavy ML packages (TensorFlow), the app will gracefully fall back to the lightweight OpenCV histogram embedding.

---

## cloud_native_app — Deep breakdown

This folder contains a separate cloud-oriented entrypoint. Typical responsibilities for `cloud_native_app/app.py` in this workspace may include:

- Exposing webhooks or REST endpoints to integrate with the Streamlit kiosk (for remote logging, centralized verification replica, or admin automation).
- Running background tasks (e.g., scheduled model refreshes or batch embedding ingestion).

If you plan to run the cloud app in production:

- Wrap the app behind authentication.
- Use environment variables for DB and API secrets.
- Deploy on a server or platform that supports long-running background processes (e.g., Azure App Service, AWS ECS, GCP Cloud Run).

---

## face_similarity_training — Deep breakdown

This area contains the scripts used to create, evaluate, and tune embeddings and thresholds. Typical files:

- `scripts/preprocess_faces.py` — face cropping, alignment, dataset prep.
- `scripts/generate_embeddings.py` — produce embeddings from images and save them (e.g., `train_embeddings.npy`).
- `scripts/threshold_analysis.py` — run pairwise comparisons, compute ROC curves, and write `similarity_scores.csv` to `results/`.

Data Usage
- Keep your training dataset separate and respect privacy rules when using biometric data.

---

## 3D Block Animation — interactive snippet

Below is an HTML/CSS/JS snippet that renders an animated 3D block grid similar to the visual style in the project screenshots. You can open this locally (save as `3d-blocks.html`) and embed into a docs site or an iframe inside your admin UI.

```html
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>3D Block Grid</title>
  <style>
    body { background:#081018; display:flex; align-items:center; justify-content:center; height:100vh; margin:0; }
    .scene { perspective:1000px; }
    .grid { width:520px; display:grid; grid-template-columns:repeat(5,100px); grid-gap:8px; transform-style:preserve-3d; }
    .block { width:100px; height:100px; background:linear-gradient(135deg,#002b36,#004e6b); border-radius:8px; box-shadow:0 8px 20px rgba(0,0,0,0.6); transform-origin:center; transition:transform 450ms cubic-bezier(.2,.9,.3,1), box-shadow 450ms; }
    .block:hover { transform:translateZ(40px) rotateX(12deg) rotateY(-8deg); box-shadow:0 30px 40px rgba(0,0,0,0.6); }
    /* animated wave */
    @keyframes floaty { 0%{transform:translateZ(0)} 50%{transform:translateZ(24px)} 100%{transform:translateZ(0)} }
    .block.animated { animation:floaty 3s ease-in-out infinite; }
    .label { font-family:Inter,system-ui; color:#a1dcf1; text-align:center; font-size:12px; padding-top:6px }
  </style>
</head>
<body>
  <div class="scene">
    <div class="grid" id="grid"></div>
  </div>
  <script>
    const grid = document.getElementById('grid');
    for(let i=0;i<20;i++){
      const b = document.createElement('div');
      b.className='block animated';
      const lbl = document.createElement('div'); lbl.className='label'; lbl.textContent='NODE '+(i+1);
      b.appendChild(lbl);
      b.style.animationDelay = (i*120)+'ms';
      grid.appendChild(b);
    }
  </script>
</body>
</html>
```

Embed tip: place the file in a static docs folder and use an `<iframe>` in your admin UI for live 3D visualizations.

---

## Supabase — schema & SQL

The app uses Supabase for two primary needs:

- `id_cards` table — stores registered users and their photo storage paths.
- `verifications` table — records successful verification events.

Below is a minimal SQL schema you can run in your Supabase SQL editor to create these tables. Adjust types and constraints for your policy and region.

```sql
-- Enable UUID extension (Postgres)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Users / ID Cards
CREATE TABLE IF NOT EXISTS id_cards (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  full_name text NOT NULL,
  rrn text UNIQUE,
  department text,
  phone text,
  email text UNIQUE,
  photo_path text,
  is_active boolean DEFAULT true,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz
);

-- Verifications
CREATE TABLE IF NOT EXISTS verifications (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  card_id uuid REFERENCES id_cards(id) ON DELETE SET NULL,
  result text NOT NULL,
  note text,
  created_at timestamptz DEFAULT now()
);

-- Indexes to help queries
CREATE INDEX IF NOT EXISTS idx_id_cards_email ON id_cards(email);
CREATE INDEX IF NOT EXISTS idx_verifications_card_id ON verifications(card_id);

-- Example: insert a sample user (replace with your own values)
INSERT INTO id_cards(full_name, rrn, department, phone, email, photo_path)
VALUES ('Alice Example','RRN-001','Engineering','+1234567890','alice@example.com','photos/sample.jpg');

-- Example: record a verification
INSERT INTO verifications(card_id, result, note)
VALUES ((SELECT id FROM id_cards WHERE email='alice@example.com' LIMIT 1), 'success', 'Test entry');
```

Supabase storage
- The app stores images under a bucket (configured as `id_photos`). Create a bucket named `id_photos` in the Supabase Storage panel and set rules as appropriate (public or signed URLs as used by the app).

Security notes
- Keep `SUPABASE_SERVICE_KEY` secret. Use Service Role keys only on trusted servers (not in client code).
- For client-side flows, use the anon public key together with RLS policies.

---

## Running locally

General prerequisites

- Python 3.8 — 3.11 recommended (this repo was adapted to work without TensorFlow for local dev)
- `pip install -r ai_native_app/requirements.txt`

Launch Streamlit app (from repository root):

```powershell
cd "D:\Freelancing\Priyan projects\app"
python -m streamlit run ai_native_app\app.py
```

If you plan to enable full DeepFace support (optional), create a separate virtualenv with a Python version compatible with TensorFlow (commonly 3.9 or 3.10), and install `deepface` plus `tensorflow`.

---

## Deployment notes

- `ai_native_app` is primarily intended for local kiosk usage. For production kiosks, package as a desktop app (Electron + embedded browser) or run it headless on a small local server and surface via a kiosk browser.
- `cloud_native_app` can be deployed to any Python-friendly PaaS. Use environment variables for Supabase keys.

---

## Troubleshooting & FAQ

- Error: `ModuleNotFoundError: No module named 'cv2'` — Run `pip install opencv-python`.
- Error: `ModuleNotFoundError: No module named 'dotenv'` — Either install `python-dotenv` or ensure `config.py` can load env vars.
- Network errors contacting Supabase — confirm `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` in `.env` and that the machine has outbound network access.

---

## Credits

Author: Arshath Farwyz (project assets and original UI/UX)

This README was produced to provide a single, navigable reference for the workspace. If you want, I can also generate a `docs/` site that renders this README with live embedded previews (3D block, sample camera feed mocking, etc.).

---

License: MIT (apply your preferred license to the repo root)
