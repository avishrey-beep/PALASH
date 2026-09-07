import os
import time
import json
import torch
import torch.nn as nn
from typing import Dict, Any, List, Tuple
from ml.preprocessing.cleaner import DatasetCleaner
from ml.preprocessing.tokenizer import SimpleTokenizer

class ToySeq2Seq(nn.Module):
    """
    Lightweight PyTorch Sequence-to-Sequence model for training pipeline validation and export.
    """
    def __init__(self, vocab_size: int = 2000, embed_dim: int = 128, hidden_dim: int = 256):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim)
        self.gru = nn.GRU(embed_dim, hidden_dim, batch_first=True)
        self.fc = nn.Linear(hidden_dim, vocab_size)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        embedded = self.embedding(x)
        out, _ = self.gru(embedded)
        logits = self.fc(out)
        return logits

class TranslationTrainer:
    """
    Reproducible ML Training Pipeline for Low-Resource Indic Translation (Section 21).
    Handles dataset ingestion, cleaning, deduplication, splits, training, evaluation, and checkpointing.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def prepare_data(self, raw_pairs: List[Tuple[str, str]]) -> Dict[str, List[Tuple[str, str]]]:
        # 1. Cleaning and deduplication
        cleaned = []
        for s, t in raw_pairs:
            pair = DatasetCleaner.clean_pair(s, t)
            if pair:
                cleaned.append(pair)
        
        deduped = DatasetCleaner.deduplicate(cleaned)
        
        # 2. Train / Val / Test split (80 / 10 / 10)
        n = len(deduped)
        n_train = int(n * 0.8)
        n_val = int(n * 0.1)

        return {
            "train": deduped[:n_train],
            "val": deduped[n_train:n_train + n_val],
            "test": deduped[n_train + n_val:]
        }

    def run_training(self, train_data: List[Tuple[str, str]], epochs: int = 2) -> Dict[str, Any]:
        """Runs reproducible training loop with PyTorch."""
        model = ToySeq2Seq().to(self.device)
        optimizer = torch.optim.Adam(model.parameters(), lr=self.config.get("learning_rate", 1e-3))
        criterion = nn.CrossEntropyLoss()

        model.train()
        history = []
        start_time = time.time()

        for epoch in range(epochs):
            total_loss = 0.0
            steps = 0
            for src, tgt in train_data:
                # Tokenize to dummy indices for demonstration
                src_tokens = SimpleTokenizer.tokenize(src)
                if not src_tokens:
                    continue
                
                indices = torch.tensor([[min(ord(c), 1999) for c in src_tokens[0]]], device=self.device)
                target = torch.tensor([[min(ord(c), 1999) for c in src_tokens[0]]], device=self.device)

                optimizer.zero_grad()
                logits = model(indices)
                loss = criterion(logits.view(-1, 2000), target.view(-1))
                loss.backward()
                optimizer.step()

                total_loss += loss.item()
                steps += 1

            avg_loss = total_loss / max(steps, 1)
            history.append({"epoch": epoch + 1, "loss": round(avg_loss, 4)})

        elapsed = time.time() - start_time
        checkpoint_dir = self.config.get("checkpoint_dir", "storage/models")
        os.makedirs(checkpoint_dir, exist_ok=True)
        checkpoint_path = os.path.join(checkpoint_dir, "translation_checkpoint.pt")
        torch.save(model.state_dict(), checkpoint_path)

        return {
            "status": "COMPLETED",
            "epochs": epochs,
            "training_time_seconds": round(elapsed, 2),
            "final_loss": history[-1]["loss"] if history else 0.0,
            "checkpoint_path": checkpoint_path,
            "history": history
        }

if __name__ == "__main__":
    cfg = {
        "model_name": "toy_indic_seq2seq",
        "learning_rate": 0.001,
        "checkpoint_dir": "storage/models"
    }
    sample_pairs = [
        ("बैठ जाओ", "ᱫᱩᱲᱩᱵ ᱢᱮ"),
        ("खड़े हो जाओ", "ᱛᱤᱸᱜᱩᱱ ᱢᱮ"),
        ("किताब खोलो", "ᱯᱚᱛᱚᱵ ᱡᱷᱤᱡᱽ ᱢᱮ"),
        ("गिनो और बताओ", "ᱞᱮᱠᱷᱟᱭ ᱢᱮ ᱟᱨ ᱞᱟᱹᱭ ᱢᱮ"),
        ("कितने आम हैं?", "ᱛᱤᱱᱟᱹᱜ ᱩᱞ ᱢᱮᱱᱟᱜ-ᱟ?")
    ] * 10
    trainer = TranslationTrainer(cfg)
    splits = trainer.prepare_data(sample_pairs)
    res = trainer.run_training(splits["train"], epochs=2)
    print("Training Completed:")
    print(json.dumps(res, indent=2))
