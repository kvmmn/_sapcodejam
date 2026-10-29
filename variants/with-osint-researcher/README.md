# 4-Agent OSINT Variant (Exercise 06 Snapshot)

This directory contains the **four-agent** configuration of the Investigator Crew, which adds an **Open-Source Intelligence (OSINT) Researcher** powered by Perplexity's `sap/sonar-pro` model on SAP Generative AI Hub:

1. **Loss Appraiser** (`sap/gemini-2.5-flash-lite` + `call_rpt1`)
2. **Evidence Analyst** (`sap/gemini-2.5-flash-lite` + `call_grounding_service`)
3. **OSINT Researcher** (`sap/gpt-4o` + `call_sonar_pro_search` via `sap/sonar-pro`)
4. **Lead Detective** (`sap/gpt-4o`)

## Running the 4-Agent Variant

You can run this variant directly from the repository root with the `--with-osint` flag:

```bash
python main.py --with-osint
```

Or copy these files into the root project to make the 4-agent crew the default:

```bash
cp variants/with-osint-researcher/investigator_crew.py ./investigator_crew.py
cp variants/with-osint-researcher/config/agents.yaml ./config/agents.yaml
cp variants/with-osint-researcher/config/tasks.yaml ./config/tasks.yaml
```
