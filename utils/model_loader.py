from transformers import LayoutLMForTokenClassification, LayoutLMTokenizerFast
import os

# 모델 캐싱
model_cache = {}
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def get_model_and_tokenizer(doctype, base_path=os.path.join(BASE_DIR, "model")):
    model_path = os.path.join(base_path, doctype)
    if not os.path.exists(model_path):
        raise ValueError(f"모델 경로가 존재하지 않습니다: {model_path}")

    if doctype not in model_cache:
        model = LayoutLMForTokenClassification.from_pretrained(
            model_path,
            use_safetensors=True
        )
        tokenizer = LayoutLMTokenizerFast.from_pretrained(model_path)
        model.eval()
        model_cache[doctype] = (model, tokenizer)

    return model_cache[doctype], model_path