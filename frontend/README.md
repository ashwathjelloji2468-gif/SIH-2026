# SENTRIQ Frontend — Quantum Migration Intelligence SaaS

A cybersecurity SaaS platform for Post-Quantum Cryptography (PQC) readiness, continuous cryptographic discovery, Mosca theorem exposure modeling, and automated NIST PQC migration.

## Tech Stack

- **Framework**: React 19 + TypeScript + Vite 8
- **Styling**: Tailwind CSS v4 + Lucide Icons + JetBrains Mono / Inter typography
- **Routing**: React Router DOM
- **Backend API**: FastAPI backend running on `/api/v1` (CycloneDX 1.6 CBOM, NIST FIPS 203/204/205 catalog)

## Getting Started

### 1. Prerequisites
Ensure the backend server is running on `http://127.0.0.1:8000`.

From the repository root:
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 2. Install Dependencies & Launch Frontend
```bash
cd frontend
npm install
npm run dev
```

The frontend will run at `http://localhost:5173`. In development mode, all `/api/v1` API requests are proxied directly to the backend at `http://127.0.0.1:8000`.

### 3. Production Build
```bash
npm run build
npm run preview
```

## Features

- **Executive Dashboard**: Cryptographic posture KPIs, algorithm distributions, and Harvest Now Decrypt Later (HNDL) alerts.
- **Project Ingestion**: Multi-project management across enterprise repositories (`pyca/cryptography`, `paramiko`, demo banking/health apps).
- **Scan Console**: Live AST & regex scan orchestrator with real-time status transitions (`QUEUED`, `RUNNING`, `COMPLETED`, `FAILED`, `CANCELLED`).
- **Inventory & Evidence Viewer**: WHAT → WHERE → WHY → WHAT NEXT explainability framework with AST code snippet viewer, line highlights, and heuristic unknown triage.
- **Interactive Mosca Analysis Model**: Real-time slider tool for $X$ (data lifetime) + $Y$ (migration time) > $Z$ (threat horizon) with scenario presets.
- **PQC Migration & Sandbox**: Quantified migration roadmaps, AST code transformation simulation (`RSA_TO_ML_KEM_HYBRID`), and automated validation test harness.
- **CycloneDX 1.6 CBOM & Reports**: Cryptographic Bill of Materials viewer, validation check, JSON download, and printable CISO executive audit report.
- **System Telemetry & Audit**: Engine rule versions (`2026.1.0`), health monitoring, and tamper-evident event audit trail.
