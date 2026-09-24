# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""genai-finetune 測驗素材：真的撞出微調工具鏈的錯誤訊息（不杜撰）。

每個案例是一小段程式＋自己的 PEP 723 依賴，用 `uv run --script` 在獨立環境跑，
收下 stdout/stderr 的關鍵行存成 JSON。GPU 案例會各自限制 VRAM（--mem-cap-gb）。

  uv run --script content/genai-intro/_spikes/spike_genai_finetune_errors.py --out errors.json
  uv run --script content/genai-intro/_spikes/spike_genai_finetune_errors.py --only version_conflict
"""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
import textwrap
from pathlib import Path

UNSLOTH_DEPS = ['"unsloth==2026.9.11"', '"trl==0.24.0"', '"transformers==5.5.0"', '"torch==2.12.1"']
TRL_DEPS = ['"trl==1.13.0"', '"peft==0.21.0"', '"transformers==5.17.0"', '"torch==2.14.0"',
            '"bitsandbytes==0.50.2"', '"accelerate==1.15.0"']

CASES = {
    # 1) 想同時要「最新 TRL」和「Unsloth」——uv 解依賴當場拒絕
    "version_conflict": (['"unsloth==2026.9.11"', '"trl==1.13.0"'], "print('resolved?!')"),

    # 2) import 順序：先 transformers 再 unsloth
    "import_order": (UNSLOTH_DEPS, """
        import transformers  # noqa: F401
        import unsloth  # noqa: F401
        print("imported")
    """),

    # 3) loss masking 標記抄錯：Qwen 的資料配上 Llama 3 的 assistant 標頭
    "wrong_response_part": (UNSLOTH_DEPS + ['"datasets==4.3.0"'], """
        import torch
        torch.cuda.set_per_process_memory_fraction(4 * 2**30 / torch.cuda.get_device_properties(0).total_memory, 0)
        from unsloth import FastLanguageModel
        from unsloth.chat_templates import train_on_responses_only
        from datasets import Dataset
        from trl import SFTConfig, SFTTrainer
        model, tok = FastLanguageModel.from_pretrained("unsloth/Qwen3-0.6B-bnb-4bit", max_seq_length=256,
                                                       load_in_4bit=True)
        model = FastLanguageModel.get_peft_model(model, r=8, lora_alpha=8, target_modules=["q_proj", "v_proj"])
        rows = [[{"role": "user", "content": f"第 {i} 筆問題"},
                 {"role": "assistant", "content": '{"category": "howto"}'}] for i in range(16)]
        texts = [tok.apply_chat_template(r, tokenize=False) for r in rows]
        trainer = SFTTrainer(model=model, processing_class=tok, train_dataset=Dataset.from_dict({"text": texts}),
                             args=SFTConfig(output_dir="/tmp/ft-err", dataset_text_field="text", max_steps=2,
                                            per_device_train_batch_size=4, report_to="none", logging_steps=1))
        trainer = train_on_responses_only(
            trainer,
            instruction_part="<|start_header_id|>user<|end_header_id|>\\n\\n",       # Llama 3 的格式
            response_part="<|start_header_id|>assistant<|end_header_id|>\\n\\n",
        )
        trainer.train()
    """),

    # 4) TRL 的 assistant_only_loss 需要 chat template 帶 {% generation %} 標記
    "assistant_only_loss": (TRL_DEPS + ['"datasets==5.0.1"'], """
        from datasets import Dataset
        from trl import SFTConfig, SFTTrainer
        rows = [{"messages": [{"role": "user", "content": f"第 {i} 筆問題"},
                              {"role": "assistant", "content": '{"category": "howto"}'}]} for i in range(8)]
        trainer = SFTTrainer(model="Qwen/Qwen3-0.6B", train_dataset=Dataset.from_list(rows),
                             args=SFTConfig(output_dir="/tmp/ft-err2", assistant_only_loss=True,
                                            max_steps=1, report_to="none", use_cpu=True))
        print("init ok; first labels:", trainer.train_dataset[0].keys())
    """),

    # 4b) 同一招換成 Llama 3.2 的 chat template（沒有 {% generation %} 標記）
    "assistant_only_loss_llama": (TRL_DEPS + ['"datasets==5.0.1"'], """
        from datasets import Dataset
        from trl import SFTConfig, SFTTrainer
        rows = [{"messages": [{"role": "user", "content": f"第 {i} 筆問題"},
                              {"role": "assistant", "content": '{"category": "howto"}'}]} for i in range(8)]
        trainer = SFTTrainer(model="unsloth/Llama-3.2-1B-Instruct", train_dataset=Dataset.from_list(rows),
                             args=SFTConfig(output_dir="/tmp/ft-err2b", assistant_only_loss=True,
                                            max_steps=1, report_to="none", use_cpu=True))
        print("init ok")
    """),

    # 5) 全參數微調 1.7B 塞進約 9.5 GB 的額度（等於一張小卡）→ OOM
    "oom_full": (TRL_DEPS + ['"datasets==5.0.1"'], """
        import torch
        torch.cuda.set_per_process_memory_fraction(9.5 * 2**30 / torch.cuda.get_device_properties(0).total_memory, 0)
        from datasets import Dataset
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from trl import SFTConfig, SFTTrainer
        tok = AutoTokenizer.from_pretrained("Qwen/Qwen3-1.7B")
        model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen3-1.7B", dtype=torch.bfloat16, device_map={"": 0})
        rows = [{"prompt": [{"role": "user", "content": f"第 {i} 筆問題"}],
                 "completion": [{"role": "assistant", "content": '{"category": "howto"}'}]} for i in range(32)]
        trainer = SFTTrainer(model=model, processing_class=tok, train_dataset=Dataset.from_list(rows),
                             args=SFTConfig(output_dir="/tmp/ft-err3", per_device_train_batch_size=8,
                                            optim="adamw_torch", bf16=True, gradient_checkpointing=True,
                                            max_steps=3, report_to="none", logging_steps=1))
        trainer.train()
    """),
}

KEEP = ("error", "Error", "×", "╰─▶", "Because", "requirements", "warn", "Warn", "Unsloth", "Tried",
        "capacity", "allocated", "init ok", "imported", "resolved", "trl", "assistant", "generation")


def run_case(name: str, deps: list[str], code: str) -> dict:
    header = "# /// script\n# requires-python = \">=3.11,<3.13\"\n# dependencies = [\n"
    header += "".join(f"#   {d},\n" for d in deps) + "# ]\n# ///\n"
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / f"ft_err_{name}.py"
        f.write_text(header + textwrap.dedent(code), encoding="utf-8")
        p = subprocess.run(["uv", "run", "--script", str(f)], capture_output=True, text=True, timeout=1800,
                           check=False)
    out = (p.stdout + "\n" + p.stderr).splitlines()
    key = [ln for ln in out if any(k in ln for k in KEEP)]
    print(f"== {name}: exit {p.returncode}")
    for ln in key[-25:]:
        print("   ", ln[:400])
    return {"exit": p.returncode, "key_lines": key[-40:], "tail": out[-30:]}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", help="只跑指定案例")
    ap.add_argument("--out", default="finetune_errors.json")
    a = ap.parse_args()
    res = {}
    for name, (deps, code) in CASES.items():
        if a.only and name not in a.only:
            continue
        res[name] = run_case(name, deps, code)
    Path(a.out).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print("wrote", a.out)


if __name__ == "__main__":
    main()
