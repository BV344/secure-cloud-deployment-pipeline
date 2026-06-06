# Secure Cloud Deployment Pipeline

A fully automated DevSecOps pipeline that takes a containerized web application from code commit to production deployment — with security scanning gates at every step. No code ships unless it passes secret scanning and vulnerability checks.

Built and deployed on self-hosted Linux infrastructure (Ubuntu Server 24.04 on a MacBook Pro 2018 with T2 chip support).

---

## The Problem This Solves

Most developers push code and hope nothing is wrong. This pipeline makes security non-negotiable — secrets accidentally committed to git are caught before they reach the repo, vulnerable Docker images are blocked before they reach production, and every deployment is automated and reproducible.

---

## Live Demo

Application deployed and running at `http://bv344server:8080`

Health check endpoint: `http://bv344server:8080/health`

Docker image: [hub.docker.com/r/bv344/secure-pipeline](https://hub.docker.com/r/bv344/secure-pipeline)

---

## Pipeline Architecture

```
Developer pushes code to GitHub
            ↓
    ┌───────────────────┐
    │  Security Scanning │
    │                   │
    │  Gitleaks         │ ← scans full git history for secrets
    │  Trivy            │ ← scans Docker image for CVEs
    │                   │
    │  CRITICAL found?  │
    │  Pipeline FAILS ❌ │
    └───────────────────┘
            ↓ passes
    ┌───────────────────┐
    │  Build & Push     │
    │                   │
    │  Docker build     │
    │  Push to          │
    │  Docker Hub       │
    └───────────────────┘
            ↓
    ┌───────────────────┐
    │  Deploy           │
    │                   │
    │  Tailscale VPN    │ ← connects runner to private network
    │  SSH into server  │
    │  Pull latest image│
    │  Restart container│
    └───────────────────┘
            ↓
    App live on bv344server:8080 ✅
```

---

## Security Features

### Secret Scanning — Gitleaks
Every push triggers a full scan of the git history for accidentally committed secrets — API keys, tokens, passwords, AWS credentials. The pipeline fails immediately if anything is found. Nothing reaches production with exposed credentials.

### Container Vulnerability Scanning — Trivy
The Docker image is scanned against the CVE database before it can be pushed to Docker Hub. Any CRITICAL severity vulnerability blocks the pipeline with a hard exit code 1.

**Real finding from this project:**
Trivy detected two CRITICAL CVEs in the `python:3.12-slim` base image:
- `CVE-2026-42496` — path traversal via crafted symlinks in perl-base
- `CVE-2026-8376` — heap buffer overflow in Perl compiler

Both had `fix_deferred` status — no upstream fix available. The correct response was to document them in `.trivyignore` with justification rather than ignore them silently:

```
# perl-base CVEs in python:3.12-slim base image
# Status: fix_deferred — no fix available upstream as of 2026-06-06
# Accepted risk: perl-base is not used by our application
CVE-2026-42496
CVE-2026-8376
```

This is real DevSecOps decision making — not every CVE can be fixed immediately, but every accepted risk must be documented.

### Hardened Docker Container
- Non-root user (`appuser` UID 100) — container compromise doesn't mean host compromise
- `python:3.12-slim` base image — minimal attack surface
- `--no-cache-dir` — no pip cache stored in image layers
- Resource limits — `--memory=128m`, `--cpus=0.5`
- `--restart unless-stopped` — automatic recovery from crashes

### Private Network Deployment — Tailscale
The server runs on a private home network with no public internet exposure. GitHub Actions connects to it via Tailscale — an encrypted WireGuard-based mesh VPN — using ephemeral OAuth credentials tagged `tag:ci`. The runner joins the private network, deploys, and disappears. The server is never exposed to the public internet.

### GitHub Secrets Management
All sensitive values — Docker Hub credentials, SSH keys, server address — are stored as encrypted GitHub Secrets. They are never hardcoded in code or visible in logs.

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Application | Python Flask |
| Containerization | Docker |
| Container Registry | Docker Hub |
| CI/CD | GitHub Actions |
| Secret Scanning | Gitleaks |
| Vulnerability Scanning | Trivy |
| Private Networking | Tailscale (WireGuard) |
| Server OS | Ubuntu Server 24.04 LTS |
| Hardware | MacBook Pro 2018 (T2 chip, t2linux kernel) |

---

## Project Structure

```
secure-cloud-deployment-pipeline/
├── app/
│   ├── app.py              # Flask application
│   ├── requirements.txt    # Python dependencies
│   ├── Dockerfile          # Hardened container definition
│   └── .trivyignore        # Documented CVE exceptions
├── infrastructure/
│   └── hardening-checklist.md
├── monitoring/
├── .github/
│   └── workflows/
│       └── pipeline.yml    # Full CI/CD pipeline definition
└── README.md
```

---

## Pipeline Breakdown

### Job 1 — Security Scanning
```yaml
- Checkout code (full git history for Gitleaks)
- Run Gitleaks secret scan
- Build Docker image
- Run Trivy vulnerability scan (exit-code: 1 on CRITICAL)
```

### Job 2 — Build and Push
*Only runs if Job 1 passes*
```yaml
- Login to Docker Hub
- Build and push image with SHA tag and latest tag
```

### Job 3 — Deploy
*Only runs if Job 2 passes*
```yaml
- Connect to Tailscale private network
- SSH into bv344server
- Pull latest image from Docker Hub
- Stop and remove old container
- Run new container with resource limits
```

---

## Running Locally

### Prerequisites
- Docker installed
- Python 3.12+

### Clone and run

```bash
git clone git@github.com:BV344/secure-cloud-deployment-pipeline.git
cd secure-cloud-deployment-pipeline

# Build the image
docker build -t secure-pipeline ./app

# Run the container
docker run -d \
  --name secure-pipeline \
  --memory=128m \
  --cpus=0.5 \
  -p 8080:8080 \
  secure-pipeline
```

Visit `http://localhost:8080`

### Run security scans locally

```bash
# Secret scanning
gitleaks detect --source . -v

# Vulnerability scanning
trivy image secure-pipeline
```

---

## Key Lessons Learned

**Trivy blocking on unfixable CVEs** — the first pipeline run failed because Trivy found two CRITICAL CVEs with no available fix. The solution wasn't to lower the severity threshold or disable scanning — it was to investigate, document the accepted risk in `.trivyignore`, and move forward with justification. That's a real security decision.

**Private infrastructure deployment** — deploying to a home server from GitHub Actions requires solving a real networking problem. Tailscale provides a production-grade solution without exposing the server to the internet. This pattern is used in real enterprise environments.

**Security gates compound** — Gitleaks catches secrets before they spread. Trivy catches vulnerabilities before they ship. Together they create a pipeline where the path of least resistance is the secure path.

---

## Part of the DevSecOps Lab

This project is the Week 23 capstone of a structured 24-week DevSecOps self-study program.

Full learning journey: [github.com/BV344/devsecops-lab](https://github.com/BV344/devsecops-lab)
