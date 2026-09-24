# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = [
#   "trl==1.13.0",
#   "peft==0.21.0",
#   "transformers==5.17.0",
#   "torch==2.14.0",
#   "bitsandbytes==0.50.2",
#   "datasets==5.0.1",
#   "accelerate==1.15.0",
# ]
# ///
"""genai-finetune 實測：Hugging Face TRL ＋ PEFT 原生寫法的 QLoRA SFT（需要 NVIDIA GPU）。

同一份資料（spike_genai_finetune_data.py）、同一組超參數，另一支
spike_genai_finetune_unsloth.py 用 Unsloth 跑——兩者的 loss 曲線、峰值 VRAM、每步秒數、
訓練前後輸出，就是課程頁 hero 與實驗場的素材（結果寫成 JSON，再注入 lesson.py）。

用法（repo 根執行；本機 RTX 4090 實測 2026-09）：
  uv run --script content/genai-intro/_spikes/spike_genai_finetune.py --eval-base --out r_trl.json
  uv run --script content/genai-intro/_spikes/spike_genai_finetune.py --mode lora16 \
      --model Qwen/Qwen3-1.7B --skip-eval --out r_lora16.json          # VRAM 校準點
  uv run --script content/genai-intro/_spikes/spike_genai_finetune.py --mode full \
      --model Qwen/Qwen3-0.6B --skip-eval --out r_full06.json          # VRAM 校準點

免費 GPU（Colab／Kaggle 的 T4）：T4 不支援 bf16，腳本自動改 fp16；4090 的秒數在 T4 上會慢好幾倍。
不需要任何 API key 或自架服務；模型從 Hugging Face 公開下載。
共用 GPU 時用 --mem-cap-gb 限制本行程最多用多少 VRAM（超過就在自己身上 OOM，不擠壞別人）。
"""

from __future__ import annotations

import argparse
import importlib.metadata as md
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from spike_genai_finetune_data import (  # noqa: E402
    SYSTEM_DETAILED,
    SYSTEM_SHORT,
    build_dataset,
    dataset_fingerprint,
    score,
    summarize,
)

TARGETS = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
# 兩個工具共用的超參數（改這裡＝兩邊一起改）
HP = {
    "lora_r": 16, "lora_alpha": 16, "lora_dropout": 0.0,
    "lr": 2e-4, "batch": 8, "grad_accum": 1, "epochs": 1, "warmup_steps": 5,
    "scheduler": "linear", "optim": "adamw_8bit", "weight_decay": 0.0,
    "max_length": 512, "seed": 3407, "max_new_tokens": 160,
}


def versions() -> dict:
    out = {}
    for p in ["unsloth", "unsloth_zoo", "trl", "peft", "transformers", "torch", "bitsandbytes",
              "datasets", "accelerate", "xformers"]:
        try:
            out[p] = md.version(p)
        except Exception:
            pass
    return out


def bf16_ok(torch) -> bool:
    """原生 bf16 要 Ampere（compute capability 8.x）以上。T4 是 7.5：
    torch.cuda.is_bf16_supported() 在新版 torch 會把「軟體模擬」也算成支援而回 True，不能拿來判斷。"""
    return torch.cuda.get_device_capability(0)[0] >= 8


def gpu_info(torch) -> dict:
    p = torch.cuda.get_device_properties(0)
    return {"name": p.name, "total_gb": round(p.total_memory / 2**30, 2), "bf16": bf16_ok(torch)}


def hp_for(a) -> dict:
    """HP ＋ 命令列覆寫（長序列情境要放寬 max_length）。"""
    return HP | {"max_length": a.max_length or HP["max_length"], "long_ctx": a.long_ctx,
                 "padding_free": bool(a.padding_free), "optim": a.optim or HP["optim"],
                 "max_steps": a.max_steps}


def cap_memory(torch, gb: float | None) -> None:
    if gb:
        total = torch.cuda.get_device_properties(0).total_memory
        torch.cuda.set_per_process_memory_fraction(min(1.0, gb * 2**30 / total), 0)


def to_prompt_completion(rows: list[dict]) -> list[dict]:
    return [{"prompt": r["messages"][:2], "completion": r["messages"][2:]} for r in rows]


def generate_all(model, tok, rows, system: str, torch, max_new_tokens: int, bs: int = 8) -> list[str]:
    """貪婪解碼；Qwen3 用 enable_thinking=False（直接回答，不先想）。"""
    tok.padding_side = "left"
    outs = []
    for i in range(0, len(rows), bs):
        chunk = rows[i:i + bs]
        texts = [
            tok.apply_chat_template(
                [{"role": "system", "content": system}, r["messages"][1]],
                tokenize=False, add_generation_prompt=True, enable_thinking=False,
            )
            for r in chunk
        ]
        enc = tok(texts, return_tensors="pt", padding=True, add_special_tokens=False).to("cuda")
        with torch.no_grad():
            gen = model.generate(**enc, max_new_tokens=max_new_tokens, do_sample=False,
                                 pad_token_id=tok.pad_token_id)
        for g in gen:
            outs.append(tok.decode(g[enc["input_ids"].shape[1]:], skip_special_tokens=True).strip())
    return outs


def evaluate(model, tok, test, system, torch, tag) -> dict:
    t0 = time.perf_counter()
    outs = generate_all(model, tok, test, system, torch, HP["max_new_tokens"])
    scores = [score(o, r["label"]) for o, r in zip(outs, test, strict=True)]
    s = summarize(scores)
    print(f"[eval {tag}] {s}  ({time.perf_counter() - t0:.1f}s)", flush=True)
    return {"summary": s, "outputs": outs, "scores": scores}


def make_step_timer(torch):
    from transformers import TrainerCallback

    class StepTimer(TrainerCallback):
        def __init__(self):
            self.times, self._t = [], None

        def on_step_begin(self, args, state, control, **kw):
            torch.cuda.synchronize()
            self._t = time.perf_counter()

        def on_step_end(self, args, state, control, **kw):
            torch.cuda.synchronize()
            self.times.append(time.perf_counter() - self._t)

    return StepTimer()


def mask_example(trainer, tok) -> dict:
    """從真實的 data collator 拿第一個 batch：哪些 token 算 loss（labels != -100）。"""
    batch = next(iter(trainer.get_train_dataloader()))
    ids, labels = batch["input_ids"][0].tolist(), batch["labels"][0].tolist()
    if "attention_mask" in batch:
        keep = [i for i, m in enumerate(batch["attention_mask"][0].tolist()) if m]
        ids, labels = [ids[i] for i in keep], [labels[i] for i in keep]
    spans, cur, cur_on = [], [], None
    for t, lab in zip(ids, labels, strict=True):
        on = lab != -100
        if cur_on is not None and on != cur_on:
            spans.append({"loss": cur_on, "text": tok.decode(cur), "n": len(cur)})
            cur = []
        cur.append(t)
        cur_on = on
    spans.append({"loss": cur_on, "text": tok.decode(cur), "n": len(cur)})
    n_loss = sum(int((b != -100).sum()) for b in batch["labels"])
    return {"spans": spans, "tokens_total": len(ids),
            "loss_tokens_first_batch": n_loss, "batch_size": len(batch["labels"])}


def run(a) -> dict:
    import torch
    from datasets import Dataset
    from peft import LoraConfig
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from trl import SFTConfig, SFTTrainer

    assert torch.cuda.is_available(), "需要 NVIDIA GPU（Colab／Kaggle 選 T4）"
    cap_memory(torch, a.mem_cap_gb)
    use_bf16 = bf16_ok(torch) and not a.fp16
    dtype = torch.bfloat16 if use_bf16 else torch.float16
    hp = hp_for(a)
    train, test = build_dataset(long_ctx=a.long_ctx)
    test = test[: a.n_test]

    torch.cuda.reset_peak_memory_stats()
    t0 = time.perf_counter()
    tok = AutoTokenizer.from_pretrained(a.model)
    model = AutoModelForCausalLM.from_pretrained(a.model, dtype=dtype, device_map={"": 0})
    load_s = time.perf_counter() - t0
    mem_load = torch.cuda.memory_allocated() / 2**30
    total_params = sum(p.numel() for p in model.parameters())
    print(f"loaded {a.model} in {load_s:.1f}s, {mem_load:.2f} GiB, dtype={dtype}", flush=True)

    res = {"tool": "trl+peft", "mode": a.mode, "model": a.model, "versions": versions(),
           "gpu": gpu_info(torch), "precision": "bf16" if use_bf16 else "fp16",
           "hp": hp, "load_s": round(load_s, 1), "mem_after_load_gib": round(mem_load, 3),
           "data_fp": dataset_fingerprint(train), "n_train": len(train), "n_test": len(test)}

    if a.eval_base:
        res["eval_base_short"] = evaluate(model, tok, test, SYSTEM_SHORT, torch, "base/short")
        res["eval_base_detailed"] = evaluate(model, tok, test, SYSTEM_DETAILED, torch, "base/detailed")
        res["system_detailed_tokens"] = len(tok(SYSTEM_DETAILED)["input_ids"])
        res["system_short_tokens"] = len(tok(SYSTEM_SHORT)["input_ids"])

    if not use_bf16 and a.mode == "qlora":
        # T4 路徑（沒有 bf16）：預量化權重的設定寫著 bf16 運算，LoRA 也會跟著建成 bf16，
        # fp16 混合精度的 GradScaler 當場報錯（NotImplementedError …unscale_cuda… 'BFloat16'）。
        # 修法：4-bit 層改用 fp16 運算；訓練器建好後把可訓練參數轉成 fp32（Unsloth 會自動做這兩件事）。
        import bitsandbytes as bnb

        for mod in model.modules():
            if isinstance(mod, bnb.nn.Linear4bit):
                mod.compute_dtype = torch.float16

    peft_config = None
    if a.mode in ("qlora", "lora16"):
        peft_config = LoraConfig(r=HP["lora_r"], lora_alpha=HP["lora_alpha"],
                                 lora_dropout=HP["lora_dropout"], target_modules=TARGETS,
                                 bias="none", task_type="CAUSAL_LM")
    cfg = SFTConfig(
        output_dir=str(Path(a.workdir) / "trl-out"),
        per_device_train_batch_size=HP["batch"], gradient_accumulation_steps=HP["grad_accum"],
        num_train_epochs=HP["epochs"], learning_rate=HP["lr"], lr_scheduler_type=HP["scheduler"],
        warmup_steps=HP["warmup_steps"], optim=hp["optim"], weight_decay=HP["weight_decay"],
        max_steps=hp["max_steps"] or -1,
        logging_steps=1, bf16=use_bf16, fp16=not use_bf16, gradient_checkpointing=True,
        max_length=hp["max_length"], seed=HP["seed"], report_to="none", save_strategy="no",
        packing=False, dataset_num_proc=1, **({"padding_free": True} if a.padding_free else {}),
    )
    ds = Dataset.from_list(to_prompt_completion(train))
    timer = make_step_timer(torch)
    trainer = SFTTrainer(model=model, args=cfg, train_dataset=ds, processing_class=tok,
                         peft_config=peft_config, callbacks=[timer])
    if not use_bf16:
        for prm in trainer.model.parameters():
            if prm.requires_grad and prm.dtype != torch.float32:
                prm.data = prm.data.float()
    trainable = sum(p.numel() for p in trainer.model.parameters() if p.requires_grad)
    res["trainable_params"], res["total_params"] = trainable, total_params
    res["mask_example"] = mask_example(trainer, tok)
    print(f"trainable={trainable:,} / total={total_params:,}; "
          f"loss tokens first batch={res['mask_example']['loss_tokens_first_batch']}", flush=True)

    torch.cuda.reset_peak_memory_stats()
    t1 = time.perf_counter()
    trainer.train()
    res["train_s"] = round(time.perf_counter() - t1, 2)
    res["peak_alloc_gib"] = round(torch.cuda.max_memory_allocated() / 2**30, 3)
    res["peak_reserved_gib"] = round(torch.cuda.max_memory_reserved() / 2**30, 3)
    res["step_s"] = [round(x, 4) for x in timer.times]
    res["loss"] = [round(h["loss"], 4) for h in trainer.state.log_history if "loss" in h]
    res["steps"] = trainer.state.global_step
    nt = [h["num_tokens"] for h in trainer.state.log_history if "num_tokens" in h]
    res["num_tokens"] = int(nt[-1]) if nt else None  # 整個 epoch 實際送進模型的 token 數（不含 padding）
    print(f"train {res['train_s']}s, steps={res['steps']}, peak reserved {res['peak_reserved_gib']} GiB, "
          f"loss {res['loss'][0]} -> {res['loss'][-1]}", flush=True)

    if not a.skip_eval:
        trainer.model.eval()
        res["eval_ft_short"] = evaluate(trainer.model, tok, test, SYSTEM_SHORT, torch, "ft/short")
    return res


def cli(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="unsloth/Qwen3-1.7B-bnb-4bit",
                    help="預設是 bitsandbytes NF4 預量化的 Qwen3-1.7B（兩個工具吃同一份權重）")
    ap.add_argument("--mode", default="qlora", choices=["qlora", "lora16", "full"])
    ap.add_argument("--eval-base", action="store_true", help="訓練前先評一次底模（短／長 prompt）")
    ap.add_argument("--skip-eval", action="store_true", help="只量訓練（VRAM 校準用）")
    ap.add_argument("--n-test", type=int, default=40)
    ap.add_argument("--long-ctx", type=int, default=0, help="長序列情境：每筆前面墊約 N 字歷史對話")
    ap.add_argument("--max-length", type=int, default=0, help="覆寫 max_length（長序列要放寬）")
    ap.add_argument("--optim", default="", help="覆寫優化器（全參數校準點用 adamw_torch）")
    ap.add_argument("--max-steps", type=int, default=0, help="只跑前 N 步（VRAM 校準用）")
    ap.add_argument("--padding-free", action="store_true", help="TRL 原生的 padding-free（對照 Unsloth 自動開的那個）")
    ap.add_argument("--fp16", action="store_true", help="強制 fp16（模擬 T4 的精度路徑）")
    ap.add_argument("--mem-cap-gb", type=float, default=float(os.environ.get("FT_MEM_CAP_GB", "0")) or None)
    ap.add_argument("--workdir", default=os.environ.get("FT_WORKDIR", "/tmp/genai-finetune"))
    ap.add_argument("--out", default="result_trl.json")
    return ap.parse_args(argv)


def main(argv=None, tool_label="trl+peft"):
    a = cli(argv)
    res = run(a)
    res["tool"] = tool_label
    Path(a.out).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print("wrote", a.out)


if __name__ == "__main__":
    main()
