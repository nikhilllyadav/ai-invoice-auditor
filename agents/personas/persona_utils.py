from typing import Any
import yaml

def load_persona(name: str) -> dict[str, Any]:
    """
    This is a utility function to load a persona file by its name.
    """
    persona = None
    with open(f"./agents/personas/{name}.yaml", "r") as f:
        persona = yaml.safe_load(f)
    
    return persona