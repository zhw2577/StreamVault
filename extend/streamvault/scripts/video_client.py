#!/usr/bin/env python3
"""StreamVault CLI - 视频解析、查询、获取、热门，一行命令搞定。"""

import argparse
import json
import re
import sys
import urllib.parse
from pathlib import Path

try:
    import requests
except ImportError:
    print("请先安装 requests: pip install requests")
    sys.exit(1)

CONFIG_FILE = Path(__file__).parent / "config.json"
CACHE_FILE = Path(__file__).parent / ".last_query.json"

DEFAULT_CONFIG = {
    "server_ip": "127.0.0.1",
    "server_port": "28082",
    "token": "your_token_here",
    "app_token": "your_app_token_here",
}

MOBILE_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"


# ── 配置 ──

def load_config() -> dict:
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return DEFAULT_CONFIG.copy()


def save_config(config: dict):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def get_server_url() -> str:
    c = load_config()
    return f"http://{c['server_ip']}:{c['server_port']}"


def get_full_url(relative_path: str) -> str:
    c = load_config()
    base = get_server_url()
    if relative_path.startswith("/app/"):
        path = relative_path[5:]
    else:
        path = relative_path.lstrip("/")
    return f"{base}/{path}?apptoken={c.get('app_token', c['token'])}"


# ── 链接识别与规范化 ──

def parse_video_link(text: str):
    """从文本中提取视频链接或口令，返回链接或 None"""
    url = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', text)
    if url:
        return url[0]
    m = re.search(r'[\$€€]([A-Za-z0-9]+)[\$€€]', text)
    if m:
        return m.group(0)
    m = re.search(r'/19\s+[A-Za-z0-9]+', text)
    if m:
        return m.group(0)
    m = re.search(r'(BV[a-zA-Z0-9]{10}|av\d+|bv[a-zA-Z0-9]{10})', text, re.IGNORECASE)
    if m:
        return f"https://www.bilibili.com/video/{m.group(0)}"
    return None


def normalize_link(raw: str) -> str:
    """将短ID/口令等转为完整URL，已经是完整URL则原样返回"""
    if not raw:
        return raw
    # 已经是完整链接
    if raw.startswith("http://") or raw.startswith("https://"):
        return raw
    # 抖音口令
    if re.match(r'^[\$€€].+[\$€€]$', raw):
        return raw
    if re.match(r'^/19\s+', raw):
        return raw
    # B站 BV/av 号
    m = re.match(r'^(BV[a-zA-Z0-9]{10}|bv[a-zA-Z0-9]{10}|av\d+)$', raw, re.IGNORECASE)
    if m:
        return f"https://www.bilibili.com/video/{m.group(1).upper()}"
    # 无法识别，原样返回
    return raw


# ── 缓存 ──

def save_cache(data: dict):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


def load_cache() -> dict | None:
    if CACHE_FILE.exists():
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


# ── 解析服务器 API ──

def api_submit(video_link: str) -> dict:
    c = load_config()
    r = requests.post(f"{get_server_url()}/api/processingVideos",
                      data={"token": c["token"], "video": video_link}, timeout=30)
    return {"success": r.status_code == 200,
            "message": "已提交解析，稍后查询列表" if r.status_code == 200 else f"请求失败: {r.status_code}"}


def api_query(page=1, size=10, name=None, platform=None, desc=None) -> dict:
    c = load_config()
    payload = {"token": c["token"], "pageNo": page, "pageSize": size, "videoprivacy": 0}
    if name:
        payload["videoname"] = name
    if platform:
        payload["videoplatform"] = platform
    if desc:
        payload["videodesc"] = desc
    r = requests.post(f"{get_server_url()}/api/findVideos", data=payload, timeout=30)
    if r.status_code != 200:
        return {"success": False, "message": f"请求失败: {r.status_code}",
                "record": {"content": [], "page": {}}}
    return r.json()


# ── 多平台热门 ──
# 返回: [{title, author, url, play, desc, cover, duration, type}, ...]
# type: "video" = 可直接提交的视频URL, "topic" = 搜索/话题页，需用web_fetch进一步获取

def fetch_bilibili_trending(size=20, **kw):
    rid = kw.get("rid", 0)
    try:
        r = requests.get("https://api.bilibili.com/x/web-interface/popular",
                         params={"ps": size, "pn": 1, "rid": rid if rid else None},
                         headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        items = r.json().get("data", {}).get("list", [])
        result = []
        for it in items:
            stat = it.get("stat", {})
            result.append({
                "title": it.get("title", "").replace("<em class=\"keyword\">", "").replace("</em>", ""),
                "author": it.get("owner", {}).get("name", "未知"),
                "url": f"https://www.bilibili.com/video/{it.get('bvid', '')}",
                "cover": it.get("pic", ""),
                "play": stat.get("view", 0),
                "desc": it.get("desc", ""),
                "duration": it.get("duration", ""),
                "type": "video",
            })
        return result
    except Exception:
        return []


def fetch_douyin_trending(size=20, **kw):
    try:
        r = requests.get("https://www.douyin.com/hot",
                         headers={"User-Agent": MOBILE_UA, "Referer": "https://www.douyin.com/"},
                         timeout=15, allow_redirects=True)
        match = re.search(r'<script\s+id="RENDER_DATA"\s+type="application/json">(.+?)</script>', r.text)
        if not match:
            return []
        raw = urllib.parse.unquote(match.group(1))
        data = json.loads(raw)
        for key in data:
            item_list = None
            section = data[key]
            if isinstance(section, dict):
                for sub_key, sub_val in section.items():
                    if isinstance(sub_val, list):
                        for entry in sub_val:
                            if isinstance(entry, dict) and (entry.get("word") or entry.get("aweme_info")):
                                item_list = sub_val
                                break
                    if item_list:
                        break
            if item_list:
                result = []
                for it in item_list[:size]:
                    word = it.get("word", "")
                    result.append({
                        "title": word,
                        "author": it.get("event_time", ""),
                        "url": f"https://www.douyin.com/search/{urllib.parse.quote(word)}",
                        "cover": "",
                        "play": it.get("hot_value", 0),
                        "desc": "",
                        "duration": "",
                        "type": "topic",
                    })
                return result
        return []
    except Exception:
        return []


def fetch_weibo_trending(size=20, **kw):
    try:
        r = requests.get("https://weibo.com/ajax/side/hotSearch",
                         headers={"User-Agent": MOBILE_UA}, timeout=15)
        items = r.json().get("data", {}).get("realtime", [])
        result = []
        for it in items[:size]:
            word = it.get("word", "")
            result.append({
                "title": word,
                "author": "微博热搜",
                "url": f"https://s.weibo.com/weibo?q=%23{urllib.parse.quote(word)}%23",
                "cover": "",
                "play": it.get("num", 0),
                "desc": it.get("label_name", ""),
                "duration": "",
                "type": "topic",
            })
        return result
    except Exception:
        return []


PLATFORM_FETCHERS = {
    "bilibili": fetch_bilibili_trending, "b站": fetch_bilibili_trending, "bili": fetch_bilibili_trending,
    "douyin": fetch_douyin_trending, "抖音": fetch_douyin_trending,
    "weibo": fetch_weibo_trending, "微博": fetch_weibo_trending,
}

PLATFORM_NAMES = {
    "bilibili": "B站", "b站": "B站", "bili": "B站",
    "douyin": "抖音", "抖音": "抖音",
    "weibo": "微博", "微博": "微博",
}


def fetch_trending(platform="bilibili", size=20, **kw):
    fetcher = PLATFORM_FETCHERS.get(platform.lower())
    if not fetcher:
        return [], f"不支持的平台: {platform}，可选: {', '.join(sorted(set(PLATFORM_NAMES.values())))}（小红书/快手需用 web_fetch）"
    return fetcher(size=size, **kw), ""


def format_number(n):
    if n is None:
        return "0"
    if isinstance(n, str):
        n = int(n)
    if n >= 100000000:
        return f"{n/100000000:.1f}亿"
    elif n >= 10000:
        return f"{n/10000:.1f}万"
    return str(n)


def format_trending(platform, items):
    name = PLATFORM_NAMES.get(platform, platform)
    if not items:
        return f"[{name}] 未获取到数据"
    has_topic = any(it.get("type") == "topic" for it in items)
    lines = [f"[{name}热门]\n"]
    for i, it in enumerate(items, 1):
        tag = " [话题]" if it.get("type") == "topic" else ""
        lines.append(f"[{i}]{tag} {it.get('title', '无标题')}")
        meta = []
        if it.get("author"):
            meta.append(f"UP: {it['author']}")
        if it.get("play"):
            meta.append(f"热度: {format_number(it['play'])}")
        if it.get("duration"):
            meta.append(f"时长: {it['duration']}")
        if meta:
            lines.append(f"    {'  |  '.join(meta)}")
        if it.get("desc"):
            lines.append(f"    {it['desc'][:70]}")
        lines.append("")
    if has_topic:
        lines.append("标记 [话题] 的为热搜词，需用 web_fetch 浏览搜索页获取视频链接后再提交。")
    return "\n".join(lines)


# ── 输出格式化 ──

def format_list(data: dict) -> str:
    videos = data.get("record", {}).get("content", [])
    if not videos:
        return "暂无视频"
    lines = []
    for i, v in enumerate(videos, 1):
        name = v.get("videoname", "未命名")[:40]
        author = v.get("videoauthor", "未知")
        plat = v.get("videoplatform", "未知")
        desc = v.get("videodesc", "")[:60]
        lines.append(f"[{i}] {name}  |  {author}  |  {plat}")
        if desc:
            lines.append(f"    {desc}")
    page = data.get("record", {}).get("page", {})
    total = page.get("totalElements", "?")
    pages = page.get("totalPages", "?")
    lines.append(f"\n共 {total} 条，第 {data.get('record', {}).get('page', {}).get('number', '?')} 页 / 共 {pages} 页")
    return "\n".join(lines)


# ── CLI 命令 ──

def cmd_submit(args):
    link = args.link
    if not link:
        text = sys.stdin.read().strip()
        if text:
            link = parse_video_link(text)
    if not link:
        print(json.dumps({"success": False, "message": "未提供链接，也无法从输入中识别"}, ensure_ascii=False))
        return
    link = normalize_link(link)
    result = api_submit(link)
    print(json.dumps(result, ensure_ascii=False))


def cmd_query(args):
    data = api_query(page=args.page, size=args.size,
                     name=args.name, platform=args.platform, desc=args.desc)
    save_cache(data)
    print(format_list(data))


def cmd_video(args):
    cache = load_cache()
    if not cache:
        print("错误：请先执行 query 查询视频列表")
        return
    videos = cache.get("record", {}).get("content", [])
    idx = args.index - 1
    if idx < 0 or idx >= len(videos):
        print(f"错误：索引超出范围（共 {len(videos)} 条）")
        return
    addr = videos[idx].get("videoaddr", "")
    if not addr:
        print("错误：该视频无地址")
        return
    print(get_full_url(addr))


def cmd_cover(args):
    cache = load_cache()
    if not cache:
        print("错误：请先执行 query 查询视频列表")
        return
    videos = cache.get("record", {}).get("content", [])
    idx = args.index - 1
    if idx < 0 or idx >= len(videos):
        print(f"错误：索引超出范围（共 {len(videos)} 条）")
        return
    cover = videos[idx].get("videocover", "")
    if not cover:
        print("错误：该视频无封面")
        return
    print(get_full_url(cover))


def cmd_info(args):
    cache = load_cache()
    if not cache:
        print("错误：请先执行 query 查询视频列表")
        return
    videos = cache.get("record", {}).get("content", [])
    idx = args.index - 1
    if idx < 0 or idx >= len(videos):
        print(f"错误：索引超出范围（共 {len(videos)} 条）")
        return
    v = videos[idx]
    lines = [
        f"名称: {v.get('videoname', '未知')}",
        f"作者: {v.get('videoauthor', '未知')}",
        f"平台: {v.get('videoplatform', '未知')}",
        f"描述: {v.get('videodesc', '')}",
        f"时间: {v.get('createtime', '未知')}",
    ]
    if v.get("videoaddr"):
        lines.append(f"视频: {get_full_url(v['videoaddr'])}")
    if v.get("videocover"):
        lines.append(f"封面: {get_full_url(v['videocover'])}")
    print("\n".join(lines))


def cmd_parse(args):
    link = normalize_link(args.text)
    print(link if link else "未识别到视频链接")


def cmd_trending(args):
    platform = args.platform or "bilibili"
    items, err = fetch_trending(platform=platform, size=args.size, rid=args.rid)
    if err:
        print(err)
        return
    if not items:
        name = PLATFORM_NAMES.get(platform, platform)
        print(f"[{name}] 未获取到数据，请检查网络或稍后重试")
        return

    print(format_trending(platform, items))

    # --submit: 只能提交 type=video 的条目
    if args.submit:
        idx = args.submit - 1
        if 0 <= idx < len(items):
            it = items[idx]
            if it.get("type") == "topic":
                print(f"\n[{args.submit}] 是热搜话题，不是视频链接。请用 web_fetch 访问 {it['url']} 获取具体视频链接后再提交。")
            else:
                result = api_submit(it["url"])
                print(f"\n已提交 [{args.submit}] {it['title']} -> {result.get('message', '')}")
        else:
            print(f"\n错误：序号超出范围（共 {len(items)} 条）")

    if args.submit_all:
        videos = [it for it in items if it.get("type") == "video"]
        topics = [it for it in items if it.get("type") == "topic"]
        for it in videos:
            result = api_submit(it["url"])
            print(f"提交 {it['title'][:30]}... -> {result.get('message', '')}")
        if topics:
            print(f"\n跳过 {len(topics)} 条热搜话题（需用 web_fetch 获取视频链接）")


def cmd_config(args):
    c = load_config()
    if args.set_ip:
        if ":" in args.set_ip:
            ip, port = args.set_ip.split(":", 1)
            c["server_ip"] = ip
            c["server_port"] = port
        else:
            c["server_ip"] = args.set_ip
    if args.set_token:
        c["token"] = args.set_token
    if args.set_apptoken:
        c["app_token"] = args.set_apptoken
    if args.set_ip or args.set_token or args.set_apptoken:
        save_config(c)
        print(json.dumps({"success": True, "server": f"{c['server_ip']}:{c['server_port']}"}))
    else:
        masked = {k: (v[:4] + "***" if isinstance(v, str) and len(v) > 6 else v) for k, v in c.items()}
        print(json.dumps(masked, indent=2, ensure_ascii=False))


def main():
    p = argparse.ArgumentParser(prog="video_client", description="StreamVault - 视频解析工具")
    sub = p.add_subparsers(dest="cmd")

    sp = sub.add_parser("submit", help="提交视频解析")
    sp.add_argument("link", nargs="?", help="视频链接、BV号或口令")
    sp.set_defaults(func=cmd_submit)

    qp = sub.add_parser("query", help="查询视频列表")
    qp.add_argument("-p", "--page", type=int, default=1)
    qp.add_argument("-s", "--size", type=int, default=10)
    qp.add_argument("-n", "--name")
    qp.add_argument("--platform")
    qp.add_argument("-d", "--desc")
    qp.set_defaults(func=cmd_query)

    vp = sub.add_parser("video", help="获取视频URL")
    vp.add_argument("index", type=int)
    vp.set_defaults(func=cmd_video)

    cp = sub.add_parser("cover", help="获取封面URL")
    cp.add_argument("index", type=int)
    cp.set_defaults(func=cmd_cover)

    ip = sub.add_parser("info", help="获取视频详情")
    ip.add_argument("index", type=int)
    ip.set_defaults(func=cmd_info)

    tp = sub.add_parser("trending", help="查看平台热门视频")
    tp.add_argument("platform", nargs="?", default="bilibili",
                    help="bilibili/b站/douyin/抖音/weibo/微博（小红书/快手用 web_fetch）")
    tp.add_argument("-s", "--size", type=int, default=20)
    tp.add_argument("--rid", type=int, default=0)
    tp.add_argument("--submit", type=int, metavar="N")
    tp.add_argument("--submit-all", action="store_true")
    tp.set_defaults(func=cmd_trending)

    pp = sub.add_parser("parse", help="从文本提取/规范化链接")
    pp.add_argument("text", help="链接、BV号、口令等")
    pp.set_defaults(func=cmd_parse)

    cfg = sub.add_parser("config", help="查看/更新配置")
    cfg.add_argument("--set-ip")
    cfg.add_argument("--set-token")
    cfg.add_argument("--set-apptoken")
    cfg.set_defaults(func=cmd_config)

    args = p.parse_args()
    if args.cmd:
        args.func(args)
    else:
        p.print_help()


if __name__ == "__main__":
    main()
