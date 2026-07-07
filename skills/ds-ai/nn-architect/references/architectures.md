# Architecture Selection Guide

## By Task Type

### Image Classification

| Scale | Architecture | Parameters | When |
|---|---|---|---|
| Quick prototype | `torchvision.models.resnet18(pretrained=True)` | 11M | Fast, good baseline |
| Production | `torchvision.models.efficientnet_b0(pretrained=True)` | 5M | Better accuracy/param ratio |
| State-of-art | `timm.create_model("vit_base_patch16_224", pretrained=True)` | 86M | Best accuracy, needs more data |
| Tiny dataset (<1k) | ResNet18 frozen + linear head | <1M trainable | Transfer learning |

### Text Classification

| Scale | Architecture | When |
|---|---|---|
| Quick prototype | TF-IDF + Linear (no deep learning needed) | <10k samples, simple task |
| Standard | `bert-base-uncased` fine-tuned | General text classification |
| Lightweight | `distilbert-base-uncased` fine-tuned | Speed/resource constrained |
| Multilingual | `xlm-roberta-base` | Non-English or mixed language |

### Tabular Data

| Architecture | When | Implementation |
|---|---|---|
| Simple MLP | Default for tabular | 2-4 hidden layers, BatchNorm, Dropout |
| TabNet | Feature selection built-in | `pytorch_tabnet` library |
| FT-Transformer | Best tabular DL performance | Feature tokenizer + Transformer |
| Embedding + MLP | Mixed categorical + numeric | Learnable embeddings for categoricals |

**Note**: For tabular data, gradient boosting (XGBoost, LightGBM) often beats deep learning. Use DL only when: very large dataset (>100k rows), complex feature interactions, or when combining with other modalities.

### Time Series

| Architecture | When | Notes |
|---|---|---|
| LSTM | Standard sequential modeling | Pack sequences for variable length |
| GRU | Similar to LSTM, fewer params | Faster training |
| Temporal CNN | Parallel processing, fixed window | Faster than RNNs |
| Transformer | Long sequences, attention patterns | Positional encoding required |
| N-BEATS | Pure forecasting | No feature engineering needed |

---

## Transfer Learning Pattern

```python
import torchvision.models as models

# Load pretrained model
model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)

# Freeze all layers
for param in model.parameters():
    param.requires_grad = False

# Replace classification head
num_classes = 10
model.fc = nn.Sequential(
    nn.Linear(model.fc.in_features, 256),
    nn.ReLU(),
    nn.Dropout(0.3),
    nn.Linear(256, num_classes),
)

# Only new layers will have gradients
```

**Training phases:**
1. Train only the new head (5-10 epochs, LR=1e-3)
2. Unfreeze last few blocks + fine-tune (10-20 epochs, LR=1e-5)
3. Optional: unfreeze all + fine-tune (5-10 epochs, LR=1e-6)

---

## Model Sizing Rules of Thumb

- **Parameters vs data**: Need ~10-100x more training samples than parameters for training from scratch.
- **Hidden size**: Start with 128-512 for tabular, scale up as needed.
- **Depth**: 2-4 layers for tabular MLP, 12+ for transformers.
- **Dropout**: 0.1-0.3 for transformers, 0.3-0.5 for MLPs.
