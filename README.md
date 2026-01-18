# RSS 到 Telegram 推送工具配置指南

本仓库通过 GitHub Actions 实现 RSS 源内容自动推送到 Telegram 群组，以下是详细配置步骤。


## 一、准备工作

1. **创建 Telegram Bot**  
   联系 Telegram 官方机器人 @BotFather，发送指令 `/newbot`，按提示设置机器人名称和用户名（用户名需以 `bot` 或 `Bot` 结尾）。完成后会获得 Bot Token（格式：`123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`），请妥善保存备用。

2. **获取群组 ID**  
   将创建的 Bot 加入目标 Telegram 群组，在群组内发送任意消息，然后将该消息转发给 @getidsbot。@getidsbot 会返回群组 ID（格式：`-1001234567890`），保存备用。

3. **创建 GitHub 个人访问令牌**  
   访问 [个人访问令牌创建地址][2]，选择“生成经典令牌”：  
   - 自定义令牌名称（如 `rss-to-telegram`）；  
   - 有效期建议设置为 90 天；  
   - **必须勾选 `repo` 权限**（用于写入仓库）；  
   创建完成后，令牌（token）只会显示一次，请立即复制并保存。


## 二、设置仓库密钥

步骤：仓库主页 → Settings → Secrets and variables → Actions → 点击右上角「New repository secret」，依次添加以下 4 个密钥：

| 密钥名称         | 说明                          |
|------------------|-------------------------------|
| `TELEGRAM_TOKEN` | 第一步获取的 Telegram Bot Token |
| `CHAT_ID`        | 第二步获取的群组 ID           |
| `RSS_URL`        | 需推送的 RSS 源地址           |
| `MY_GITHUB_TOKEN`| 第三步创建的 GitHub 令牌      |

添加完成后示例：  
[![密钥设置示例](https://img.cdn.vin/dai/20251020/1760968222781.png)](https://img.cdn.vin/dai/20251020/1760968222781.png)


## 三、测试与验证

1. 进入仓库主页 → 点击顶部「Actions」；  
2. 左侧导航栏选择工作流「RSS to Telegram」；  
3. 点击「Run workflow」按钮，在弹出窗口中再次点击「Run workflow」手动触发运行；  
4. 运行后查看目标 Telegram 群组是否收到消息：  
   - 若收到消息，说明配置成功；  
   - 若未收到，可在 Actions 页面进入对应工作流的运行记录，查看报错信息排查问题。

## 四、Bangumi 时间胶囊示例

以用户 asashiki 为例，如果要把 Bangumi 的时间胶囊内容同步到 Telegram，可按下列方式设置：

1. 将 `RSS_URL` 设置为 `https://bangumi.tv/feed/user/<你的 ID>/timeline`，例如 `https://bangumi.tv/feed/user/asashiki/timeline`。
2. 当前脚本会自动读取每条 RSS 项目的 `<description>` 内容，去除 HTML 标签并做 `MarkdownV2` 转义，然后在文本最前面拼接 `主人` 再推送到 Telegram。
3. Bangumi 的 GUID/链接会直接作为帖子唯一 ID，不再需要 `thread-xxx.htm` 之类的过滤逻辑，重复运行也不会再次推送相同记录。

完成配置后，Telegram 群组中会出现类似 `主人听过 XXX` 的文字，内容即为时间胶囊里的描述文本。


## 注意事项
- 当前默认只推送 `<description>` 中的文字，如果希望保留 HTML 超链接，可按需修改 `rss_pusher.py` 中的 `extract_description`。
- 仍可用于 [大佬论坛（www.dalao.net）][3] 的帖子结构（/thread-[tid].htm），若目标站点采用不同的 GUID 规则，可以调整 `extract_post_id` 以获得稳定的唯一 ID。


[2]: https://github.com/settings/tokens
[3]: https://www.dalao.net/
