from flask import request, jsonify
from . import api_blueprint
from utils.preprocessing import preprocess
from utils.doc_type import get_doctype_from_tokens
from utils.model_loader import get_model_and_tokenizer
import os, json, torch
from transformers import LayoutLMForTokenClassification, LayoutLMTokenizerFast

@api_blueprint.route("/api/ai/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json()
        tokens = data.get("tokens")
        bboxes = data.get("bboxes")

        if not tokens or not bboxes:
            return jsonify({"error": "tokens와 bboxes는 필수입니다."}), 400

        # 문서 유형 자동 감지
        doctype = get_doctype_from_tokens(tokens)

        if not doctype:
            return jsonify({"error": "문서 유형을 감지할 수 없습니다."}), 400

        # 모델 로딩
        (model, tokenizer), model_path = get_model_and_tokenizer(doctype)

        label_map_path = os.path.join(model_path, "label_map.json")
        with open(label_map_path, "r", encoding="utf-8") as f:
            label2id = json.load(f)
        id2label = {v: k for k, v in label2id.items()}

        # 전처리
        encoding, word_ids, valid_token_indices = preprocess(tokens, bboxes, tokenizer)

        with torch.no_grad():
            inputs = {k: v for k, v in encoding.items() if k != "offset_mapping"}
            outputs = model(**inputs)
            predictions = outputs.logits.argmax(-1).squeeze().tolist()

        # predictions가 tensor인 경우 squeeze()를 통해 리스트로 변환
        if isinstance(predictions, torch.Tensor):
            predictions = predictions.squeeze().tolist()

        # 예측 라벨을 첫 번째 서브토큰에 대해서만 할당
        # 중요 로직. LayoutLM은 단어를 토큰별로 나누고 해당 서브토큰까지 인식할 수 있기 때문에
        # 이 + #력 + ##서 이런식임. 때문에 첫번째 서브토큰인 '이'+#력+##서 를 하나의 단어로 취급하고 뒤에
        # 두 개의 서브토큰은 무시하도록 함.
        labels = []
        tokens_cleaned = []
        bboxes_cleaned = []
        seen_word_ids = set()

        for i, word_id in enumerate(word_ids):
            if word_id is None or word_id in seen_word_ids:
                continue
            seen_word_ids.add(word_id)

            if word_id < len(tokens) and word_id < len(bboxes):
                label = id2label.get(predictions[i], "O")
                labels.append(label)
                tokens_cleaned.append(tokens[word_id])
                bboxes_cleaned.append(bboxes[word_id])
        return jsonify({
            "labels": labels,
            "doctype": doctype,
            "bbox": bboxes,
            "tokens": tokens
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500