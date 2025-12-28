import asyncio
from agent.model_manager import ModelManager


PROMPT = """You are a planning agent. For any user goal, output a concise, phase-based execution plan with checkboxes and 1–3 sentence guidance per phase.

Rules:
- Phases (in order): Research -> Design -> Development -> Presentation -> Testing/Finalization -> Delivery.
- Under each phase, list 4–8 concrete, ordered tasks with '- [ ]' checkboxes.
- Keep tasks specific, actionable, and scoped to the user's goal; classroom-friendly if educational.
- Include brief tooling/format hints when relevant (e.g., JS/CSS/HTML; Canvas/SVG/Three.js).
- Avoid filler; no prose outside the plan.
- Do not invent constraints beyond the user's ask.
- If animations or code are involved, note frameworks or file types briefly (e.g., HTML/CSS/JS).
- End with a short 'Deliverables' block listing expected artifacts/links/files.

User goal:
'I am a middle school physics teacher preparing to teach the law of conservation of momentum. Could you create a series of clear and accurate demonstration animations and organize them into a simple presentation html?'"""


async def main():
    mm = ModelManager()
    res = await mm.generate_text(PROMPT)
    print(res)


if __name__ == "__main__":
    asyncio.run(main())
