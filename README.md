# 國營試煉 Online V0.2 — iPhone 多人共用地圖驗收包

## 內容
- `index.html`：手機 Safari 直接玩的像素地圖與答題介面（必須經網站伺服器提供，不是點開本機 HTML）
- `server.py`：aiohttp 同時提供網頁與 WebSocket 連線、房間、位置同步、伺服器判題與共享 Boss 血量
- `render.yaml`：Render 免費 Web Service 部署設定
- `requirements.txt`：Python 依賴

這是**供 iPhone 驗證的 HTML5 連線客戶端**，不是 Godot 原生 iOS App，也沒有把先前 Godot 專案直接匯出成 iOS。保留先前 Godot 專案作為未來原生客戶端基礎，之後需改接同一份 WebSocket 協定。

## 零成本部署（手機 Safari）
1. 將此資料夾的四個檔案上傳到 GitHub 新 repository 的根目錄（可以用 GitHub 手機網頁介面；如上傳 ZIP，需先解壓縮，不能只上傳 ZIP）。
2. 前往 https://dashboard.render.com/ ，使用 GitHub 登入。
3. New → Web Service → 選擇該 repository。
4. Runtime 選 Python、Instance Type 選 Free，Build Command `pip install -r requirements.txt`，Start Command `python server.py`。
5. Deploy 後取得 `https://...onrender.com` 網址。先開啟 `/health` 應看到 `{"ok":true,...}`。
6. 兩支手機分別在 Safari 開啟**同一網址**，輸入不同暱稱及相同房間代碼，點「進入新手村」。
7. 玩家 A 移動方向鍵，玩家 B 應即時看到角色移動。兩人分別答題，共同減少 Boss HP。

注意：免費 Render 服務可能休眠、首次喚醒延遲，並有用量與服務限制；不適合正式商用。此原型資料都在伺服器記憶體，重啟後清空；沒有帳號、永久存檔或反作弊完整防護。請勿公開大量邀請玩家。

## 本機開發（有電腦時）
```
pip install -r requirements.txt
python server.py
```
開啟 `http://localhost:8080`，兩個瀏覽器分頁可做基本同步測試。

## 訊息協定
Client → Server: `join {name,room}`, `move {dx,dy}`, `question`, `answer {choice}`。
Server → Client: `joined`, `state {players,boss,round,log}`, `question {text,options}`, `result {correct,explanation,xp}`, `error`。

## 驗收條件
- 兩支不同手機同房間，互相看得到玩家
- 一支手機移動，另一支同步更新
- 玩家 A 答對，玩家 B 看到 Boss 血量減少 100
- 兩人合計答對 6 次，Boss 進入下一輪
- 任一手機關閉網頁，另一支的在線人數與角色同步更新

## 已知限制
目前使用簡單色塊像素風、無地圖碰撞完整驗證、無永久帳號與角色存檔；連線同步以小規模測試為主。手機網頁版本不是正式原生 App。正式 MMORPG 必須增加帳號驗證、資料庫、伺服器分區、訊息限速、題庫管理與部署監控。
