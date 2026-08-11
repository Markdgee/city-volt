"""
CityVolt — Agentic Pipeline Orchestrator
==========================================
Chains five agents (Researcher -> Designer -> Maker -> Communicator -> Manager),
each a separate call to the Anthropic API with its own system prompt.

The Researcher is given a real tool (query_eu_vehicle_data) that performs a LIVE
HTTP GET against Eurostat's public REST API (ec.europa.eu) at the moment it is
called. Nothing about the dataset is hardcoded here.

*** DATASET CODE — CONFIRMED FROM EUROSTAT'S OWN ARTICLE ***
DATASET_CODE below (road_eqr_zev) is a real Eurostat table code, confirmed from
the source citation on their "Key figures on transport - passenger car
registrations" Statistics Explained article (road_eqr_zev = zero-emission
vehicle registrations, by country). It was not tool-verified from this sandbox
(no access to ec.europa.eu here), so before your first real run, do one quick
sanity check yourself:
  Paste this into a browser:
  https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/road_eqr_zev?format=JSON&lang=EN
  You should see a wall of JSON. If you instead get an error page, tell Claude
  the exact error and the JSON structure of a working table so the parsing
  logic in this file and docs/index.html can be adjusted.

Note: there is a second related table, road_eqr_carpda (total passenger car
registrations by motor energy, all fuel types). That's useful later if you
want to compute EV *share* of total registrations rather than raw EV counts —
not needed for the current pipeline, but worth knowing it exists.

Usage:
    export ANTHROPIC_API_KEY=sk-ant-...   (never commit this — see .env.example)
    python pipeline.py
"""

import os
import json
import datetime
from pathlib import Path

import requests
import anthropic

MODEL = "claude-sonnet-4-6"
EVIDENCE_DIR = Path(__file__).parent.parent / "evidence"
AGENTS_DIR = Path(__file__).parent.parent / "agents"

# ---------------------------------------------------------------------------
# Live data tool — Eurostat REST API.
# ---------------------------------------------------------------------------
DATASET_CODE = "road_eqr_zev"  # Zero-emission vehicle registrations by country. See docstring above.
EUROSTAT_ENDPOINT = f"https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/{DATASET_CODE}"

EU_DATA_TOOL = {
    "name": "query_eu_vehicle_data",
    "description": (
        "Query live EU vehicle registration statistics from the Eurostat REST API. "
        "Returns real, current data broken down by country (geo) and other "
        "dimensions available on the dataset. Always call this — do not guess at "
        "figures or countries."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "geo": {
                "type": "string",
                "description": (
                    "Optional comma-separated ISO country codes to filter to, "
                    "e.g. 'DE,FR,IT,ES,PL'. Leave blank for all available."
                ),
            },
            "time_period": {
                "type": "string",
                "description": "Optional year or period filter, e.g. '2023'.",
            },
        },
    },
}


def query_eu_vehicle_data(geo=None, time_period=None):
    """Executes a LIVE GET request against Eurostat's REST API. Not cached, not mocked."""
    params = {"format": "JSON", "lang": "EN"}
    if geo:
        params["geo"] = geo
    if time_period:
        params["time"] = time_period

    resp = requests.get(EUROSTAT_ENDPOINT, params=params, timeout=25)
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# Orchestration helpers (identical pattern to a standard pipeline; kept simple
# and readable so it's easy to defend in your Reflection / viva if asked).
# ---------------------------------------------------------------------------

def load_system_prompt(filename: str) -> str:
    text = (AGENTS_DIR / filename).read_text()
    start = text.index("```\n") + 4
    end = text.index("\n```", start)
    return text[start:end]


def save_evidence(stage_name: str, content: str):
    EVIDENCE_DIR.mkdir(exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = EVIDENCE_DIR / f"{ts}_{stage_name}.md"
    path.write_text(content)
    print(f"  [saved -> {path}]")


def run_researcher(client: anthropic.Anthropic) -> str:
    system_prompt = load_system_prompt("01_researcher.md")
    messages = [
        {
            "role": "user",
            "content": (
                "Begin the engagement. Query live EU vehicle registration data using "
                "your tool, find one concrete finding about the affordable/compact EV "
                "segment, and produce your Research Brief."
            ),
        }
    ]

    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1500,
            system=system_prompt,
            tools=[EU_DATA_TOOL],
            messages=messages,
        )
        messages.append({"role": "assistant", "content": response.content})

        tool_calls = [b for b in response.content if b.type == "tool_use"]
        if not tool_calls:
            text = "".join(b.text for b in response.content if b.type == "text")
            return text

        tool_results = []
        for call in tool_calls:
            print(f"  [Marlowe is querying live EU data: {call.input}]")
            try:
                result = query_eu_vehicle_data(**call.input)
                result_text = json.dumps(result, indent=2)[:6000]
            except Exception as e:
                result_text = (
                    f"ERROR querying live data: {e}. road_eqr_zev is a real Eurostat code, "
                    f"but if this still 404s or errors, double check for typos or try the "
                    f"related table road_eqr_carpda instead (see module docstring)."
                )
            tool_results.append(
                {"type": "tool_result", "tool_use_id": call.id, "content": result_text}
            )
        messages.append({"role": "user", "content": tool_results})


def run_agent(client: anthropic.Anthropic, system_file: str, upstream_output: str, opener: str) -> str:
    system_prompt = load_system_prompt(system_file)
    response = client.messages.create(
        model=MODEL,
        max_tokens=1500,
        system=system_prompt,
        messages=[{"role": "user", "content": f"{opener}\n\n---\n\n{upstream_output}"}],
    )
    return "".join(b.text for b in response.content if b.type == "text")


def main():
    client = anthropic.Anthropic()

    print("=== 1/5 Researcher (Marlowe) — querying LIVE EU vehicle data ===")
    research_brief = run_researcher(client)
    print(research_brief)
    save_evidence("01_researcher", research_brief)

    print("\n=== 2/5 Designer (Iris) ===")
    solution_concept = run_agent(
        client, "02_designer.md", research_brief,
        "Here is Marlowe's Research Brief. Design a Solution Concept."
    )
    print(solution_concept)
    save_evidence("02_designer", solution_concept)

    print("\n=== 3/5 Maker (Deshi) ===")
    build_note = run_agent(
        client, "03_maker.md", solution_concept,
        "Here is Iris's Solution Concept. Produce your Build Note."
    )
    print(build_note)
    save_evidence("03_maker", build_note)

    print("\n=== 4/5 Communicator (Sasha) ===")
    marketing = run_agent(
        client, "04_communicator.md", build_note,
        "Here is Deshi's Build Note. Write the Go-to-Market Materials."
    )
    print(marketing)
    save_evidence("04_communicator", marketing)

    print("\n=== 5/5 Manager (Priya) ===")
    chain_context = (
        f"RESEARCH BRIEF:\n{research_brief}\n\n"
        f"SOLUTION CONCEPT:\n{solution_concept}\n\n"
        f"BUILD NOTE:\n{build_note}\n\n"
        f"GO-TO-MARKET MATERIALS:\n{marketing}"
    )
    exec_summary = run_agent(
        client, "05_manager.md", chain_context,
        "Here is the full chain from Marlowe, Iris, Deshi, and Sasha. Write the Executive Summary."
    )
    print(exec_summary)
    save_evidence("05_manager", exec_summary)

    print("\nDone. Full evidence trail saved in ../evidence/")


if __name__ == "__main__":
    main()
