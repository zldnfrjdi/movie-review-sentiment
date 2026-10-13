from pathlib import Path

import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer

MODEL_DIR = Path(__file__).parent / "serving_model"


class SentimentAnalyzer:
    def __init__(self):
        self.tokenizer = Tokenizer.from_file(str(MODEL_DIR / "tokenizer.json"))
        self.tokenizer.enable_truncation(max_length=128)

        sess_options = ort.SessionOptions()
        sess_options.intra_op_num_threads = 1
        self.session = ort.InferenceSession(
            str(MODEL_DIR / "model_int8.onnx"),
            sess_options,
            providers=["CPUExecutionProvider"],
        )

    def predict(self, text: str) -> tuple[str, float]:
        enc = self.tokenizer.encode(text)
        feed = {
            "input_ids": np.array([enc.ids], dtype=np.int64),
            "attention_mask": np.array([enc.attention_mask], dtype=np.int64),
            "token_type_ids": np.array([enc.type_ids], dtype=np.int64),
        }
        logits = self.session.run(["logits"], feed)[0][0]

        probs = np.exp(logits - logits.max())
        probs = probs / probs.sum()
        pos_prob = float(probs[1])

        label = "긍정" if pos_prob >= 0.5 else "부정"
        return label, round(pos_prob, 4)
