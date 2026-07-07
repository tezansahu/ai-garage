---
name: nn-architect
description: Design and implement neural network architectures in PyTorch or Keras from task descriptions. Trigger when the user asks to "build a neural network", "design a CNN/RNN/transformer", "deep learning model", "PyTorch model", "Keras model", "neural net for images/text/tabular", "create a training loop", "implement attention", or describes a deep learning task. Also triggers on "what architecture should I use", "training not converging", "model architecture advice", or requests for specific components like "add batch normalization", "implement dropout", "learning rate scheduler".
---

# NN Architect

Design, implement, and train neural networks with production-quality code and best practices.

---

## Workflow

```
1. Understand task and data
2. Select architecture (references/architectures.md)
3. Implement model
4. Implement training loop
5. Add training utilities (checkpointing, logging, scheduling)
```

---

## Step 1 -- Task Identification

| Task | Data type | Architecture family |
|---|---|---|
| Image classification | Images | CNN (ResNet, EfficientNet) or ViT |
| Object detection | Images + boxes | YOLO, Faster R-CNN |
| Text classification | Text sequences | Transformer encoder (BERT) |
| Text generation | Text sequences | Transformer decoder (GPT) |
| Tabular classification/regression | Structured | MLP, TabNet, FT-Transformer |
| Time series forecasting | Sequential numeric | LSTM, Temporal CNN, Transformer |
| Recommendation | User-item interactions | Embedding + MLP |
| Anomaly detection | Various | Autoencoder, VAE |

---

## Step 2 -- Select Architecture

Read `references/architectures.md` for detailed architecture selection guidance.

---

## Step 3 -- Implement Model

**Default framework**: PyTorch (unless user requests Keras/TensorFlow).

### PyTorch Model Template

```python
import torch
import torch.nn as nn

class MyModel(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int, output_dim: int, dropout: float = 0.3):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.BatchNorm1d(hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, output_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)
```

### Architecture Best Practices
- **Always include**: BatchNorm or LayerNorm, Dropout, residual connections (for deep nets).
- **Initialization**: PyTorch defaults (Kaiming) are fine for ReLU networks.
- **Activation functions**: ReLU for hidden layers (default), GELU for transformers, Sigmoid/Softmax only at output.
- **Output layer**: No activation for regression, Sigmoid for binary, LogSoftmax for multiclass (with NLLLoss) or raw logits (with CrossEntropyLoss).

---

## Step 4 -- Training Loop

### PyTorch Training Template

```python
import torch
from torch.utils.data import DataLoader
from tqdm import tqdm

def train_one_epoch(model, dataloader, optimizer, criterion, device):
    model.train()
    total_loss = 0
    correct = 0
    total = 0

    for batch in tqdm(dataloader, desc="Training"):
        inputs, targets = batch
        inputs, targets = inputs.to(device), targets.to(device)

        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, targets)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()

        total_loss += loss.item() * inputs.size(0)
        if outputs.dim() > 1:  # Classification
            correct += (outputs.argmax(dim=1) == targets).sum().item()
        total += inputs.size(0)

    avg_loss = total_loss / total
    accuracy = correct / total if correct else None
    return {"loss": avg_loss, "accuracy": accuracy}


@torch.no_grad()
def evaluate(model, dataloader, criterion, device):
    model.eval()
    total_loss = 0
    correct = 0
    total = 0

    for batch in dataloader:
        inputs, targets = batch
        inputs, targets = inputs.to(device), targets.to(device)
        outputs = model(inputs)
        loss = criterion(outputs, targets)

        total_loss += loss.item() * inputs.size(0)
        if outputs.dim() > 1:
            correct += (outputs.argmax(dim=1) == targets).sum().item()
        total += inputs.size(0)

    avg_loss = total_loss / total
    accuracy = correct / total if correct else None
    return {"loss": avg_loss, "accuracy": accuracy}
```

---

## Step 5 -- Training Utilities

### Main Training Script Template

```python
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = MyModel(input_dim, hidden_dim, output_dim).to(device)
optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-2)
criterion = nn.CrossEntropyLoss()
scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=num_epochs)

best_val_loss = float("inf")
patience_counter = 0
patience = 10

for epoch in range(num_epochs):
    train_metrics = train_one_epoch(model, train_loader, optimizer, criterion, device)
    val_metrics = evaluate(model, val_loader, criterion, device)
    scheduler.step()

    print(f"Epoch {epoch+1}: train_loss={train_metrics['loss']:.4f}, val_loss={val_metrics['loss']:.4f}")

    # Checkpointing
    if val_metrics["loss"] < best_val_loss:
        best_val_loss = val_metrics["loss"]
        patience_counter = 0
        torch.save({
            "epoch": epoch,
            "model_state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "val_loss": best_val_loss,
        }, "best_model.pt")
    else:
        patience_counter += 1
        if patience_counter >= patience:
            print(f"Early stopping at epoch {epoch+1}")
            break
```

### Hyperparameter Defaults

| Hyperparameter | Default | Notes |
|---|---|---|
| Optimizer | AdamW | Better generalization than Adam |
| Learning rate | 1e-3 (from scratch), 1e-5 (fine-tuning) | |
| Weight decay | 1e-2 | Regularization |
| Batch size | 32 (small data), 64-256 (large) | Largest that fits in memory |
| Epochs | 50-100 with early stopping | patience=10 |
| Gradient clipping | max_norm=1.0 | Prevents exploding gradients |
| Scheduler | CosineAnnealing or OneCycleLR | |

### Common Issues and Fixes

| Problem | Diagnosis | Fix |
|---|---|---|
| Loss not decreasing | LR too high or too low | Try 10x lower/higher, use LR finder |
| Val loss increasing while train decreases | Overfitting | More dropout, weight decay, data augmentation, fewer params |
| NaN loss | Exploding gradients or bad data | Gradient clipping, check for NaN/Inf in data |
| Training very slow | CPU bottleneck or bad batch size | Use GPU, increase batch size, num_workers in DataLoader |
| Accuracy stuck at random | Learning rate too low or architecture too simple | Try higher LR, add capacity |
