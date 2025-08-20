# main.py
from domain_obj import ProjectState
from agents_ import Orchestrator, Asker, Scribe
from agents import Runner

def step_until_user_or_final(session):
    """
    Advance internal agent steps (e.g., Orchestrator checks state and hands off)
    until we either need user input (Asker) or have a final result (Scribe).
    Returns the current step.
    """
    while True:
        step = session.step()
        if step.agent in ("Asker", "Scribe"):
            return step
        # Otherwise Orchestrator (or another internal agent) is doing work; keep stepping.

if __name__ == "__main__":
    breakpoint()
    state = ProjectState()

    print("Project Planner (type 'done' when finished answering)")
    print("----------------------------------------------------")

    session = Runner(
        agents=[Orchestrator],
        entry_agent="Orchestrator",
        state=state,
    )

    try:
        # Prime the loop: run internal logic until the user-facing Asker or terminal Scribe
        step = step_until_user_or_final(session)

        while True:
            if step.agent == "Asker":
                # Ask the model-chosen question
                question = step.message_to_user or "Tell me more about your project."
                print(f"\nAsker: {question}")
                user_input = input("You: ").strip()

                if user_input.lower() == "done":
                    # Optional note back to Asker (could trigger Orchestrator completeness check)
                    session.say("Asker", "User indicates they are done.")
                else:
                    # Let Asker extract structure via its tool(s)
                    session.say("Asker", user_input)

                # After user response, advance until next user question or final output
                step = step_until_user_or_final(session)

            elif step.agent == "Scribe":
                # Scribe returns the final Markdown
                output = step.result  # produced by render_markdown()
                print("\n-------- FINAL PROJECT PLAN (Markdown) --------")
                print(output)
                break

    except KeyboardInterrupt:
        print("\nExiting. Goodbye!")
