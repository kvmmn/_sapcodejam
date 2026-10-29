import sys
from pathlib import Path

VARIANT_DIR = Path(__file__).parent / "with-osint-researcher"
if str(VARIANT_DIR) not in sys.path:
    sys.path.insert(0, str(VARIANT_DIR))

from investigator_crew import InvestigatorOsintCrew  # type: ignore


def run_osint_crew(payload: dict, suspect_names: str):
    return InvestigatorOsintCrew().crew().kickoff(
        inputs={
            "payload": payload,
            "suspect_names": suspect_names,
        }
    )
