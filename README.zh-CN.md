[English](README.md) | **简体中文**

# WarmCard - AI 贺卡生成器

一个基于 Flask 的网页应用，使用 AI（DeepSeek API）生成个性化贺卡。支持多种场合、语气、语言和篇幅。

## 功能

- **12 种场合**：生日、圣诞、新年、情人节、纪念日、毕业、早日康复、感谢、祝贺、道歉、友谊、鼓励
- **5 种语气**：真挚、幽默、正式、诗意、随性
- **3 种语言**：中文、英文、中英混合
- **3 种篇幅**：短、中、长
- 通过 DeepSeek API 生成祝福语
- 响应缓存，提升速度
- 按 IP 限流
- 可分享的贺卡链接
- 使用情况统计

## 环境要求

- Python 3.12+
- DeepSeek API 密钥（或任何兼容 OpenAI 的 API）

## 安装

1. 克隆仓库：
   ```bash
   git clone https://github.com/Kylekk29/WarmCard.git
   cd WarmCard
   ```

2. 创建并激活虚拟环境：
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   source venv/bin/activate  # Linux/Mac
   ```

3. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

4. 创建 `.env` 文件：
   ```env
   AI_API_KEY=your_deepseek_api_key
   AI_MODEL=deepseek-chat
   AI_BASE_URL=https://api.deepseek.com
   ADMIN_KEY=your_admin_key
   ```

5. 运行应用：
   ```bash
   python app.py
   ```

打开 `http://localhost:5000/` 即可制作贺卡。收件人可以打开同一主机上的 `/card/<id>` 分享链接。任何拿到链接的人都可以查看贺卡。

## API 接口

| 方法 | 接口 | 说明 |
|--------|----------|-------------|
| GET | `/api/occasions` | 列出所有场合、语气、语言和篇幅 |
| POST | `/api/kyle-card` | 生成一张贺卡 |
| POST | `/api/share` | 创建可分享的贺卡 |
| GET | `/api/share/<id>` | 获取已分享的贺卡 |
| GET | `/api/health` | 健康检查（含统计） |
| GET | `/api/analytics` | 使用统计（需要管理员密钥） |

### 生成贺卡

```json
POST /api/kyle-card
{
  "name": "Alice",
  "occasion": "birthday",
  "tone": "heartfelt",
  "language": "chinese",
  "length": "medium",
  "sender": "Bob"
}
```

## 部署

可通过 `WARMCARD_LOG_DIR` 指定可写的持久化目录。若 `/home/xmascard/logs/` 已存在，则默认使用该目录，否则使用 `app.py` 旁边的 `logs/`。目录内保存 `shares.json`、统计数据和日志。使用 JSON 存储时，请运行单个应用进程。

运行 `python -m unittest discover -s tests` 可以验证分享流程和 API 行为，无需实际的 DeepSeek 密钥。
