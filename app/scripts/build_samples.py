"""把 sibo/samples/_prompts/*.output.md 打包成种子示例报告 sibo/samples/*.json。

示例报告的生成方式：用 builder 导出真实 prompt（system + user），由 Claude 按同一 prompt 生成输出。
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from sibo.ai.citations import validate  # noqa: E402

D = Path(__file__).resolve().parent.parent / "sibo/samples"
for meta_f in sorted((D / "_prompts").glob("*.meta.json")):
    name = meta_f.name.replace(".meta.json", "")
    out_f = D / "_prompts" / f"{name}.output.md"
    if not out_f.exists():
        print("缺少输出：", name)
        continue
    meta = json.loads(meta_f.read_text())
    text = out_f.read_text().strip()
    _, cites, warns = validate(text, set(meta["allowed_ids"]))
    meta["output_md"] = text
    (D / f"{name}.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1))
    print(f"{name}: {len(text)} 字符, 引用 {len(cites)} 条, 警告 {warns}")
