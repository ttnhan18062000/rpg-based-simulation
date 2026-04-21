import json
from dataclasses import dataclass, asdict
from typing import Dict, Any

@dataclass(slots=True)
class Sub:
    name: str

@dataclass(slots=True)
class Top:
    payload: Dict[str, Any]

data = Top(payload={"state": Sub(name="item")})
raw = asdict(data)
print(f"Raw: {raw}")
print(f"Type of state in payload: {type(raw['payload']['state'])}")
