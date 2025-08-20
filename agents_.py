from agents import Agent, handoff, tool, function_tool
from domain_obj import ProjectState

# --- Tools shared by agents ---

@function_tool  
def record_info(state: ProjectState, 
                **kwargs):
    """
    Record any structured fields extracted by the Asker.
    Accepted keys: project_name, goal, audience, constraints, key_tasks, note
    """
    if "project_name" in kwargs and kwargs["project_name"]:
        state.project_name = kwargs["project_name"]
    if "goal" in kwargs and kwargs["goal"]:
        state.goal = kwargs["goal"]
    if "audience" in kwargs and kwargs["audience"]:
        state.audience = kwargs["audience"]
    if "constraints" in kwargs and kwargs["constraints"]:
        state.constraints.extend(
            c for c in kwargs["constraints"] if c and c not in state.constraints
        )
    if "key_tasks" in kwargs and kwargs["key_tasks"]:
        state.key_tasks.extend(
            t for t in kwargs["key_tasks"] if t and t not in state.key_tasks
        )
    if "note" in kwargs and kwargs["note"]:
        state.notes.append(kwargs["note"])
    return {"ok": True, "missing": state.missing_fields()}

@function_tool
def is_done(state: ProjectState) -> bool:
    """Return True if we have enough info to write the plan."""
    return len(state.missing_fields()) == 0

@function_tool
def render_markdown(state: ProjectState) -> str:
    """Create the final Markdown doc."""
    title = state.project_name or "Untitled Project"
    lines = [
        f"# {title}",
        "",
        "## Overview",
        f"- **Goal:** {state.goal or '—'}",
        f"- **Audience:** {state.audience or '—'}",
        "",
        "## Constraints",
    ]
    lines += [f"- {c}" for c in (state.constraints or ["—"])]
    lines += ["", "## Key Tasks"]
    lines += [f"- {t}" for t in (state.key_tasks or ["—"])]
    if state.notes:
        lines += ["", "## Notes"] + [f"- {n}" for n in state.notes]
    return "\n".join(lines)

# --- Agent 3: Asker ("Interviewer") ---

Asker = Agent(
    name="Asker",
    instructions=(
        "You are the interviewing face of the chat. Ask one concise question at a time. "
        "When the user answers, extract fields with `record_info` (use function args!) and "
        "then yield control back to Orchestrator. Keep a helpful, pragmatic tone. "
        "Focus first on: project_name, goal, audience. Then gather constraints, key_tasks."
    ),
    tools=[record_info],           # Asker only needs to write info
    allow_handoff=True
)

# --- Agent 2: Scribe ("Documenter") ---

Scribe = Agent(
    name="Scribe",
    instructions=(
        "You never talk to the user. You synthesize the final Markdown using `render_markdown` "
        "and return it as the single output message content."
    ),
    tools=[render_markdown],
    allow_handoff=False
)

# --- Agent 1: Orchestrator ("Project Manager") ---

def _missing_prompt(missing: list[str]) -> str:
    order = ["project_name", "goal", "audience", "constraints", "key_tasks"]
    missing_sorted = [f for f in order if f in missing]
    field = missing_sorted[0] if missing_sorted else "goal"
    mapping = {
        "project_name": "What would you like to call this project?",
        "goal": "What is the primary objective or outcome you want?",
        "audience": "Who is the target audience or end user?",
        "constraints": "Any constraints (time, budget, data, compliance)?",
        "key_tasks": "List 3–5 key tasks or milestones.",
    }
    return mapping.get(field, "Could you add more detail?")

Orchestrator = Agent(
    name="Orchestrator",
    instructions=(
        "You do not speak to the user. You decide whether more info is needed. "
        "Use `is_done` to check completeness. If not done, hand off to Asker with a single "
        "clear question to ask the user (put it in `message_to_user`). If done, hand off to Scribe."
    ),
    tools=[is_done],
    allow_handoff=True,
    # A small controller to decide next step after each turn:
    controller=lambda ctx: (
        handoff("Scribe") if ctx.tools.is_done()
        else handoff("Asker", message_to_user=_missing_prompt(ctx.state.missing_fields()))
    )
)
