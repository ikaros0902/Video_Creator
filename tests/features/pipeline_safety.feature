Feature: 安全的單一影片管線
  Scenario: 舊專案轉換保留原始內容
    Given 具有雙版本畫面的舊專案
    When 轉換為單一影片
    Then 原始腳本有獨立備份
    And 單一畫面使用原始完整版本

  Scenario: 已存在備份時拒絕轉換
    Given 具有雙版本畫面的舊專案
    And 原始腳本備份已存在
    When 轉換為單一影片
    Then 轉換應失敗且原始腳本不變

  Scenario: 缺少動畫時拒絕輸出
    Given 時間軸需要動畫但檔案不存在
    When 檢查影片素材
    Then 素材檢查應拒絕輸出

  Scenario: 語音內容變更後對齊結果過期
    Given 有效的語音與對齊結果
    When 語音檔案內容變更
    Then 對齊資料應被拒絕
