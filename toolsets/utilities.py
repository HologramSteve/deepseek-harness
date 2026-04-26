from .toolkit import tool, toolset
from datetime import datetime
import math

@toolset
class UtilityToolset:
    @tool
    def get_current_time(self, timezone: str = "local") -> str:
        """Get the current date and time. Use only when needed."""
        return f"The current time is {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    @tool
    def calculate_math(self, expression: str) -> float:
        """Evaluate a mathematical expression. Only use for math."""
        # Note: in a real app, use a safe math parser rather than eval.
        expression = str(expression)
        allowed_names = {k: v for k, v in math.__dict__.items() if not k.startswith("__")}
        return eval(expression, {"__builtins__": {}}, allowed_names)
