from agents import Agent, handoff, function_tool
from domain_obj import ProjectState
import logging

logger = logging.getLogger(__name__)

# --- Tools shared by agents ---

@function_tool  
def record_info(project_name: str = None, 
                goal: str = None,
                audience: str = None, 
                constraints: list[str] = None,
                key_tasks: list[str] = None,
                note: str = None):
    """
    Record any structured fields extracted by the Asker.
    Accepted fields: project_name, goal, audience, constraints, key_tasks, note
    """
    # Get the current state from context (this will be injected by the framework)
    logger.info(f"Recording info: {project_name}, {goal}, {audience}, {constraints}, {key_tasks}, {note}")
    from agents import get_current_span
    ctx = get_current_span().context
    state = ctx.state
    
    if project_name:
        state.project_name = project_name
    if goal:
        state.goal = goal
    if audience:
        state.audience = audience
    if constraints:
        state.constraints.extend(
            c for c in constraints if c and c not in state.constraints
        )
    if key_tasks:
        state.key_tasks.extend(
            t for t in key_tasks if t and t not in state.key_tasks
        )
    if note:
        state.notes.append(note)
    return {"ok": True, "missing": state.missing_fields()}

@function_tool
def is_done() -> bool:
    """Return True if we have enough info to write the plan."""
    from agents import get_current_span
    ctx = get_current_span().context
    state = ctx.state
    return len(state.missing_fields()) == 0

@function_tool
def render_markdown() -> str:
    """Create the final Markdown doc."""
    from agents import get_current_span
    ctx = get_current_span().context
    state = ctx.state
    
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

# --- Helper function ---

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

# --- Agent 3: Asker ("Interviewer") ---

Asker = Agent(
    name="Asker",
    instructions=(
        "You are a friendly project planning assistant having a conversation with a user about their project. "
        
        "Your job is to: "
        "1. Respond naturally and conversationally to what the user says "
        "2. Extract any project information from their message and save it using record_info "
        "3. Ask engaging follow-up questions to learn more "
        
        "Information to gather: project name, goals, target audience, constraints, and key tasks. "
        
        "IMPORTANT: Always use record_info when you learn something new about the project. "
        "Be helpful, engaging, and show genuine interest in their project. "
        "Keep responses concise but friendly."
    ),
    tools=[record_info],
)

# --- Agent 2: Scribe ("Documenter") ---

Scribe = Agent(
    name="Scribe",
    instructions=(
        "You are a professional document writer. Your job is to create a comprehensive project plan document. "
        
        "Use the `render_markdown` tool to generate a well-formatted project document based on all the "
        "information that has been collected during the conversation. "
        
        "Make the document professional, complete, and actionable. Include all available project details."
    ),
    tools=[render_markdown],
)

# --- Agent 1: Orchestrator ("Project Manager") ---

Orchestrator = Agent(
    name="Orchestrator", 
    instructions=(
        "You do not speak to the user. You are the project manager that coordinates the workflow. "
        "First, use `is_done` to check if we have all required information. "
        "If we have everything, hand off to Scribe to generate the final document. "
        "If we're missing information, hand off to Asker to gather more details from the user."
    ),
    tools=[is_done],
    handoffs=["Asker", "Scribe"]
)
