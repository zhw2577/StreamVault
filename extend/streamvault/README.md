# StreamVault - 视频图文解析与下载 CLI

连接自建 StreamVault 解析服务器，支持**视频和图文（图集）**内容的解析与下载。

支持平台：抖音、B站、快手、小红书、微博、YouTube 等全平台。

## 安装依赖

```bash
pip install requests
```

## 快速开始

### 1. 配置服务器地址

```bash
# 查看/更新配置
python scripts/video_client.py config

# 设置服务器地址和 Token
python scripts/video_client.py config --set-ip 127.0.0.1:28082 --set-token YOUR_TOKEN
```

配置文件优先级：`scripts/config.json` > 代码中的默认值。其中 `token` 和 `app_token` 均为读写全局 Token，需替换为你服务器的实际值。

### 2. 提交视频/图文解析

```bash
# 直接提交链接
python scripts/video_client.py submit "https://www.bilibili.com/video/BV1RYXQBKEEd"

# 提交 BV 号（自动转换为完整 URL）
python scripts/video_client.py submit "BV1RYXQBKEEd"

# 提交抖音口令
python scripts/video_client.py submit "$abc123$"
```

提交成功后，请稍后在服务器查看解析结果。

### 3. 查询已解析的视频列表

```bash
# 查看第一页
python scripts/video_client.py query

# 指定页码和每页数量
python scripts/video_client.py query -p 2 -s 20

# 按名称搜索
python scripts/video_client.py query -n "关键词"

# 按平台筛选
python scripts/video_client.py query --platform "抖音"
```

### 4. 获取视频详情

```bash
# 根据列表序号获取视频下载地址
python scripts/video_client.py video 3

# 获取封面
python scripts/video_client.py cover 3

# 获取完整信息
python scripts/video_client.py info 3
```

### 5. 查看平台热门

```bash
# B站热门（返回可直接提交的视频链接）
python scripts/video_client.py trending
python scripts/video_client.py trending bilibili --submit 3    # 直接提交第 3 个
python scripts/video_client.py trending bilibili --submit-all  # 提交全部

# 抖音热搜（返回热搜话题词，需进一步获取视频链接）
python scripts/video_client.py trending douyin

# 微博热搜
python scripts/video_client.py trending weibo

# B站指定分区
python scripts/video_client.py trending bilibili --rid 4
```

### 6. 链接解析与规范化

```bash
python scripts/video_client.py parse "BV1RYXQBKEEd"
# 输出: https://www.bilibili.com/video/BV1RYXQBKEEd
```

## 命令参考

| 命令 | 说明 |
|------|------|
| `submit <链接>` | 提交视频/图文解析 |
| `query` | 查询视频列表（支持 `-p` 页码、`-s` 每页数、`-n` 名称、`--platform` 平台、`-d` 描述） |
| `video <序号>` | 获取视频下载地址（依赖最近一次 query） |
| `cover <序号>` | 获取封面地址 |
| `info <序号>` | 获取视频详情 |
| `trending [平台]` | 查看热门（bilibili/douyin/weibo，支持 `--submit N` 和 `--submit-all`） |
| `parse <文本>` | 提取/规范化链接 |
| `config` | 查看/更新服务器配置 |

