# 문서 타입 인식
def get_doctype_from_tokens(tokens):
    doctype_keywords = {
        "resume": ["이력서"]
        # 필요 시 계속 추가
    }

    for doctype, keywords in doctype_keywords.items():
        for keyword in keywords:
            if keyword in tokens:
                return doctype
    return None