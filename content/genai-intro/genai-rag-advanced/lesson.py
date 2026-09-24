import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="進階 RAG：父子檢索、混合搜尋與 Rerank（實驗場）")


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # 🧪 進階 RAG：父子檢索、混合搜尋與 Rerank（實驗場）

    這是本課的**實驗場**。每一節都有拉桿和開關——拉完，下面的分數立刻用
    **41 題有標準答案的考卷**重新打一次，所有數字都是你的瀏覽器當場算的。

    素材都是真的：一份虛構咖啡機「拿鐵大師 LM-500／500S／700」的手冊（20 節、90 句）；
    句子與問題的**真向量**由 jina-embed（jinaai/jina-embeddings-v5-text-small-retrieval，1024 維）
    實測算好打包在這裡；**BM25、融合、所有指標都在這裡現場算**；
    rerank 分數是事先用 cross-encoder `BAAI/bge-reranker-v2-m3` 在 CPU 上算好的實測值
    （cross-encoder 是個 5 億多參數的模型，瀏覽器裡跑不動）。實測日期 2026-09。
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
    import base64
    import html as html_mod
    import re

    import matplotlib.pyplot as plt
    import numpy as np
    return base64, html_mod, np, plt, re


@app.cell
def _():
    # ── DATA BEGIN（由 _spikes/spike_genai_rag_advanced.py --part emit 產生；勿手改，重產方式見 NOTES.md）──
    # 手冊：20 節（父塊）× 每節幾句（子塊）。虛構教材，模型不可能背過。
    SECTIONS = [
        ('開箱與首次使用', [
            '包裝內含主機、水箱、雙份濾杯把手、蒸氣鋼杯，以及一包 DC-300 除垢劑。',
            '首次使用前，先把濾水芯浸泡在冷水中 5 分鐘，再裝進水箱底部的卡槽。',
            '水箱裝滿冷水、不放咖啡粉，按沖煮鍵讓水流完；這樣的空水循環要連做兩次。',
            '接著打開蒸氣旋鈕空噴 10 秒，把蒸氣管裡的製造殘留排乾淨。',
            '最後在設定選單把水質硬度設成你家的等級（1 到 4 級，出廠值為 3 級）。',
        ]),
        ('機型差異', [
            'LM-500 是單鍋爐機型，同一時間只能沖煮或打奶泡其中一件事。',
            'LM-500S 加裝蒸氣預熱，從沖煮切換到打奶泡只要約 5 秒。',
            'LM-700 是雙鍋爐機型，可以一邊萃取一邊打奶泡。',
            'LM-700 的水箱為 1.8 公升，LM-500 與 LM-500S 為 1.2 公升。',
            'LM-500 與 LM-500S 使用 54 mm 把手，LM-700 使用 58 mm 把手。',
        ]),
        ('沖煮義式濃縮', [
            '單份濃縮用 18 公克咖啡粉，雙份濾杯用 20 公克。',
            '填粉後以約 15 公斤的力道垂直壓粉，粉面要壓平。',
            '把手鎖緊後按單杯鍵，理想萃取時間是 25 到 30 秒，萃取量約 36 毫升。',
            '不到 20 秒就流完，代表研磨太粗或粉量不足。',
            '超過 35 秒還在滴，代表研磨太細或壓粉太用力。',
        ]),
        ('研磨設定', [
            '內建錐刀磨豆機共有 15 段刻度，1 最細、15 最粗。',
            '義式濃縮建議從第 5 段開始，每次只調一格。',
            '調整刻度必須在磨豆機運轉時進行，停機時硬轉會卡住刀盤。',
            '研磨過細會導致過度萃取、流速變慢，嚴重時觸發防堵塞保護而自動停機。',
        ]),
        ('沖煮溫度', [
            '預設沖煮溫度為 92°C，可以 1°C 為單位調整，範圍 88 到 96°C。',
            '淺焙豆適合 93 到 95°C；深焙豆建議 88 到 90°C，可以減少苦味。',
            '溫度越高萃取越強，苦味也越明顯。',
        ]),
        ('奶泡與蒸氣', [
            '請使用冷藏約 4°C 的鮮奶，奶量不超過鋼杯的一半。',
            '蒸氣管先空噴 2 秒排掉冷凝水，再把噴頭埋入奶面下約 1 公分。',
            '聽到嘶嘶的進氣聲約 3 秒後，把噴頭壓深，讓牛奶旋轉加熱到 60 到 65°C。',
            '用完立刻以濕布擦拭蒸氣管並空噴 1 秒，避免奶垢堵住噴孔。',
        ]),
        ('熱水功能', [
            '轉開熱水旋鈕即可出熱水，出水溫度約 85°C。',
            '熱水與蒸氣共用同一支管路，出熱水前請先空噴 2 秒。',
            '泡茶時建議先出 50 毫升熱水溫杯，再倒掉。',
        ]),
        ('除垢', [
            '有裝濾水芯時，除垢週期可以從 3 個月延長到 6 個月。',
            '除垢燈亮起代表累積用水量已達設定值，請在一週內完成除垢。',
            '先取下濾水芯，再把一包 DC-300 除垢劑與 1 公升清水混合倒入水箱。',
            '長按沖煮鍵 5 秒進入除垢模式，機器會分段流出除垢液，全程約 20 分鐘。',
            '除垢液流完後，沖洗水箱並裝滿清水，再按一次沖煮鍵跑完清水循環。',
            '最後裝回濾水芯，除垢燈熄滅即完成；除垢途中請勿關機。',
        ]),
        ('日常清潔', [
            '滴水盤與粉渣盒每天清空，滴水盤的浮標升起時要立刻倒掉。',
            '沖煮頭每週以溫水沖洗一次，並用附贈的刷子刷掉殘粉。',
            '每月逆洗沖煮頭一次：把盲碗裝進把手、放入一錠清潔錠，長按單杯鍵 10 秒。',
            '機身以擰乾的濕布擦拭，切勿整機沖水或放進洗碗機。',
        ]),
        ('零件與耗材型號', [
            'WF-12：濾水芯，LM-500 與 LM-500S 用，每 2 個月或 50 公升更換一次。',
            'WF-21：濾水芯，LM-700 專用，每 3 個月或 80 公升更換一次；與 WF-12 外觀相似，不可混用。',
            'DC-300：除垢劑，一盒 3 包，一包兌 1 公升清水。',
            'CL-10：沖煮頭清潔錠，一盒 8 錠，每月逆洗用一錠。',
            'GS-54：矽膠墊圈，54 mm 把手用，建議每年更換。',
            'GS-58：矽膠墊圈，58 mm 把手用，建議每年更換。',
            'SN-4：四孔蒸氣噴頭，可替換原廠的單孔噴頭 SN-1，奶泡更快更細。',
            'BK-20：20 公克雙份濾杯，另售的 BK-14 為 14 公克單份濾杯。',
        ]),
        ('省電與待機', [
            '機器閒置 30 分鐘後自動進入省電待機，按任意鍵即可喚醒。',
            '喚醒後約 40 秒完成預熱，指示燈由閃爍轉為恆亮。',
            '自動待機時間可在設定選單改成 15、30 或 60 分鐘。',
        ]),
        ('設定選單', [
            '同時長按單杯鍵與雙杯鍵 3 秒進入設定選單。',
            '用單杯鍵往下、雙杯鍵往上切換項目，按沖煮鍵確認。',
            '可設定的項目有沖煮溫度、自動待機時間、水質硬度與單杯萃取量。',
            '長按沖煮鍵 10 秒可恢復出廠設定。',
        ]),
        ('App 連線', [
            'LM-500S 與 LM-700 可用「拿鐵大師」App 連線，LM-500 不支援。',
            '首次配對時長按雙杯鍵 5 秒，指示燈快閃即進入配對模式。',
            'App 可以遠端預熱、記錄每杯萃取時間，並在需要除垢時推播提醒。',
        ]),
        ('安全注意事項', [
            '運轉中的沖煮頭與蒸氣管溫度很高，請勿直接觸碰。',
            '請使用 110V 單獨插座，不要與電暖器共用延長線。',
            '兒童須在大人陪同下使用。',
            '長時間不使用時，請倒空水箱與滴水盤並拔掉插頭。',
        ]),
        ('故障碼 E01–E05：水路', [
            'E01：水箱缺水或沒有放好，請加水並確認水箱卡到底。',
            'E02：水泵抽不到水，多半是水路進了空氣，請跑兩次清水循環排氣。',
            'E03：流量計沒有訊號，請取下濾水芯後重開機；仍出現請送修。',
            'E04：水路壓力過高，通常是沖煮頭堵塞，請做一次逆洗。',
            'E05：除垢程序被中斷，請重新長按沖煮鍵 5 秒完成除垢。',
        ]),
        ('故障碼 E06–E10：研磨與沖煮', [
            'E06：豆槽沒有咖啡豆，請補充咖啡豆。',
            'E07：研磨室堵塞，請關機拔插頭，取下豆槽後用附贈的刷子清出卡住的粉塊。',
            'E08：粉渣盒已滿或沒有裝好，請清空後重新裝回。',
            'E09：把手沒有鎖到定位，請重新鎖緊把手。',
            'E10：萃取流速過慢，請把研磨調粗一格後再試。',
        ]),
        ('故障碼 E11–E15：溫度與蒸氣', [
            'E11：溫度感測器異常，請關機 10 分鐘後重開，持續出現請送修。',
            'E12：加熱器過熱保護啟動，請關機冷卻 30 分鐘。',
            'E13：蒸氣壓力過高，請先關閉蒸氣旋鈕，等待 3 分鐘洩壓。',
            'E14：蒸氣管堵塞，請用通針疏通噴孔後空噴 5 秒。',
            'E15：預熱逾時，請確認室溫高於 5°C，並檢查電壓是否為 110V。',
        ]),
        ('故障碼 E16–E20：電子與連線', [
            'E16：主機板通訊錯誤，請拔插頭 1 分鐘後重開，仍出現請送修。',
            'E17：觸控面板沒有回應，請用乾布擦乾面板後重開機。',
            'E18：App 連線失敗，請確認手機與機器連在同一個 2.4GHz Wi-Fi。',
            'E19：韌體更新失敗，請保持連線並重新執行更新，更新中勿拔插頭。',
            'E20：滴水盤沒有裝好，請推到底直到聽見喀一聲。',
        ]),
        ('常見問題', [
            '咖啡變苦：多半是過度萃取，把研磨調粗一格，或把沖煮溫度調低 2°C。',
            '咖啡偏酸、喝起來水水的：多半是萃取不足，把研磨調細一格，或多加 1 公克粉。',
            '奶泡太粗、泡泡很大：噴頭埋得太淺，或鮮奶不夠冰。',
            '沖煮頭周圍漏水：通常是矽膠墊圈老化，或把手沒有鎖緊。',
            '機器完全沒反應：確認電源線兩端插緊、插座有電，再按下機身背面的過熱保護復位鈕。',
        ]),
        ('保固與送修', [
            '本產品自購買日起提供 2 年保固，送修時需出示發票或電子保卡。',
            '人為損壞、摔落，以及未定期除垢造成的水垢堵塞，不在保固範圍內。',
            '送修前請倒空水箱與滴水盤，並用原廠紙箱或同等級的緩衝材包裝。',
            '保固期外的維修收取檢測費 500 元，維修報價經你同意後才會施工。',
        ]),
    ]
    # 考卷：(問題, 題型, 標準答案＝第幾個子塊)；proc＝步驟題 pin＝單點題 kw＝型號／故障碼 para＝換句話說
    QUESTIONS = [
        ('除垢的完整步驟是什麼？', 'proc', [31, 32, 33, 34]),
        ('新機第一次使用前要做哪些準備？', 'proc', [1, 2, 3, 4]),
        ('怎麼打出綿密的奶泡？', 'proc', [22, 23, 24]),
        ('怎麼沖一杯標準的義式濃縮？', 'proc', [10, 11, 12]),
        ('萃取時間不對，要怎麼判斷問題出在哪？', 'proc', [13, 14]),
        ('日常清潔要做哪些事？', 'proc', [35, 36, 37, 38]),
        ('送修要準備什麼？', 'proc', [86, 88]),
        ('手機 App 要怎麼配對？', 'proc', [54, 55]),
        ('奶泡的牛奶要加熱到幾度？', 'pin', [24]),
        ('單份濃縮要放幾公克咖啡粉？', 'pin', [10]),
        ('機器閒置多久會自動待機？', 'pin', [47]),
        ('水質硬度出廠設定是幾級？', 'pin', [4]),
        ('保固期外維修要付多少檢測費？', 'pin', [89]),
        ('研磨刻度可以在停機時調整嗎？', 'pin', [17]),
        ('深焙豆適合用幾度沖煮？', 'pin', [20]),
        ('熱水出水溫度大約幾度？', 'pin', [26]),
        ('螢幕顯示 E07 怎麼辦？', 'kw', [67]),
        ('E05 是什麼意思？', 'kw', [65]),
        ('出現 E13 要怎麼處理？', 'kw', [73]),
        ('E16 錯誤碼代表什麼？', 'kw', [76]),
        ('E11 一直出現怎麼辦？', 'kw', [71]),
        ('E18 怎麼排除？', 'kw', [78]),
        ('E03 需要送修嗎？', 'kw', [63]),
        ('E09 怎麼辦？', 'kw', [69]),
        ('WF-12 多久要換一次？', 'kw', [39]),
        ('WF-21 可以裝在 LM-500 上嗎？', 'kw', [40]),
        ('CL-10 要怎麼用？', 'kw', [42, 37]),
        ('GS-58 適用哪一台？', 'kw', [44, 9]),
        ('DC-300 一包要配多少水？', 'kw', [41, 31]),
        ('LM-700 的水箱多大？', 'kw', [8]),
        ('SN-4 是什麼？', 'kw', [45]),
        ('咖啡喝起來很苦，該怎麼調？', 'para', [81]),
        ('打出來的牛奶都是大泡泡，哪裡做錯了？', 'para', [83]),
        ('插了電卻完全不會動，怎麼辦？', 'para', [85]),
        ('把手旁邊一直滴水是什麼問題？', 'para', [84]),
        ('味道很淡又帶酸，是什麼原因？', 'para', [82]),
        ('早上按下去要等多久才能用？', 'para', [48]),
        ('摔到地上壞掉可以免費修嗎？', 'para', [87]),
        ('除垢做到一半停電了會怎樣？', 'para', [65, 34]),
        ('出國兩個月不在家，機器要怎麼處理？', 'para', [60]),
        ('可以一邊萃取一邊打奶泡嗎？', 'para', [5, 7]),
    ]
    # 真向量：jina-embed (jinaai/jina-embeddings-v5-text-small-retrieval)，1024 維，int8 對稱量化（每向量一個 scale）
    Q_B64 = (
        "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"
        "0w4DFwy9BEo="
    )
    Q_SCALES = [0.00086328, 0.000846987, 0.000979713, 0.000873947, 0.00101265, 0.000862807, 0.000977533, 0.00103923, 0.000909901, 0.00087732, 0.000870308, 0.00113795, 0.00124622, 0.000942253, 0.00100843, 0.00106013, 0.00121509, 0.0011294, 0.000904188, 0.00110584, 0.000972158, 0.00110733, 0.00103876, 0.00110035, 0.000966678, 0.000878684, 0.00098774, 0.000832259, 0.0010385, 0.000938085, 0.000959409, 0.000934178, 0.00113092, 0.000985519, 0.00109702, 0.00140182, 0.00110718, 0.00108778, 0.00129006, 0.000869695, 0.000806455]
    C_B64 = (
        "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"
    )
    C_SCALES = [0.00109466, 0.000864467, 0.000923477, 0.00136707, 0.00100419, 0.00106592, 0.00100476, 0.000848935, 0.000928687, 0.000932456, 0.000855341, 0.00172954, 0.00106816, 0.0013869, 0.00124128, 0.00112955, 0.00119738, 0.00104737, 0.000960886, 0.00119709, 0.00103849, 0.00109269, 0.00099696, 0.00129837, 0.00103706, 0.00132364, 0.000982643, 0.00111492, 0.000924257, 0.000811916, 0.00114605, 0.00104634, 0.00107372, 0.00117515, 0.0013583, 0.00106941, 0.00129486, 0.00116316, 0.00102857, 0.00086004, 0.000934975, 0.00101153, 0.00132545, 0.00104272, 0.00109493, 0.0009702, 0.000964792, 0.00107311, 0.00117587, 0.000998218, 0.00104274, 0.00116604, 0.000979923, 0.00134781, 0.000910829, 0.00104758, 0.00106048, 0.00113391, 0.00110161, 0.00149883, 0.000975586, 0.00121653, 0.00106594, 0.00128147, 0.00115967, 0.00139934, 0.00117531, 0.000984227, 0.00112544, 0.00127517, 0.00104557, 0.00132123, 0.00117018, 0.00132121, 0.00150295, 0.00112086, 0.00127951, 0.00126854, 0.00126803, 0.00127703, 0.00135943, 0.000882622, 0.00101694, 0.00100551, 0.00105304, 0.001134, 0.00122589, 0.00134344, 0.00122964, 0.00124437]
    # 預先算好的相似度矩陣（int16，÷10000）：子塊前面加上章節標題再算向量的版本、固定大小切塊的版本
    HDR_B64 = (
        "sBEMD/wOSBEPEFsFzwZDBkgFjQPFB6IJCAzCC6sLyArIDF8MaQwYCLwITQqMB54LLgjEEq4IuwutCZ0UhRZZGeEYnhu0GhoR"
        "2xP8E8gSnAtOCzoUhhBBCjYKmgeHCuwFAwj2A6sKlAyICugMegRfB08O7ApFB3sHCw7PCZoKrwrWDagSjwoADssN2gxdDXEH"
        "igjtCRAKGQilBt8IaAXEB/oJZQnuB10Hegw2CmoI0BETDi8KBBITFSERcxLiD1MHIgwTCOYIygdgBYgHFgheB5kHkAiJC40M"
        "ggmbBrcDbgMKCh0NKQkjDhsGgQ0PC/gJWgtbDrIM/Q27Do0Kggy6C3ASxArjCq8L/wl5Cm8KJwkJCEIL6wzeCKUKMwvrCGAM"
        "YgfeDJYKfgoNC+0KRBCUC+wJjQpZC64Kcgh9CpILuAosCjEIqgiECcwJ9QpqCb4KWAnJCaQKpQTPBK4HDghaDoAKhAoJE20J"
        "vwuQC6YSRA/jCxAPhhKmEOIGNwUXDqEOTREoDjkP2gd9DogKaQz2CAAKdQpPGJ0YTxfPFcMJOwv7DzMH9QUjC30MQQt7C+4I"
        "CQriDQILwwedBwEIjglAB54G4Q+DCl4IlwiVBlwQ/RJeDisLmgzzCTcMvAs+CFkG0AnmB+0I7QeCCyYKxgyeDdgLMAu0DbsG"
        "eQjLCncKhghWBUEHEwY4Bt4HSg6eDZ4XbArMCKYELQbrCA8EiAy0DMgVYAzNDZMPThD8Di8IHAatHKYXnBxiGb8YxgsIGEoM"
        "uQ0DDgsOmA/YEhsR2RAEDlcKngqUE7sJZgkPDXcOXw0/DBELkg5AEXELZAl4CdYJlQwqBtcFPAtBDZoISQoKB1wPSRWbElQL"
        "KA39CVkNVgsgCN8FlQnnCFoJxQknDSIMGhBwD4INNAyYEHAGnAeVCI8IiAi7BbAGGwZyBXMIURRZE6wQXQubCBMEugc+CAkE"
        "2wqxDfIMWg5WDOIITg2cCogINwdJCLcILxRYEr0T2AkzDXIOaRSbCicLchEXCkUNuQs+DRQKsQuACooP9w9sDeAR8gxUD6kL"
        "RAkpC1oJGQtjC2QLuQo8CakIuwkQClsLYw7/C+8LAQxrDgsOuAZuDWsPjAx1CUcGLg6lDn4QLRAgEaYQ/A54EJgQbhCSFY0O"
        "9w4+EPIP/Q99DcoNXQwPDYMPMhIYEZ8ONRAWD9cK/wvuCV4LVw2FCrUJ3AwZCsYDaARtA8oD9gFFBLIFEQZ5BUkFMAbKB7oG"
        "nwaQA2UCdQKMBccHagQtDskEmgiQBq0N/w6UEGwM3BHLDi4WVRaXE9IUAwzQC1MPPBCfBoUG6gT2B2AE4QQMBJEGrwhLCAUH"
        "wwJ5A/4JgAemBLoGRAweBnIGsQcmCQ0KogbICd8JHAheB6QEnQS4BWYGkAUoBG0GkgOlBZQGlwOBA6AEGAeaBJMFYw2VCq8G"
        "SAx2CiwJPgoECQAEcQcqBHAGMwUjBZcHMgaCCMsItQZ4CKcJOQgIBosESgS2BdUHvwWHCYMEiQkQBkUKnguwC3cKSQyhDDkK"
        "8wo0CEILmgkiCZkLyAncCxsLbwjuBi0HGwnpBloHYAcQB3sKHAWfB+AIqge/CBcHUgtHDN0KtwytC7MLkgqFC2wMzQsnC/IK"
        "AQmxCRYL/AotDhwLMwlCC9ELnQWQBeoFKAswCukU6RIdGXYV8QXbBRsGqge0CNEDhgZtBb8D3AUVA70D7AYkBGUEbQSoBs8F"
        "twXNBP4D1wP6BCYGGgalBiYFvQa/BAAEtARdBdcHvgbZB9gDQQWVBzEJigP+A3EE1QRpBmQGygRAA0gJHgfQCFYPWAutBrcN"
        "zQ9MGeURKgWtBUkHpwSMBSoFYQZcBSgGpwR9BdMFjwlsBnIGpgUHBmgGsQXwBvQIpxArCvQHIANPA84CWQXPB7MFYQTYBVQE"
        "DQpVCt4OtAuXC+IPyhPYDwAIcwTyC1EMqQ9iDUsOSwdPDJYI6QdVFfIUxBCYHmUYYR9dFNUSEQ6QFDcHAgctCA0M4Qf2CJgG"
        "lAmXC+cHBwYsBmcG/wbnBH4E1Qy3CM8HFA18B5wLtQ8oELkJDAtDCe8LqRImDVsHXQk1B68G7AaRCoAKpgo3C6UKZQlpC0IN"
        "6Q+NDr8NoQ8UBhEH5waoBvcG9g4KC5sUNwnVCTwFRQaeBiEGTAzPCTwUXQhxC48NfQx4DG0IkwWWINgW+hfzE3ITNg3oFU4M"
        "7At0DL0O0wrmD80L6gzmCAMIoQdDEasIigchDGkLhgiLCIwIgQk8DcwFYgkdCV8MuQvIBiYHrgl5EFoH6wgXB/YMAxEID5gH"
        "awsLCDQKeAdJCV4F4wXEBm4GRwdeCR8JkxCHDoMNowkeDi4FcwbZBs0FwwaPBL4FGQWFBDUGYxRvFOkMmgYKB3IE3wWoBWsE"
        "nQm7CiMKqAtkCHUIGw29CIIIkwb/ArwEcAtXB2AK2wqNB40Nkg0DCFQF9AJNBzcKignqCTsIjAiTBekLGgzlBtIQywjmC+YI"
        "zAd0CfYOpAmuCQUIcQexCAUIzQVMBeAc6BPhGqwMsQgUDZsP9gY5DMwLYAiOCWYG4xGWCuEJSAo1CjoLGQnsC1cLewtfCsEM"
        "MA6kDPkKvAw0C/8LDApmCuIKZgQvAw0FmAdMEl0L1Am+CMUI4AuHDRYNvQhmIcYFsAcWBewKsAX7Bk8J9wogC9sLaw17EHsN"
        "FAwmDuAKxAv5CN8IGgkhCF0QhArlDHQNSQ86DiQMrgy/DY4JHwrfCT8Kjw0/DUsMfgsLCqQJtAiaCSsFogezB9oJ2goZE1cN"
        "7QQBCKEIOggcBd4EpwlPDg4OMw/3D7gOuwerCfsKhgqpDKQItwiVCZwJzAntBagHYge6B/wKJgqvDNAJoQrGBawHZQ2dCswH"
        "BworCSoHpAjTCCgGcAiRBVIITweDA24FCwjWB1UKDAhkB5QICQq1B6wG8QVpBUgGtwbMCNMIbgfPBboPgA6gCsYNpQp8DVkI"
        "DglFCCsMsgy9C3ILqAnhC3wLaAb9B84KLAtxCgcHzQWRBt0LWAUTCIQJ8QeyCsgFUgxgDRULiA1BDbUNFAoVDLAMHg0IDBAO"
        "7w2wDBAMvA0rDY0NIQuDDEgN2wZxBYYFWQqqDCYXyhVFEashmAcwBzMJwgkyDtcILAxLCYEI2gldBVMJwQrXDO4OJhYgExYe"
        "PBZxC2UIOQa3BscIwgk9CqIIlwaBBBgJdgrwBwANCQncDEwJBwnsCRgLWwkCCS8JhAroC00LOQkoCMQNfwv6DosLyAw3DxkO"
        "iAg2BnIKjgloBXIDiQmxCfYIDAzBC/EMoQ7LETER4BHPEvELZguJCzMKxgrTCOoKfQfFCCIKnQn/CGAH5ghsC/cGMgo6BwMK"
        "mgvPCkYQJwqWDJENog17DJYGDAXfE0sSqBTREwAV+Q4MEX4MsgrEFjUiCxULERINfRJRC1YO1ghPEdAJ2wlDC3EP6QktC8MG"
        "3Q1iDpwHGAdYBz4KKAuQBR8GoQhsC6AHMgwqBvoJxQ+qEWcLQAq3CGEMJhCACBYEkwb5BcoFCQfNC7kMWhFOEHwNVAtfD7kJ"
        "zQsuC1AK+QuwBAcGCQXuBAMGrBQxD98LdgvaB2UEqAccBagFWAz0DIEOUQubEFEK/gzPCRANHgXkB6AI5wxJCosLyQXSCDcG"
        "5wgAGB0UIRMLEJcOfhP2C20gIBbUF0EMAg7DDOYNDgzVDKMJ9wtVCYQKDwxdDEYKPgjTBdMFOQluCOsGbQtXB44IhQwHElAK"
        "yQbeBi0N9hPYDYcFgw2LDZQO4w2MEHwP5Af1CRAKgQlWC3kQPhJZEVYRABLCBqAH/Qe0B3EL6AzwC8wJuAyqCu0GZQw5CRQJ"
        "ZQjIB24IwQlRCucHLAqICz8KgQm1AvQFsQXkB/MIUAUECIIJOAvHB5wFJAZ/B9sJuwcQC3cIFAjtBTcHOg1oCMoLUAmhDXsI"
        "8AfbB04MjAcfCRwI6QfHCFcIDQkQBkkN4A3jCtANXA2gCYMRJwv1CRIL4AmAC/AF4QjCEl4QJBIcEusSjhD7EgcToRK1EbcS"
        "EhEMEdIRwBG6ERUW+xAYElkRhgfKBtoIiQpJEo8KXArrCHgJxgYrBisGfQRFCPALJwvZBVcKuwwUAxIFXwUeBrgHiQVZChIE"
        "3QUpBNEDCgSMA6kDFQP6A3IFBgQOBloEpgW5BBQHRwSwBYwDrAR0BNsFtQlKBbYG5AZXCi8KSgXMBVMHzAdVB5gGhwYqBmMH"
        "dQoJCKkFUwS8B/MEugR7FbAS1xIBE0YUyw2uDRMPZg+RDvEPAQ9IDgoPphDsDaAOJw66DgkO4gPkA+0CyATwB3gGtwVfBlIJ"
        "rQpGCTAJNwuGCpUDYQVBBIIEaARqBMEGaQc3BoUI1wUlB8QHPQkEBSYEIwRsBWcI3wWOCvIGlgccBT4I4AoXDLYK+grkCykJ"
        "SwmnCSkKSQgnCCQLWApnCGQI8AZ/BhELTAkcCLcK8AkqB9gMqARjBxIJEQn9CfQImQpQDxANbQ5OD3YP4gv3DWQOPg/fDd0Q"
        "FBHNEx0R1A/HDaEQtA1JD38O/QSCBD8G4gm5C60IrwkVClsHvAU7BI0FBgZwBzsG3wawBBYGGAVrBTQFRga7CHAJJAbLBmQG"
        "0gnRBpwEvARlBkYFIwdRBtkFtwWHA/4E7ge1BJUH/APbBesDlwN3BDUFCQbsBZQG6wgBB2MGuAhgBp8HxwgzCGgHVAjMBYUJ"
        "NwWYCLEF8QbGCY0FQwZOFtkS2ROBFREVMhRDFCQWZRauFYUW/BWrFikXChfqGrkZHBpFGlYYRAaYBVEHbQnhCj8JAgp/B5EI"
        "SQfPBh8JTQldCTAG0QclBl4FUwWYBH0GGQdnCBQKDwaqCI8ItAtrBw4F6wRXB3oIGQfkCe8HzwamBfMGyQvyBqEJUgi1CoAI"
        "MQj7CNsJlgi+COAGmAqiCE4IxwdRBYIMuAx+C7ILmAviCLkOUAcsCn4Kbgm7D7kG/AmAFIYSPBMyFKYTIRE/EoETRRPgEgEb"
        "qxg7GBoY3hgdFI0VVxRbFWATKggjCPwJVAz2EL0J6Qg/COAHAgkBCJgJ9Ap5CTUFTAbEBQEH7QWaCIUH4QcNCBIJiQR4CIAG"
        "BQo5BoYGWQelBzIJfgY2DNgHHwjvBx0I5gpMC8sKNAtMDNwIAwhzCGcKPQefB0kJAQkICEkMuAaYB+4HSgi2BmMI0AnQBykJ"
        "2gV4Bq4JSAl5CuAIzwvlD1gPBQ5eEP4PIwwKDnoOfg0jDvsPMRAMEYoReRBkDlcQphEeEMEPqwjPCOwHEgpKCgUGvwgjCQwH"
        "XQuyCIMIKAhACQEH/wc7Bi4IQgdWAf0CgQR0Bu4H3QXlBqMILAmqAyMEKwO4A+wEdQQ8B+gEDQeVA2ILzQrNChMJYwkbC3AH"
        "UAivBScKQgvqCkEOFQn3CioKcAgmBZ0JUwj6BtkFVwVYBVoJVAYxBYQGPgbnCIcGFAqrE7AQ9hMQEuERGhCIEIIRaBEIELIP"
        "Dg6wDvANIg4VEawP1QykD+wPWQUaBYwEuwlZCzUSoBFoEtsRpQasBhcJ5gdbCasF+AZfBiAF7gVTBGgGoga/Bk4HBgRvCCIH"
        "iQebCHsG0QSnBcoG+AQxCWoGqQWoBYQG5AeBCFwJXQgQCh0HUAfyBysIOgYhBi4IkAfbB9UHcAbbBW8KMQntCO8JDAq9B8YM"
        "fwcYB2YI9gaMCE8FggdNEZIPxg+kEIIRXw/ED7IQmRNrEGgOhg2/DRgOXA2dDSsQEQ7hEKMOXAYdBuYF1weHCi8HOwjOB70H"
        "2QkODcsKkwr7CkAF4QerBDMIpwWhA3cDpwc9BksHzAdCCZ8HQAd3BoMCTQJPBroIdAUzCgkGzwkeB3wRwQyPCn4K+AljC3UK"
        "gwsUC0IM7BjAGG8L4gsYDJ0LMAtuCtoIzQiqCjIIFQiJBgIK4AIlCdsGrQb1CNQGWA1jCnIKiguzCqgJjQZHB9sIxggMCGIK"
        "Bgv8CU4KpwkCB8YIKwhSCYMJJwQCBMgFnAfhBg8PDwwEDFYKkwncB+4GiQV0BisSpxCsDZwRyRIKBKEEuwSdBZgEewdqBn4F"
        "uAUrBE0CAwIRBYsGOAQIB7EEQQVZBi8E8wPNBsIHRQZpBtgEoQXHBW4KcRNLE0AICAjgBysHmAe0BwwHKAV4BnsF7AavBmwH"
        "MBE+BiMFYAWwCEkFjQYHC48KrAqYCcEJpwVfBiwHYwdhBpEKYgm0CDsKXgr9B/8ISAnQCGAJ2AHsAtsDXgSyB1sGOwWEB5MG"
        "jgm5CqAK1wvXCnAIaQlLCJsIGQl2Bj0IAQnZB8YI0wfvCdMGbweoBYQE3gSDCKEIPAZTCdEFPAccB4YGGgmNCrkJfgm9CToH"
        "8gmyCzkLKwnVCHMKgBZAB3oGewdLB2YJpQgSCBULawvHB1sMiAnbCbkIWwcqC40JnQl2CDIHVwjVCPAI8wiiCTcKKQvGC7UK"
        "EgpGCm4KFQqxB9IJIQidCHYI4QTEBAEGiQfeCHwG7wXEB7QFaAbXAzoDHQTGBv0IDwmABSsKCw1sBQAElQPaA24EzQRoCEIE"
        "kgQTBDcFVwL+A+wDOgSEBIkGTgVJBlICeQPqA2wFSAOfA1gAvgK7AnUGkgaeBPgFVATDDqEV2gaiBn8EfASdBFkFvgWBBPwE"
        "YQp5BeYDvAPsBTQF5wORB3YGTQb3BqUHTAQRBVcGXgVLBRwGtQWVBX0GWQcKBTUGkAiIBnMEfgLDAjQDPAP+Bp0E6wNaA0kE"
        "ihUiDSkQBgpBDf8IjQqbCNIOMQamDJMJDwt/CLAIWwcMCjsH5wfKCLIIXAVJCpgJ3QmGB0UJGgpIDc8JwQnyFBcJcQoxCTAJ"
        "wwf1BqEIBg0sDegaCgusBZMF+wiXC8MGSQcQB6IISAkCCx8FhAf0BvMF8AaGBkwGqgtaDAcLEwycCzoKHwlhCJMJdwVDCZQF"
        "LAecB/4GLweWAhYExgNlAz8IaQeuC0QHsQZWBcYDfgdNDDYEhA7zDa4OVAeWCsURKRD8FUch4xQZBjMFiwicBWIFRwcxBkYG"
        "aQiGBukEzAPkCM4I0AckB88K0gfRCwMKzgocDikK0AxUCskJOwbEBu8JCRNpFKANrQlnBiwGwgbECuoFxQVBBkYH6Qg2Ch4G"
        "3xCpBOYF3wbVBZgEPg31DeYLLAyMCz4KwAaPCFUJCAfLB8wFwQU3BhoH+QYRBH4GOwOvAl4IhgSwB2EGkgfoBi4GJAo7DlQG"
        "MQNVAlkChgQQBboC2gS3ApgCCQWFAd0DwgMHBaIFigLLBHYDegR3A38DwwRDBmsEbQQXBAAD3gM2AkMCwQIfAngELgPnAjUC"
        "4QORA2gEQQNxAp4DDAaNCRAGThUMBk4EhwavA4sFxAT4AxgGAAW+BLQDWAT1BFgESgPtBFgE5gTvBrUF7wJfBGAFRQU+BcIE"
        "kwTrBGUH0wQdBWcFPQaVBjsEsAEZAI0D7wTuBGYE4AORA9YDOgpxCm4TxQfMDWMMjwxJDZAGBwWZE9gMiBFyEHAQdgmJEToO"
        "WA0+DBUSHBODDk4LSQ1CCroIGQY5EakLLQn5DNwLxQo4DfcHEAptDd0HsgjSCCYJJgnBBqAGwgjXC+EF9gbABYYNYBLcEGkJ"
        "MAz4B9EMaAkzBrsDFwaDCBgJwAkBDEoLoRLED1wMWQvYEFgHnAfnB+QHgQcDBkcHNQYLBnMIWx+KHGAQ6QskCf0EkwhmB1oF"
        "zQnZCHYOaQzeC8oNCg+eDgEI8wOSCWkMLgwiEIUPNwV9Cs0J8w3GCIUInwnSFiIVwRQaFMQIrwppDYAHzgjpCgcLHwslCgwK"
        "yghbCjQIsAdFCEIJ7wj5Be4FEw5ACm8EEQbDA0MJRQ3rCuII7AhjBlUItww0BxYGIwoSDA8NRAwDEFgNSw3KDoEOMAxsD/MJ"
        "8wq5DAQN3gvzCLwJSgkDCfkLAg7+DagdWg/ICSsFLApiCHkEMApuCkMLcAttCCcHHQpfB58H2AUEBM4GQge6CSIJ2gUVBkIM"
        "xgy6BqkE9ANeBgoJtQhBC5EJGQmmBQcIeAzhCjoLLQsbDycK1ghZCboN0wgNCT8KAAnjCAgJMglTBioROhCzDE8JGArjB/0N"
        "JQc7CKgH9QsFEYgF3w9cEZkRMRF7EKcPwg4sEWMRwBGHD30PLQ8HDuUPlBCbEdITNw+DEA8TNAcGCDwK5Q3RGhsKhwsDCvQJ"
        "AAu1CwQN9QpCCzMHyAixB2cKfQi7AxsEeQp0CgYN2QUdB6EKWw9iB/wFkgaSBUgLjAd5C5MMxg3eCzAMgg+3C4gMdQ3EDZYQ"
        "agtvDPUNFw4UDrMKsAq2CwsMkwkxCS4IlgfHBvsJLAtzCq8JdgdzCC4LGAtRBygGhxCZEvkSMROjE3URJAzWDRMNshDGDiQM"
        "dQt5DVEOgAs/CoILXwqaCe8SpgqTDkkLjRa0C/AHKRHpDRYImwUdBgQHVwV2CRAFNwaHBBQFNgPnBTAG6AVqC/8K8AOPCMcF"
        "2gnYBg0KLgxBCHoGEgepBS0FjQSyBysIqwlNB1IGzAWwB1kFzgU+B2wFbgfHBv0GsAaNBGAEIgZ+BvcF8wZ8Bf4FKQcQB1sG"
        "FAVIBh0HxQYUBkoG2AYlCiwKAAuGCt8I3gkECQoJLwj5C2gImwfCBz8I0gjGB20J8gjtCPsKkRBYFAcNRgxcCUwFswezBQYG"
        "nwfqDw4MWg2YCrEFmQtMBXgElAXgBtcIEA8aCTMM6AYGC04HXQfQBn4GBQTXCDQNlgkxDOQGeQt8CD4M+AspCNAOxAjzCCoI"
        "aQr5DKQHVQkVCRMGcwmPCesIlwZJBb8RKRLkD/IMlgmvCRANMwbkD+QK6gY+CHYHaQvNBogG4QbDCLYJYQa9B7wH3givCJYG"
        "3Af7B1AIYgeSBsQH1QSTBvoGqwOKA+kElgbqBmEIZgbWBoEGsgYWBmMG4QXtBgkEoQTXBO8FEgT/AAwDAgNFBYgGmQWnBKEH"
        "KQlUBMECzQJwAzIEsQPZBhQElAMvA3EINwlNCLwIvwhPCbUJaggBB6EKgwhUCLEJ7wiNCrEKNgceBRcIjAWDBS0FXAXjBMEK"
        "IAV3BEsFxwUABuQDxglxDMcKegufC5MLQwtdDIcMpw2DC3gJ0AijCAQJyQjOCrMLcgnUCqEMMgYsBVMGHQzzCY0QiBZ8EPkS"
        "9A7FCxIO2Q6qC9II8wqFCb8HgwTBBwwKBQyUDcUOwgnqCmkPSBKECu8JoQl+Cp8L/gl2EaUKrgxjCRISSxZME98WIRXgFxQP"
        "HRCyD9oQ7wtXCyES5A5rCrsKpAgEC3UPaw9eDTwKSwxbC3oOWAYCCecN7g3DDRsGjBFpDY0OWg4QETAV2A0FEv0RaBCPEN0O"
        "gRCtD+0Ohg9/DUgPpQtvDSYQtwoBCcIJKw8EEakJOxLACyYM/w3HC2MMpQ1YCn4IwQsuCm4JIgh/BAQGqQnyCJUJVAm7CHcN"
        "SQwLB8MExgOTCIULdQgNDtIHYApeBr0NMgsmC9QQIw29Di0LMAzLC/4UiwtZC0IKJQqECVkJSgelCNsQyQuEDs0MUQutCeoP"
        "kwcWCYAMmAvUCz8HPhO2C3QLgAsODHsMrQqcDYMN1g1yDOULhwwNDN0LRAwADe0NJAxvDF4MGwbTBEsGlgh4EiMP5g3RDq0M"
        "ZwxKC+MQhAwUCIERdxJbFmAGswTwDRQKSxVZDAsNmQgeDcQKzQ/rB2cJcA3dFNoTVRMFEfUHyApZDv4IYgXECToMGwkBC64I"
        "MglADIIIigcTCK0GmAfdA2IDPw1sC20HSwhoBiQPtRHLESYIGw6UCaUQWgupCHcFdgg7BBEH+AW3CFoIpwwVDasKigmYD+8E"
        "VQa4B7AGUQZmBJUEwgRCBK8FYxCVD9UREQcYBsUDZgSDBVUD"
    )
    WIN_SIZES = [60, 150, 300, 600]
    WINDOWS = {
        60: [[0, 1], [2], [3], [4], [5, 6], [7], [8, 9], [10], [11, 12], [13, 14], [15], [16, 17, 18], [19, 20], [21, 22], [23, 24], [25, 26], [27, 28], [29], [30], [31, 32, 33], [34, 35, 36], [37, 38], [39], [40], [41, 42], [43, 44, 45], [46], [47, 48], [49], [50], [51, 52], [53, 54], [55], [56, 57], [58, 59], [60, 61, 62], [63, 64], [65, 66], [67], [68, 69], [70, 71, 72], [73, 74, 75], [76, 77], [78, 79], [80, 81], [82, 83], [84, 85], [86, 87], [88, 89], [90, 91], [92, 93], [94, 95], [96], [97, 98], [99, 100], [101], [102, 103], [104, 105], [106], [107], [108], [109]],
        150: [[0, 1, 2, 3, 4], [5, 6, 7, 8, 9], [10, 11, 12, 13], [14, 15, 16, 17, 18, 19], [20, 21, 22, 23, 24], [25, 26, 27, 28, 29], [30, 31, 32, 33, 34, 35, 36], [37, 38, 39, 40], [41, 42, 43, 44, 45], [46, 47, 48, 49], [50, 51, 52, 53], [54, 55, 56, 57, 58], [59, 60, 61, 62, 63, 64], [65, 66, 67, 68, 69, 70], [71, 72, 73, 74, 75, 76], [77, 78, 79, 80, 81], [82, 83, 84, 85, 86, 87], [88, 89, 90, 91, 92], [93, 94, 95, 96, 97], [98, 99, 100, 101, 102], [103, 104, 105, 106, 107], [108, 109]],
        300: [[0, 1, 2, 3, 4, 5, 6, 7, 8, 9], [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20], [21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32], [33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44], [45, 46, 47, 48, 49, 50, 51, 52, 53], [54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66], [67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78], [79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89], [90, 91, 92, 93, 94, 95, 96, 97, 98, 99], [100, 101, 102, 103, 104, 105, 106, 107, 108, 109]],
        600: [[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20], [21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44], [45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66], [67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89], [90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109]],
    }
    WIN_B64 = {
        60: (
            "8xBGD+MO6BIJDqwGTgjTBeEGeQiCDFIMmgxODfAICAqOBwgOGwooEKgSSRXyF04Z4BzRE04UzhAeCy4LZBY0ChAHFgi4CCQH"
            "IAznDBkEZg6gCoYMGA1tDIoUWAxfDRIMJAl9DgYHwAltBR8MBgm4BykL1AqSCNgSVA6dCkoS9xT9DCAOOwx0B5sLSgi3BysI"
            "oAmUCn0KcgvBB8gEgQpuD/kKwgxkDWML6A6DDaYPCA2BDEgRxgoTC2oMpwr2CMQG2A6aCWoKVgw3B+AOKwxhDh8N6Ao4Cq8K"
            "PA26CecKugwNDFMMRgq/DAsEpgQlCeQOLwswC5ETLQovC4ILthM4DwsL8hC1FGoH9AowEDQS0Q7VDMEMEgxqDKsYwhYuFU0S"
            "GhHdB7ELrg3cDF4LHQ+7CcwHUwi6CV0HqRALC7AKPA4+E6kLNw3cDwcMnQk6DLELPwvtD6EL5QxLCBYPNwg3CE4GYAl9DekN"
            "8xc7CdkEmgdFCRwEvgu8DM0WKgz3DN0QkxFiCC4SsxdtFyQQYRa6DkcRww+vE/IQyRBiDkMSrQp5DTAPSQ6TDkcSYAqVCTYK"
            "vQyRBvwLbg4zC88N9BYCC80NeBFODPIJDQx+DUkNMxFeClENWQcQDGAJuAc9Bg4JqBN3ExUSTggFBKMITwjbA3QKMw16DbQP"
            "qwwrCM8Mwwf+CB4J7RXdFg0NthOICzEPTwqvDiUN3A2PDeMQrA1YEj4OVgs5DCAJGwuICzULYgk5CfEI1g6TDcoOEQ5YB8sT"
            "hQudDnsSxREREXcPLxF2F4gQcRJQERAPJgxrEOYQ0A5GEcQOVQvGDnoKtgzgDPgKMgm2DcIItQTfBGMEewMzBZ4GEwbuBmMH"
            "eAQiA6wF4whgBc8KdwtgDhgQ/QwbEe0XihHiDT8MXQxQFEYHkARjBoMFTQVRCGkGUQL/B/EGGgpBCNYICQvNCPkJwAXVBQYJ"
            "WQROBgkDoAjyAv0CZgX5A5MFBQ3NCrAGVwyZCtgINwpfCL4D3wZjBvAFAAZaBhsJggeQCUkG8QQwBjkJZQbHB3IJ3AqFC/EK"
            "LwzwCyMIEQzFCH0IugtgC2UHhAQeCZkGogZxCgkFXQmkCOwKcgsuDH4LgAqZC9gJ4AtWC/oLmA4CB8kLBQUgBe4HSQytFHAO"
            "TRnfEusF2AVyBkQHeAhdBB8HggNHBg8E+Qf1BvkEKgWyBYwEoAR0BkwGPwZGBoEEawW/CAsIYwSSB8wH8wOOBDgF9gb9BBgD"
            "ZQhGC3oICRKGDcIURgYRBzMGhAamBnMFVQmxBuIH3QbgBTgI7RQ9CuwCNgNaBEsIxwWCBPMFWAS3Cf0JKw/MC3MKBBLcFS0J"
            "iQrFC2gPOQyMC7YJ0Bb/FDMdGRa3HOoX/BJlCIcIBA3kCdsImgxFBk4G0wYFB54FGw3ICuMNfgwCEjEKkgsiD5sSkwlpCeQJ"
            "7goBCycIpw3GD3ENjw+kB70GIQjnDlsL8BYqCm4FqgdlBk4GuAsvCfcUtQdqCl8PUA5VCcMNxiGUFsAQJxX2DfEOkxACETUM"
            "JQ0JCmIODAlPDBkMmglnCkwOOQXtCQoKgg2bBw0KEBJ2CR4MlBKVBwoMrA64CbkF0QiNCesJixKFDBAMLgaRCPgHcQXgBCMG"
            "5BPWFCEN3wZoBHoGowUZBKQJvgoZC/wMawmDCccMNAjNBdMEjw3CDf8Jxg94CSMGBgeWCzoLWAtuB2INpQc0ETcL/gmSCqMN"
            "ngnWCUQHkAhsBcwHXxzaG38LXw9uBzUPxgnfDjIMlglNCx4KAwwtClIQvg1FDfUNtQmyDN8DegLnB98SswtGCwgJOgqEC3kN"
            "fwxXCT0hSQbFB3sL5AhuCBUL/w4vDh0MTA8VDCAJDwvMCaQOZwycDjcOhgyjDUELqAp3CtgMpwysDF4KIwgZCM4HTwmsEDgN"
            "CwXjCtUHaAyrDhwP6AphByEKAw2qCAMK3AgiBzgHJQyeCYoM7gsHBt0HaQ8aCl4IuQl6CG0GUwneCLgFcQe+B9kGRQSNCDYK"
            "qgcQClwITwduBcoHsgdcCmoIJRCCCjcOoQt8CqIIXAy4C8sKRwqpCysFHAaPDKkJfwZ7DI8FNAogCWcMRguLDHYN+wjUCwAL"
            "bBBdDHcOKA5RCNQMMwbnBGgI1A5NF90Tlg/nIkIHqgctCrMKfQ5lCRwMBgiJCoYI4gsaFQYUkxzRDNUI0gb0Cm0L0gt/BgcK"
            "qAiZDYALPwthCiILlgiMCPYIhguGCJ0H6g5FEP8O+gwRCY4LtQjMCTIKSgwVELcNPw5AEZoNbwwiCqoLdgZJC5gJaAgHCjYM"
            "DAeDCqsHLgsxC1sKhxBsCi0LXA8OEE0Hvg3MEhsSkA9oFLQNJxj7ILYQYg17ET8P6Q+gCr0K1Q92C7UKgA/7BmcH7weJC6AG"
            "sAi7DNAMxgoKE7oL5ApdEKQPoQYMBzQKxw4/Ef8I5Q2JCwoLfAyGBk0F5gbQFGQP9Q4MCEgEHwjgBAIGCwzkDOQOmQx7EWwL"
            "Kw4PDiEJzwcpDaILDwg8CKIYXRRrD1wQBhPkGhsYGw4UDUMORg28CxIKFQpdC9sLTQl/Bt0ISgkKDOoJdxGACh8HnAy3E00O"
            "xA/CD6ALfgeZByQP3BGcDw4QJgezB9kL6AycC94M1Ar/BkUOZQnFCUoI3wcXCWQKQAtYCNMLfwkZCbsDGwbzCfQFxArnCGcG"
            "UQfCCtYHfws0COoJ4QigDJsLIwk6CJYLsAbSCBoH0Ac/CFAFXA50C3oK6hDQCr8KlwsHD1YQABEtE4kSgBOtEcMTHhDiEWEW"
            "2w8CE8sGqwVnC98SqQqvC+8IMQrSBs4FlAXfA/AHjwz/CT4Kygx+AssEwQW3B0cF8ATzA3ADIgRfAxIF7gPdBMQElAeBBGgE"
            "ygSHBtkIVgRGBvMI1AQgBX8HrgU1Bq4H8QoJBzEGhA+8DKsNgxIiDQQPnQ5JDX4JqBEzDB4MXw12A5wDqwRVCGQGJAYnBgQJ"
            "cwqwCH4ITwvICekE4AUMBRUGLwUECDIHCgfFCSsG+ARKBQ8KbgdzClsIeAlrDJcLrguHCfEJ6QnzBwYI2wv3CLYGlAVqC1sI"
            "tgjKDEgElwk4ClAPUQ44DkIPoQzEEB8QmhLTFJUPhhB8DdkPOwQSA54I/QsKCWkKSgoBCIwF0AOaBU0G8wdpBvMF+wWyBa0E"
            "TAYyCPgG4wiTB8AE9gUTBlEHSAfaBP8FHgU0CM8ERwQqBbMFQAXoBAgH0gZoCLkFKgndBkIH2glKBTII5ghAEPYOQRD9E4MP"
            "aRF9FAATIBECGWYWsxJnE5cFTgTcCTMLcgnBCj4HpggJB44GvwnTCesJEAe9B1cFPAZmBWQHywlVByALfAjPBU4HNAmDBwsK"
            "fgbdCHQHkQozCZUIUwmkCAgIhAhJCMYIfgeKBRENUAuPCQgPxwZfCp8NvhCKEdcQrhIzEJAT4BbAGkISwBZCFSYUXxUSBysG"
            "MwzAEAwKoQoxCI8IaAh3B6wJ2gsVCZIFawZpB1MHoAl+CL0HNQd1CTYHlAh9B7gJJQf9CgcLEAnxCloLUAveCB0JoQn4BnkH"
            "Rgp8Co4GBgfrCNMHSgmlCdUFJAkeCjMPsQ4SDUEO1g3PEBkQKhD2EPEQSg6aFJEPmgeoBy0KNApOBnMKQgmtB3ILVQjDB6IH"
            "sglnBvwGXgcPBnQB3gSQBysHQQroBJgE0gN6BlsFcgcyBuwLZwvGCScKgQlvBqwLJAoSCsALJQrtBqwCVAouBngFqAm6BgcH"
            "GwivEPIP5xJ1EdYP3BCjDsoQBw+aDkAROArvD7IEOAR6BxgNHhKBD/0R0xBrBj0GTglWCMIIIAY4B8AErQYnBW0GKAffBfcH"
            "YAk/BnkFOweOBegImAYsB5wIHAo5CXkHSgj6B3cFhAW/B30H0AVsBZEJiAjnCLsMEgcvCIsIOA4aDpEOuhHHD8UTdw/zDvwM"
            "nA0tDu0MThH+BVMFzgfQChUHtQjDB/8HmQl6DM4JmQrFCu4EdwbKB60E8gQCCQsLPgnVCEYHGAOqBtAKEQfJCsQIvxHQCz0L"
            "DguDDYsMXAyoGQgZLQwPDuMK8wivCugKdQjNCfgCfgoBCAwNDgytCv0HWwadCUsIXQ6mC6IIvwgMCH8MmgPTAxoH+AfqD+kM"
            "rgtYC6wJ4weIBkAFDQeeEkYQ0BGgEVsE8wRoBo4HwAU6BRQC3gSfBxMFzwfzBJwEuQdgCMYGVQYSBtQK8xOHEzcItgYfBw0H"
            "wgfBBW4GfAceEtUFiwdwChcJDggyBxsGJAmlCJ8JYQbUCdMH9QghCl8BtQKrBLoI+gYEBsMHNAeFCQ0KgglLCzMJkAnuCcUI"
            "fwp4BwwJMwlLCRYHxQbTBKEI/Qm5B5oJjAcfCFEKiwpFCq8I9wvZCWsJUwlEEicHogedB20KDQmmCY4MfwkKCu8JFQvnCFEI"
            "mglxBwcKpAx2DM0KGwqcCXMIuglXBIgEUAcrCSsHsQbkBxQGkgZqAzsC9gIpBykJAwjKCXQMPAamAwoFIwY3BPUEWQXfA5UE"
            "tgQ8BucEhgJ2A7YFVwOCAeYCBgfKBnwEXgUGEQgHqgUcBUEE4ATvBOcKpQQJBQsHRQU4BKoGLAVdCJIFyQXfBBcIqQaVDIIG"
            "AgKEAjAEswe0BDUEzwJVBP0VigyzD5IJRQxmCjMLChCfCH0OSQyNC20KXwhECiMJwQoUC8sKLwsVDGALZBXeCSQLzwpSCI0J"
            "rwzqDPEV+gSnB3AL3giWCLsLFgV5CJ0KRwhyDcYNTg35BnMKvgl8CkAG+AkBBwQDOQRbCCQHswvsB9IFIgSWCCoNigRJDq4N"
            "1A12B1oKYRIqFMAitBRkB+YJOgjoB+oHTQi+BaQIGwpXCH0LhQnDCwEP5wrnDI0K9gfsCiwT9RQHDDQGewa8ChkInweSCooF"
            "shIXCGUHWw4VEIsM8waLCZsKCwgcB10I6gaLBh8DqQclBJQHLAgZCGQGKgvXDrsGNQMCAisCcwRfBUwDJAR0Av0FqQAcAzYE"
            "nAPmA7cDdQMuBssEgAQoBIMCdAIBAuMEQgPyAuEDKAWbAusBjgR+CJgXQgVqBfAD2APBBToFQQSoBOEDigNfBs8EwwIZBusE"
            "awWJBe4E2gWEBSIGYQEhAOgEZwXbBCAExQPfA0wJeQrhFDQIxg29DL8NJQatCiAUbRFtDgwQLBAlD5oVhg+6C3UNugqMD2QL"
            "9AxcDBcMiwr+Da4GBAnSCY0KPAdCCW0MwQdQDIoUggnTDJgPYwneBpoLsQxrDLYUqgn6DZAJbAp8CDEIOgb5CL8e8RzCEQkJ"
            "4wTyCTYHTgVHCboIFg/zDNEL3Q7QEIAI6wh5CpYLfA4ZCc8NqAp2CScWwhOfE+kQ7Q47CB0L1wunC4UKGwvABl0HbwgICikG"
            "fg5eCrwHYAhWDYQJSAkpChoMDg1KEFAPLQ2pDroNCg++CsoPDQxDCtsIAAyMDLcMJB9pCZIFbw1sCNMERgrFClwMmguGCXEH"
            "ZAkFBy8FcgWDCCYLvwbWDrkH1gRzBksKlQrCCxcIRQrdCwAMig3/CqkJnA3JBysIGwgqB6cHTQaNEXYLXgkoDj4HNgmcEBoQ"
            "aBTTEFMPPhCLE+wOvRH9D24S6hN9DcYSEQZoBpINXBqYCuQNzAo5CzYKQwxSDp0McQyOB+oIfAouCi4EPwxwD58HDw+wCF8G"
            "rAVTDVAIIQ4rDkAOggwyDUkNOxAtDCEO+wxRDTcK8wugCPsH3AjiCRYMaAqkBygLmgofE2EUbxPFDTkM0Q6EDsgMMxAYChkM"
            "MgrgEXMJOAyREBcLFwgAE1wNwwg+Be4FowevBckJmQRDBaEEIAW9BS4F7QkjB6QIdwfwCp0IrgYmB3AF6Qb9CPYGvgb5Ba0F"
            "uwd0BAsHlQZbB7QEjwVFBm8G5gWeB+cGUAX6BpUGXgh1C9QK4gdsCbYGuApbCWkHhgnHCM8HYQpCD5wU8w0iCVYFgQpEBV8G"
            "mweVD5AKbgzTBxYH+woTBVQHLgkOET4PrwmyCAoI4gYWCbUORwthDIoKmw20CGYPqQmwCecN4gYNCv8JCgiHCu0GxQahE9ER"
            "/Ap+DUsG9RGUCGQLKQhxCAULlwdNCZgIbwpNDNgJXgl9BcoIsgMtBNQGBgelCM4G8QZ4B4EGOQZwBp4G+gbvA6MEhQWJA4YC"
            "8QNZB0UFOQlqBYsDnQMUBZgEFgaCBHAIlAhUCYwI7QmPBrQLNQcmB6MIGQoZBmQC/wf2BSkFvgpiBWEFAwZ6CtYKAgqOCwgK"
            "2guQCO0KyghcCE8Mkgd8DKYFwAS3CYoL1hCiFIIQchNXDusLUw8UEUQL/QnsC7sHzAatCJYMfw8PC2wTUgsoCpAKqQ23C6YQ"
            "BBD/E5wSMRfdFskQbBASEC4LxgoLErMJ7QeYClERKw6ODMIOdgZbDg8Quw8ZENoOzRa5DscQqQ+NEbQRtA8ND18JPBAnCmAI"
            "JQ7wEN4JJRRnDHsN6g2zC6QMUA4aC4AI1wtICI4HEgaZCsMLpQkZDnQICwYuCLwMAQpRDccK6A3BC1IRzA7NDXcMexOUC3QL"
            "PAueCXkG/Qd8ETwQ/QreD50HJQ0TDb0Pnw2SC6MMLww6DnELxQ7pDcQMeg8kCw8ObgVjBOcIhBPdD5gOlw/xDccLFwsUEfcL"
            "vgaJEzsXRgY8CcMOIxeyDqoMjQ5qC3sOKxWtEWgRwg6pDwMJlwotDe4K5ApSDUMHAAg1CfIHzgNKDjEMlAk0DQMVrgj2Dv8S"
            "bAxACGIJnQldCtAO6QhkD6YG9gpLBpIGAAYKCPYPuw8eEiwGtgPnBL0FQwM="
        ),
        150: (
            "MRNyC+0HzwvdDKgJARLOFyMa9hGREV4LoAo8DBIMpRDsCxIM+whyC6IOaA7OFLULMQjNCnQLtwdqDfUNVQ/wDRkOWA4ADBsN"
            "Mw2+CswJzwzvCtoH7AxHEF8SLhTMDtwQ7BFjFV4W2woZDa0MugrhEtER9RHvC4wNvxB7DJQHKRNoC5QIFBTmE54WBBUdGmgT"
            "khJuDXIPMg9eDOoPYBVkE2QM2w4aEvQKqgbAFWIMFAiaDSkNKApMFEkRYg74DesRqgzPC6cMXw2YECMPCg/NEnESShI4DvYS"
            "cBHBDMYNOAcaBSMGrQY8BL4LZQ/NFYgRyhHJCNAGJAceCPIJQwg0CHwGIAXEBx0KsApiBz8GPAczCLIF/AdYC0IMpglcDP8K"
            "wgenCdYK1gyUCZIMiA5/B2gO5xiLBwcHpQSFBnAGDAWuBu0FUAaEBZMF8QdVCL4RSgbWBV0GgAdCD5gEgwY6BcwOXhTMDf0M"
            "dRS/HIYaPwpPCmEK5geQDwoTsBAJEdkL9w3NEdIHbBAWDdgHIRKhEBMYjBchF1oSgQ3EC8gK7QsdDFoPPxIAENgICwt5EhMI"
            "GgW4E8cIKQbNC98KVQetDQgNVAdNC0APQwu2DJUKhhFzE3wOeQzTCkMKnw/pC6oG5g5jCnoMLBWgC/kMVhCsC/oMNQ9JDcQM"
            "Rw+6C94NmAqfC6gORgmcCtEHOA17DMELbQgoCIQG7AgeCc4G8QmXD4gL2QtDDWkL1gjCCk4M1QymCboPGQ77B14QmRrGCSgO"
            "/wlHE8EVTwm4C4wLxgszDNAK1w8cD98NhQrIDYUOPg5dCkgKKA0mCjMR+hFjEQEUhhgdH1AR+wzsC4sMFwq5DasTwRG2DaAM"
            "CxLPDfoFcxITDk8GHw4yEZQNbAp/EpcUZBfcDlwNwgu9DG8LMBBkDFEU4hC/C7ET2Ae7DaUQNAyGCW8MqgiZB+YJ9wcuCqMK"
            "TgrECCoJqQtzC2EOOxFOEPERJBN9FGkLOg8jCk4GEwt9Cf8E8gchBFIEqAV2BIAHOAYTCXoGDwozD9oMkw1gDPgMhwcrB1UH"
            "6ApJB54FaAc0CI0FgAkpC7sKGQp4CrEK9QjzCSUPdg3BDSkTHA++BysMDQoqBVIHzwXLBXEIcQW1BosGdQT1BUYGcwkxB4MI"
            "2RGPEXkS2BNWGQwJPwyhCCkI3gjsBe0HUwoHB5QIKQmMCGUJ7QmfC7sK2guuE2MQZBL/F/8UvgsfDwgJ4wkpCDUIugfSCYEI"
            "wgojCvoJ1AhjCZAMpAhzCW8Ozg1jDukQzA+OC7kKJwl2Ct0IuQWxBeAH1gQpB1QMVgqICpcMGQp2Bk0JvQ8tEQcP7A+zEIwI"
            "CQ9zE3EIqQjHBT0GRwmTBr0HjwhSCDkHdAe4CeEIrwrGDpsOzw9cDlcPuAlcCpkIBwtRCJ0GtwgeCLUEUgmTEEQN8xWUGC0P"
            "zgkxCKEKLAu2BkkNwAkhB0sLzA2dCPwPqw+MBrgG0gNNBxIH0wZqEC0Rago5BgwPGApsCAgHagk3CXMFzAdaCE4LaQqqCQUJ"
            "8AhuBiQJXArfCd8KZQ0RCpYJIAyOCvoHLggEDPcIngZdCc8HDQUFCTEJ8QQqBlIFGQYYBJwCqQVEB7cPLwQ+B8YGtAQ6BUcG"
            "MAcZAy4GCwOLFV0N7hBJDOkLpQoKDOoQ/AvOCowQrQuTCyYK8QvNC18KlwhbAxoLvgl2DPENkRS6HEUJUwlVB7MKPQ7LDBwP"
            "4BFiCoAJFhAtDDMMOgm6CKIESwndCy4PdgLwBKICHwOJBJ0ESwTFAgoDuAMHBHUNWwT4BNcEIgWDA/oF3wYUAhgG1gNvEesR"
            "RxGMEX8VshVnD8wMEAxJDLoL2Q19EgUS8gk7DgQUIgvdB1AfzgwgCEkN2BHJC+0Lag6qESEUagqGC7YKDQpED20LvAxgD58Q"
            "rQ/4DkMK5ROQD6QI1AsLCfcFcQkYCuwFMAthDHQMwwpFCpcNhQplC+QTmxHtD0YSRRJcC9EUCQwPDH8LcwthCtULEwdtDDAO"
            "sA5nDkoPBg6vCsILbhBcE8oOIA8VDBQRjBQ+DzgG5AcNBgYGMQhZCpwGIgjOBaEH4gc5ByoHkwcKCXsKygm1CZYJ3xMDC94G"
            "Aw2jCfUHCQ9ZCncIBwtfDn8KTgsYC0kOXxLoDZoJhAiOB7UKfAfNBRkJKwi0BSQGHwR3BW0GswPiBZgI9Ai9CAIKXwmnBBEI"
            "vwnCC3kJHwq2DGwIVw+nFCAQagzYCBQNrA+OCrgQ9BX7FGIQhw8pEM8NGA4cEgkTJw/bEmUOrwwtFEEOzA5oCy0I1gtSDL4H"
            "Mw0CEP8OdQ/kDTQPjQzLDssOEA3BC4APgg4ZCE8QSg+6ETEUVw6ZFGwS2RSRE7UL+wsMDMcJcBBaE1cSoQpLDCgRkQl/BWMS"
            "WQmdBQ=="
        ),
        300: (
            "og9ICjsMkRaHEqwLmQoPD/kM3AxXERwKeAsCDoMNwQ18DF0K0A3LCpEUyxCsFr4PDAzCFLgQBBHxDAEUWBXHGeAVthFlDyYU"
            "9RG8E2ALHBVtDfEPPRB6D2kLUw5aEKkSkxJ2EuYKJAbJBsQPTRIlCA0HgAlsCbwGNQn3Bg0IFQrZCo8JqwoOC18OsQxvBw4G"
            "fAYhBjMFxwygDTAG7w09BZUSQQ4bG3IRmAr6EdMQFRAmDVISxBLFGdkS3w1pDIoRxA6wEfYHZhO0Cx8LOgz1DBULLRF3DHoL"
            "xQ45CwwQCQ0TDsoPBQ1+DWUK9wthC2AMIgjcB6MIKw2mC7QJfAs7DEoP7A46DDMPMxQhC30L3w+jDFkPDw3NDOQSjhPZGQoR"
            "/g0VEWEPfROYCswSSw/nDLUU/hfYDIsNKA8QEPAO+w0UCzIJowrQCoMIsgxMEJAQ7hQ6DOwJ5gg1BY8FfgbrCCwP8gtoDEcG"
            "5AirBqAH+woVCgoKLQutDUESngitBVkGZgdEBn0FmwhGDgsS2RYrCu4HWweWCfUITAncCyUPYhG5FeQLvQiBCO0I0gqfCLML"
            "vwvMDegPCwoGCmMGfwddCrIKjAjjDe0OIBHSDLcI0wZyCMUIXweFCqsMIA4PDxQJfwlnCMUH8gxBFU4MdQjGCOsLxQnnDq4N"
            "mQZ9BjYOPwlwEVUHFgk0BnILnAoBCJ8JPws8CuwKpAhtCikHiAfpB5gF5wSNBbIMzwhNBb0GDwU8E1YPFAzyD2QMdAtGDZYL"
            "bAiRClIUjBfrCTIOOQ3pCbkUMgpwCCEKKAPoAogEwQInBL8KMAVCBeUGhAOXEmkTjBWrD+EMvxEFEYIULwvIHNMPIww5E20N"
            "hwr9DmcPyBBmD4gUMwqgB6sK9wuKCl4MoQ6ODy4Uxg5ACx4M7Qu5Dx8OZQ0TEBsRlBIlEK8GZwajCJsGuwebB4sJuAkNC/IP"
            "TgyNDPAJ6QvSCjMPswoVCTUKMQeEBXUEHQagB9EIxQdBCZ0KrQwDDkkOIAscD+UTkRAID7cOJRJsEgIQdg2VCgYM1Q6LDnwO"
            "jg28DCEQug2CFPsRMBYPDw8LTBTfEM4QsgmIEw=="
        ),
        600: (
            "MA4oEhEQIwxaDWUPfw2lDuILiAzXFMoVHBLoENgSfBnEFR4U3BIeFAoP6RCGDbIQgxOTCfcLoA7yB3IIXQihCSsKwwolDl8H"
            "pAbLCPwLSQnUEX4Y1w+nENUQFBfAEjoQZBCXEcwLIg4BEPMLbQ2AD8MO7w1aClsM9QdOC9IKiQuED3cOYhN7DsQNyg13FCoZ"
            "QBEnEZoRNA4WFEsOyA6kDmUKUwsnCw0Q2RCqCccFkAfKDg0KOwigCZ0KjwuDDvoFLgfFBhYP0hHkB64JSAtvD3wRlQhVCrIJ"
            "MgzjDcAIJgr2CccNLBBPCEYJbwmqDN4MIQliCs4SIAijC18OTAcIDvoQ2AeGCyYJIgzJCvgImQe0BSUHfwicBTgSJA8iDb4M"
            "3QpLFH4LrwyWE88JLQMzBO4F1QQPBS4UnxUgEXESbhhVDygSuQ12D+USRQmLC4EMIg67EIsL6gwoDq8PFxL3Bm4Iigh6CQsO"
            "+AzQChcOagpeCd0EeAcfCH8Jjw00DccSwxCcD1ER+QwGD+wPKg1hD0IVxBWMES8RsBE="
        ),
    }
    # cross-encoder（BAAI/bge-reranker-v2-m3）對「每題 × 每個子塊」的實測分數（logit，int16 ÷1000），CPU 上事先算好
    CE_B64 = (
        "6Ood5JPYeeWs1ujU79Tt1N/U3NT+1tjjVuPp1OXUqNcF2rTWbtbh1OnU5tTi1DXjItZ35uvUCtYP1RPwlO0n9+T/2f3a/e3l"
        "+em75wrk5dQ/1Vvn6dbh1OHU79Th1OTUM9Xh1OjU8tS82zTV5NT91NDm5tT31N/UCtdJ1dzU6NSP1ab17NRO4xDX8NQB1eXU"
        "7NT21LvW3NTn1PHUBNXr1ObU9dTc1OTUGNXo1C3VmOd+3FHV3thk/EbfYtfx12LWz9iE1UrVBNXf1F3cAdnr1BTV99T41H7W"
        "4NR71unU4NRL1cTek9m33zLYvdnm1AjV6NRG19HZ/NoT2a/eotUE253n7tQF1drU2tTh1OLU7NTd1B3Va9vm1OLU7dQA2/zU"
        "5tSx3OnUUNUP1avWj90M3dvU3dTs1O7U7tRS2+vU9tQJ1e7UANXq1OXU8ODe1PfU8NTl1DzV39Td1PfU5dQE30rb4NTO5ePU"
        "3tQx21DbRtxC2PHfqe+t5+TU7tQb4wfktuQk14XVH9Xm1LvVSdX71OrU+9SD1+Lqq+QX5QTe7NS41eTU+dSP2zjl2Nbp1OLU"
        "utow18jV69Th1N3U3tT31PbU3uvm1OjU6NT81O3U7Njn1FrY6tSm1/bU9tQJ1dvU6dTp1B/VANXk1KfV6tTC1+PUAdXj1APV"
        "5dTq1ODU4dQM1enUHdUY1ebUvdY+1XDi6tTl1ODU49Tn1P7U8NQZ2BHhDdx31TnXnNsu2rPWy9Wf7XDaNexd1+LU59St5ujU"
        "9tS/4NPZWtdD2BHgnN/j2AjYRNcd5OjU69SR2SLleNvp1OvUitpr5VTXK9Uy1W7WH9zt1O3UfdW32vjU6NTs1PPVEOMj3jHf"
        "79SY20jXptX21O3U8NTq1OvU59TI1T/Z9NQr1enUCdWQ1gPV7NT+1FLVH9X/1PXUGdUI1aPYNd4n2uPUi9Xk1OLU69T61OrU"
        "4tTB2UHVVtg52HzVCdWS3PjU8tSS2vHYB/jM8s3tM9Uy4NjeTObd1S3XjOMR1WrYM9rl1OvU79Qb2RTb59vG1Yvf89Q71jfW"
        "6NR11d3U8tVN1RXVHtXw1PDU9dSh1xDVFtXB2NHXpuVI3x3k7tRa3rTl59Tp1N/UadXt3JDXh9je1zHiuNXb2+7XP9lr8hnY"
        "7dRl1qzVPuRZ1s/VWtXy1PTez+MZ6Bfbt9dS2eXULdWe1e3U/9SQ1QLc/9Xh1OPU7NTa1OzU/dTc1N3U+9Te1PzU3NTn1N3U"
        "7NT+1PXU79Tp1BnV69RL397U9tTt1ALVJtYN1aHV+tzp1r/sBeOY5d7n4tTg1GfVwdje1N3U2tTk1N/U69Tv1APV39QE1enU"
        "C9X81JDW4tT/1N7UTN7l1NnU5tRb1YPV79Te1eDUA9X11OXU+tTt1N3U69Tv1OnUDdXx1NvUBtXf1N3U4dQD1d7UuNde1dzU"
        "l99R5xbdsdYS1ebU6NTi1OXU5NQD1qPixdrj1OfU3tT11LHa4NTs1F/VDtWa3JPaAtWm1+bUxNeM1jTWENVA4gLYOd2f3eLg"
        "gd3h34DY5dQS1SrYDtXl1OfU7dTe1OfUdNbl1ObU5tQr1e7U6NRC1ajV6dTp1PfU0NoB3ODUXOKW1V/VotWr3ArV69Rh1fTc"
        "7tTr1IHVYNwd4fzU6dRh1ezdU9X31ujUBtWw1av9idiGB3Pi89QD1eXUAtXm1P7U6NTx1PnU5NTc1NzU39Qa1RPV8NTi1ODU"
        "3dT11AfVBdUT1e/UC9X01PnU8dQF1e/UA9Xj1N3UA9Xf1OLUDNXz1PjU9NTi1P7U9dTq1OTU3tTx1ODU6tTm1OjU6tTf1OjU"
        "rNZm7ZHXBtXn1OfU89Ts1BbV7NQU1evU9NTc1PbU89QM1efUE9UM1QPV49To1OrUdOTp1ObUAtXu1CDVAtXr1ODU6dTi1NvU"
        "39TA1YzV/9Yk4UDlgezW6ILVTdXl1uDUuepF1iXV4NR71eLU4tSD/rDwMufP8uHkhgbI2ILsHdWn3+DU7dTh1DPg5dTh1OPU"
        "UtVH2RfV4tQI1dzU7dTk1OTU39oc2uHUKt5N2+XU/t5C3gHi49QD1pPX7NbG1eLU49Tf1NzU5dTl1CzZ6dTk1ODU5tTg1OLU"
        "bt/i1OLU5+vo1PHU+NTt1ObUmN7s1GjlINXs1O7U69Th1OHU5dRN1Vfd5NRp1TLVIdV918nbmds2GrPpYO6a4JrX6dRP5OXU"
        "fNd32BzXzdnh1KXW9tTd1NzU59Rk2ebU59Tp1LjV39Ti1ODV7dRs193U7dVU1u3WF9jj1OPU9dTS7uHU5NQL1f3WxtnP2P/U"
        "7NSG19vV3tTv1OTU5tTd1OjU5tTi1FbWhtjf1qzV89Sy1vDU6NTg1N7UXdX31PfUBtUA1WvV39pE9+nU49Tk1D3V7dTm1N3U"
        "3NSD1eHU39fn1HPVFNf21PHU6NT/1P7UUOI417nW+dTr1HPVr+Ll1P3U8NQD1cnVcNXt1OjU7dQC1YThNNbh1ITk4NQK1efU"
        "+9Ql1erUAtnS2d3U39Tt1O3U39T01GURSeVPAhTV69Tk2cTd69TC3ujU5tTl1OPUbtb11N7U+9Xo1KrZ/tRn1urU7NTo1Bre"
        "TNzf103Vydb61/7U8NTt1OXU8dQE1RbV4NTK5hrb+dTh1ObUtdYo1eLUCdUlFGrW99Qu1Zva3tqu1bvVUOJF147ZQNg821PW"
        "G9a94qPjpdsp1QfVTdrf1HPcFNUY1RHdL95D1dva6NQO1QTV5NQF1ezUy9vW2oraVta61oXWDNdu3enU/NQ72BPWV9W87d7k"
        "+NQi1jTV6dTo1NzU5tRL2ezWM9V63m/c5NT73VDV5tSg3CDVVtcD2RLVdNzi1OzU79Ts1KvWc9aI1eDUPNXi1BLYrd271wTV"
        "4tTd1PHU4dTo1ODU59Th1OHU4dTc1PrU29T71O7U3NT+1N3U3dTd1AHV7NT+1OLU9tTu1OPU5dQI1dba59Tj1N/U49Tg1ODU"
        "+dTc1N7ULtW21eDU39T51PnU4tTn1OPU4tTp1P7U3NTm1OXU5NTi1ODU5dTk1NzU6dTw1NzU6NTm1ObU5NTt1ObU5NTi1IPV"
        "6dTi1OHUjtXu1OTU4dTl1OTUBtX61P7U39Tn1HvkLuAJ1RAY+NQF1d7UHNUq2ozV7tTv1ezUjNbg1HTVQtw54MvbTeCV3jMQ"
        "sv6h3pLb7tTn1OLU+dTe1OHU5NTh1C3e6NTn1GXb4tT52P7V49Qh1RfVQdWL1efU59Rh1UPV6tTv1FrebdUg7VrVX9vl5/He"
        "4dV91jje69Tv1N3UJdXc1NvU59Tt1A3b8tQY5OPU6tTf4IDVU9Ua1eDUytjl1OzU/9Tr1OTUVdaP1RLV4tRp163XfdU71RvV"
        "EtWT2XLaU9kY5SPbzd772aze8N4v4jLV+Oj45KLbot9e3CDgxtdi+vQUGuWu3nraFOv81Drt9ddW6ejU4tTc1Xvm4Nbk1OnU"
        "791L3YPWbddS2TjWb9nh1ODUINWp3+DUeNcy3gDVo+G63t7h6NTV1m/VPN6S1eXU/tTh1NvU3dT51xDfftWk2+PU3dSB1+LU"
        "Yt6Q1eDUMejk1OfU9dTq1FHVI+uO1d3Uptbw1JzV3dTl1N7UbtVu1jfV5NRH3e3U29UV1Tfc8dTe1OPUPuHj1OLU4dTx1OrU"
        "4dSe+iblntej1YLVKOjf1EIRmuZk5PfUC9VH1W7Y8dT51N/U39Ti1OPUB9Y01/fU4NTp1OjU4dRL1eTUO9Xl1OfUQNZM3O/U"
        "69Tj1DTVA9Xn1NzU8tQl1XjV39Q41ebU/9Tf1PLU7dTe1OfUKdXj1ODUqePm1PLUDNX/1BrV2djk1N7Uddbm1OLU4dSA1d/U"
        "39T+1OjU/9QQ2OfU3tTk1OnU7tTp1OvU5dQL1pbX4NTl1OrUBtXe1PfUBNX71ODU4tT61NvUBtUN1eXUKdnu1PjZ5NRV3+3U"
        "49Ty1CLX6NTs1N7U4dTq1OrU7tTk1E/c+9kV1f/UENro1NHh8NRG2enU7tTn1N/UY9Wh2rDcNd+S24vaQNW2AVbjkNxr2G/g"
        "cNob3RHc9drH453oqtqg2xzX3tTe1OLU9tXs6hXY7tQB3HPgZNVQ1eXU6tTv1LfY69Qm1e3U69Tn1N7UB9bB3ejfQNWK2hDV"
        "3taR1enUntbe1EDV49Ti1ObUmNXc1OrULuHe1OXV59Qm1fjU4NT01N/UgtVK1ajV3Nhq1VbVqdbn1OTXMdXr1OzU6NQg1ejU"
        "AtVF1f/UbtVd1d/U6tT045zmCuR57RgGNtxT6W/nn+Bs5jXi7uWO4RbjHOug3kjdmNuV2ifgntWO2bbVxNcz1xDVDtbm1OfU"
        "P9Uk34jaFeJ+3PPU79Ts1ObU5NQD3FzYkN0B2A7b6tT31ETWS9xz1e3UH9vr1aTfJd8S4wjVj9U12DXWD+F34d/hmeGX5V7l"
        "k+Bh4OXgONVQ1SnW5dXz1PPUINUH1dLb99jt1PjUCtjv1Djf69S11wDVqN051enUf9yF3uXglOYN4bbfJNYN6mzeHd1e30rk"
        "veGs/5Xlz98g5XDjxNwH2r/ac97K2T/ZU91E7CPWjtsc4DrZ59T21N7U6dQD1fHU5NTs1O3U6tTf1N/UjdUV6EDoA9Xu1PDU"
        "59Xp1OjU4NTl1OHU5dTk1OHU5dTj1O3UFeLk1ArV4dSP1efU99Tn1OXUoNWY1e7UsNWw1fDVINbm1O/VJtXt1PPU79Th1C7V"
        "8dQL1ejU6Nfy1N/U7NQi5EPnZ+Ia5YHg9NzE6SDmB+Mw5SLkAeOC4/Tli+TqAjLl2ORQ4WTgo9Wn1c7WF9vk4PPU4dYb1fDU"
        "4NTj2efUzdY21+XU4dTi1O/U5NT81N7U4tVs1fLh4dTv1AbV3tji1OvUIdXe1IfVVNb/2eLU6NTe1BvVE9ww3X/a0Ni74MDa"
        "dtWk2JnVNtUH1fTUJNbw1O/UTNXh1BTbnNZA1fPUrNXn1B/c89Tr1e3UPtWx2OLUmdlm273fLuhH3Y3c/dQg6IvZ0tl25WgF"
        "X+Ju3gDjAeCI6UTkGNoL2jPae9qS2SrVSd5O7OvULNUO2jXV7tWz4PfUXtnc2frU7NQd1e/U7NSy4GXWd+kV1WHW69Tz1PTU"
        "TtYo1Q3V19vg1PncYti53ufU8tT51PDVs9Y05A7lzd4l4dzcMtfu2iDYCdXh1QPZo9Xt1O/UC9Ug1QvV99Ts1BPV2tgP1Z/V"
        "AdVE193XMNUo1d7U4dUe2rPfjdzW2pjfw9Ub52jZZ9dz3mbajtkJ3WXeCuBZ2A7e8O6h18/bTtcY2vfUl9UI4QTVpdXG1xjV"
        "Rtn01/LUAtVY1fnU6NQH1fXU8tRK1fbU6tol1frUCtUU1XXYBtYA1oXVb9rh1OnV5dQc2OzU7tTi1K7bLtam1djYINaE3Tjg"
        "UdZB1m7VW9Y5117Xr9Zg1k/WNtXq1BTXE9b+1PLU7NQ61fLU89T81HDWYtXq1sDVItWg29DcjgcS37nbKdge4pbaJ9ou3ujt"
        "mNgb1zPdA9tO7onX7dQy1y7aC9YX3fLU1NVg3xX3rOLr6r3j/dXr4bTV1ttr3QrV79RD1erU69SG10za9d7+1P3U7NQ+1UnX"
        "RtsP2afV4dn41CfbpNec4KDZYtX/1dPV59aM3Ongidz75K/ba9vM2snfYtUG1mfV4dny1PPUjtXy1Cnk0dsG1jXWJNko1YDf"
        "BtVj3ufV99XC3OzUYtny3Dvi/OO04OXgANlb7wjtN/us6UfkZOIK4h7i3N/m4azkIN5Z4BjdIdiF3PfUZNXK68TcndYc3HTX"
        "UtZI4SjV7NZs1ZXVqdb91BvVPNX21ObUj+GY11zVstYv2K7YpNXm1ufU69Tj1DzZ/tSC2SHV/9Xn1BDuct731fvlhtYu2d3g"
        "5Nfe5YjVQBLFBULVReM+5K3kaNZZ1abgINwW5DDVG9Xo1x3a/9Qx3BzV9NR11evUq9gN1Y3VCdU91bnZ79R/1u7U79Q81Vfd"
        "NNzM1r3WUdXv1O/U79QX1erU4NTe1ODUr9X61fvqr9iR1mvZlddm5PPU59Q81mv2yO8x3/7t4PKD1THXsNlG1d7U5dbf1JjX"
        "9tdQ1uPU6NXj1OfW3tT61PLU+9V71prW4NRL11vXAtVS2XDY29Qz1gzVCPrYBmvVXtXy1PTU0daX1QXV6tR+1ebU6dTB1ufU"
        "avV61zbVB9mA3O3UidX11N/U29Tl1OPU99QB2KTV4tQw1uDU8tTh1PPUVdXb1N/U59Tj1I3a3NTi1ObUBNV51yvXK9Vf2fPU"
        "1N3P7Rzdh+RR4kjaF9hL3APVqdYX63LokutB1oLV89us2S7jr9/X4OzZ1N6S28fpUOIK6tHkduAC3Z7XcNay4rvtTeja4Afe"
        "XeB36QPmC9pm1/PdCAXH1qLW79dv1rbml9o32tPgouay4bTgTtXo5oHfVuEY50XfH9741ZzWKtXk1tvX8dTy4lvV4NWq4FXW"
        "7dac16Pd+dft1BrV+tSO1YTYMNXy3AnWvtZ/4f3dqtUU5OXU69eD2NvU5tT02XnZJdWc2PbVyePz1N3UKdvg1OHUyNrq1JnW"
        "9NRj2pfW3tTg1HvV3dTq1FfX2dXk1PXU5tQG1crZ6tQr1eDU3tT71HPVnNUG2FzVBNVB36P82tZM1T3aB9VZ1fXU7dQS2PTU"
        "Ytfa1uvU+tRM2QPX9NTz1OPUGdXu1O/U+NRR2uzU9dQ71QDVMdXr1OvUjNX11PbUCdXr1PDU4dTd1ObU6tQ42ZLcUdV31uLU"
        "Q/Xr4snX9tSo2lPXC9hg1bLnqdUh5pTZWegy1d3UQNUV1eHUTdVO2RDVD9Wk1gvi+NTj1wXhiuMs4lrYBdbuELvZztvP11TV"
        "59QT1djVHd663CgXdNn41PzUTNXg4gHV5tT21O3URtY03e3U7tQo2uXUm9Zg1ePUGNac4Z3Z/dRF1enU7tSV1ePU7dQW1enU"
        "7NTy1HfVj9Xh1OjU9NTj1EDV5dTX1u3U7tTt1NPXItXa2ZPYwuLj3N/e5tSr1kzhWeDA9QEbkQTN15vV2eSR1d7UANnk1ODU"
        "3NSE3uPU2tTk1Obh5dTf1OndZtd81gPV/9SE2xDZVddY1WHW39QN1erUyOLw+f/X59Qy1Z/VK9VN3kHV+dT21O7UB9Wc2u7U"
        "SOV91ezU6dTt1OTUddd326nW99Tr1O3U89QF1e3U4tTk1OvU69Tn1OLULtXj1OfU6tTo1K3X3dTq1N3U4dQc1XXY+9R42ubU"
        "utc71vfU7dQp1mDa7NRv1+vU8dRA1fPU3NkF1fDUfdj51CnVWNcs1ujUt9UT1cjV+dRG1QHVLtXf1O/U7tj51BrWFNUT1fzU"
        "3dQh1uDUgtUF1jzZetst1tTV2hSz1aPdwtZG1fnU/NQU1ufU79Sc1R3VV9jz1OPU5tRJ1cvWGtb94QfV9dR92RHV8dSg1dnX"
        "XNeG2ajcQNYu1hbVPtVi1fXU/NT41ebUfdVK13XYptcb1RjV3tQx1bji9NTz1uPU5dRq193U5NSE7uDUFObl1N7U5dSw3NzU"
        "5NSR4Qb3Zu/g1N3U49Tx1ODU6tQy2APVEdX01IjV4dTn1OTU3dQr2ODU4NTk1N3U4NT91PrU3dQu1vrUC9Xm1OzUQN6Q2CvV"
        "5dRz1vLU8tQH1ezU5dTe1PnU6dTm1ObUBdXx1OTU+NQp2+rU5NTh1PXU4NT01APVFNUS1d7UyQ5EAHnV69Tp1OLUBdXl1PTU"
        "5dRM2BbahOCx2UHf8uLR5OTU59RQ1dTV7eD04Y/g49Tw1ELVw96s2R3Vg9Ut3x7tBeQc7u7WK9WT1+jU7dRc2pDa8tko1UjW"
        "sNXN1krb5NTr1OPU59Tm1OfUX+xU1eXU5dTm1ObUBOBQ1Tvg99Q21WvVx9X01NnUOtY/3mbW9dRx2enY89Rn24fVgNVu2+fU"
        "/9RI1bLV9NTr1APV8tTp1EDcANxx2+4K/d//1ePULNbP1+TU29QX1fLU8NXj1N/U5NTk1ObU29Tk1O/U2tQA1frU29T21AfV"
        "8NTy1BDV/dQT1eDUEtXk1ObU4dTj1ObU5NQ51XzV69QT1uDU9dTo1BvV3tTi1OTU3NTe1ODU4dTb1C/mctXl2ujUsNXx1Dni"
        "5tQV1ePU4tQz3eDUyeKd1zjX6OXl1O3U4dTW4+HUMdXe1GXdJdX41P/URdbg58/s2dUZ1+TU7tTe1OHUItWB/1zVFNXi1UjW"
        "ptr/1CfV69Q91eLU49Tf1ODUrNXa1NvU3eGG5Arz4dQA1ejU39Tc1PnU4tQN1QTV4NQ11uzU6NTl1OzUmNfh1ofWINWa1S/b"
        "3dQ44UnXG9U11UrV5tQj15bX4tTa1OjU7tQI1RLV7NT21OPU7NTu1OTU69Tr1NzUQtgR3Gfb7dSr3OjU8dR21t/UMeDo1O3U"
        "5dTn1OLV39Tm1OvU99Tv1Gbc59TD1+3iGQfy1OPU8OES3OPU39T91O3Uk9Xv1OvU4tTq1NvU59Rf1dzUEtUj1k3V3NTj1ODU"
        "4dTm1F7Zq+De1F3VudUU1eTU3tTl1ePU5tTN1RTVMtX51NzU5NQA1RfV49To1EnVdNXg1N/U59Qj1enU59Tr1OvUBdXd1O/U"
        "4tTg1OLU5NTl1N7U5NQW1bPV49TN1ebU7NRF1eTU39Tm1ezU8NTm1AvV4dTk1OrU89Tk1OPUM+aD8vbcNtne1N3U8dTh1NvU"
        "39QQ3vnUO+Pm1DHVZNzy1OrU79T41JrWofHx5jfg5NQd1erU3NQJ1ePUANWi1Vnig9+T3R7cgt4B1QLfbt/n1CbpYtX51CPa"
        "+dRw4eDUw9an1enUadfy1PHUCdXw1LXtxuk56STk2tb51MPm9tT45fHU4tTy1OnUUdVf1eLU79Tr1Bjj7tRo1ejUP9Xn1Dzd"
        "cd0a6DfeKNaA1SDV6tT01C7d3dTd1OvU49Sd2+na39Tk1OTU39Te1O7U4dTh1O3U/NTo1PnU4NT31OjU/dTn1O3U29QS1eHU"
        "5dT+1BbVA9UT1eTUBNXh1OLU8tQB1e7U4NTm1N7U3tTk1OTU4tTe1ODU5dTf1NvU3tTm1OfU3dTm1ODU9NTn1BTV4dQH1ejU"
        "59T01OTUBNXl1N/U5tTj1OHU5tTn1OXU89Tj1OPU6tQI1ebUDNUE1eLU8tTq1OjU/NTw1ODUC9X21BTV5dQi1QzfcfBu3U3n"
        "x9ot1fHU6Nn11ODU5NTp1OjU3NTh1N/UJNYX1ffU39Tw1BTfh+fd1PTU9tTr1DvV4tTP1eLU79Tn1Ljr1uVJ5Obp9uXr9AHX"
        "4NQ41dDV5dTo1H3i49Tg1ODU4dTg1CbfK9Ug2urUq9Xe1BDd5NTo1IfX6NTz1NzUDdbz1ALV+9Xp1Nrw6tS63u/U6tTk1N3V"
        "+NRl1XDVKNUo1UTX6dTx1H7V3NTf1P3U5NTX45rY0uSr1bbW4dUn1kDYNtfk1HvV79Rs1e/U5tTe1ODUAdX11ALV5tTz1OjU"
        "39QF1d/U3dTl1APV4tT51DbX6dTl1OnU7NQr2C/iPNUj1aDW4NTe1cbjEtXv1OnU4tTl1OfU5tTj1D/m59T61e7U/NQs1fPU"
        "8tTl1OfU6tTt1OrUjuH61OPUC9Xp1OnU6tSP1/DU69Tm1HjV9tTq1OfU+NT11PPU69Tm1OrU4NTf1ADV4dSy4urV8tQE2enU"
        "4tRU1x3WYdoK1YT3YOi0FuXU39QS7VLX6+Qf1ebU6NSN4IvVoN1h1iXWsuNO1lLljd3X3VfVTdb+3rnV5tS91jPc7tTm1OfU"
        "9NRn1d/U5dRb1fHUMdb81PvUD+KJ2uTU49Tp1JjZot3U2xXV7tTK3jPg4dTo1C/V5dTf1AbV/dTk1L7Y8tRQ1+DUA9UI3wTV"
        "5dTh1N3U4tQM1Q3VFdUN1ULVOtzo29DZ5NTh1ODU7dTy1O3U"
    )
    # ── DATA END ──
    return (
        CE_B64,
        C_B64,
        C_SCALES,
        HDR_B64,
        QUESTIONS,
        Q_B64,
        Q_SCALES,
        SECTIONS,
        WINDOWS,
        WIN_B64,
        WIN_SIZES,
    )


@app.cell
def _(
    CE_B64,
    C_B64,
    C_SCALES,
    HDR_B64,
    QUESTIONS,
    Q_B64,
    Q_SCALES,
    SECTIONS,
    WIN_B64,
    WIN_SIZES,
    base64,
    np,
):
    # 攤平手冊：單位（unit）＝章節標題行或一句；子塊＝一句；父塊＝一整節
    UNITS, CHILDREN, CHILD_UNIT, CHILD_SEC, SEC_UNITS = [], [], [], [], []
    for _s, (_title, _sents) in enumerate(SECTIONS):
        _ids = [len(UNITS)]
        UNITS.append(f"【{_title}】")
        for _t in _sents:
            CHILD_UNIT.append(len(UNITS))
            CHILD_SEC.append(_s)
            CHILDREN.append(_t)
            _ids.append(len(UNITS))
            UNITS.append(_t)
        SEC_UNITS.append(_ids)
    TITLES = [_t for _t, _ in SECTIONS]
    Q_TEXT = [_q for _q, _, _ in QUESTIONS]
    Q_TYPE = [_ty for _, _ty, _ in QUESTIONS]
    Q_GOLD = [_g for _, _, _g in QUESTIONS]

    def _i8(b64, scales, n):
        _v = np.frombuffer(base64.b64decode(b64), dtype=np.int8).reshape(n, -1)
        _v = _v.astype(np.float32) * np.array(scales, dtype=np.float32)[:, None]
        return _v / np.linalg.norm(_v, axis=1, keepdims=True)

    def _i16(b64, n, scale):
        return np.frombuffer(base64.b64decode(b64), dtype=np.int16).reshape(n, -1).astype(np.float64) / scale

    # 向量檢索的相似度＝問題向量 · 子塊向量（都已單位化，所以內積就是 cosine）——現場算
    DENSE = _i8(Q_B64, Q_SCALES, len(Q_TEXT)) @ _i8(C_B64, C_SCALES, len(CHILDREN)).T
    HDR = _i16(HDR_B64, len(Q_TEXT), 10000)
    WIN_SIM = {_w: _i16(WIN_B64[_w], len(Q_TEXT), 10000) for _w in WIN_SIZES}
    CE = _i16(CE_B64, len(Q_TEXT), 1000)
    return (
        CE,
        CHILDREN,
        CHILD_SEC,
        CHILD_UNIT,
        DENSE,
        HDR,
        Q_GOLD,
        Q_TEXT,
        Q_TYPE,
        SEC_UNITS,
        TITLES,
        UNITS,
        WIN_SIM,
    )


@app.cell
def _(CHILD_SEC, CHILD_UNIT, Q_GOLD, Q_TYPE, SEC_UNITS, UNITS, WINDOWS, np, re):
    # ── 本課全部的檢索零件（跟實測 spike 同一份邏輯）──
    _TOKEN_RE = re.compile(r"[a-z0-9]+(?:[-.][a-z0-9]+)*|[一-鿿]+")
    TYPES = [("proc", "步驟題"), ("pin", "單點題"), ("kw", "型號／故障碼"), ("para", "換句話說")]
    TYPE_NAME = dict(TYPES)

    def tokenize(text):
        """BM25 的切詞：英數整詞（e07、wf-12）＋中文字元 bigram（Lucene CJK 的切法）。"""
        _toks = []
        for _m in _TOKEN_RE.findall(text.lower()):
            if "一" <= _m[0] <= "鿿":
                _toks += [_m] if len(_m) == 1 else [_m[_i : _i + 2] for _i in range(len(_m) - 1)]
            else:
                _toks.append(_m)
        return _toks

    def bm25_fit(docs, k1=1.5, b=0.75):
        _dt = [tokenize(_d) for _d in docs]
        _vocab = {_t: _i for _i, _t in enumerate(sorted({_t for _d in _dt for _t in _d}))}
        _tf = np.zeros((len(docs), len(_vocab)), dtype=np.float32)
        for _i, _d in enumerate(_dt):
            for _t in _d:
                _tf[_i, _vocab[_t]] += 1
        _dl = _tf.sum(1)
        _df = (_tf > 0).sum(0)
        _idf = np.log(1 + (len(docs) - _df + 0.5) / (_df + 0.5))
        _w = _tf / (_tf + k1 * (1 - b + b * _dl[:, None] / _dl.mean()))
        return _vocab, _w, _idf

    def bm25_query(model, query):
        _vocab, _w, _idf = model
        _ids = [_vocab[_t] for _t in tokenize(query) if _t in _vocab]
        if not _ids:
            return np.zeros(_w.shape[0], dtype=np.float32)
        return (_w[:, _ids] * _idf[_ids]).sum(1).astype(np.float32)

    def dense_lists(sim):
        return [[int(_i) for _i in np.argsort(-_row, kind="stable")] for _row in sim]

    def bm25_lists(bm):
        """BM25 只列出「至少命中一個詞」的文件——分數 0 的不算被檢索到。"""
        return [[int(_i) for _i in np.argsort(-_row, kind="stable") if _row[_i] > 0] for _row in bm]

    def rrf_lists(a, b, k=60, wa=1.0, wb=1.0):
        """Reciprocal Rank Fusion：score(d) = Σ w / (k + 名次)；沒出現在某張清單就不拿那一份。"""
        _out = []
        for _la, _lb in zip(a, b):
            _sc = {}
            for _w, _lst in ((wa, _la), (wb, _lb)):
                for _r, _d in enumerate(_lst, 1):
                    _sc[_d] = _sc.get(_d, 0.0) + _w / (k + _r)
            _out.append(sorted(_sc, key=lambda _d, _s=_sc: -_s[_d]))
        return _out

    def rerank_lists(lists, ce, n):
        """第一階段的前 n 名交給 cross-encoder 重排，其餘照原順序接在後面。"""
        return [sorted(_l[:n], key=lambda _d, _q=_qi: -ce[_q][_d]) + _l[n:] for _qi, _l in enumerate(lists)]

    def list_metrics(lists, k=3):
        _rows = []
        for _qi, _lst in enumerate(lists):
            _g = set(Q_GOLD[_qi])
            _r = next((_n for _n, _i in enumerate(_lst, 1) if _i in _g), None)
            _rows.append({"hit1": int(bool(_lst) and _lst[0] in _g), "reck": len(_g & set(_lst[:k])) / len(_g),
                          "mrr": 1.0 / _r if _r else 0.0, "rank": _r})
        return _rows

    def score(lists, k=3):
        """依題型彙總：第一名就對幾題、recall@k、MRR。"""
        _rows = list_metrics(lists, k)
        _out = {}
        for _t in ["proc", "pin", "kw", "para", "all"]:
            _sel = [_r for _r, _qt in zip(_rows, Q_TYPE) if _t == "all" or _qt == _t]
            _out[_t] = {"n": len(_sel), "hit1": sum(_r["hit1"] for _r in _sel),
                        "reck": float(np.mean([_r["reck"] for _r in _sel])),
                        "mrr": float(np.mean([_r["mrr"] for _r in _sel]))}
        return _out, _rows

    def context_units(kind, lst, k, win_size=None):
        """塞進 prompt 的單位：child＝前 k 句；parent＝前 k 句所在的整節（去重）；win＝前 k 個固定大小切塊。"""
        if kind == "child":
            return {CHILD_UNIT[_i] for _i in lst[:k]}
        if kind == "parent":
            return {_u for _i in lst[:k] for _u in SEC_UNITS[CHILD_SEC[_i]]}
        return {_u for _i in lst[:k] for _u in WINDOWS[win_size][_i]}

    def coverage(kind, lists, k, win_size=None):
        """每題：標準答案句有幾成進了 prompt、是否全部進去、prompt 幾個字。"""
        _rows = []
        for _qi, _lst in enumerate(lists):
            _u = context_units(kind, _lst, k, win_size)
            _g = [CHILD_UNIT[_c] for _c in Q_GOLD[_qi]]
            _c = sum(_x in _u for _x in _g) / len(_g)
            _rows.append({"cov": _c, "full": int(_c == 1.0), "chars": sum(len(UNITS[_x]) for _x in _u)})
        _proc = [_r["full"] for _r, _t in zip(_rows, Q_TYPE) if _t == "proc"]
        _single = [_r["full"] for _r, _t in zip(_rows, Q_TYPE) if _t != "proc"]
        return {"proc_full": sum(_proc), "n_proc": len(_proc), "single": sum(_single), "n_single": len(_single),
                "chars": float(np.mean([_r["chars"] for _r in _rows])), "rows": _rows}

    return (
        TYPES,
        TYPE_NAME,
        bm25_fit,
        bm25_lists,
        bm25_query,
        coverage,
        dense_lists,
        rerank_lists,
        rrf_lists,
        score,
        tokenize,
    )


@app.cell
def _(CHILDREN, DENSE, HDR, Q_TEXT, bm25_fit, bm25_lists, bm25_query, dense_lists, np):
    # 三張「第一階段」清單：向量、向量（子塊加章節標題）、BM25
    BM25_MODEL = bm25_fit(CHILDREN)
    BM25 = np.stack([bm25_query(BM25_MODEL, _q) for _q in Q_TEXT])
    L_DENSE = dense_lists(DENSE)
    L_HDR = dense_lists(HDR)
    L_BM25 = bm25_lists(BM25)
    return BM25_MODEL, L_BM25, L_DENSE, L_HDR


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 1️⃣ 考卷：41 題，每題都有標準答案

    每一招進階手法都有代價，所以動手前先出考卷。41 題分四型，每題標好「答案在手冊哪幾句」：

    - **步驟題**（8 題）：答案橫跨同一節好幾句，例如「除垢的完整步驟」——少一句就是錯的操作
    - **單點題**（8 題）：答案就一句，例如「單份濃縮放幾公克粉」
    - **型號／故障碼**（15 題）：問題裡有 `E07`、`WF-21` 這種代碼，差一個字就是另一回事
    - **換句話說**（10 題）：使用者的用詞跟手冊不一樣，例如「摔到地上」vs 手冊的「摔落」

    打分用三個指標：**第一名就對**（hit@1：排第一的那句就是標準答案）、
    **recall@3**（標準答案句有幾成進了前 3 名）、**MRR**（第一個對的排第 r 名就得 1/r 分，再平均）。
    選一型，看天真版——只用向量、一句一塊——把每題的答案排在第幾名：
    """
    )
    return


@app.cell
def _(TYPES, mo):
    q_filter = mo.ui.dropdown(
        options={"全部 41 題": "all", **{f"{_n}": _t for _t, _n in TYPES}},
        value="全部 41 題",
        label="看哪一型",
    )
    q_filter
    return (q_filter,)


@app.cell
def _(CHILDREN, L_DENSE, Q_GOLD, Q_TEXT, Q_TYPE, TYPES, TYPE_NAME, mo, q_filter, score):
    _sc, _rows = score(L_DENSE)
    _lines = []
    for _qi, _q in enumerate(Q_TEXT):
        if q_filter.value not in ("all", Q_TYPE[_qi]):
            continue
        _r = _rows[_qi]["rank"]
        _mark = "✅ 第 1 名" if _r == 1 else f"⚠️ 第 {_r} 名"
        _gold = "／".join(CHILDREN[_g][:18] + "…" for _g in Q_GOLD[_qi])
        _lines.append(f"| {_q} | {TYPE_NAME[Q_TYPE[_qi]]} | {_gold} | {_mark} |")
    _table = "\n    ".join(_lines)
    _sum = "\n    ".join(
        f"| {_n} | {_sc[_t]['hit1']}/{_sc[_t]['n']} | {_sc[_t]['reck']:.2f} | {_sc[_t]['mrr']:.2f} |"
        for _t, _n in TYPES + [("all", "**全部**")]
    )
    mo.md(
        f"""
    | 問題 | 題型 | 標準答案句 | 向量檢索把它排第幾 |
    | --- | --- | --- | --- |
    {_table}

    **天真版（向量、一句一塊）的成績單：**

    | 題型 | 第一名就對 | recall@3 | MRR |
    | --- | --- | --- | --- |
    {_sum}

    看起來不差——但「第一名就對」不等於「答案完整」：步驟題的答案有好幾句，
    排第一的那句對了，其他步驟可能根本沒進 prompt。這就是 2️⃣ 要處理的事。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 2️⃣ 父子檢索：用小塊找、用大塊給

    切塊的兩難：**切小**（一句一塊），向量很「尖」、找得準，但步驟題只撈到零碎幾句；
    **切大**（幾百字一塊），步驟湊齊了，但一塊裡混了好幾個主題，向量被稀釋、單點題反而找不準，
    prompt 還一路變胖。**父子檢索**（parent-child／small-to-big）拆開兩件事：
    用**子塊**（一句）去比對，找到之後把它所在的**父塊**（整節）交給模型。

    拉「取前幾名」，比較五種固定大小的切法和父子檢索（★）：
    """
    )
    return


@app.cell
def _(mo):
    pc_k = mo.ui.slider(start=1, stop=5, step=1, value=3, label="取前幾名（top-k）", show_value=True)
    pc_k
    return (pc_k,)


@app.cell
def _(L_DENSE, WIN_SIM, WIN_SIZES, coverage, dense_lists, np, pc_k, plt):
    _k = pc_k.value
    _res = [coverage("child", L_DENSE, _k)] + [
        coverage("win", dense_lists(WIN_SIM[_w]), _k, _w) for _w in WIN_SIZES
    ]
    _pc = coverage("parent", L_DENSE, _k)
    _labels = ["1 sentence"] + [f"{_w} chars" for _w in WIN_SIZES]
    _x = np.arange(len(_labels))
    _xp = len(_labels) + 0.5
    _proc = [_r["proc_full"] / _r["n_proc"] for _r in _res]
    _single = [_r["single"] / _r["n_single"] for _r in _res]
    _fig, (_a1, _a2) = plt.subplots(
        2, 1, figsize=(6.4, 5.6), sharex=True, gridspec_kw={"height_ratios": [3, 2]}
    )
    _a1.plot(_x, _proc, "o-", color="#4C72B0", lw=2, label="multi-step Qs: every step in prompt")
    _a1.plot(_x, _single, "s-", color="#DD8452", lw=2, label="other Qs: answer fully in prompt")
    _a1.scatter([_xp - 0.12], [_pc["proc_full"] / _pc["n_proc"]], marker="*", s=260, color="#4C72B0", zorder=5,
                edgecolor="#1C2B33")
    _a1.scatter([_xp + 0.12], [_pc["single"] / _pc["n_single"]], marker="*", s=260, color="#DD8452", zorder=5,
                edgecolor="#1C2B33")
    _a1.axvline(len(_labels) - 0.25, color="#8A9AA3", ls=":", lw=1)
    _a1.set_ylim(0, 1.08)
    _a1.set_ylabel("share of questions")
    _a1.set_title(f"The chunking dilemma (top-{_k})  -  stars = parent-child")
    _a1.legend(loc="lower right", fontsize=8)
    _a1.grid(alpha=0.3)
    _a2.bar(_x, [_r["chars"] for _r in _res], color="#C9D2D8", edgecolor="#1C2B33")
    _a2.bar([_xp], [_pc["chars"]], color="#55A868", edgecolor="#1C2B33")
    _a2.set_ylabel("avg prompt chars")
    _a2.set_xticks(list(_x) + [_xp])
    _a2.set_xticklabels(_labels + ["parent-\nchild"], fontsize=8)
    _a2.grid(axis="y", alpha=0.3)
    _fig.tight_layout()
    _fig
    return


@app.cell
def _(L_DENSE, WIN_SIM, WIN_SIZES, coverage, dense_lists, mo, pc_k):
    _k = pc_k.value
    _named = [("一句一塊（子塊）", coverage("child", L_DENSE, _k))]
    _named += [(f"固定 {_w} 字", coverage("win", dense_lists(WIN_SIM[_w]), _k, _w)) for _w in WIN_SIZES]
    _named += [("**★ 父子檢索**", coverage("parent", L_DENSE, _k))]
    _rows = "\n    ".join(
        f"| {_n} | {_r['proc_full']}/{_r['n_proc']} | {_r['single']}/{_r['n_single']} | "
        f"{_r['chars']:.0f} 字（≈{_r['chars'] * 1.14:.0f} tokens） |"
        for _n, _r in _named
    )
    mo.md(
        f"""
    **top-{_k} 的實際數字**（步驟題 8 題；其他 33 題的答案只有一兩句）：

    | 切法 | 步驟題：步驟全進 prompt | 其他題：答案全進 prompt | prompt 平均長度 |
    | --- | --- | --- | --- |
    {_rows}

    固定大小的切法只能在「湊齊步驟」和「prompt 變胖、其他題找不準」之間二選一；
    父子檢索用一句一塊去找（找得準），交出去的是整節（步驟齊）。
    token 粗估：中文 1 字 ≈ 1.14 token（主線第 1 課實測的刀工）。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 3️⃣ 混合搜尋：向量＋BM25，用 RRF 融合

    向量檢索懂「意思」，但對 `E07` 這種代碼很鈍——它覺得 `E07` 跟 `E17` 長得差不多。
    **BM25** 是老派的關鍵字檢索：數「問題裡的詞在這句出現幾次、這個詞在全手冊有多稀有」，
    `e07` 只出現在一句裡，所以一命中就排第一。中文沒有空格，這裡用**字元 bigram** 切詞
    （「除垢燈」→「除垢」「垢燈」），英數代碼整個當一個詞。

    兩張排名怎麼合？**RRF（Reciprocal Rank Fusion）**：每張清單的第 r 名得 `w/(k+r)` 分，加總再排。
    只看名次、不看原始分數——因為 cosine 落在 0–1、BM25 可以到十幾，直接相加會被 BM25 綁架。
    拉 BM25 的權重，看哪些題型變好、哪些變差：
    """
    )
    return


@app.cell
def _(mo):
    hy_w = mo.ui.slider(start=0.0, stop=1.0, step=0.05, value=1.0, label="BM25 權重 w（向量固定 1）", show_value=True)
    hy_k = mo.ui.slider(start=1, stop=100, step=1, value=60, label="RRF 的 k", show_value=True)
    mo.hstack([hy_w, hy_k], wrap=True, justify="start", gap=2)
    return hy_k, hy_w


@app.cell
def _(L_BM25, L_DENSE, hy_k, hy_w, rrf_lists):
    L_HYBRID = rrf_lists(L_DENSE, L_BM25, k=hy_k.value, wb=hy_w.value)
    return (L_HYBRID,)


@app.cell
def _(L_BM25, L_DENSE, L_HYBRID, TYPES, np, plt, score):
    _names = ["dense (vector)", "BM25 (keyword)", "hybrid (RRF)"]
    _colors = ["#4C72B0", "#DD8452", "#8172B2"]
    _scores = [score(_l)[0] for _l in (L_DENSE, L_BM25, L_HYBRID)]
    _cats = [_t for _t, _ in TYPES] + ["all"]
    _xt = ["multi-step", "single-fact", "code / part no.", "paraphrase", "ALL 41"]
    _x = np.arange(len(_cats))
    _fig, _ax = plt.subplots(figsize=(6.4, 3.8))
    for _j, (_n, _c, _s) in enumerate(zip(_names, _colors, _scores)):
        _v = [_s[_t]["hit1"] / _s[_t]["n"] for _t in _cats]
        _ax.bar(_x + (_j - 1) * 0.27, _v, width=0.27, color=_c, edgecolor="#1C2B33", label=_n, zorder=3)
    _ax.set_xticks(_x)
    _ax.set_xticklabels(_xt, fontsize=9)
    _ax.set_ylim(0, 1.12)
    _ax.set_ylabel("hit@1 (share of questions)")
    _ax.set_title("Which retriever puts the right sentence first?")
    _ax.legend(fontsize=8, ncol=3, loc="upper center")
    _ax.grid(axis="y", alpha=0.3)
    _fig.tight_layout()
    _fig
    return


@app.cell
def _(L_BM25, L_DENSE, L_HYBRID, Q_TEXT, Q_TYPE, TYPE_NAME, hy_k, hy_w, mo, score):
    _sd, _rd = score(L_DENSE)
    _sb, _rb = score(L_BM25)
    _sh, _rh = score(L_HYBRID)

    def _fmt(r):
        return "—（沒命中任何詞）" if r is None else f"第 {r} 名"

    _chg = []
    for _qi, _q in enumerate(Q_TEXT):
        _a, _b = _rd[_qi]["rank"], _rh[_qi]["rank"]
        if (_a == 1) != (_b == 1):
            _tag = "🟢 救回來" if _b == 1 else "🔴 被拖下水"
            _chg.append(f"| {_tag} | {_q} | {TYPE_NAME[Q_TYPE[_qi]]} | {_fmt(_a)} | {_fmt(_rb[_qi]['rank'])} | {_fmt(_b)} |")
    _tbl = "\n    ".join(_chg) if _chg else "| — | 這組設定跟純向量的第一名完全一樣 | | | | |"
    mo.md(
        f"""
    **目前設定（w={hy_w.value:.2f}、k={hy_k.value}）**：第一名就對——
    向量 {_sd['all']['hit1']}/41、BM25 {_sb['all']['hit1']}/41、**混合 {_sh['all']['hit1']}/41**
    （型號題 {_sd['kw']['hit1']} → {_sh['kw']['hit1']}／15，換句話說 {_sd['para']['hit1']} → {_sh['para']['hit1']}／10）。

    跟純向量比，「第一名對不對」有變的題目：

    | 變化 | 問題 | 題型 | 向量 | BM25 | 混合 |
    | --- | --- | --- | --- | --- | --- |
    {_tbl}

    BM25 對換句話說題幾乎是瞎的——「摔到地上」跟手冊的「摔落」bigram 一個都對不上，
    它只撈得到剛好共用「可以」這種虛詞的句子；權重給太大，它就把向量原本排對的題目拖下水。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    **BM25 試打區**——BM25 不需要任何模型，所以任何字都能現場查。試試 `E07`、`E17`、`GS-54`，
    再試一句換句話說（例如「摔到地上」），看它什麼時候準、什麼時候交白卷：
    """
    )
    return


@app.cell
def _(mo):
    bm_q = mo.ui.text(value="螢幕顯示 E07 怎麼辦？", label="查詢", full_width=True)
    bm_q
    return (bm_q,)


@app.cell
def _(BM25_MODEL, CHILDREN, bm25_query, bm_q, html_mod, mo, np, tokenize):
    _toks = tokenize(bm_q.value)
    _s = bm25_query(BM25_MODEL, bm_q.value)
    _order = [int(_i) for _i in np.argsort(-_s, kind="stable")[:5] if _s[_i] > 0]
    _vocab = BM25_MODEL[0]
    _hit = [_t for _t in _toks if _t in _vocab]
    _items = "".join(
        f'<li style="margin:4px 0"><b style="font-family:monospace">{_s[_i]:.2f}</b>　{html_mod.escape(CHILDREN[_i])}</li>'
        for _i in _order
    ) or '<li style="color:#C44E52">一句都沒命中——BM25 在這題交白卷（向量檢索還是會給你「最像的」幾句）</li>'
    mo.Html(
        '<div style="font-size:13.5px;line-height:1.7">'
        f'<div>切出來的詞：<span style="font-family:monospace">{html_mod.escape(" · ".join(_toks)) or "（空）"}</span></div>'
        f'<div>在手冊裡出現過的：<span style="font-family:monospace;color:#DD8452">{html_mod.escape(" · ".join(_hit)) or "（沒有）"}</span></div>'
        f'<ol style="margin:6px 0 0 18px;padding:0">{_items}</ol></div>'
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 4️⃣ Rerank：讓 cross-encoder 把前 N 名重排

    前面的向量檢索是 **bi-encoder**：問題、句子**各自**變成向量再比，所以句子的向量可以事先算好存起來，
    查詢時只算一次問題向量——快，但兩邊從頭到尾沒「見過面」。
    **cross-encoder** 把「問題＋一句」**一起**讀進模型、直接輸出相關度——準得多，
    但每一對都要跑一次模型，沒辦法事先算。所以標準做法是兩段式：
    第一階段（向量或混合）撈前 N 名，cross-encoder 只重排這 N 個。

    本機實測（bge-reranker-v2-m3、CPU 14 執行緒）：**約 45 ms 一對**，重排 20 個候選 ≈ 0.9 秒。
    拉 N，看分數和代價怎麼變：
    """
    )
    return


@app.cell
def _(mo):
    rr_first = mo.ui.dropdown(
        options={"向量（dense）": "dense", "混合（沿用 3️⃣ 的設定）": "hybrid"},
        value="向量（dense）",
        label="第一階段",
    )
    rr_n = mo.ui.slider(start=1, stop=40, step=1, value=20, label="交給 reranker 的候選數 N", show_value=True)
    mo.hstack([rr_first, rr_n], wrap=True, justify="start", gap=2)
    return rr_first, rr_n


@app.cell
def _(CE, L_DENSE, L_HYBRID, np, plt, rerank_lists, rr_n, score):
    _ns = list(range(1, 41))
    _fig, _ax = plt.subplots(figsize=(6.4, 3.8))
    for _l, _name, _c in ((L_DENSE, "dense -> rerank", "#4C72B0"), (L_HYBRID, "hybrid -> rerank", "#8172B2")):
        _base = score(_l)[0]["all"]["hit1"]
        _curve = [score(rerank_lists(_l, CE, _n))[0]["all"]["hit1"] for _n in _ns]
        _ax.plot(_ns, _curve, "-", color=_c, lw=2, label=_name)
        _ax.axhline(_base, color=_c, ls="--", lw=1, alpha=0.7)
    _ax.axvline(rr_n.value, color="#2A7F8E", lw=1.5, ls=":")
    _ax.text(rr_n.value + 0.5, 27.3, f"N={rr_n.value}", color="#2A7F8E", fontsize=9)
    _ax.set_xlabel("N = candidates handed to the cross-encoder")
    _ax.set_ylabel("hit@1 (out of 41)")
    _ax.set_ylim(27, 41)
    _ax.set_yticks(np.arange(28, 42, 2))
    _ax.set_title("Rerank: dashed = before rerank, solid = after")
    _ax.legend(fontsize=8, loc="lower right")
    _ax.grid(alpha=0.3)
    _fig.tight_layout()
    _fig
    return


@app.cell
def _(CE, CHILDREN, L_DENSE, L_HYBRID, Q_TEXT, np, rerank_lists, rr_first, rr_n, mo, score):
    _base = L_DENSE if rr_first.value == "dense" else L_HYBRID
    _after = rerank_lists(_base, CE, rr_n.value)
    _s0, _r0 = score(_base)
    _s1, _r1 = score(_after)

    def _p(x):
        return 1 / (1 + np.exp(-x))

    _chg = []
    for _qi, _q in enumerate(Q_TEXT):
        _a, _b = _r0[_qi]["rank"], _r1[_qi]["rank"]
        if (_a == 1) != (_b == 1):
            _tag = "🟢 救回來" if _b == 1 else "🔴 排錯了"
            _top = _after[_qi][0]
            _chg.append(
                f"| {_tag} | {_q} | 第 {_a} 名 → 第 {_b} 名 | {CHILDREN[_top][:16]}…（{_p(CE[_qi][_top]):.2f}） |"
            )
    _tbl = "\n    ".join(_chg) if _chg else "| — | 沒有任何一題的第一名改變 | | |"
    mo.md(
        f"""
    **{'向量' if rr_first.value == 'dense' else '混合'} → rerank（N={rr_n.value}）**：
    第一名就對 {_s0['all']['hit1']} → **{_s1['all']['hit1']}**／41，MRR {_s0['all']['mrr']:.3f} → {_s1['all']['mrr']:.3f}；
    型號題 {_s0['kw']['hit1']} → {_s1['kw']['hit1']}／15，換句話說 {_s0['para']['hit1']} → {_s1['para']['hit1']}／10。
    這一步在 CPU 上約多花 **{rr_n.value * 45 / 1000:.1f} 秒**／每次查詢（N × 45 ms，本機實測）。

    | 變化 | 問題 | 標準答案名次 | rerank 後的第一名（相關度） |
    | --- | --- | --- | --- |
    {_tbl}

    reranker 不是神：它也會把原本排對的題目排錯（🔴），而且**只能重排第一階段撈到的 N 個**——
    正確答案不在前 N 名，它就無能為力。
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 5️⃣ 組你自己的管線

    三招可以疊起來用。每個開關都會用同一份考卷重新打分，跟「天真版」（向量、一句一塊、同樣的 k）並排比較。
    多一個開關：**子塊加章節標題**——算向量前把「除垢｜」這種章節名貼在每句前面
    （Anthropic 叫它 contextual retrieval 的最簡版），讓「最後裝回濾水芯」這種句子知道自己在講除垢。
    """
    )
    return


@app.cell
def _(mo):
    pl_ret = mo.ui.dropdown(
        options={"向量（dense）": "dense", "BM25": "bm25", "混合（沿用 3️⃣ 的權重）": "hybrid"},
        value="向量（dense）",
        label="第一階段檢索",
    )
    pl_hdr = mo.ui.switch(value=False, label="子塊加章節標題")
    pl_rr = mo.ui.switch(value=False, label="Rerank")
    pl_n = mo.ui.slider(start=1, stop=40, step=1, value=20, label="rerank 候選數 N", show_value=True)
    pl_ctx = mo.ui.dropdown(
        options={"一句一塊（子塊）": "child", "父子（展開成整節）": "parent"},
        value="一句一塊（子塊）",
        label="交給模型的是",
    )
    pl_k = mo.ui.slider(start=1, stop=5, step=1, value=3, label="取前幾名 k", show_value=True)
    mo.vstack(
        [
            mo.hstack([pl_ret, pl_hdr], wrap=True, justify="start", gap=2),
            mo.hstack([pl_rr, pl_n], wrap=True, justify="start", gap=2),
            mo.hstack([pl_ctx, pl_k], wrap=True, justify="start", gap=2),
        ]
    )
    return pl_ctx, pl_hdr, pl_k, pl_n, pl_ret, pl_rr


@app.cell
def _(CE, L_BM25, L_DENSE, L_HDR, hy_k, hy_w, pl_hdr, pl_n, pl_ret, pl_rr, rerank_lists, rrf_lists):
    _d = L_HDR if pl_hdr.value else L_DENSE
    _base = {"dense": _d, "bm25": L_BM25, "hybrid": rrf_lists(_d, L_BM25, k=hy_k.value, wb=hy_w.value)}[pl_ret.value]
    L_MINE = rerank_lists(_base, CE, pl_n.value) if pl_rr.value else _base
    return (L_MINE,)


@app.cell
def _(L_DENSE, L_MINE, TYPES, coverage, np, pl_ctx, pl_k, plt, Q_TYPE):
    _k = pl_k.value
    _base = coverage("child", L_DENSE, _k)["rows"]
    _mine = coverage(pl_ctx.value, L_MINE, _k)["rows"]
    _cats = [_t for _t, _ in TYPES] + ["all"]
    _xt = ["multi-step", "single-fact", "code / part no.", "paraphrase", "ALL 41"]

    def _rate(rows, t):
        _sel = [_r["full"] for _r, _qt in zip(rows, Q_TYPE) if t == "all" or _qt == t]
        return sum(_sel) / len(_sel)

    _x = np.arange(len(_cats))
    _fig, _ax = plt.subplots(figsize=(6.4, 3.8))
    _ax.bar(_x - 0.2, [_rate(_base, _t) for _t in _cats], width=0.4, color="#C9D2D8", edgecolor="#1C2B33",
            label="naive: dense, 1 sentence per chunk", zorder=3)
    _ax.bar(_x + 0.2, [_rate(_mine, _t) for _t in _cats], width=0.4, color="#55A868", edgecolor="#1C2B33",
            label="your pipeline", zorder=3)
    _ax.set_xticks(_x)
    _ax.set_xticklabels(_xt, fontsize=9)
    _ax.set_ylim(0, 1.15)
    _ax.set_ylabel("answer fully in prompt")
    _ax.set_title(f"Did every needed sentence reach the model? (top-{_k})")
    _ax.legend(fontsize=8, loc="upper center", ncol=2)
    _ax.grid(axis="y", alpha=0.3)
    _fig.tight_layout()
    _fig
    return


@app.cell
def _(L_DENSE, L_MINE, coverage, mo, pl_ctx, pl_k, score):
    _k = pl_k.value
    _s0, _ = score(L_DENSE, _k)
    _s1, _ = score(L_MINE, _k)
    _c0 = coverage("child", L_DENSE, _k)
    _c1 = coverage(pl_ctx.value, L_MINE, _k)
    mo.md(
        f"""
    | 指標（top-{_k}） | 天真版 | **你的管線** |
    | --- | --- | --- |
    | 第一名就對（41 題） | {_s0['all']['hit1']} | **{_s1['all']['hit1']}** |
    | recall@{_k} | {_s0['all']['reck']:.2f} | **{_s1['all']['reck']:.2f}** |
    | MRR | {_s0['all']['mrr']:.3f} | **{_s1['all']['mrr']:.3f}** |
    | 步驟題：步驟全進 prompt（8 題） | {_c0['proc_full']} | **{_c1['proc_full']}** |
    | 其他題：答案全進 prompt（33 題） | {_c0['single']} | **{_c1['single']}** |
    | prompt 平均長度 | {_c0['chars']:.0f} 字 | **{_c1['chars']:.0f} 字** |

    前三列看**排序**（跟交給模型的是子塊還是父塊無關），後三列看**模型實際拿到什麼**。
    挑一題，看你的管線把什麼送進 prompt：
    """
    )
    return


@app.cell
def _(Q_TEXT, mo):
    pl_q = mo.ui.dropdown(options=Q_TEXT, value=Q_TEXT[0], label="逐題檢視")
    pl_q
    return (pl_q,)


@app.cell
def _(CHILDREN, CHILD_SEC, CHILD_UNIT, L_MINE, Q_GOLD, Q_TEXT, SEC_UNITS, TITLES, UNITS, html_mod, mo, pl_ctx, pl_k, pl_q):
    _qi = Q_TEXT.index(pl_q.value)
    _lst = L_MINE[_qi][: pl_k.value]
    _gold = set(Q_GOLD[_qi])
    _gold_units = {CHILD_UNIT[_g] for _g in _gold}

    def _li(text, ok):
        _c = "#2E7042" if ok else "#1C2B33"
        _bg = "#E4F2E7" if ok else "transparent"
        return (f'<li style="margin:3px 0;padding:2px 6px;border-radius:6px;background:{_bg};color:{_c}">'
                f'{"✅ " if ok else ""}{html_mod.escape(text)}</li>')

    if pl_ctx.value == "child":
        _body = "".join(_li(CHILDREN[_i], _i in _gold) for _i in _lst)
    else:
        _secs = []
        for _i in _lst:
            if CHILD_SEC[_i] not in _secs:
                _secs.append(CHILD_SEC[_i])
        _body = "".join(
            f'<li style="margin:6px 0"><b>【{html_mod.escape(TITLES[_s])}】</b><ul style="margin:2px 0 0 14px;padding:0">'
            + "".join(_li(UNITS[_u], _u in _gold_units) for _u in SEC_UNITS[_s][1:])
            + "</ul></li>"
            for _s in _secs
        )
    _got = sum(1 for _g in _gold if (_g in _lst) or (pl_ctx.value == "parent" and CHILD_SEC[_g] in {CHILD_SEC[_i] for _i in _lst}))
    mo.Html(
        '<div style="font-size:13.5px;line-height:1.7;border:2px solid #C9D2D8;border-radius:12px;padding:10px 14px">'
        f'<div style="font-weight:800;margin-bottom:4px">送進 prompt 的內容（標準答案句 {_got}/{len(_gold)} 句在裡面，綠色）</div>'
        f'<ol style="margin:0 0 0 18px;padding:0">{_body}</ol></div>'
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## 6️⃣ 換你動手

    挑戰題在教學頁的「換你動手」，全部用上面的拉桿和開關就做得到。做完再打開解答對照：
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.accordion(
        {
            "💡 LEVEL 1 參考解答（2️⃣ 把 k 拉到 1）": mo.md(
                r"""
    k=1 時，「其他題：答案全進 prompt」一句一塊是 **25/33**，固定 150 與 300 字都掉到 **18/33**，
    600 字回到 23/33，父子檢索最高 **28/33**。

    為什麼切大塊反而找不準：一塊 300 字裡可能同時講除垢、清潔、耗材——它的向量是這些主題的「平均」，
    跟任何一個具體問題都只有中等相似度；一句一塊的向量只講一件事，對上了就很尖。
    父子檢索的分數用的就是一句一塊的向量，所以它繼承了「找得準」；交出去的卻是整節，所以步驟也齊
    （k=1 時步驟題 5/8 全進——排第一的那句剛好在正確的那一節，就整節帶走）。
    """
            ),
            "💡 LEVEL 2 參考解答（3️⃣ 找 BM25 權重）": mo.md(
                r"""
    把 w 從 1 往下拉：w=1.00 時型號題 15/15、換句話說只剩 5/10，全部 33/41；
    **w=0.25～0.30** 是「型號題還保得住 15/15」的最低權重，這時換句話說回到 7/10，全部 **35/41**——
    跟純向量（35/41）**一樣多**，只是錯的題目不同：型號題全對了，換句話說題錯了 3 題。

    這就是這份手冊的真相：**單靠混合搜尋，並沒有比純向量好**，只是把錯誤從一型搬到另一型。
    混合真正的價值在第一階段「撈得全」——它要配 4️⃣ 的 reranker 才完整。
    （別的語料結果會不同：代碼越多、越像，BM25 的權重越值得給高。這正是要有考卷的原因。）
    """
            ),
            "💡 LEVEL 3 參考解答（5️⃣ 組出最好的管線）": mo.md(
                r"""
    目標：第一名就對 ≥ 38/41、步驟題 8/8 全進、其他題 ≥ 31/33、prompt 越短越好。

    一組做得到的設定：**向量 → Rerank N=3 → 父子 → k=2**：38/41、8/8、31/33，平均約 **242 字**。
    再打開「子塊加章節標題」、N 改 5：38/41、8/8、**32/33**，約 **237 字**——這是實測格點搜尋裡
    符合條件、字數最少的一組（全部組合的搜尋在本課 spike 裡）。

    怎麼確認自己做對了：表格的「第一名就對」≥ 38、步驟題欄是 8、其他題 ≥ 31。
    注意 N 拉大（20、40）反而掉到 37——候選越多，reranker 越有機會把干擾句排上來。
    （天真版 k=3 是 35/41、步驟題只有 **1/8** 全進、94 字；多花約 150 字，換來每一題步驟都完整。）
    """
            ),
        }
    )
    return


if __name__ == "__main__":
    app.run()
