def tool(func):
    func._is_tool = True
    return func

def toolset(cls):
    cls._is_toolset = True
    return cls