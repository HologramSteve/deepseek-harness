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

