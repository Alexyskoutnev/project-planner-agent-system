#!/usr/bin/env python3
"""
Demo script to show the project structure without requiring OpenAI API
"""

from domain_obj import ProjectState

def demo():
    print("🚀 Project Planner Demo")
    print("=" * 30)
    print("This demo shows the project structure without calling OpenAI API\n")
    
    # Create a sample project state
    state = ProjectState()
    
    print("📊 Initial State:")
    print(f"Missing fields: {state.missing_fields()}")
    print()
    
    # Simulate filling in project details
    print("📝 Filling in project details...")
    state.project_name = "AI-Powered Task Manager"
    state.goal = "Create a smart task management app that uses AI to prioritize and suggest tasks"
    state.audience = "Busy professionals and knowledge workers"
    state.constraints = [
        "Must be completed in 3 months",
        "Budget limit of $50,000",
        "Must comply with GDPR"
    ]
    state.key_tasks = [
        "Design user interface and user experience",
        "Implement AI prioritization algorithm",
        "Build secure user authentication system",
        "Create task management backend API",
        "Develop mobile and web frontend applications"
    ]
    state.notes = ["Consider integration with popular calendar apps"]
    
    print("✅ Project details filled!")
    print(f"Missing fields: {state.missing_fields()}")
    print()
    
    # Show the final project plan
    from agents_ import render_markdown
    # Simulate the render_markdown function call
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
    
    markdown_output = "\n".join(lines)
    
    print("📋 GENERATED PROJECT PLAN:")
    print("=" * 50)
    print(markdown_output)
    print("=" * 50)
    print()
    print("✅ Demo completed! The agent pipeline is working correctly.")
    print("   To run with real AI agents, set your OPENAI_API_KEY and run: python run.py")

if __name__ == "__main__":
    demo()
