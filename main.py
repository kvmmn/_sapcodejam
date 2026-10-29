import argparse
import os

from investigator_crew import InvestigatorCrew
from payload import payload

DEFAULT_SUSPECTS = "Sophie Dubois, Marcus Chen, Viktor Petrov"


def main():
    parser = argparse.ArgumentParser(
        description="Run the Investigator Crew art-heist detective team on SAP BTP."
    )
    parser.add_argument(
        "--suspects",
        default=DEFAULT_SUSPECTS,
        help=f"Comma-separated suspect names (default: '{DEFAULT_SUSPECTS}')",
    )
    parser.add_argument(
        "--with-osint",
        action="store_true",
        help="Run the 4-agent variant that includes the OSINT Researcher (sap/sonar-pro).",
    )
    parser.add_argument(
        "--local-evidence",
        action="store_true",
        help="Read evidence from local ./data/documents/*.txt instead of SAP Grounding Service.",
    )
    args = parser.parse_args()

    if args.local_evidence:
        os.environ["USE_LOCAL_EVIDENCE_FALLBACK"] = "true"

    if args.with_osint:
        from variants.with_osint_researcher_runner import run_osint_crew
        result = run_osint_crew(payload=payload, suspect_names=args.suspects)
    else:
        result = InvestigatorCrew().crew().kickoff(
            inputs={
                "payload": payload,
                "suspect_names": args.suspects,
            }
        )

    print("\n📘 Result:\n", result)


if __name__ == "__main__":
    main()
