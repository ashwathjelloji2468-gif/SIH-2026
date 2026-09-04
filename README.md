<div align="center">

# 🛡️ SENTRIQ
### **Quantum Migration Intelligence & Continuous Cryptographic Agility**

[![CI/CD Pipeline](https://github.com/ashwathjelloji2468-gif/SIH-2026/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/ashwathjelloji2468-gif/SIH-2026/actions)
[![CycloneDX 1.6](https://img.shields.io/badge/CBOM-CycloneDX%201.6-06B6D4?style=flat-square&logo=json)](https://cyclonedx.org)
[![NIST Standards](https://img.shields.io/badge/NIST-FIPS%20203%20%7C%20204%20%7C%20205-10B981?style=flat-square)](https://csrc.nist.gov/projects/post-quantum-cryptography)
[![Frontend](https://img.shields.io/badge/Frontend-React%2019%20%7C%20Vite%208%20%7C%20Tailwind-38BDF8?style=flat-square&logo=react)](https://react.dev)
[![Backend](https://img.shields.io/badge/Backend-FastAPI%20%7C%20Python%203.11-4F46E5?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![Deployment](https://img.shields.io/badge/Deploy-Vercel%20%2B%20Render-black?style=flat-square&logo=vercel)](https://vercel.com)

<p align="center">
  <b>Empowering CISOs, security architects, and cryptographic engineers to discover, model, and migrate enterprise infrastructure to Post-Quantum Cryptography (PQC).</b>
</p>

[Explore Features](#-key-capabilities) • [Architecture](#-system-architecture) • [Getting Started](#-getting-started) • [Mosca Theorem](#-mosca-threat-engine) • [Deployment](#-cloud-deployment)

---

</div>

## 🌐 Overview

The advent of Cryptanalytically Relevant Quantum Computers (CRQCs) renders classical public-key cryptography (RSA, ECC, Diffie-Hellman) obsolete via Shor’s Algorithm. Today’s critical enterprise data is already exposed to **Harvest Now, Decrypt Later (HNDL)** adversarial interception.

**SENTRIQ** is an enterprise-grade cybersecurity SaaS platform providing end-to-end Quantum Migration Intelligence. It combines deterministic AST/regex source discovery, scientific threat modeling, automated code refactoring simulation, and official **CycloneDX 1.6 Cryptographic Bill of Materials (CBOM)** generation.

---

## 🎯 The Core Product Workflow

SENTRIQ enforces a coherent 10-stage transition lifecycle:

```mermaid
flowchart LR
    A[Discover] --> B[Understand]
    B --> C[Prove]
    C --> D[Assess]
    D --> E[Prioritize]
    E --> F[Recommend]
    F --> G[Simulate]
    G --> H[Validate]
    H --> I[Plan]
    I --> J[Monitor]
```

### The 4-Step Explainability Framework
Every cryptographic finding within the platform deterministically answers:
1. **WHAT**: Identifies the primitive (`RSA`, `ECDSA`, `AES-128`), key size, and cryptographic purpose.
2. **WHERE**: Precise repository path, source file location, and line numbers with code snippets.
3. **WHY**: Quantum vulnerability rationale separated from detection confidence (0.00–1.00).
4. **WHAT NEXT**: Replacement pathway to NIST-standardized Post-Quantum algorithms (`ML-KEM-768`, `ML-DSA-65`, `SLH-DSA`).

---

## ✨ Key Capabilities

| Capability | Description | Standards |
| :--- | :--- | :--- |
| **AST Codebase Discovery** | Recursively analyzes AST nodes and cryptographic imports to locate algorithms, keys, and protocols. | Python AST, Regex Heuristics |
| **CycloneDX 1.6 CBOM** | Full-fidelity machine-readable Cryptographic Bill of Materials export, validation, and JSON download. | CycloneDX v1.6 Spec |
| **Interactive Mosca Simulator** | Computes the fundamental inequality $X + Y > Z$ to detect active Harvest Now, Decrypt Later (HNDL) exposure windows. | Dr. Michele Mosca Model |
| **NIST PQC Catalog** | Integrated knowledge base of standardized post-quantum candidate algorithms and parameter sets. | FIPS 203, FIPS 204, FIPS 205 |
| **Sandbox Refactoring** | Isolated code transformation simulations (e.g. `RSA_TO_ML_KEM_HYBRID`) with diff viewers. | AST Rewriting Engine |
| **Regression Validation Suite** | Automated test runner verifying build integrity, unit test pass rates, and residual risk scores. | Automated Test Harness |
| **Executive PDF Reporting** | Clean, printable CISO reports summarizing enterprise posture, exposure gap, and milestones. | Audit & Compliance Ready |
| **Tamper-Evident Audit Trail** | Immutable chronological logs tracking scans, classifications, and human reviews. | Governance & Telemetry |

---

## 📐 System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           SENTRIQ FRONTEND                              │
│             React 19 • Vite 8 • Tailwind CSS v4 • Lucide Icons          │
├─────────────┬─────────────┬─────────────┬─────────────┬─────────────────┤
│  Dashboard  │  Inventory  │ Risk/Mosca  │  Migration  │  Reports (CBOM) │
└──────▲──────┴──────▲──────┴──────▲──────┴──────▲──────┴────────▲────────┘
       │             │             │             │               │
       └─────────────┴─────────────┼─────────────┴───────────────┘
                                   │ /api/v1 REST
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           FASTAPI BACKEND                               │
│              Python 3.11 • SQLAlchemy ORM • Pydantic v2                 │
├─────────────────┬───────────────────┬──────────────────┬────────────────┤
│ Source Scanners │ Knowledge Base    │ Risk Calculator  │ CBOM Generator │
│ (AST & Regex)   │ (NIST PQC 2026.3) │ (Mosca & Impact) │ (CycloneDX 1.6)│
└────────┬────────┴─────────┬─────────┴────────┬─────────┴────────┬───────┘
         │                  │                  │                  │
         ▼                  ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              PERSISTENCE & STORAGE (SQLite / PostgreSQL)                │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🧮 Mosca Threat Engine

The platform implements the mathematical urgency condition:

$$\mathbf{X + Y > Z}$$

- **$X$ (Data Shelf-Life)**: How long sensitive customer, medical, or classified data must remain secure (e.g., 10–30 years).
- **$Y$ (Migration Time)**: Time required to refactor enterprise infrastructure and achieve cryptographic agility (e.g., 2–5 years).
- **$Z$ (Quantum Threat Horizon)**: Anticipated arrival of Cryptanalytically Relevant Quantum Computers (CRQCs) (Target: **2033**).

> **Exposure Rule:** If $X + Y > Z$, data is already compromised by adversaries harvesting encrypted traffic today.

---

## 🚀 Getting Started

### Prerequisites
- **Node.js**: `v20+` or `v24+`
- **Python**: `v3.11+`
- **Git**

---

### Local Installation

#### 1. Clone the Repository
```bash
git clone https://github.com/ashwathjelloji2468-gif/SIH-2026.git
cd SIH-2026
```

#### 2. Start the Backend API
```bash
cd backend
python -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
*The FastAPI backend will be live at `http://127.0.0.1:8000` (`/docs` for Swagger).*

#### 3. Start the Frontend Application
In a new terminal window:
```bash
cd frontend
npm install
npm run dev
```
*The SENTRIQ UI will be live at `http://localhost:5173`.*

---

## ☁️ Cloud Deployment

The repository includes pre-configured deployment templates:

### 1. Backend on Render
- Infrastructure declared in [`render.yaml`](./render.yaml).
- In the [Render Dashboard](https://dashboard.render.com), choose **New + Blueprint** and select this repository.
- Render configures Python 3.11, dependencies, and `/api/v1/health` probes automatically.

### 2. Frontend on Vercel
- SPA rewrites declared in [`frontend/vercel.json`](./frontend/vercel.json).
- In the [Vercel Dashboard](https://vercel.com), import this repository:
  - **Root Directory**: `frontend`
  - **Build Command**: `npm run build`
  - **Output Directory**: `dist`
  - **Environment Variable**: `VITE_API_URL` = `https://your-render-app.onrender.com`

### 3. Continuous Integration & Delivery
- Automated via [`.github/workflows/ci-cd.yml`](./.github/workflows/ci-cd.yml).
- Automatically triggers linting, TypeScript compilation, and pytest execution on all pull requests and pushes to `main`.

---

## 🧪 Automated Testing

### Backend Test Suite
```bash
cd backend
PYTHONPATH=. pytest tests/ -v
```

### Frontend Build Verification
```bash
cd frontend
npm run build
```

---

## 📜 Scientific Standards & References
- **NIST FIPS 203**: Module-Lattice-Based Key-Encapsulation Mechanism (ML-KEM)
- **NIST FIPS 204**: Module-Lattice-Based Digital Signature Algorithm (ML-DSA)
- **NIST FIPS 205**: Stateless Hash-Based Digital Signature Algorithm (SLH-DSA)
- **CycloneDX v1.6**: Cryptographic Bill of Materials (CBOM) Schema

---

## ⚖️ License & Disclosure
Distributed under the MIT License.

> **Disclaimer**: *SENTRIQ communicates statistical coverage and algorithmic limitations. 100% cryptographic discovery is never claimed; heuristic unknowns require human architectural review.*
