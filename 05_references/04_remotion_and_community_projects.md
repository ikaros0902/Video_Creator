# Remotion 與社群開源相關專案分析（`05_references/04_remotion_and_community_projects.md`）

除了上述三個核心專案外，GitHub 上結合 **Remotion** 與 **HyperFrames** 做 AI 自動化剪片的開源生態系已相當成熟。以下彙整官方指南與指標性社群專案的特色，說明哪些做法值得參考、哪些已經被 `Video_Creator` 超越或吸收。

## 1. 官方指南：`remotion-dev/skills`

- **核心內容**：Remotion 官方維護的 Agent Skill 集合，規範 `useCurrentFrame()`、`spring()` 物理阻尼、`interpolate(..., { extrapolateRight: "clamp" })`、`<OffthreadVideo>` 與字體載入規範（禁止 `CSS animation` 或 `setTimeout`，避免多人併發渲染時畫面閃爍不同步）。
- **對應本專案**：`remotion/src/Main.tsx` 已全面使用 `<OffthreadVideo>`、`spring()` 與 `extrapolateRight: "clamp"`，我們並將規範精煉至 [`03_skills/04_remotion_master/SKILL.md`](../03_skills/04_remotion_master/SKILL.md)。
- **硬體加速實踐**：`vc/render.py` 已接入 Remotion 官方推薦的 `--gl=angle --hardware-acceleration=if-possible` 旗標，並搭配兩次嘗試自動回退 CPU 機制防禦企業 VPN / 顯卡瞬斷。

## 2. 社群精選專案分析與可借鏡設計

| 專案名稱 | 技術組合 | 值得參考的亮點 | 相對本專案的優劣評估 |
| :--- | :--- | :--- | :--- |
| **`haidrrrry/claude-remotion-skill`** | Claude Code + Remotion | 強調「非線性緩動曲線（Bezier / Spring）」、「元件錯落進場（Staggered reveals）」、「動態漸層網格背景（Gradient Mesh）」與靜態圖片的 Ken Burns 微推拉運鏡 | 極適合拿來強化純簡報轉影片的動感；本專案的 `cameraTransform` (`dolly_in` / `dolly_out`) 已對螢幕錄影提供類似且錨定標註框中心的推鏡邏輯 |
| **`addsumtech/topic-to-video`** | Prompt / 投影片 + TTS + Remotion | 提供極簡的「主題關鍵字 / 簡報 → 旁白 → Remotion MP4」端到端範例，適合研究如何快速從文件草擬初版腳本 | 缺少 `facts.yaml` 事實追溯與 `public/internal` 雙軌脫敏檢查；適合把它的「主題展開 Prompt」用在 BMAD Phase 1 前期靈感發想 |
| **`geekjourneyx/hyperframes-motion-director`** | 多階段分鏡設計 Agent + HyperFrames | 把「README / 技術文章 → 9:16 產品宣傳短片」拆成多階段 Proposal：先出視覺節奏提案、使用者確認後才產生 GSAP 程式碼 | 其「多階段動畫規格書」思路很契合我們的 BMAD 流程，未來若需產出直式社群短影音（Shorts / Reels）可直接參考其 9:16 版型配置 |
| **`bestagentkits/motion-video-skill`** | HTML/GSAP + TTS + 逐字卡拉 OK 字幕 + FFmpeg | 在純網頁動畫內做輕量化字詞高亮（Karaoke word highlight）並靠 FFmpeg 合流 | 實作輕巧不需 Node Remotion 專案；但若場景穿插高解析度軟體操作錄影與複雜自動標註框，仍以本專案的 Remotion 總裝架構更穩定 |
| **`yt-hyperframes-agent`** | 口播去氣口剪輯 + LLM 自動配 B-roll | 利用自動剪除空白氣口（類比本專案安裝的 `auto-editor`）再由 LLM 為各段落自動配對 HyperFrames B-roll 插入畫面 | 與本專案工具鏈高度互補：我們目前已經裝妥 `auto-editor 29.3.1`，未來做真人錄製口播課時可直接用這個模式剪掉結巴空拍後交給 `vc align` |

## 3. 總結：未來擴充建議優先序

1. **短影音版（9:16）範本擴充**：參考 `geekjourneyx/hyperframes-motion-director`，在 `vc/hf_scenes.py` 與 `remotion/` 支援 `meta.size = [1080, 1920]` 的直式安全距版型。
2. **真人口播自動剪氣口整合**：把已安裝的 `auto-editor` 接成可選前處理子指令（例如 `vc trim-silence`），專門處理真人螢幕教學兼顧口播的原始錄影。
3. **漸層網格與錯落字卡動效**：持續把 `haidrrrry/claude-remotion-skill` 與 `lemo-opuscar` 的視覺元素沉澱進 `04_styles/` 與 `vc/hf_scenes.py`。
