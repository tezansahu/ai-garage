# Agentic Workflow Patterns

## Core Concepts

An agent = LLM + Tools + Loop. The LLM decides which tool to call, observes the result, and
decides what to do next until the task is complete.

---

## Agent Architectures

### ReAct (Reason + Act)
The most common pattern. LLM alternates between reasoning and tool calls.

```
User: "What's the weather in the city where Apple HQ is?"
Agent:
  Thought: I need to find Apple HQ location first.
  Action: search("Apple headquarters location")
  Observation: Cupertino, California
  Thought: Now I can get the weather for Cupertino.
  Action: get_weather("Cupertino, CA")
  Observation: 72F, sunny
  Answer: The weather in Cupertino, CA (Apple HQ) is 72F and sunny.
```

### Multi-Agent
Multiple specialized agents collaborate:
- **Router**: Dispatches to the right specialist agent.
- **Planner**: Breaks complex tasks into sub-tasks.
- **Executor**: Runs individual sub-tasks.
- **Critic**: Reviews outputs for quality.

Use when: Task requires multiple domains of expertise or parallel execution.

### Plan-and-Execute
1. Planner LLM creates a step-by-step plan.
2. Executor LLM runs each step.
3. Re-planning after each step if needed.

Use when: Complex multi-step tasks where upfront planning improves reliability.

---

## Tool Definition Pattern

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "search_database",
            "description": "Search the product database by name or category. Use when the user asks about available products, pricing, or inventory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query string"
                    },
                    "category": {
                        "type": "string",
                        "enum": ["electronics", "clothing", "food"],
                        "description": "Filter by product category"
                    }
                },
                "required": ["query"]
            }
        }
    }
]
```

**Tool design principles:**
- Description is crucial -- it's how the LLM decides when to use the tool.
- Include "Use when..." in the description.
- Keep parameter schemas simple; avoid deeply nested objects.
- Return structured data (JSON), not free text.
- Include error information in tool responses.

---

## Agent Loop Implementation

```python
import openai

def run_agent(user_message: str, tools: list, max_turns: int = 10):
    messages = [
        {"role": "system", "content": AGENT_SYSTEM_PROMPT},
        {"role": "user", "content": user_message}
    ]

    for _ in range(max_turns):
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )
        msg = response.choices[0].message
        messages.append(msg)

        if msg.tool_calls:
            for call in msg.tool_calls:
                result = execute_tool(call.function.name, call.function.arguments)
                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(result)
                })
        else:
            return msg.content  # Agent is done

    return "Agent exceeded maximum turns."
```

---

## Guardrails

- **Max iterations**: Always cap the agent loop (default: 10 turns).
- **Token budget**: Track cumulative tokens; abort if over budget.
- **Tool sandboxing**: Validate tool inputs before execution; never run arbitrary code.
- **Human-in-the-loop**: For high-stakes actions (send email, make purchase), confirm with user.
- **Graceful degradation**: If a tool fails, the agent should note the failure and try an alternative.
