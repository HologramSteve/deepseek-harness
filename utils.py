import importlib.util
import inspect
from pathlib import Path


def getToolSet(name: str):
    path = Path(f"./toolsets/{name}.py")

    if not path.exists():
        raise FileNotFoundError(f"Toolset '{name}' not found")

    # load module dynamically
    spec = importlib.util.spec_from_file_location(f"toolsets.{name}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    tool_functions = []

    # search for class containing tool methods
    for _, obj in inspect.getmembers(module, inspect.isclass):

        for method_name, method in inspect.getmembers(obj, inspect.isfunction):
            if getattr(method, "_is_tool", False):
                instance = obj()  # instantiate class
                tool_functions.append(getattr(instance, method_name))

    return tool_functions

import re

def extract_ai(message: str):
    pattern = re.compile(r"```(\w+)?\n(.*?)```", re.DOTALL)

    result = []
    last_end = 0

    for match in pattern.finditer(message):
        start, end = match.span()
        lang = match.group(1)
        code = match.group(2)

        # Text before the code block
        if start > last_end:
            text = message[last_end:start].strip()
            if text:
                result.append({
                    "type": "text",
                    "content": text
                })

        # Code block
        result.append({
            "type": "code",
            "language": lang or "",
            "content": code.strip()
        })

        last_end = end

    # Remaining text after last code block
    if last_end < len(message):
        text = message[last_end:].strip()
        if text:
            result.append({
                "type": "text",
                "content": text
            })

    return result