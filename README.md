# Deepseek API Harness
> Now with DeepSeek V4 support!

This wrapper allows easy access to the DeepSeek API, [docs here](https://api-docs.deepseek.com/).

> Note this model is biased when it comes to Chinese politics, such as if Taiwan is a country.

## Chapters
1. Getting started
2. Models
3. Temperature
4. Tools
5. Prompting
6. Parralel prompting

## 1. Getting started
The API wrapper resolves around the `Agent` class. This class saves history, allows for tooling, different models, the whole API.
To start, make an instance of the `Agent` class and fill in the following parameters.

- `system_prompt`: the system prompt for the AI. Use this for general purpose. *Note that when not including a 'speak english' section it tends to speak Chinese.*.
- `api_key`: your API key as a string. If left empty, the wrapper falls back to `DEEPSEEK_API_KEY` from your environment or `.env` file.

Create a `.env` file in the project root with:
```env
DEEPSEEK_API_KEY=your-deepseek-api-key
```

Example:
```python
agent = Agent(
  system_prompt="You are a helpful coding assistant. Speak English.",
  api_key="your-deepseek-api-key"
)
```

Then also fill out the following non-required parameters for a better experience.
- `tools`. Default: [], An array of functions that the AI can use. Learn more at the [tools chapter](#4-tools).
- `model`. Default: Models.FLASH. Learn more at the ['models' chapter](2-models). 
- `temperature`. Default: Temperature.CONVERSATION. Learn more at the ['temperature' chapter](#3-temperature).
- `thinking`. Default: `False`. This determines whether the model should think. All models support the thinking mode. This will then return a response called 'reasoning_content' in the reply.
- `expanded_output`. The default max output is `32000` tokens, with this that becomes `384.000` tokens (a lot). We normally prevent unnecessarily long outputs by capping it.
- `on_event`, default = None, a function that will be called on events like tool calls and tool call completions
- `log`: debug logging
- `self_prompt`, default = `False`, allow the AI to spawn subagents to do tasks in parralel.

### Reply
The `prompt()` function will return an instance of the `AIResponse` class.
These are the values it holds:
- `content`: The raw AI reply in text
- `reasoning`: The raw thinking of the AI in text
- `reasoning_tokens`: The amount of tokens used when producing `reasoning`
- `prompt_tokens`: How many tokens the total input was
- `completion_tokens`: How many output tokens were produced
- `total_tokens`: The total amount of tokens handled.

## 2. Models
There are 4 models active (24-4-2026, d-m-y) as of now.
- `deepseek-chat` [Deepseek V4 Flash (non-thinking)](https://api-docs.deepseek.com/news/news260424)
- `deepseek-reasoner` [Deepseek V4 Flash (thinking)](https://api-docs.deepseek.com/news/news260424)
- `deepseek-v4-flash` [Deepseek V4 Flash](https://api-docs.deepseek.com/news/news260424)
- `deepseek-v4-pro` [Deepseek V4 Pro](https://api-docs.deepseek.com/news/news260424)

We only allow access to `deepseek-v4-flash` and `deepseek-v4-pro` with the "Models' enum. This is because `deepseek-chat` and `deepseek-reasoner` will be removed from the API by 24-7-2026 (d-m-y). 
- Models.FLASH for `deepseek-v4-flash`
- Models.PRO for `deepseek-v4-pro`

## 3. Temperature
The temperature inputted determines how creative and unpredictable the model is. We provide an enum based off the offical guide.
- `Temperature.CODING` (0.0) - Used for coding tasks where it needs 1 good output.
- `Temperature.MATH` (0.0) - Used for math where it needs 1 good output.
- `Temperature.DATA_ANALYSIS` (1.0) - Normal temperature for data interaction.
- `Temperature.DATA_CLEANING` (1.0) - Normal temperature for data interaction.
- `Temperature.CONVERSATION` (1.3) - For usage in normal chatbots, for a nice varied conversation.
- `Temperature.TRANSLATION` (1.3) - To get accurate and nice translations.
- `Temperature.WRITING` (1.5) - Used for creative writing.

## 4. Tools
To add a tool the AI can use, write a function, for example.
```python
def get_weather(city):
    """Get the weather for a specific city."""
    return "24 degrees celcius"
```
Note:
- Make sure to describe the function in great detail in the built in python comments with """""".

You can also use toolsets, in the `./toolsets` dir there are a few toolsets to use.
Use 
```python
agent.add_toolset("name")
```
or
```python
agent.add_toolset("all")
```
for all toolsets.

You can add tools to the agent when making the class instance, in an array
```python
tools = [get_weather, ...]
```
or add it later with
```python
agent.add_tool(get_weather)
```

The AI will call the tools and the wrapper does the rest.

> If you made some cool tools, PLEASE share them!!

## 5. Prompting
Get an actual reply out of the model with the `prompt()` function. See all parameters below:
- `message`: The input for the AI model. (required)
- `thinking_mode`: If not enabled at the init, force thinking.
- `remember`: input `False` if the input and answer shouldn't be stored in the history.
- `is_system`: input `True` if the message is said by the system, mostly used internally.
- `stream`: input `True` if you need a stream of the ouput. Uses `yield`.
- `codingLanguage`: The forced coding language, will also make the temperature `Temperature.CODING` and force an output in that language.
- `json_schema`: provide a JSON object here and the AI will turn the `message` into that format. Good for text extraction.
- `max_reasoning`: input `True` for max effort reasoning. Will have better performance but perform worse.

## 6. Parallel Prompt

Runs multiple prompts in parallel. This works like `prompt()`, but accepts an array of messages and processes them concurrently using subagents.

* **prompts**: `list`
  An array of message sets to execute in parallel.

* **max_workers**: `int` *(default: 10)*
  The maximum number of subagents running at the same time.

* **useHistory**: `bool`
  Whether subagents inherit the main agent’s conversation history.

* ****kwargs**
  Additional parameters passed directly to the normal `prompt()` function.

Each prompt is handled by a separate subagent and executed concurrently until all prompts are completed.
