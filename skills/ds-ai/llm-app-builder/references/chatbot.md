# Chatbot Patterns

## Architecture

```
User Message -> Conversation Memory -> System Prompt + Context -> LLM -> Response
                     ^                                                      |
                     +------------------------------------------------------+
```

---

## Conversation Memory Strategies

| Strategy | When to use | Implementation |
|---|---|---|
| Full history | Short conversations (<20 turns) | Pass all messages to LLM |
| Sliding window | Long conversations | Keep last N messages (default: 20) |
| Summary + recent | Very long conversations | Summarize older messages, keep last 5-10 verbatim |
| RAG-enhanced | Knowledge-heavy chatbots | Retrieve relevant past messages + knowledge base chunks |

---

## System Prompt Template

```python
CHATBOT_SYSTEM_PROMPT = """You are {bot_name}, a {role_description}.

## Personality
- {personality_trait_1}
- {personality_trait_2}

## Rules
- {rule_1}
- {rule_2}
- If you don't know something, say so honestly.
- Keep responses concise unless the user asks for detail.

## Knowledge
{optional_knowledge_base_context}
"""
```

---

## Multi-Turn Implementation

```python
from openai import OpenAI

client = OpenAI()

def chat(messages: list[dict], user_input: str) -> str:
    messages.append({"role": "user", "content": user_input})

    response = client.chat.completions.create(
        model="gpt-4o-mini",  # Use cheaper model for chat
        messages=messages,
        temperature=0.7,
        max_tokens=1024
    )
    reply = response.choices[0].message.content
    messages.append({"role": "assistant", "content": reply})
    return reply
```

---

## UI Options

| Framework | Best for | Setup complexity |
|---|---|---|
| Streamlit `st.chat_input` | Quick prototypes | Minimal |
| Gradio `ChatInterface` | HF ecosystem, sharing | Minimal |
| Chainlit | Production chat UIs | Moderate |
| Next.js + Vercel AI SDK | Production web apps | Higher |

**Default**: Streamlit for prototypes. Example:

```python
import streamlit as st
from openai import OpenAI

st.title("My Chatbot")
client = OpenAI()

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

for msg in st.session_state.messages[1:]:  # Skip system prompt
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if prompt := st.chat_input("Type a message..."):
    reply = chat(st.session_state.messages, prompt)
    st.rerun()
```

---

## Production Considerations

- **Rate limiting**: Implement per-user rate limits (e.g., 20 messages/minute).
- **Content filtering**: Add input/output moderation (OpenAI Moderation API or custom rules).
- **Conversation persistence**: Store conversations in a database for analytics and debugging.
- **Streaming**: Use streaming responses for better UX (reduces perceived latency).
- **Fallback**: If LLM API is down, return a friendly error message rather than crashing.
