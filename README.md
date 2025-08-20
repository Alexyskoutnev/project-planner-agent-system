# Project Planner chatbox
- Guide users through idea development
- Provide recommendations
- Automatically save structured information

Agent Architecture
# Agent 1: The Orchestrator Agent (The "Project Manager")
This is the master controller. It doesn't talk to the user directly but manages the workflow and state of the project planning session.

Core Responsibility: Control the flow of the conversation.

Actions:

Receives initial input from the user.

Delegates the task of asking questions to the Asker Agent.

Keeps track of the information gathered (e.g., project name, goals, tasks).

Decides when enough information has been collected to generate a plan.

Once the information-gathering phase is complete, it hands over the collected data to the Scribe Agent.

# Agent 3: The Asker Agent (The "Interviewer")
This is the conversational "face" of your chatbox. It's an expert at dialogue, guiding the user, and providing helpful advice.

Core Responsibility: Interact with the user to develop the idea.

Actions:

Asks guiding questions to help the user flesh out their project ("What is the main goal of this project?", "Who is the target audience?").

Listens to the user's responses and extracts key information.

Passes this structured information back to the Orchestrator Agent after each interaction.

# Agent 2: The Scribe Agent (The "Documenter")
This agent is a specialist in synthesis and formatting. It doesn't talk to the user; it just takes raw data and turns it into a polished, structured document.

Core Responsibility: Record and structure the final output.

Actions:

Receives the complete set of notes and conversational data from the Orchestrator Agent.

Analyzes the entire conversation.

Generates a well-formatted project document (e.g., a Markdown file, a JSON object, a Notion page).