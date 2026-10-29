from pathlib import Path
from dotenv import load_dotenv
from crewai import Agent, Task, Crew

from investigator_crew import call_rpt1
from payload import payload

# Load .env from the same directory as this script
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

# Create a single Loss Appraiser Agent (Exercises 02 & 03 progression)
appraiser_agent = Agent(
    role="Loss Appraiser",
    goal=(
        f"Predict the missing values of stolen items using the RPT-1 model "
        f"via the call_rpt1 tool using this payload {payload} as input."
    ),
    backstory="You are an expert insurance appraiser specializing in fine art valuation and theft assessment.",
    llm="sap/gpt-4o",
    tools=[call_rpt1],
    verbose=True,
)

appraise_loss_task = Task(
    description=(
        f"Analyze the theft crime scene and predict the missing values of stolen items "
        f"using the RPT-1 model via the call_rpt1 tool. Use this dict {payload} as input."
    ),
    expected_output="JSON with predicted values for the stolen items.",
    agent=appraiser_agent,
)

crew = Crew(
    agents=[appraiser_agent],
    tasks=[appraise_loss_task],
    verbose=True,
)


def main():
    result = crew.kickoff(inputs={"payload": payload})
    print("\n" + "=" * 50)
    print("Insurance Appraiser Report:")
    print("=" * 50)
    print(result)


if __name__ == "__main__":
    main()
