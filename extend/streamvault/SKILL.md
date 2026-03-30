---
name: streamvault
description: "视频图文解析与下载工具，连接自建解析服务器，支持抖音、B站、快手、小红书、微博、YouTube等全平台。支持视频和图文（图集）内容。当用户涉及以下意图时触发：(1)解析/下载/保存/提取/获取视频或图文：下载视频、下载图片、解析视频、保存图片、提取视频、获取视频、获取图文、帮我下载、抓取视频、下载图集、保存图文、拿一下这个视频/图片、这个图集好看、帮我存一下图；(2)粘贴或提到链接/口令：用户直接发送http(s)链接、抖音口令($xxx$)、B站BV号、分享文本；(3)提到平台名+内容：抖音视频/抖音图文、B站视频、快手视频/快手图文、小红书图文/小红书笔记、微博图片/微博视频、这个抖音链接、帮我看看这个链接；(4)查询视频列表/搜索：查看视频列表、看看有哪些视频、我的视频、视频库、搜索视频、找一下视频；（注意：query 仅支持视频，图文提交后请直接在服务器查看）(5)获取封面/预览：封面、缩略图、视频封面；(6)视频相关配置：视频配置、服务器地址；(7)平台热门/热搜/推荐：B站热门、抖音热门、微博热搜、快手热门、小红书热门、热门视频、热搜榜、现在最火的视频、推荐视频、有什么好看的、热搜视频、帮我看看有什么好玩的、最近什么视频火、看看抖音/B站/微博/小红书/快手。"
metadata: {"clawdbot":{"emoji":"🎬","requires":{"bins":["python3"],"pip":["requests"]}}}
---

# StreamVault - 视频图文解析与下载

连接自建解析服务器，支持**视频和图文（图集）**内容。**所有操作通过 `scripts/video_client.py` 一行命令完成，不要写临时文件。**

## 配置

查看：`python {skill_dir}/scripts/video_client.py config`

更新：`python {skill_dir}/scripts/video_client.py config --set-ip IP:PORT --set-token TOKEN`

配置文件优先级：`scripts/config.json` > 代码中 `DEFAULT_CONFIG`

---

## 命令速查

### submit — 提交视频/图文解析

```bash
python {skill_dir}/scripts/video_client.py submit "链接或口令"
python {skill_dir}/scripts/video_client.py submit "BV1RYXQBKEEd"
```

支持：http(s)完整链接、BV号（自动转 `https://www.bilibili.com/video/BVxxx`）、av号、抖音口令。
适用：视频链接、图文/图集链接、笔记链接，解析服务器会自动识别内容类型。

**submit 行为：提交成功即结束，告知用户"已提交成功，请稍后在服务器查看"。不要主动 query 检查结果。**

### query — 查询/搜索视频列表（仅视频）

```bash
python {skill_dir}/scripts/video_client.py query
python {skill_dir}/scripts/video_client.py query -p 2 -s 20
python {skill_dir}/scripts/video_client.py query -n "关键词"
python {skill_dir}/scripts/video_client.py query --platform "抖音"
```

`-p` 页码(从1开始) `-s` 每页数 `-n` 名称 `--platform` 平台 `-d` 描述。可组合。
查询结果自动缓存，video/cover/info 通过序号引用。

**注意：query 仅支持已解析的视频内容，图文提交后请直接在服务器查看，不支持通过此接口查询。**

### video / cover / info — 获取URL/封面/详情

```bash
python {skill_dir}/scripts/video_client.py video 3
python {skill_dir}/scripts/video_client.py cover 3
python {skill_dir}/scripts/video_client.py info 3
```

### parse — 提取/规范化链接

```bash
python {skill_dir}/scripts/video_client.py parse "BV1RYXQBKEEd"
# 输出: https://www.bilibili.com/video/BV1RYXQBKEEd
```

### trending — 各平台热门视频

```bash
# B站热门（默认，返回可直接提交的视频URL）
python {skill_dir}/scripts/video_client.py trending
python {skill_dir}/scripts/video_client.py trending bilibili --submit 3
python {skill_dir}/scripts/video_client.py trending bilibili --submit-all

# 抖音热搜（返回热搜话题词，不是视频链接）
python {skill_dir}/scripts/video_client.py trending douyin

# 微博热搜（返回热搜话题词，不是视频链接）
python {skill_dir}/scripts/video_client.py trending weibo

# B站分区
python {skill_dir}/scripts/video_client.py trending bilibili --rid 4
```

---

## 热门内容工作流（重要）

### B站：直接获取视频链接

B站有公开 API，`trending bilibili` 返回的每条都是真实视频URL，可直接 `--submit N` 提交。

### 抖音/微博/小红书：视频+图文都支持

这些平台同时有视频和图文内容。AI 在用 web_fetch 提取链接时，**视频和图文链接都可以 submit**，解析服务器会自动识别内容类型。

### 抖音/微博：返回的是热搜话题，不是视频链接

`trending douyin/weibo` 返回热搜词，标记为 `[话题]`，**不能直接 submit**。

正确流程：
1. `trending douyin` 展示热搜列表
2. 用户选择某个话题
3. **AI 用 web_fetch 访问对应的搜索页 URL**（列表中已给出），从页面中提取实际视频或图文链接
4. `submit "提取到的完整URL"`

### 小红书/快手：无公开 API，完全依赖 web_fetch

1. **AI 用 web_fetch 直接访问**：
   - 小红书热门：`https://www.xiaohongshu.com/explore`
   - 快手热门：`https://www.kuaishou.com/hot`
2. 从返回内容中提取视频/图文标题和链接
3. `submit "完整URL"`

---

## 完整工作流

```
用户给链接/BV号 → submit "链接" (自动规范化) → "已提交成功，请稍后在服务器查看" → 结束
    ↓
用户要列表/搜索 → query → 格式化展示
    ↓
用户要视频/封面/详情 → video/cover/info 序号 → 返回URL → 结束
    ↓
用户要看热门(B站) → trending bilibili --submit N → "已提交" → 结束
    ↓
用户要看热门(抖音/微博) → trending → 用户选话题 → web_fetch → 提取链接 → submit → 结束
    ↓
用户要看热门(小红书/快手) → web_fetch → 提取链接 → submit → 结束
```

## 注意事项

1. 不要写临时文件，所有操作直接执行命令
2. submit 成功后即结束，告知用户"已提交成功，请稍后在服务器查看"，**不要主动 query 检查**
3. submit 会自动将 BV号/av号 转为完整URL，抖音口令原样传入
4. 抖音/微博 trending 返回热搜词，必须用 web_fetch 获取实际链接后才能 submit
5. video/cover/info 依赖最近一次 query 的缓存
6. 分页从 1 开始
7. **图文内容只支持 submit 提交，不支持 query 查询，提交后直接在服务器查看**
