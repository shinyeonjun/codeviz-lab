def ensure_utf8_encodable(value: str, *, field_label: str) -> None:
    try:
        value.encode("utf-8", errors="strict")
    except UnicodeEncodeError as error:
        raise ValueError(
            f"{field_label}에 잘못된 유니코드 문자가 포함되어 있습니다. "
            "복사한 코드의 특수문자나 이모지를 다시 확인해 주세요."
        ) from error
