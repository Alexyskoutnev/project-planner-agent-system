from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

@dataclass
class ProjectState:
    project_name: Optional[str] = None
    goal: Optional[str] = None
    audience: Optional[str] = None
    constraints: list[str] = field(default_factory=list)
    key_tasks: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    
    def missing_fields(self) -> list[str]:
        missing = []
        if not self.project_name:
            missing.append("project_name")
        if not self.goal:
            missing.append("goal")
        if not self.audience:
            missing.append("audience")
        if not self.constraints:
            missing.append("constraints")
        if not self.key_tasks:
            missing.append("key_tasks")
        return missing
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for serialization"""
        return {
            "project_name": self.project_name,
            "goal": self.goal,
            "audience": self.audience,
            "constraints": self.constraints,
            "key_tasks": self.key_tasks,
            "notes": self.notes
        }