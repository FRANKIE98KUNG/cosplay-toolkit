# B站会员购详情页抓取参考

## 详情页 URL 规律

- 分享短链：`https://b23.tv/<code>`（302 跳转）
- 跳转目标：`https://mall.bilibili.com/neul-next/ticket-renovation/detail.html?id=<id>...`
- 等价详情页：`https://show.bilibili.com/platform/detail.html?id=<id>`

## 解析短链接（Windows Git Bash）

```bash
curl -sI "https://b23.tv/<code>" -H "User-Agent: Mozilla/5.0" | grep -i location
```

从 `Location:` 里提取 `id=<数字>`。

## 抓详情页

用 WebFetch 抓 `https://show.bilibili.com/platform/detail.html?id=<id>`，要求提取：
- 活动完整名称、副标题/主题
- 时间（起止日期时刻）
- 场馆/地址（含区）
- 票价（各票种+开售时间）
- 参展嘉宾（coser/声优/唱见全名单）
- 活动介绍、入场规则、主办方

## 已踩过的坑

1. `show.bilibili.com/platform/search?keyword=` 返回 404（搜索页不是这个路径）
2. `show.bilibili.com/api/ticket/project/search` / `list` 接口有风控和复杂参数校验（返回"被降级过滤"或参数错误），不要依赖
3. `api.bilibili.com/x/web-interface/search/type?search_type=show` 返回 code=-1200 被降级过滤
4. 首页 `show.bilibili.com/platform/home.html` 是 JS 渲染，curl 拿不到活动数据，但 WebFetch 能拿到部分热门活动卡片

## 结论

拿到短链接 → `curl -sI` 解析 id → WebFetch 详情页，是唯一可靠路径。不要试图用关键词搜索 API 命中 SPA 详情页。
