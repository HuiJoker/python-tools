from .data import normalize_text


def sanitize_template_filename(name: str) -> str:
    bad_chars = '<>:"/\\|?*'
    cleaned = str(name).strip()
    for ch in bad_chars:
        cleaned = cleaned.replace(ch, "_")
    return cleaned or "模板"

def parse_col_ref(value) -> int:
    if isinstance(value, int):
        if value <= 0:
            raise ValueError(f"非法列号: {value}")
        return value

    text = str(value).strip().upper()
    if not text:
        raise ValueError("列不能为空")

    if text.isdigit():
        num = int(text)
        if num <= 0:
            raise ValueError(f"非法列号: {value}")
        return num

    if all("A" <= ch <= "Z" for ch in text):
        col = 0
        for ch in text:
            col = col * 26 + (ord(ch) - ord("A") + 1)
        return col

    raise ValueError(f"无法识别列: {value}")

def parse_optional_col_ref(value):
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return parse_col_ref(text)

def validate_mapping_config(raw: dict) -> dict:
    if not isinstance(raw, dict):
        raise ValueError("配置必须是 JSON 对象")

    name_col = parse_col_ref(raw.get("name_col", 2))
    data_start_row = int(raw.get("data_start_row", 6))
    header_primary = int(raw.get("header_row_primary", 4))
    header_secondary = int(raw.get("header_row_secondary", 5))
    score_max = float(raw.get("score_max", 10))

    if data_start_row <= 0 or header_primary <= 0 or header_secondary <= 0:
        raise ValueError("行号必须大于0")
    if score_max <= 0:
        raise ValueError("score_max 必须大于0")

    dims = raw.get("dimensions", [])
    if not isinstance(dims, list) or not dims:
        raise ValueError("dimensions 不能为空")

    parsed_dims = []
    for idx, dim in enumerate(dims, start=1):
        if not isinstance(dim, dict):
            raise ValueError(f"第{idx}个维度格式错误")
        name = str(dim.get("name", "")).strip()
        if not name:
            raise ValueError(f"第{idx}个维度名称为空")

        direct_col = parse_optional_col_ref(dim.get("direct_col", ""))
        sum_cols_raw = dim.get("sum_cols", [])
        if not isinstance(sum_cols_raw, list) or not sum_cols_raw:
            raise ValueError(f"维度[{name}] 的 sum_cols 不能为空")
        sum_cols = [parse_col_ref(c) for c in sum_cols_raw]

        item_names = dim.get("item_names", [])
        if item_names and (not isinstance(item_names, list) or len(item_names) != len(sum_cols)):
            raise ValueError(f"维度[{name}] 的 item_names 数量必须与 sum_cols 一致")

        parsed_dims.append(
            {
                "name": name,
                "direct_col": direct_col,
                "sum_cols": sum_cols,
                "item_names": item_names if item_names else [],
            }
        )

    return {
        "name_col": name_col,
        "data_start_row": data_start_row,
        "header_row_primary": header_primary,
        "header_row_secondary": header_secondary,
        "score_max": score_max,
        "dimensions": parsed_dims,
    }

def pick_recommended_header(primary_text: str, secondary_text: str) -> str:
    p = normalize_text(primary_text)
    s = normalize_text(secondary_text)
    if not p and not s:
        return ""
    if not p:
        return s
    if not s:
        return p

    if looks_like_group_header(p) and not looks_like_group_header(s):
        return s
    if looks_like_group_header(s) and not looks_like_group_header(p):
        return p

    # 默认优先主表头
    return p

def looks_like_group_header(text: str) -> bool:
    t = normalize_text(text).replace(" ", "")
    return ("%" in t) or ("（" in t and "）" in t) or ("(" in t and ")" in t)

def looks_like_subtotal(text: str) -> bool:
    t = normalize_text(text).replace(" ", "")
    return ("小计" in t) or ("总计" in t) or ("总分" in t)

