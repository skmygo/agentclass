# 密碼閘收斂：含教學 API key 的課才上鎖

## Why

同日稍早的 topic-order-and-topic-gate 把 llm-apps 整個主題（主題頁＋10 課）都鎖了。
但上鎖的實際目的是不讓硬編在課程裡的教學 virtual key 被路人直接看到——
沒 key 的課（fastmcp4 四堂、mcp-servers）與主題頁本身沒有需要遮的東西，鎖了只是增加學員摩擦。

## What Changes

- 上鎖原則改為**課程層級**：notebook 或教學頁含教學 API key 的課才掛 gate；
  主題頁與無 key 課程移除 gate。
- llm-apps 實際上鎖 5 堂：litellm-basics、litellm-tools、qdrant-basics、rag-zh、rag-mcp-agent
  （掃描確認 mcp-servers 只有 `API_KEY=secret` 文件範例、非真 key）。
- 五堂仍共用 `data-gate="llm-apps"` 群組——輸入一次全通，體驗與整主題鎖相同。
- spec requirement 由「主題密碼閘」改寫為「課程密碼閘」；site.md、NOTES.md 同步。

## Impact

- `content/llm-apps/`：主題頁與 5 個課程頁移除 gate 行；`gate.js` 本身不動
- `openspec/specs/interactive-lesson/spec.md`、make-lesson skill `site.md`、llm-apps `NOTES.md`
