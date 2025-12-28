from utils.utils import log_step, log_error
import argparse
import asyncio
import json
import os
import subprocess
from pathlib import Path
import yaml
from dotenv import load_dotenv
from mcp_servers.multiMCP import MultiMCP
from agent.agent_loop3 import AgentLoop  # 🆕 Use loop3
from pprint import pprint

BANNER = """
──────────────────────────────────────────────────────
🔸  Agentic Query Assistant  🔸
Type your question and press Enter.
Type 'exit' or 'quit' to leave.
──────────────────────────────────────────────────────
"""

POLICY_PREAMBLE = """POLICY:
- Do not sign in, create accounts, or enter passwords/OTP/payment details.
- If a login wall appears, stop and report BLOCKED_BY_POLICY.
- Save artifacts to ./outputs and reference exact file paths in the final JSON.
"""


def load_mcp_configs():
    with open("config/mcp_server_config.yaml", "r", encoding="utf-8") as f:
        profile = yaml.safe_load(f)
        return list(profile.get("mcp_servers", []))


def ensure_dirs(*paths: Path):
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)


def verify_evidence(evidence_items):
    results = []
    for item in evidence_items or []:
        file_path = Path(item.get("file", "")).expanduser()
        exists = file_path.exists()
        results.append({"file": str(file_path), "exists": exists})
    return results


def start_recording(flow_id: str, run_dir: Path):
    cmd = (Path("scripts/obs_start.cmd")
           if Path("scripts/obs_start.cmd").exists()
           else None)
    env_cmd = os.getenv("OBS_START_CMD")
    command = None
    if env_cmd:
        command = env_cmd.format(flow_id=flow_id, run_dir=str(run_dir.resolve()))
    elif cmd:
        command = f'"{cmd}" "{flow_id}" "{run_dir.resolve()}"'
    if not command:
        return None
    log_step(f"🎥 Starting recording for {flow_id}", symbol="🎥")
    try:
        return subprocess.Popen(command, shell=True)
    except Exception as e:
        log_error("OBS start failed", e)
        return None


def stop_recording(flow_id: str, proc=None):
    env_cmd = os.getenv("OBS_STOP_CMD")
    if proc:
        try:
            proc.terminate()
        except Exception:
            pass
    if env_cmd:
        try:
            subprocess.Popen(env_cmd.format(flow_id=flow_id), shell=True)
        except Exception as e:
            log_error("OBS stop failed", e)


async def interactive(loop: AgentLoop) -> None:
    log_step(BANNER, symbol="")
    conversation_history = []

    while True:
        print("\n\n")
        query = input("📝  You: ").strip()
        if query.lower() in {"exit", "quit"}:
            log_step("Goodbye!", symbol="👋")
            break

        # Construct context string from past rounds
        context_prefix = ""
        for idx, (q, r) in enumerate(conversation_history, start=1):
            context_prefix += f"Query {idx}: {q}\nResponse {idx}: {r}\n"

        full_query = context_prefix + f"Query {len(conversation_history)+1}: {query}"

        try:
            response = await loop.run(full_query)  # 🔄 stateless loop sees full pseudo-history
            conversation_history.append((query, response.strip()))
            log_step("Agent Resting now", symbol="😴")
        except Exception as e:
            if "Unknown SSE event" in str(e):
                pass  # suppress event noise like ping
            else:
                log_error("Agent failed", e)

        follow = input("Continue? (press Enter) or type 'exit': ").strip()
        if follow.lower() in {"exit", "quit"}:
            log_step("Goodbye!", symbol="👋")
            break


async def run_flows(flows_file: str, loop: AgentLoop):
    flows_path = Path(flows_file)
    if not flows_path.exists():
        raise FileNotFoundError(f"Flows file not found: {flows_file}")

    flows_data = yaml.safe_load(flows_path.read_text(encoding="utf-8")) or {}
    flows = flows_data.get("flows", [])
    if not flows:
        log_error("No flows defined in flows.yaml")
        return

    runs_root = Path("runs")
    outputs_root = Path("outputs")
    ensure_dirs(runs_root, outputs_root)

    results_index = []

    for flow in flows:
        flow_id = flow.get("id") or f"flow_{len(results_index)}"
        prompt_body = flow.get("prompt", "").strip()
        full_prompt = f"{POLICY_PREAMBLE.strip()}\n\nTASK:\n{prompt_body}"

        flow_dir = runs_root / flow_id
        ensure_dirs(flow_dir)

        log_step(f"🚀 Running flow: {flow_id}", symbol="🚀")
        recorder_proc = start_recording(flow_id, flow_dir)
        response = await loop.run(full_prompt)
        stop_recording(flow_id, recorder_proc)

        evidence_results = verify_evidence(flow.get("evidence", []))
        success = getattr(loop, "status", "") == "success" and all(r["exists"] for r in evidence_results)

        trace = {
            "flow_id": flow_id,
            "prompt": full_prompt,
            "response": response,
            "success": success,
            "evidence": evidence_results,
            "artifacts_dir": str(flow_dir.resolve()),
            "session": loop.session.to_json() if getattr(loop, "session", None) else {},
            "context": loop.ctx.get_context_snapshot() if getattr(loop, "ctx", None) else {},
        }

        trace_path = flow_dir / "result.json"
        trace_path.write_text(json.dumps(trace, indent=2), encoding="utf-8")
        log_step(f"📝 Saved run result: {trace_path}", symbol="📝")

        results_index.append(
            {
                "flow_id": flow_id,
                "success": success,
                "result_path": str(trace_path.resolve()),
            }
        )

    index_path = runs_root / "index.json"
    index_path.write_text(json.dumps(results_index, indent=2), encoding="utf-8")
    log_step(f"📚 Wrote run index: {index_path}", symbol="📚")


async def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Agentic Query Assistant")
    parser.add_argument("--run", dest="flows_file", help="Path to flows.yaml for scripted runs")
    args = parser.parse_args()

    log_step('Loading MCP Servers...', symbol="📥")
    configs = load_mcp_configs()
    multi_mcp = MultiMCP(server_configs=configs)
    await multi_mcp.initialize()

    loop = AgentLoop(
        perception_prompt="prompts/perception_prompt.txt",
        decision_prompt="prompts/decision_prompt.txt",
        browser_decision_prompt="prompts/browser_decision_prompt.txt",
        summarizer_prompt="prompts/summarizer_prompt.txt",
        multi_mcp=multi_mcp,
        strategy="exploratory"
    )

    try:
        if args.flows_file:
            await run_flows(args.flows_file, loop)
        else:
            await interactive(loop)
    finally:
        await multi_mcp.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
