# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = [
#   "unsloth==2026.9.11",
#   "unsloth_zoo==2026.9.7",
#   "trl==0.24.0",
#   "peft==0.21.0",
#   "transformers==5.5.0",
#   "torch==2.12.1",
#   "bitsandbytes==0.50.2",
#   "datasets==4.3.0",
# ]
# ///
"""genai-finetune 實測：Unsloth 版的 QLoRA SFT（需要 NVIDIA GPU；Unsloth 不支援 CPU）。

跟 spike_genai_finetune.py（TRL＋PEFT 原生）吃同一份資料、同一組超參數（HP 從那支 import），
差別只在「用哪個工具」。注意版本現實：unsloth 2026.9.11 釘住 trl<=0.24.0、transformers<=5.5.0，
跟最新的 trl 1.13.0 裝不進同一個環境——所以這支自己一個 PEP 723 環境。

  # Unsloth（主角）
  uv run --script content/genai-intro/_spikes/spike_genai_finetune_unsloth.py --out r_unsloth.json
  # 對照組：同一個環境（trl 0.24、transformers 5.5），但不用 Unsloth、走 TRL＋PEFT 原生寫法
  uv run --script content/genai-intro/_spikes/spike_genai_finetune_unsloth.py --tool trl --out r_trl024.json

免費 GPU（Colab／Kaggle 的 T4）：腳本自動改 fp16；秒數會比 4090 慢好幾倍。
平台預裝的 torch／CUDA 驅動常變動，這支用 uv 自建環境；裝不起來時改用 Unsloth 官方的免費 notebook
（https://unsloth.ai/docs/get-started/unsloth-notebooks）——同一套 FastLanguageModel → SFTTrainer 流程。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def run_unsloth(a) -> dict:
    # Unsloth 必須在 transformers／trl／peft 之前 import，它才能把自己的加速核心 patch 進去
    from unsloth import FastLanguageModel
    from unsloth.chat_templates import train_on_responses_only

    import time

    import torch
    from datasets import Dataset
    from trl import SFTConfig, SFTTrainer

    import spike_genai_finetune as base
    from spike_genai_finetune_data import SYSTEM_SHORT, build_dataset, dataset_fingerprint

    HP = base.hp_for(a)
    assert torch.cuda.is_available(), "Unsloth 需要 NVIDIA GPU（Colab／Kaggle 選 T4）"
    base.cap_memory(torch, a.mem_cap_gb)
    use_bf16 = base.bf16_ok(torch) and not a.fp16
    train, test = build_dataset(long_ctx=a.long_ctx)
    test = test[: a.n_test]

    torch.cuda.reset_peak_memory_stats()
    t0 = time.perf_counter()
    model, tok = FastLanguageModel.from_pretrained(
        model_name=a.model, max_seq_length=HP["max_length"], load_in_4bit=(a.mode == "qlora"),
        dtype=torch.bfloat16 if use_bf16 else torch.float16,
    )
    load_s = time.perf_counter() - t0
    mem_load = torch.cuda.memory_allocated() / 2**30
    model = FastLanguageModel.get_peft_model(
        model, r=HP["lora_r"], lora_alpha=HP["lora_alpha"], lora_dropout=HP["lora_dropout"],
        target_modules=base.TARGETS, bias="none", use_gradient_checkpointing="unsloth",
        random_state=HP["seed"],
    )
    res = {"tool": "unsloth", "mode": a.mode, "model": a.model, "versions": base.versions(),
           "gpu": base.gpu_info(torch), "precision": "bf16" if use_bf16 else "fp16", "hp": HP,
           "load_s": round(load_s, 1), "mem_after_load_gib": round(mem_load, 3),
           "data_fp": dataset_fingerprint(train), "n_train": len(train), "n_test": len(test)}

    # Unsloth 官方食譜：先用 chat template 把 messages 攤平成文字，再只對回答算 loss
    texts = [tok.apply_chat_template(r["messages"], tokenize=False) for r in train]
    cfg = SFTConfig(
        output_dir=str(Path(a.workdir) / "unsloth-out"), dataset_text_field="text",
        per_device_train_batch_size=HP["batch"], gradient_accumulation_steps=HP["grad_accum"],
        num_train_epochs=HP["epochs"], learning_rate=HP["lr"], lr_scheduler_type=HP["scheduler"],
        warmup_steps=HP["warmup_steps"], optim=HP["optim"], weight_decay=HP["weight_decay"],
        max_steps=HP["max_steps"] or -1,
        logging_steps=1, bf16=use_bf16, fp16=not use_bf16, max_length=HP["max_length"],
        seed=HP["seed"], report_to="none", save_strategy="no", packing=False, dataset_num_proc=1,
    )
    timer = base.make_step_timer(torch)
    trainer = SFTTrainer(model=model, processing_class=tok, args=cfg,
                         train_dataset=Dataset.from_dict({"text": texts}), callbacks=[timer])
    trainer = train_on_responses_only(trainer, instruction_part="<|im_start|>user\n",
                                      response_part="<|im_start|>assistant\n")
    res["trainable_params"] = sum(p.numel() for p in model.parameters() if p.requires_grad)
    res["mask_example"] = base.mask_example(trainer, tok)
    print(f"trainable={res['trainable_params']:,}; loss tokens first batch="
          f"{res['mask_example']['loss_tokens_first_batch']}", flush=True)

    torch.cuda.reset_peak_memory_stats()
    t1 = time.perf_counter()
    trainer.train()
    res["train_s"] = round(time.perf_counter() - t1, 2)
    res["peak_alloc_gib"] = round(torch.cuda.max_memory_allocated() / 2**30, 3)
    res["peak_reserved_gib"] = round(torch.cuda.max_memory_reserved() / 2**30, 3)
    res["step_s"] = [round(x, 4) for x in timer.times]
    res["loss"] = [round(h["loss"], 4) for h in trainer.state.log_history if "loss" in h]
    res["steps"] = trainer.state.global_step
    print(f"train {res['train_s']}s, steps={res['steps']}, peak reserved {res['peak_reserved_gib']} GiB, "
          f"loss {res['loss'][0]} -> {res['loss'][-1]}", flush=True)

    if not a.skip_eval:
        FastLanguageModel.for_inference(model)
        res["eval_ft_short"] = base.evaluate(model, tok, test, SYSTEM_SHORT, torch, "unsloth ft/short")
    return res


def main() -> None:
    import json

    argv = sys.argv[1:]
    tool = "unsloth"
    if "--tool" in argv:
        i = argv.index("--tool")
        tool = argv[i + 1]
        del argv[i:i + 2]
    import spike_genai_finetune as base

    a = base.cli(argv)
    if tool == "unsloth":
        res = run_unsloth(a)
    else:  # 對照組：同環境（trl 0.24）但不 import unsloth，走 TRL＋PEFT 原生寫法
        res = base.run(a)
        res["tool"] = "trl+peft (trl 0.24 env)"
    Path(a.out).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print("wrote", a.out)


if __name__ == "__main__":
    main()
