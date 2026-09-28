"""診斷：錨點的 alternative_readings 為何是空的。"""

from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

from cognitive_core.assets import prompt  # noqa: E402
from cognitive_core.llm import Client  # noqa: E402
from cognitive_core.models import AnchorDraft, anchor_json_schema  # noqa: E402

TEXT = "他昨天走了"

schema = anchor_json_schema()
print("=== 送給模型的 schema ===")
print(json.dumps(schema, ensure_ascii=False)[:900])
print(f"\n  頂層 required: {schema.get('required')}")
print(f"  有 $defs: {'$defs' in schema}")
if "$defs" in schema:
    print(f"  $defs 內容: {list(schema['$defs'])}")

client = Client()
msgs = [{"role": "system", "content": prompt("reflect").body},
        {"role": "user", "content": f"分析這句話：{TEXT}"}]

for label, rf in [
    ("tier1 json_schema",
     {"type": "json_schema",
      "json_schema": {"name": "out", "strict": True, "schema": schema}}),
    ("tier2 json_object", {"type": "json_object"}),
]:
    print(f"\n=== {label} ===")
    try:
        raw = client.text("reflect", msgs, response_format=rf, max_tokens=1500,
                          temperature=0.0)
        print("  原始輸出：", raw[:500])
        try:
            obj = json.loads(raw)
            u = obj.get("uncertainty", {})
            print(f"  uncertainty 鍵: {sorted(u)}")
            print(f"  alternative_readings: {u.get('alternative_readings')}")
            d = AnchorDraft.model_validate(obj)
            print(f"  驗證後 n_readings = {d.uncertainty.n_readings}")
        except Exception as e:  # noqa: BLE001
            print(f"  解析/驗證失敗：{type(e).__name__}: {str(e)[:200]}")
    except Exception as e:  # noqa: BLE001
        print(f"  ❌ {type(e).__name__}: {str(e)[:200]}")
