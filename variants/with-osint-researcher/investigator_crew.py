from crewai import Agent, Crew, Task, Process
from crewai.project import CrewBase, agent, task, crew
from crewai.tools import tool

from investigator_crew import call_rpt1, call_grounding_service


@tool("call_sonar_pro_search")
def call_sonar_pro_search(search_query: str) -> str:
    """Search the web using Perplexity's sonar-pro model on SAP Generative AI Hub
    for real-time intelligence about crimes, suspects, and criminal patterns.

    Args:
        search_query: The search query about crimes, suspects, or criminal patterns

    Returns:
        Search results with source citations from the web
    """
    from litellm import completion

    try:
        response = completion(
            model="sap/sonar-pro",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a web search assistant specializing in criminal intelligence. "
                        "Search for accurate, recent information and always provide source citations with URLs and dates."
                    ),
                },
                {"role": "user", "content": search_query},
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error calling sonar-pro web search: {str(e)}"


@CrewBase
class InvestigatorOsintCrew:
    """Four-agent sequential crew adding the OSINT Researcher (sap/sonar-pro) from Exercise 06."""

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
    def intelligence_researcher_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["intelligence_researcher_agent"],
            verbose=True,
            tools=[call_sonar_pro_search],
        )

    @task
    def research_criminal_network(self) -> Task:
        return Task(
            config=self.tasks_config["research_criminal_network"],
            context=[self.analyze_evidence_task()],
        )

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
            context=[
                self.appraise_loss_task(),
                self.analyze_evidence_task(),
                self.research_criminal_network(),
            ],
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
