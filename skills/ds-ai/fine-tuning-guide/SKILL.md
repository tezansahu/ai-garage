---
name: fine-tuning-guide
description: End-to-end LLM fine-tuning workflow -- dataset preparation, LoRA/QLoRA configuration, training, and evaluation. Trigger when the user asks to "fine-tune a model", "fine-tune an LLM", "train a language model", "LoRA", "QLoRA", "adapt a model", "custom model training", "fine-tune BERT/Llama/Mistral/GPT", "prepare training data for fine-tuning", or wants to customize a foundation model for a specific task. Also triggers on "should I fine-tune or prompt engineer", "dataset format for fine-tuning", "how to fine-tune", "Hugging Face training".
---

# Fine-Tuning Guide

Fine-tune language models efficiently with proper data prep, LoRA config, and evaluation.

---

## Workflow

```
1. Decide: fine-tune vs. alternative approaches
2. Prepare dataset
3. Select base model and method
4. Configure and train
5. Evaluate and iterate
```

---

## Step 1 -- Should You Fine-Tune?

| Approach | When | Cost |
|---|---|---|
| **Prompt engineering** | Task achievable with good prompts, sufficient quality | Free |
| **Few-shot examples** | Need consistent format/style, small improvement needed | Free |
| **RAG** | Model needs access to private/up-to-date knowledge | Low |
| **Fine-tuning** | Need specific style/behavior/domain that prompts can't achieve | Moderate |
| **Full training** | Building a new capability from scratch | High |

**Fine-tune when:**
- Prompt engineering gives 70-80% quality but you need 95%+
- You have 100+ high-quality examples of desired behavior
- You need consistent output format that prompts can't reliably enforce
- You're optimizing for cost (fine-tuned small model replaces large model prompting)
- Domain-specific terminology or reasoning patterns needed

---

## Step 2 -- Prepare Dataset

### Format: Instruction Tuning (Chat Format)

```jsonl
{"messages": [{"role": "system", "content": "You are a medical coding assistant."}, {"role": "user", "content": "Code this diagnosis: chest pain on exertion"}, {"role": "assistant", "content": "ICD-10: R07.9 - Chest pain, unspecified. Consider also I20.9 if angina suspected."}]}
{"messages": [{"role": "system", "content": "You are a medical coding assistant."}, {"role": "user", "content": "Code this procedure: knee replacement"}, {"role": "assistant", "content": "CPT: 27447 - Total knee arthroplasty."}]}
```

### Dataset Size Guidelines

| Task | Minimum | Good | Great |
|---|---|---|---|
| Style/format adaptation | 50 | 200 | 500+ |
| Domain knowledge injection | 200 | 500 | 2000+ |
| Complex reasoning | 500 | 2000 | 10000+ |
| Classification | 100/class | 500/class | 2000+/class |

### Quality Checklist

```python
# Validation script for training data
import json
from pathlib import Path

def validate_dataset(path: str):
    issues = []
    examples = [json.loads(l) for l in Path(path).read_text().splitlines() if l.strip()]

    for i, ex in enumerate(examples):
        # Check structure
        if "messages" not in ex:
            issues.append(f"Row {i}: missing 'messages' key")
            continue

        msgs = ex["messages"]
        roles = [m["role"] for m in msgs]

        # Must end with assistant
        if roles[-1] != "assistant":
            issues.append(f"Row {i}: must end with assistant message")

        # Must have at least user + assistant
        if "user" not in roles or "assistant" not in roles:
            issues.append(f"Row {i}: needs both user and assistant messages")

        # Check for empty content
        for m in msgs:
            if not m.get("content", "").strip():
                issues.append(f"Row {i}: empty {m['role']} message")

    print(f"Total examples: {len(examples)}")
    print(f"Issues found: {len(issues)}")
    for issue in issues[:20]:
        print(f"  - {issue}")

    return len(issues) == 0
```

### Train/Val Split
```python
import random
random.seed(42)
random.shuffle(examples)
split = int(len(examples) * 0.9)
train, val = examples[:split], examples[split:]
```

---

## Step 3 -- Select Base Model and Method

### Base Model Selection

| Model | Size | When | Hugging Face ID |
|---|---|---|---|
| Llama 3.1 8B | 8B | General purpose, good quality/size balance | `meta-llama/Llama-3.1-8B-Instruct` |
| Mistral 7B | 7B | Strong for size, fast inference | `mistralai/Mistral-7B-Instruct-v0.3` |
| Phi-3 Mini | 3.8B | Resource constrained, surprisingly capable | `microsoft/Phi-3-mini-4k-instruct` |
| Qwen 2.5 7B | 7B | Strong math / code capabilities | `Qwen/Qwen2.5-7B-Instruct` |
| Gemma 2 9B | 9B | Google ecosystem, strong multilingual | `google/gemma-2-9b-it` |

### Fine-Tuning Method

| Method | VRAM needed | When |
|---|---|---|
| **LoRA** | 8-16 GB | Default -- best quality/efficiency trade-off |
| **QLoRA** | 4-8 GB | Consumer GPU (RTX 3090/4090, T4) |
| **Full fine-tune** | 40+ GB | Maximum quality needed, multi-GPU available |
| **API fine-tune** | None (cloud) | OpenAI or Anthropic models, no GPU available |

---

## Step 4 -- Configure and Train

### LoRA with Hugging Face + PEFT

```python
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer
import torch

# Load model
model_id = "meta-llama/Llama-3.1-8B-Instruct"
tokenizer = AutoTokenizer.from_pretrained(model_id)
tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(
    model_id,
    torch_dtype=torch.bfloat16,
    device_map="auto",
)

# LoRA config
lora_config = LoraConfig(
    r=16,                     # Rank -- higher = more capacity, more VRAM
    lora_alpha=32,            # Scaling factor
    target_modules=["q_proj", "v_proj", "k_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)

model = get_peft_model(model, lora_config)

# Training
training_args = TrainingArguments(
    output_dir="./output",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    lr_scheduler_type="cosine",
    warmup_ratio=0.1,
    bf16=True,
    logging_steps=10,
    save_strategy="epoch",
    evaluation_strategy="epoch",
    save_total_limit=2,
    report_to="none",
)

trainer = SFTTrainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
    tokenizer=tokenizer,
    max_seq_length=2048,
)

trainer.train()
trainer.save_model("./final-model")
```

### QLoRA (4-bit quantization)

Add to model loading:
```python
from transformers import BitsAndBytesConfig

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
)

model = AutoModelForCausalLM.from_pretrained(model_id, quantization_config=bnb_config, device_map="auto")
model = prepare_model_for_kbit_training(model)
```

### Key Hyperparameters

| Parameter | Default | Notes |
|---|---|---|
| LoRA rank (r) | 16 | 8 for simple tasks, 32-64 for complex |
| Learning rate | 2e-4 | Lower (1e-5) if model is forgetting |
| Epochs | 3 | Monitor val loss -- stop if increasing |
| Batch size (effective) | 16 | batch_size * gradient_accumulation |
| Max sequence length | 2048 | Match data; longer = more VRAM |

---

## Step 5 -- Evaluate

### Automated Evaluation

```python
# Generate on held-out test set
model.eval()
results = []
for example in test_set:
    prompt = format_prompt(example["messages"][:-1])  # Everything except target
    output = generate(model, tokenizer, prompt)
    results.append({
        "input": example["messages"][-2]["content"],
        "expected": example["messages"][-1]["content"],
        "generated": output,
    })

# Compute metrics depending on task:
# Classification: accuracy, F1
# Generation: ROUGE, BERTScore, or LLM-as-judge
```

### LLM-as-Judge Evaluation
```python
# Use a strong model (GPT-4o) to evaluate fine-tuned model outputs
judge_prompt = """Rate the following response on a scale of 1-5:
1 = Incorrect/Unhelpful, 5 = Perfect

Question: {question}
Expected: {expected}
Response: {generated}

Score (1-5):"""
```

### What to Check
- **Task accuracy**: Does it get the right answer?
- **Format compliance**: Does it follow the expected output format?
- **Hallucination**: Does it make up information?
- **Catastrophic forgetting**: Can it still do general tasks?
- **Edge cases**: How does it handle unusual or adversarial inputs?
