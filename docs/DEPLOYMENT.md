# Deployment & Setup Guide

This guide walks through running **Investigator Crew** locally via the CLI, serving it over the **Agent-to-Agent (A2A)** protocol, deploying it to **SAP BTP Cloud Foundry**, and integrating it into **SAP Joule**.

---

## Prerequisites

- **Python 3.12 or 3.13** (`3.13.11` is used on Cloud Foundry via `runtime.txt`)
- Access to an **SAP BTP Subaccount** with:
  - **SAP AI Core** (`extended` plan) & **Generative AI Hub** deployments for:
    - `gemini-2.5-flash-lite`
    - `gpt-4o`
    - `sap-rpt-1-large` (SAP's Relational Pre-trained Transformer for tabular data)
    - *(Optional, for 4-agent OSINT variant)* `sonar-pro`
  - **SAP Document Grounding Service** vector pipeline populated with the 8 evidence files in [`data/documents/`](../data/documents/)
- *(For Cloud Deployment)* **Cloud Foundry CLI (`cf`)** v8+
- *(For Joule Integration)* **SAP Joule Studio CLI (`joule`)**

---

## 1. Local Setup

### 1.1 Create a Virtual Environment & Install Dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 1.2 Configure Environment Variables

Copy the template and fill in your SAP AI Core service key credentials:

```bash
cp .env.example .env
```

Required variables in `.env`:

| Variable | Description |
| :--- | :--- |
| `LITELLM_PROVIDER` | Set to `sap` |
| `AICORE_AUTH_URL` | OAuth2 URL from your `generative-ai-hub` service key |
| `AICORE_CLIENT_ID` | Client ID from your service key |
| `AICORE_CLIENT_SECRET` | Client secret from your service key |
| `AICORE_BASE_URL` | AI Core API base URL (`.../v2`) |
| `AICORE_RESOURCE_GROUP` | Resource group containing your model deployments (e.g., `ai-agents-codejam`) |
| `RPT1_DEPLOYMENT_URL` | Full `/predict` inference URL for your `sap-rpt-1-large` deployment |
| `GROUNDING_PIPELINE_ID` | Vector pipeline ID from SAP AI Launchpad containing the documents in `data/documents/` |

---

## 2. Running Locally via CLI

### Standard 3-Agent Crew (SAP Grounding Service + SAP-RPT-1 + Gen AI Hub)

```bash
python main.py
```

### Local Evidence Fallback (No Vector Pipeline Required)

If you want to test the CrewAI workflow before setting up the Grounding Service vector pipeline in SAP AI Launchpad, pass `--local-evidence` (or set `USE_LOCAL_EVIDENCE_FALLBACK=true` in `.env`) to search `./data/documents/*.txt` directly:

```bash
python main.py --local-evidence
```

### 4-Agent OSINT Crew Variant (`+ Perplexity sonar-pro`)

To include the fourth agent (**Open-Source Intelligence Researcher**) that cross-references internal evidence with web searches via `sap/sonar-pro`:

```bash
python main.py --with-osint
```

### Single-Agent Starter (`basic_agent.py`)

To test only the `Loss Appraiser` agent and `SAP-RPT-1` tabular prediction tool in isolation:

```bash
python basic_agent.py
```

---

## 3. Running the A2A Server Locally

Start the FastAPI A2A server on `http://localhost:8080`:

```bash
python server.py
```

### Verify Health & A2A Agent Card

In a second terminal:

```bash
# 1. Check health endpoint
curl http://localhost:8080/health

# 2. Inspect the A2A AgentCard discovery document
curl -s http://localhost:8080/.well-known/agent-card.json | python3 -m json.tool
```

### Send a Test A2A JSON-RPC `message/send` Request

```bash
curl -X POST http://localhost:8080/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "test-1",
    "method": "message/send",
    "params": {
      "message": {
        "role": "user",
        "messageId": "msg-1",
        "parts": [
          {
            "kind": "text",
            "text": "Sophie Dubois, Marcus Chen, Viktor Petrov"
          }
        ]
      }
    }
  }'
```

---

## 4. Deploying to SAP BTP Cloud Foundry

1. **Review `manifest.yml`**:
   Update the application `name` (e.g. `investigator-crew-<your-suffix>`), `AICORE_RESOURCE_GROUP`, `RPT1_DEPLOYMENT_URL`, and `GROUNDING_PIPELINE_ID` to match your SAP BTP environment.
2. **Log in to Cloud Foundry and push**:

```bash
cf login --sso
cf push
```

> **Note:** `.cfignore` automatically excludes `.env`, `docs/`, `assets/`, `data/`, and local virtual environments so your credentials never leave your laptop and the droplet stays compact. On Cloud Foundry, SAP AI Core credentials are injected automatically via the bound `generative-ai-hub` service instance.

---

## 5. Integrating with SAP Joule

1. **Create a BTP Destination**:
   In SAP BTP Cockpit (**Connectivity → Destinations**), create an HTTP destination (e.g., `INVESTIGATOR_AGENT_025`) pointing to your Cloud Foundry application URL (`https://investigator-crew-<suffix>.cfapps.<region>.hana.ondemand.com`) with `Authentication: NoAuthentication`.
2. **Update the System Alias**:
   In [`joule/investigator_capability/capability.sapdas.yaml`](../joule/investigator_capability/capability.sapdas.yaml), verify that `destination` under `system_aliases.INVESTIGATOR_AGENT` matches your BTP Destination name.
3. **Compile and Deploy the Digital Assistant Capability**:

```bash
cd joule
joule login
joule deploy -c -n <your_assistant_name>
```

Once deployed, open SAP Joule and ask:
> *"Investigate the art theft case for suspects Sophie Dubois, Marcus Chen, and Viktor Petrov."*
