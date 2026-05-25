import os
import json
import inspect
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from openai import OpenAI
from enums import *
from utils import getToolSet

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

DEFAULT_API_KEY = os.getenv("DEEPSEEK_API_KEY")


class Agent():
    def add_toolset(self, name):
        if name.lower() == "all":
            added = []
            for filename in os.listdir("toolsets"):
                if filename.endswith(".py") and not filename.startswith("__") and filename != "toolkit.py":
                    toolset_name = filename[:-3]
                    self.add_toolset(toolset_name)
                    added.append(toolset_name)
            return f"Toolsets added: {', '.join(added)}"

        functions = getToolSet(name.lower())

        for func in functions:
            t = Tool(func)
            self.tools.append(t.schema)
            self.tool_map[t.name] = t.func
        
        return f"Toolset '{name}' added!"
    
    def scaled_prompt(self, prompts):
        """Spin up multiple subagents based on the prompts array of prompt. Will return an array of prompt completions."""
        if isinstance(prompts, str):
            prompts = json.loads(prompts)
        return str(self.parallel_prompt(prompts, 10, True))


    def execute_tool(self, tool_call):
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)

        func = self.tool_map[name]   # <-- direct lookup
        return func(**args)
    
    def test_api_key(self, key):
        url = "https://api.deepseek.com/user/balance"

        payload={}
        headers = {
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + key
        }

        response = requests.request("GET", url, headers=headers, data=payload).json()
        
        return response['is_available']



    def addHistory(self, message, is_system=False):
        author = ""
        if is_system:
            author = "system"
        else:
            author = "user"
        self.history.append({"role": author, "content": message})
        return True
    
    def clear_reasoning(self):
        for item in self.history:
            if hasattr(item, 'reasoning_content'):
                item.reasoning_content = None

    def set_max_output(self, expanded_output=False):
        # max token outu
        if self.model == Models.FLASH:
            if expanded_output:
                self.max_output = 384000
            else:
                self.max_output = 32000
        elif self.model == Models.PRO:
            if expanded_output:
                self.max_output = 384000
            else:
                self.max_output = 64000
        else:
            raise ValueError("Can't decide expanded output.")
        
        return True
    
    def clear_history(self):
        self.history = []
        self.addHistory(self.sysprompt, True)

        return self.history


    def add_tool(self, func):
        tool = Tool(func)
        self.tools.append(tool.schema)
        self.tool_map[tool.name] = tool.func

        return True

    def __init__(self, system_prompt, api_key=None, tools=None, model=None, temperature=Temperature.CONVERSATION, thinking=False, expanded_output=False, on_event=None, log=False, self_prompt=False):
        self.on_event = on_event
        self.log = log
        self.api_key = api_key or DEFAULT_API_KEY

        if not self.api_key:
            raise ValueError("Api key not found. Pass api_key to Agent or set DEEPSEEK_API_KEY in your environment or .env file.")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.deepseek.com/beta"
        )
        
        # test api key
        is_available = self.test_api_key(self.api_key)
        if not is_available:
            raise KeyError("API key invalid. It's possible your API key is invalid itself or your balance is not enough.")

        if not tools:
            tools = []

        # add the own tool
        if self_prompt:
            tools.append(self.scaled_prompt)

        # store tools locally correctly
        if tools:
            tools = [Tool(func) for func in tools]

        if tools is not None:
            self.tools = [t.schema for t in tools]
            self.tool_map = {t.name: t.func for t in tools}
        else:
            self.tools = []
            self.tool_map = {}

        # determine model used
        if model is None:
            self.model = Models.FLASH
        else:
            self.model = model
        
        # max token outu
        self.set_max_output(expanded_output=expanded_output)
        
        self.thinking = thinking
        self.applyThinkingRules = self.thinking
        
        # self.force_thinking = force_thinking
        self.history = []
        self.sysprompt = system_prompt
        self.addHistory(system_prompt, True)
        
        
        # determine temp
        if isinstance(temperature, Temperature):
            self.temperature = temperature.value
        elif isinstance(temperature, (int, float)):
            self.temperature = float(temperature)
        else:
            self.temperature = 1.3
        
    def prompt(self, message, thinking_mode=False, remember=True, is_system=False, stream=False, codingLanguage=None, json_schema=None, max_reasoning=False):
        extra_body = {"thinking": {"type": "disabled"}}
        reasoning_effort = None
        if thinking_mode or self.thinking:
            extra_body = {"thinking": {"type": "enabled"}}

            if max_reasoning:
                reasoning_effort = "max"
            else:
                reasoning_effort = "high"

        if is_system:
            author = "system"
        else:
            author = "user"
            
        
        # force json?
        old_max_output = self.max_output
        response_format = None
        if json_schema != None:
            # force_json = True
            response_format = {'type': 'json_object'}
            self.set_max_output(True)
            
            message = message + ". JSON  schema you should use: " + str(json_schema)

        messages = self.history + [{'role': author, "content": message}]

        # force stop when done coding with stop = ['```']
        stop = None
        if codingLanguage != None:
            stop = []
            stop.append("```")

            old_temp = self.temperature
            self.temperature = Temperature.CODING

            # force model to start writing code
            messages.append(
                {"role": "assistant", "content": "```" + codingLanguage.lower() + "\n", "prefix": True}
            )
        else:
            old_temp = self.temperature

        kwargs = {}
        if response_format is not None:
            kwargs["response_format"] = response_format
        
        

        response = self.client.chat.completions.create(
            model=self.model.value,
            messages=messages,
            stream=stream,
            temperature=self.temperature,
            extra_body=extra_body,
            max_tokens=self.max_output,
            tools=self.tools,
            stop=stop,
            reasoning_effort=reasoning_effort,
            **kwargs
        )

        self.temperature = old_temp
        self.max_output = old_max_output

        
        if remember:
            self.addHistory(message, is_system)
            
        if stream:
            def generate():
                full_content = ""
                full_reasoning = ""
                tool_calls_dict = {}

                for chunk in response:
                    delta = chunk.choices[0].delta
                    content_chunk = getattr(delta, "content", "") or ""
                    reasoning_chunk = getattr(delta, "reasoning_content", "") or ""
                    
                    full_content += content_chunk
                    full_reasoning += reasoning_chunk
                    
                    # Buffer streaming tool calls
                    tool_calls_chunk = getattr(delta, "tool_calls", None)
                    if tool_calls_chunk:
                        for tc in tool_calls_chunk:
                            idx = tc.index
                            if idx not in tool_calls_dict:
                                tool_calls_dict[idx] = {
                                    "id": tc.id or f"call_{idx}",
                                    "function": {"name": getattr(tc.function, "name", "") or "", "arguments": ""}
                                }
                            if getattr(tc.function, "arguments", None):
                                tool_calls_dict[idx]["function"]["arguments"] += tc.function.arguments

                    # Only yield if there's actual text content to show
                    if content_chunk or reasoning_chunk:
                        yield {
                            "content": content_chunk,
                            "reasoning": reasoning_chunk,
                            "full_content": full_content,
                            "full_reasoning": full_reasoning,
                            "is_finished": getattr(chunk.choices[0], "finish_reason", None) is not None
                        }
                
                if tool_calls_dict:
                    # Reconstruction of the tool_calls for execution
                    class DummyFunction:
                        def __init__(self, name, arguments):
                            self.name = name
                            self.arguments = arguments
                    class DummyToolCall:
                        def __init__(self, id, function):
                            self.id = id
                            self.function = function

                    parsed_calls = []
                    history_tool_calls = []
                    for idx, tc_data in sorted(tool_calls_dict.items()):
                        parsed_calls.append(DummyToolCall(tc_data["id"], DummyFunction(tc_data["function"]["name"], tc_data["function"]["arguments"])))
                        history_tool_calls.append({
                            "id": tc_data["id"],
                            "type": "function",
                            "function": {
                                "name": tc_data["function"]["name"],
                                "arguments": tc_data["function"]["arguments"]
                            }
                        })
                    
                    # Store the original AI message with the tool call
                    message_to_save = {
                        "role": "assistant",
                        "content": full_content or None,
                        "tool_calls": history_tool_calls
                    }
                    if full_reasoning: message_to_save["reasoning_content"] = full_reasoning
                    self.history.append(message_to_save)

                    # Execute the tools sequentially
                    for call in parsed_calls:
                        try:
                            args = json.loads(call.function.arguments, strict=False)
                        except json.JSONDecodeError:
                            args = {}
                        
                        name = call.function.name
                        if self.on_event: self.on_event("tool_call", {"name": name, "args": args})
                        result = self.execute_tool(call)
                        
                        self.history.append({
                            "role": "tool",
                            "tool_call_id": call.id,
                            "content": str(result)
                        })
                        if self.on_event: self.on_event("tool_result", {"name": name, "result": str(result)})

                    # Continue streaming the follow up
                    yield from self.prompt("Tool(s) executed. Please continue.", is_system=True, remember=False, stream=True)
                else:
                    if remember:
                        self.history.append({"role": "assistant", "content": full_content})

            return generate()
            

        tool_calls = response.choices[0].message.tool_calls

        if tool_calls is None:
            tool_calls = []
            
        if len(tool_calls) > 0:
            # Append the actual tool execution to history so the model knows it was executed
            self.history.append(response.choices[0].message)
            
            for call in tool_calls:
                try:
                    args = json.loads(call.function.arguments, strict=False)
                except json.JSONDecodeError:
                    # Sometimes the model produces invalid JSON (like unescaped quotes)
                    # For safety, pass an empty dict, or a special error to the tool.
                    args = {}
                    print(f"Warning: Failed to parse tool arguments for {call.function.name}. Using empty args.")
                
                name = call.function.name

                if self.on_event:
                    self.on_event("tool_call", {"name": name, "args": args})

                result = self.execute_tool(call)

                reasoning = getattr(response.choices[0].message, "reasoning_content", None)

                self.history.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": str(result),
                    "reasoning_content": reasoning
                })
                
                if self.on_event:
                    self.on_event("tool_result", {"name": name, "result": str(result)})

            # Send the result back to the model, without saving "Continue" to history
            return self.prompt((
                "Tool(s) executed. Please continue." " "
                ), is_system=True, remember=False)




        

        if len(tool_calls) == 0 and remember:
            # Only append the text response if there are no tool calls
            self.history.append({"role": "assistant", "content": response.choices[0].message.content})

        data = {
            "prompt_tokens": getattr(response.usage, "prompt_tokens", 0) if response.usage else 0,
            "total_tokens": getattr(response.usage, "total_tokens", 0) if response.usage else 0,
            "debug": {
                "completion_tokens": getattr(response.usage, "completion_tokens", 0) if response.usage else 0,
                "reasoning_tokens": getattr(getattr(response.usage, "completion_tokens_details", None), "reasoning_tokens", 0) if response.usage else 0
            },
            "content": response.choices[0].message.content,
            "reasoning": getattr(response.choices[0].message, "reasoning_content", None)
        }

        # log
        if self.log:
            os.makedirs("ai-logs", exist_ok=True)
            

            path = os.path.join("ai-logs", datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".log")
            with open(path, "w", encoding="utf-8") as f:
                f.write(data['content'])



        self.clear_reasoning()
        return AIResponse(data)
    
    def parallel_prompt(self, prompts, max_workers=10, useHistory=True, **kwargs):
        results = [None] * len(prompts)

        base_history = list(self.history) if useHistory else []
        # Exclude any trailing tool calls in history that haven't been resolved yet
        if base_history:
            last_msg = base_history[-1]
            if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
                base_history = base_history[:-1]
            elif isinstance(last_msg, dict) and last_msg.get('tool_calls'):
                base_history = base_history[:-1]

        def run(index, message):
            local_agent = Agent(self.sysprompt, api_key=self.api_key, model=self.model)
            local_agent.history = list(base_history)
            response = local_agent.prompt(message, **kwargs)
            return index, response

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(run, i, p)
                for i, p in enumerate(prompts)
            ]

            for future in as_completed(futures):
                i, res = future.result()
                results[i] = res

        return results
