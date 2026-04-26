import inspect
from enum import Enum

class Tool():
    def __init__(self, func):
        self.func = func
        self.name = func.__name__
        self.description = func.__doc__ or ""
        self.schema = self._build_schema()
    
    def _build_schema(self):
        sig = inspect.signature(self.func)

        properties = {}
        required = []

        type_map = {
            str: "string",
            int: "integer",
            float: "number",
            bool: "boolean"
        }

        for name, param in sig.parameters.items():
            ann = param.annotation
            json_type = type_map.get(ann, "string")

            properties[name] = {
                "type": json_type,
                "description": name
            }

            # required if no default
            if param.default is inspect.Parameter.empty:
                required.append(name)

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }

    def to_dict(self):
        return self.schema


class Temperature(Enum):
    CODING = 0.0
    MATH = 0.0
    DATA_ANALYSIS = 1.0
    DATA_CLEANING = 1.0
    CONVERSATION = 1.3
    TRANSLATION = 1.3
    WRITING = 1.5

class Models(Enum):
    FLASH = "deepseek-v4-flash"
    PRO = "deepseek-v4-pro"


class AIResponse():
    def __init__(self, data):
        self.prompt_tokens = data.get('prompt_tokens')
        self.total_tokens = data.get('total_tokens')

        debug = data.get('debug', {})
        self.completion_tokens = debug.get('completion_tokens')
        self.reasoning_tokens = debug.get('reasoning_tokens')

        self.content = data.get('content')
        self.reasoning = data.get('reasoning')
