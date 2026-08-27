import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="模型是怎麼練成的：預訓練到 RLHF（實驗場）")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # 🧪 模型是怎麼練成的：預訓練到 RLHF（實驗場）

    這是本課的**實驗場**。左側教學讀到哪，就回到這裡動手做——
    每一格程式碼都可以**直接修改、立即重跑**（點格子右上的 ▶，或按 `Ctrl+Enter`）。
    改壞了也沒關係：重新整理頁面就會回到原版。

    這一課有三筆帳要親手算：**微調的參數帳**（LoRA 為什麼能在消費級 GPU 上跑）、
    **蒸餾的溫度**（暗知識是怎麼被蒸出來的）、**GRPO 的群組優勢**
    （DeepSeek-R1 那套 RL 在算什麼）。三筆都是真公式真計算。
    """
    )
    return


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _():
    # 科學套件集中在這格 import，回傳給全 notebook 用
    import matplotlib.pyplot as plt
    import numpy as np
    return np, plt


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 1️⃣ 微調的參數帳：全參數 vs LoRA

    一個 Transformer 的參數量完全由架構決定。下面的計算機用 Llama 3 的架構比例
    （head 維度 128、GQA 4:1、MLP 放大 3.5 倍、詞表 128,256）——
    預設值就是 **Llama-3-8B 本人**（算出來 8.03B）。

    **LoRA** 的想法：底模全部凍結，只在每個投影矩陣旁邊掛一對低秩小矩陣
    （r 就是那個「秩」），可訓練參數量 ＝ r × (輸入維度 + 輸出維度)，
    掛滿七個投影也只有全參數的零點幾 %。訓練記憶體的帳也跟著翻盤：
    全參數要存「權重＋梯度＋Adam 狀態」（約 12 bytes/參數），
    LoRA 底模只要放權重（2 bytes/參數），梯度與優化器只付小矩陣的錢。
    """
    )
    return


@app.cell
def _(mo):
    hid = mo.ui.slider(start=1024, stop=8192, step=1024, value=4096,
                       label="hidden size（模型寬度）", show_value=True)
    layers = mo.ui.slider(start=8, stop=80, step=4, value=32,
                          label="層數", show_value=True)
    lora_r = mo.ui.dropdown(
        options={"r = 4": 4, "r = 8": 8, "r = 16（常用預設）": 16,
                 "r = 32": 32, "r = 64": 64, "r = 256": 256},
        value="r = 16（常用預設）", label="LoRA 秩 r（掛滿七個投影）")
    mo.vstack([hid, layers, lora_r])
    return hid, lora_r, layers


@app.cell
def _(hid, layers, lora_r):
    # Llama 3 架構比例：head_dim=128、GQA 4:1、MLP 3.5x、詞表 128256（8B 不綁定 lm_head）
    VOCAB, HEAD_DIM = 128256, 128
    H, L, R = hid.value, layers.value, lora_r.value
    n_heads = H // HEAD_DIM
    n_kv = max(n_heads // 4, 1)
    inter = int(3.5 * H)

    emb = VOCAB * H
    attn = H * (n_heads * HEAD_DIM) + 2 * H * (n_kv * HEAD_DIM) + (n_heads * HEAD_DIM) * H
    mlp = 2 * H * inter + inter * H
    per_layer = attn + mlp + 2 * H
    total = emb + L * per_layer + H + VOCAB * H

    # LoRA 掛七個投影：q,o 各 r*2H；k,v 各 r*(H+H/4)；gate,up,down 各 r*4.5H → 合計 r*20H/層
    lora = (2 * R * (H + n_heads * HEAD_DIM) + 2 * R * (H + n_kv * HEAD_DIM)
            + 2 * R * (H + inter) + R * (inter + H)) * L

    full_mem_gb = total * 12 / 1024**3          # bf16 權重2 + 梯度2 + Adam fp32 8
    lora_mem_gb = (total * 2 + lora * 12) / 1024**3
    return full_mem_gb, lora, lora_mem_gb, total


@app.cell
def _(full_mem_gb, lora, lora_mem_gb, np, plt, total):
    _fig, (_ax1, _ax2) = plt.subplots(1, 2, figsize=(7.4, 3.9))
    _p = [total / 1e6, lora / 1e6]
    _ax1.bar(["full", "LoRA"], _p, color=["#C44E52", "#55A868"],
             edgecolor="#1C2B33", linewidth=1.1, zorder=3)
    for _i, _v in enumerate(_p):
        _lab = f"{_v/1000:.2f}B" if _v >= 1000 else f"{_v:.1f}M"
        _ax1.text(_i, _v * 1.25, _lab, ha="center", fontsize=10, fontweight="bold")
    _ax1.set_yscale("log")
    _ax1.set_ylim(min(_p) * 0.2, max(_p) * 12)
    _ax1.set_ylabel("trainable params (M, log)")
    _ax1.set_title("trainable parameters")
    _ax1.grid(axis="y", alpha=0.3, zorder=0)

    _m = [full_mem_gb, lora_mem_gb]
    _ax2.bar(["full", "LoRA"], _m, color=["#C44E52", "#55A868"],
             edgecolor="#1C2B33", linewidth=1.1, zorder=3)
    for _i, _v in enumerate(_m):
        _ax2.text(_i, _v + max(_m) * 0.03, f"{_v:.0f} GB", ha="center", fontsize=10, fontweight="bold")
    _ax2.axhline(24, color="#4C72B0", linestyle="--", linewidth=1.6, zorder=2)
    _ax2.text(1.45, 24, " RTX 4090 (24GB)", va="bottom", ha="right",
              fontsize=8.5, color="#4C72B0", fontweight="bold")
    _ax2.set_ylim(0, max(max(_m) * 1.18, 30))
    _ax2.set_ylabel("training memory (GB)")
    _ax2.set_title("weights + grads + Adam states")
    _ax2.grid(axis="y", alpha=0.3, zorder=0)
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(full_mem_gb, lora, lora_mem_gb, mo, total):
    mo.md(
        f"""
    目前設定：全參數 **{total/1e9:.2f}B**，訓練記憶體約 **{full_mem_gb:.0f} GB**；
    LoRA 可訓練 **{lora/1e6:.1f}M**（佔 {lora/total*100:.2f}%），
    記憶體掉到約 **{lora_mem_gb:.0f} GB**（皆未含 activation；
    底模再用 4-bit 量化——QLoRA——還能再砍一大截）。

    可訓練參數佔比 0.5% **不代表**行為只改變 0.5%：低秩更新疊加在每一層的
    注意力與 MLP 上，改風格、學任務格式綽綽有餘——這是業界微調的預設起手式。

    ## 2️⃣ 蒸餾：溫度把暗知識蒸出來

    **知識蒸餾**＝大模型（老師）教小模型（學生）。關鍵不是抄答案，
    是抄**答案的分布**：老師看一張貓的圖，輸出「貓 88%、狗 8%、老虎 4%、汽車 0.1%」——
    「狗比汽車像貓 80 倍」這件事叫**暗知識（dark knowledge）**，
    one-hot 標籤裡完全沒有。

    把 softmax 除以溫度 T 再算，分布會被「蒸軟」，暗知識才浮得出來。
    拉拉看（老師 logits 固定為 [5.0, 2.6, 1.8, −2.0]）：
    """
    )
    return


@app.cell
def _(mo):
    temp_t = mo.ui.slider(start=1.0, stop=10.0, step=0.5, value=4.0,
                          label="蒸餾溫度 T", show_value=True)
    temp_t
    return (temp_t,)


@app.cell
def _(np, plt, temp_t):
    _logits = np.array([5.0, 2.6, 1.8, -2.0])
    _classes = ["cat", "dog", "tiger", "car"]

    def _softmax(z, t):
        e = np.exp(z / t - (z / t).max())
        return e / e.sum()

    _p1, _pt = _softmax(_logits, 1.0), _softmax(_logits, temp_t.value)
    _x = np.arange(4)
    _fig, _ax = plt.subplots(figsize=(7.0, 3.9))
    _ax.bar(_x - 0.2, _p1, width=0.38, color="#9AA7AE", edgecolor="#1C2B33",
            linewidth=1.0, zorder=3, label="T = 1 (hard-ish)")
    _ax.bar(_x + 0.2, _pt, width=0.38, color="#DD8452", edgecolor="#1C2B33",
            linewidth=1.0, zorder=3, label=f"T = {temp_t.value:g} (soft)")
    for _i in range(4):
        _ax.text(_i + 0.2, _pt[_i] + 0.02, f"{_pt[_i]:.2f}", ha="center",
                 fontsize=9, fontweight="bold", color="#B25C22")
    _ax.set_xticks(_x, _classes)
    _ax.set_ylabel("teacher probability")
    _ax.set_ylim(0, 1.02)
    _ax.set_title("temperature reveals dark knowledge (dog >> car)")
    _ax.legend(fontsize=9)
    _ax.grid(axis="y", alpha=0.3, zorder=0)
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    T=1 時貓拿走 0.883，其他類別幾乎看不見；T=4 時分布變成 0.46 / 0.25 / 0.21 / 0.08——
    正解還是第一名，但「狗、老虎比汽車像貓」的排序資訊被放大到學生看得見。
    學生同時學兩個目標：**軟標籤的 KL 散度**（抄老師的分布）＋
    **真標籤的交叉熵**（別忘了正解），這就是蒸餾 loss 的標準配方。

    ## 3️⃣ GRPO：一組答案，比出優勢

    RLHF 的老路（PPO）要多養一個跟模型一樣大的 value model 來估「這步值多少分」。
    **GRPO（DeepSeek-R1 用的）** 把它整個砍掉：同一題抽一**組**答案（例如 8 個），
    對過答案後，**組內標準化**就是每個答案的優勢：

    ```
    advantage = (reward − 組平均) / 組標準差
    ```

    答對的被推高、答錯的被壓低，全組相對比較、不用 value model——
    記憶體直接省一半。勾勾看哪些答案對，看優勢怎麼變：
    """
    )
    return


@app.cell
def _(mo):
    grpo_checks = mo.ui.array(
        [mo.ui.checkbox(value=_v, label=f"答案{_i+1}")
         for _i, _v in enumerate([True, False, False, True, False, False, False, True])],
    )
    mo.hstack(list(grpo_checks), justify="start", gap=1.2)
    return (grpo_checks,)


@app.cell
def _(grpo_checks, np, plt):
    _r = np.array([1.0 if _v else 0.0 for _v in grpo_checks.value])
    _adv = (_r - _r.mean()) / (_r.std() + 1e-8)
    _fig, _ax = plt.subplots(figsize=(7.0, 3.7))
    _colors = ["#55A868" if _a > 0 else "#C44E52" if _a < 0 else "#9AA7AE" for _a in _adv]
    _ax.bar([f"a{_i+1}" for _i in range(8)], _adv, color=_colors,
            edgecolor="#1C2B33", linewidth=1.0, zorder=3)
    _ax.axhline(0, color="#1C2B33", linewidth=1.2)
    _ax.set_ylabel("advantage (group-normalized)")
    _ax.set_title(f"{int(_r.sum())}/8 correct -> mean advantage is always 0")
    _ax.grid(axis="y", alpha=0.3, zorder=0)
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    試一件重要的事：**全部勾對**（或全部不勾）——優勢瞬間全變 0，這一題就什麼都教不了。
    GRPO 要學得動，題目難度必須落在「有人對有人錯」的地帶；
    這就是為什麼 RL 訓練的資料配題比演算法本身還關鍵。

    DeepSeek-R1 的驚喜在於：**只靠這種「答案對不對」的 RL**（不給人類示範怎麼推理），
    模型自己長出「等等，我重新檢查一遍」的反思與回溯——論文裡把那一刻叫
    **Aha Moment**。這條「純 RL 湧現推理」的路線，就是第 4 課 reasoning model 的出身。

    ## 4️⃣ 你的實驗區

    下面這格是你的，改完按 ▶ 重跑。挑戰在左頁「換你動手」，做完再開解答對照。
    """
    )
    return


@app.cell
def _(full_mem_gb, lora, lora_mem_gb, np, total):
    # ===== 你的實驗區 =====
    # 上面滑桿的當前設定會直接反映在這裡（預設＝Llama-3-8B）
    print(f"全參數: {total/1e9:.2f}B 參數 → 訓練記憶體約 {full_mem_gb:.0f} GB")
    print(f"LoRA: {lora/1e6:.1f}M 可訓練參數（佔 {lora/total*100:.2f}%）→ 約 {lora_mem_gb:.0f} GB")

    # LEVEL 2 起點：自己算一次蒸餾軟標籤
    my_logits = np.array([5.0, 2.6, 1.8, -2.0])
    my_T = 4.0
    my_p = np.exp(my_logits / my_T) / np.exp(my_logits / my_T).sum()
    print("軟標籤 T=4:", my_p.round(3), " 狗/汽車 =", round(my_p[1] / my_p[3], 1), "倍")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.accordion(
        {
            "💡 LEVEL 1 參考解答": mo.md(
                r"""
    把 LoRA 的 r 從 16 改成 64：可訓練參數從 41.9M 變 **167.8M**（0.52% → 2.09%），
    訓練記憶體從約 15 GB 變 **約 17 GB**——參數翻了 4 倍，記憶體只多一點點，
    因為大頭（底模權重 15 GB）根本沒動。

    但 r 不是越大越好：常用起手式就是 r=8～16，效果不夠再往上調；
    r 拉太大，小資料集上反而容易過擬合（記住了你的 5,000 筆對話的措辭，
    而不是學到風格）。
    """
            ),
            "💡 LEVEL 2 參考解答": mo.md(
                r"""
    實驗區印出 T=4 的軟標籤是 `[0.46, 0.253, 0.207, 0.08]`，狗/汽車 ≈ **3.2 倍**——
    這個「狗比汽車像貓」的排序就是暗知識。T=1 時正解獨拿 0.883，
    學生只學得到「答案是貓」；T 拉到 4 之後，類別之間的**相對關係**才浮出來。

    T 也不是越高越好：拉到 10 你會看到分布趨平（0.33 / 0.26 / 0.24 / 0.17），
    暗知識又被「蒸過頭」稀釋掉了。實務上 T=2～4 是常見範圍，
    而且學生 loss 要同時保留一份真標籤的交叉熵當錨。
    """
            ),
            "💡 LEVEL 3 參考解答": mo.md(
                r"""
    全部勾對之後：`reward − mean = 0`，優勢全部歸零——
    這一組樣本對模型參數的更新量是 **0**，等於白算了一整組推理。
    全部答錯也一樣。

    這對應到 RL 訓練實務的一條鐵律：**題目要配在模型的能力邊緣**
    （通過率既不是 0% 也不是 100% 的題目才有訊號）。
    訓練中模型變強後，原本「有人對有人錯」的題會逐漸變成全對——
    所以資料集要隨訓練進程換難度，否則有效訊號越來越稀。
    """
            ),
        }
    )
    return


if __name__ == "__main__":
    app.run()
