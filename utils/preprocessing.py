import torch

# 추론 과정 시 사용할 데이터 전처리
def preprocess(tokens, bboxes, tokenizer):
    encoding = tokenizer(
        tokens,
        is_split_into_words=True,
        return_offsets_mapping=True,
        padding="max_length",
        truncation=True,
        max_length=512,
        return_tensors="pt"
    )

    word_ids = encoding.word_ids(batch_index=0)
    bbox_padded = []
    valid_token_indices = []
    
    for i, word_id in enumerate(word_ids):
        if word_id is not None and word_id < len(bboxes):
            bbox_padded.append(bboxes[word_id])
            valid_token_indices.append(i)
        else:
            bbox_padded.append([0, 0, 0, 0])

    encoding["bbox"] = torch.tensor([bbox_padded], dtype=torch.int32)
    return encoding, word_ids, valid_token_indices