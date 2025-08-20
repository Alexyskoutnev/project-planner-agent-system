import os
import logging
from domain_obj import ProjectState
from agents_ import Orchestrator, Asker, Scribe
from agents import Runner, RunConfig

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('project_planner.log')
    ]
)

logger = logging.getLogger(__name__)

def interactive_project_planner():
    
    state = ProjectState()
    logger.info("Initialized project state")
    
    print("🚀 Interactive Project Planner")
    print("=" * 40)
    print("I'll help you plan your project step by step!")
    print("You can type 'quit' at any time to exit.\n")
    
    conversation_history = []
    
    try:
        while True:
            missing = state.missing_fields()
            
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("👋 Goodbye!")
                break
                
            if not user_input:
                print("Please tell me something about your project.")
                continue
            
            conversation_history.append(f"User: {user_input}")
            logger.info(f"User input: {user_input}")
            
            context_messages = "\n".join(conversation_history[-5:])  # Last 5 messages
            full_input = f"Previous conversation:\n{context_messages}\n\nLatest user input: {user_input}"
            
            print("\n🤖 Processing with AI agents...")
            logger.info("Starting agent workflow")
            
            result = Runner.run_sync(
                starting_agent=Orchestrator,
                input=full_input,
                context=state,
                max_turns=100,
                run_config=RunConfig(
                    workflow_name="Project Planner",
                    trace_include_sensitive_data=False
                )
            )
            
            logger.info(f"Agent workflow completed. Output type: {type(result.output)}")
            
            if isinstance(result.output, str) and result.output.startswith("#"):
                print("\n📋 FINAL PROJECT PLAN GENERATED!")
                print("=" * 50)
                print(result.output)
                print("=" * 50)
                
                while True:
                    choice = input("\nWould you like to (c)ontinue editing, (s)ave to file, or (q)uit? ").lower()
                    if choice.startswith('c'):
                        break
                    elif choice.startswith('s'):
                        filename = input("Enter filename (or press Enter for 'project_plan.md'): ").strip()
                        if not filename:
                            filename = "project_plan.md"
                        with open(filename, 'w') as f:
                            f.write(result.output)
                        print(f"✅ Saved to {filename}")
                        break
                    elif choice.startswith('q'):
                        print("👋 Goodbye!")
                        return
                    else:
                        print("Please enter 'c', 's', or 'q'")
                        
            else:
                # Show agent response
                response = str(result.output)
                print(f"\n🤖 AI: {response}")
                conversation_history.append(f"AI: {response}")
                logger.info(f"AI response: {response}")
            
            # Show updated state info
            print(f"\n📊 Current project state:")
            if state.project_name:
                print(f"   📝 Project: {state.project_name}")
            if state.goal:
                print(f"   🎯 Goal: {state.goal}")
            if state.audience:
                print(f"   👥 Audience: {state.audience}")
            if state.constraints:
                print(f"   ⚠️  Constraints: {', '.join(state.constraints)}")
            if state.key_tasks:
                print(f"   ✅ Key Tasks: {len(state.key_tasks)} items")
            if state.notes:
                print(f"   📌 Notes: {len(state.notes)} items")
                
            print("-" * 50)
                
    except KeyboardInterrupt:
        print("\n👋 Exiting. Goodbye!")
    except Exception as e:
        logger.error(f"Error in agent workflow: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        print("Check the logs for more details.")

if __name__ == "__main__":
    interactive_project_planner()