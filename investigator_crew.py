import json
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the same directory as this script BEFORE importing crewai
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)
os.environ.setdefault("CREWAI_TRACING_ENABLED", "false")

from crewai import Agent, Crew, Task, Process
from crewai.project import CrewBase, agent, task, crew
from crewai.tools import tool
from gen_ai_hub.proxy.native.sap.client import RPTClient
from gen_ai_hub.document_grounding.client import RetrievalAPIClient
from gen_ai_hub.document_grounding.models.retrieval import (
    RetrievalSearchInput,
    RetrievalSearchFilter,
)
from gen_ai_hub.orchestration.models.document_grounding import DataRepositoryType

DEFAULT_GROUNDING_PIPELINE_ID = "0d3b132a-cbe1-4c75-abe7-adfbbab7e002"
DEFAULT_RPT1_MODEL_NAME = "sap-rpt-1-large"


def _search_local_evidence(user_question: str, max_chunks: int = 5) -> str:
    """Optional local fallback that searches ./data/documents/*.txt when USE_LOCAL_EVIDENCE_FALLBACK=true."""
    docs_dir = Path(__file__).parent / "data" / "documents"
    if not docs_dir.exists():
        return json.dumps({"error": f"Local evidence directory not found at {docs_dir}"})

    terms = [
        t.lower()
        for t in user_question.replace(",", " ").replace(".", " ").split()
        if len(t) > 2
    ]
    scored = []
    for doc_path in sorted(docs_dir.glob("*.txt")):
        content = doc_path.read_text(encoding="utf-8")
        content_lower = content.lower()
        score = sum(content_lower.count(term) for term in terms)
        scored.append((score, doc_path.name, content))

    scored.sort(key=lambda item: (-item[0], item[1]))
    chunks = [
        {"document": name, "relevance_score": score, "content": text}
        for score, name, text in scored[:max_chunks]
    ]
    return json.dumps({"source": "local_evidence_fallback", "chunks": chunks}, indent=2)


@tool("call_rpt1")
def call_rpt1(payload: dict) -> str:
    """Call SAP-RPT-1 tabular foundation model to predict missing values in the payload.

    Args:
        payload: A dictionary containing the stolen items data with [PREDICT] placeholders.
                 This should be the exact payload provided in the task inputs.

    Returns:
        JSON string with predicted insurance values and item categories.
    """
    model_name = os.getenv("RPT1_MODEL_NAME", DEFAULT_RPT1_MODEL_NAME)
    try:
        rpt1_client = RPTClient()
        response = rpt1_client.predict(body=payload, model_name=model_name)
        if response:
            return json.dumps(response.json(), indent=2)
        return f"Error {response.status_code}: {response.text}"
    except Exception as e:
        return f"Error calling RPT-1: {str(e)}"


@tool("call_grounding_service")
def call_grounding_service(user_question: str) -> str:
    """Call the SAP Document Grounding Service to retrieve relevant case evidence chunks."""
    max_chunks = int(os.getenv("GROUNDING_MAX_CHUNKS", "5"))

    if os.getenv("USE_LOCAL_EVIDENCE_FALLBACK", "false").lower() in ("1", "true", "yes"):
        return _search_local_evidence(user_question, max_chunks=max_chunks)

    pipeline_id = os.getenv("GROUNDING_PIPELINE_ID", DEFAULT_GROUNDING_PIPELINE_ID)
    try:
        retrieval_client = RetrievalAPIClient()
        search_filter = RetrievalSearchFilter(
            id="vector",
            dataRepositoryType=DataRepositoryType.VECTOR.value,
            dataRepositories=[pipeline_id],
            searchConfiguration={"maxChunkCount": max_chunks},
        )
        search_input = RetrievalSearchInput(
            query=user_question,
            filters=[search_filter],
        )
        response = retrieval_client.search(search_input)
        return json.dumps(response.model_dump(), indent=2)
    except Exception as e:
        return f"Error calling Grounding Service: {str(e)}"


@CrewBase
class InvestigatorCrew:
    """Three-agent sequential investigation crew on SAP BTP (Loss Appraiser -> Evidence Analyst -> Lead Detective)."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def appraiser_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["appraiser_agent"],
            verbose=True,
            tools=[call_rpt1],
        )

    @task
    def appraise_loss_task(self) -> Task:
        return Task(config=self.tasks_config["appraise_loss_task"])

    @agent
    def evidence_analyst_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["evidence_analyst_agent"],
            verbose=True,
            tools=[call_grounding_service],
        )

    @task
    def analyze_evidence_task(self) -> Task:
        return Task(config=self.tasks_config["analyze_evidence_task"])

    @agent
    def lead_detective_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["lead_detective_agent"],
            verbose=True,
        )

    @task
    def solve_crime(self) -> Task:
        return Task(
            config=self.tasks_config["solve_crime"],
            context=[self.appraise_loss_task(), self.analyze_evidence_task()],
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,  # Automatically collected by @agent decorator (all 3 agents)
            tasks=self.tasks,    # Automatically collected by @task decorator (all 3 tasks)
            process=Process.sequential,  # Tasks run in order: appraise -> analyze -> solve
            verbose=True,
        )
