#!/usr/bin/env python3
"""
Simple console chat with backend agent processing
"""

import os
from domain_obj import ProjectState
from agents_ import Orchestrator, Asker, Scribe
from agents import Runner

class ProjectPlannerBackend:
    """Backend that handles agent processing"""
    
    def __init__(self):
        self.state = ProjectState()
        self.conversation = []
        
    def process_user_input(self, 
                           user_input: str,
                           max_turns: int = 10):
        
        self.conversation.append(f"User: {user_input}")
        
        try:
            recent_context = "\n".join(self.conversation[:])
            
            enhanced_input = f"""
Previous conversation:
{recent_context}

Current user message: {user_input}

Instructions: You are a friendly project planning assistant. Respond naturally to the user's message about their project. 
When you learn project information, use the record_info tool to save it. 
Ask engaging follow-up questions to learn about: project name, goals, target audience, constraints, and key tasks.
Be conversational and helpful.
"""
            
            # Run the Asker agent with enhanced context
            result = Runner.run_sync(
                starting_agent=Asker,
                input=enhanced_input,
                context=self.state,
                max_turns=max_turns
            )
            response = str(result.final_output)
            self.conversation.append(f"AI: {response}")
            return response
            
        except Exception as e:
            return f"Sorry, I had an issue: {e}"
    
    def generate_final_document(self):
        """Generate final project document"""
        try:
            result = Runner.run_sync(
                starting_agent=Scribe,
                input="Generate the final project document",
                context=self.state,
                max_turns=2
            )
            return str(result.output)
        except Exception as e:
            return f"Error generating document: {e}"
    
    def get_status(self):
        """Get current project status"""
        missing = self.state.missing_fields()
        status = f"""
Project: {self.state.project_name or 'Not set'}
Goal: {self.state.goal or 'Not set'}
Audience: {self.state.audience or 'Not set'}
Constraints: {len(self.state.constraints)} items
Tasks: {len(self.state.key_tasks)} items
Missing: {', '.join(missing) if missing else 'Nothing - ready to generate document!'}
"""
        return status.strip()

def main():
    
    backend = ProjectPlannerBackend()
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() == 'quit':
                print("Goodbye!")
                break
                
            elif user_input.lower() == 'status':
                print(backend.get_status())
                
            elif user_input.lower() == 'done':
                print("\nGenerating your project document...")
                document = backend.generate_final_document()
                print("\n" + "="*50)
                print("YOUR PROJECT DOCUMENT")
                print("="*50)
                print(document)
                print("="*50)
                
                # Save option
                save = input("\nSave to file? (y/n): ").strip().lower()
                if save.startswith('y'):
                    filename = input("Filename (or Enter for project_plan.md): ").strip() or "project_plan.md"
                    with open(filename, 'w') as f:
                        f.write(document)
                    print(f"Saved to {filename}")
                break
                
            else:
                response = backend.process_user_input(user_input, max_turns=10)
                print(f"AI: {response}")
                
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
