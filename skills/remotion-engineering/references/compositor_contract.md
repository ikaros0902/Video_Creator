# 合成邊界

Remotion 是最終合成層：讀取 timeline 產生的 props，放入語音、字幕、錄影片段與已渲染的動畫。
HyperFrames 負責字卡與 HTML 動畫；Manim 負責幾何與科學示意。三者共用旁白對齊出的影格時序。

不要在合成層重新估算旁白時間。素材路徑應位於工作區，避免輸出使用另一台機器的磁碟代號。
調整影格率後，必須重新建立時間軸並確認影格數。public 版本不得包含私有錄影或品牌截圖。

參考：[Remotion 官方 Agent Skills](https://github.com/remotion-dev/skills)。官方技能涵蓋合成、動畫、媒體與渲染。本地文件定義本專案的接入邊界。
