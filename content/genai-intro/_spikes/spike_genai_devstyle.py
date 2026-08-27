# /// script
# requires-python = ">=3.11"
# dependencies = ["tiktoken"]
# ///
"""genai-devstyle 課的定軌 spike：context engineering 的 token 帳（tiktoken o200k_base 真算）。

同一個客服問題、三種塞 context 的姿勢，token 數差多少：
  A. 什麼都塞：整份 FAQ ＋ 完整 10 輪歷史
  B. 只塞相關：檢索後的相關段落 ＋ 完整歷史
  C. 工程化：相關段落 ＋ 歷史摘要

跑法：uv run --script content/genai-intro/_spikes/spike_genai_devstyle.py
"""

import tiktoken

enc = tiktoken.get_encoding("o200k_base")
n = lambda s: len(enc.encode(s))  # noqa: E731

FAQ_SECTIONS = {
    "退貨政策": "商品到貨後 7 天內，保持包裝完整即可申請退貨；食品、貼身衣物與客製化商品除外。退款於收到退回商品後 5–7 個工作天內原路退回。若為商品瑕疵，來回運費由本公司負擔；非瑕疵退貨，運費 80 元由買家自行負擔。退貨前請先在會員中心填寫退貨申請單，取得退貨編號後再寄出，未附退貨編號的包裹將無法受理。",
    "運送說明": "台灣本島訂單滿 990 元免運，未滿收取運費 80 元；離島地區一律收取 150 元。出貨時間為付款完成後 1–2 個工作天，宅配送達約再加 1–2 天。超商取貨限重 5 公斤、單邊長度不得超過 45 公分。冷凍商品僅提供黑貓宅配，無法超商取貨。出貨後會發送含物流編號的通知信，可於官網「訂單查詢」頁追蹤。",
    "會員與點數": "註冊會員即贈 100 點購物金，每 1 點折抵 1 元，消費每滿 100 元回饋 2 點。點數效期為發放日起一年，逾期自動失效。生日當月消費享 95 折，可與點數折抵併用，但不可與其他優惠券疊加。會員等級依近 12 個月累積消費計算：白銀 5,000 元、黃金 20,000 元、白金 60,000 元，等級越高回饋越多。",
}
HISTORY = [
    ("user", "你們家的保溫瓶有 500ml 的嗎？"),
    ("assistant", "有的，經典保溫瓶有 350ml、500ml、750ml 三種容量，500ml 目前有霧黑、奶茶、森林綠三色現貨。"),
    ("user", "奶茶色好看，保冷效果如何？"),
    ("assistant", "500ml 經典保溫瓶為雙層 316 不鏽鋼真空結構，保冷約 24 小時、保溫約 12 小時。"),
    ("user", "好，那我下單一支奶茶色 500ml。"),
    ("assistant", "已為您加入購物車：經典保溫瓶 500ml 奶茶色，售價 880 元。結帳時可選擇宅配或超商取貨。"),
    ("user", "順便問一下你們最近有活動嗎？"),
    ("assistant", "本月全館滿 1,500 元折 100 元，會員生日當月另有 95 折優惠。"),
    ("user", "了解，我先結帳了，用超商取貨。"),
    ("assistant", "收到，訂單已成立（編號 A123456），超商取貨約 2–3 個工作天到店，到店後會發簡訊通知您。"),
]
SUMMARY = "顧客已購買經典保溫瓶 500ml 奶茶色（880 元，訂單 A123456，超商取貨，尚未到貨）。"
QUESTION = "我剛剛買的那個保溫瓶如果不喜歡，可以退嗎？運費誰出？"
SYSTEM = "你是購物網站的客服，請根據提供的資料用繁體中文回答，資料裡沒有的不要瞎掰。"

faq_all = "\n\n".join(f"【{k}】{v}" for k, v in FAQ_SECTIONS.items())
hist_all = "\n".join(f"{r}: {t}" for r, t in HISTORY)

a = n(SYSTEM) + n(faq_all) + n(hist_all) + n(QUESTION)
b = n(SYSTEM) + n(f"【退貨政策】{FAQ_SECTIONS['退貨政策']}") + n(hist_all) + n(QUESTION)
c = n(SYSTEM) + n(f"【退貨政策】{FAQ_SECTIONS['退貨政策']}") + n(SUMMARY) + n(QUESTION)

print(f"A 全塞（整份 FAQ＋10 輪歷史）: {a} tokens")
print(f"B 只塞相關段落＋完整歷史   : {b} tokens（省 {(a - b) / a:.0%}）")
print(f"C 相關段落＋歷史摘要       : {c} tokens（省 {(a - c) / a:.0%}）")
print(f"FAQ 全文 {n(faq_all)} / 相關段 {n(f'【退貨政策】{FAQ_SECTIONS['退貨政策']}')} tokens；"
      f"歷史 {n(hist_all)} / 摘要 {n(SUMMARY)} tokens")
assert a > b > c and (a - c) / a > 0.5, "工程化組裝應省超過一半"
print("\nSPIKE OK: genai-devstyle")
