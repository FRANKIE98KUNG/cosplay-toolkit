---
name: coser-image-collector
description: 全网搜集指定coser的高清cosplay图片并下载到本地。支持微博、B站动态、元气小站等多平台图片采集，自动去重并保存高清原图。当用户要求"搜集XX的cos图包"、"下载XX的cos图片"、"爬取XX的cosplay照片"、"全网找XX的cos图"时使用。
---

# Coser 图片全网收集器

从多个平台收集指定coser的高清cosplay图片，自动去重并下载到本地。

## 工作流程

### 1. 搜索并确认coser身份

使用 `general_search` 搜索coser名字，确认其在各平台的账号：
- 微博：搜索 `{coser名} 微博`，获取用户ID
- B站：搜索 `{coser名} bilibili`，获取UID
- 元气小站：搜索 `{coser名} yuanqxz`，确认是否有专题页面

### 2. 从微博收集图片

使用 `computer_use_tool` (plane="bu") 操作浏览器：

1. 导航到 `https://weibo.com/u/{用户ID}`
2. 如遇登录拦截，调用 `interaction.request_action` (type="browserControl") 请用户登录
3. 滚动加载目标时间范围的微博（默认近一年）
4. 用JavaScript提取图片URL：

```javascript
const imgs = document.querySelectorAll('img');
const urls = new Set();
imgs.forEach(img => {
    const src = img.src || img.getAttribute('data-src');
    if (src && src.match(/wx\d+\.sinaimg\.cn\//)) {
        let clean = src.split('?')[0];
        clean = clean.replace(/\/(orj360|thumb150|square|small)\//, '/mw2000/');
        if (clean.match(/wx\d+\.sinaimg\.cn\/(mw2000|large|orj1080)\//)) {
            urls.add(clean);
        }
    }
});
```

**要点**：
- 微博图片优先使用 `mw2000` 高清版本
- 滚动时持续提取，避免懒加载遗漏
- 注意博主可能设置"仅展示半年/一年内微博"

### 3. 从B站动态收集图片

1. 导航到 `https://space.bilibili.com/{UID}/dynamic`
2. 滚动加载动态
3. 提取图片URL，过滤视频封面和表情：

```javascript
const imgs = document.querySelectorAll('img');
const urls = new Set();
imgs.forEach(img => {
    const src = img.src || img.getAttribute('data-src');
    if (src && src.includes('hdslb.com') && !src.includes('face') && !src.includes('emoji')) {
        let clean = src.split('?')[0].replace(/@.*$/, '');
        if (clean.includes('new_dyn') || clean.includes('article')) {
            urls.add(clean);
        }
    }
});
```

### 4. 从元气小站收集图片

1. 导航到 `https://www.yuanqxz.com/`，搜索coser名字
2. 进入其标签页，提取所有文章链接
3. 逐篇访问文章，提取图片URL（通常是sinaimg.cn域名）

### 5. 合并去重并下载

1. 将所有平台的URL合并，用 `Sort-Object -Unique` 去重
2. 使用 `scripts/download_images.py` 下载图片
3. 保存到 `{工作目录}/{coser名}_全网收集/` 文件夹

## 下载脚本

使用 `scripts/download_images.py` 批量下载，支持：
- 断点续传（跳过已存在文件）
- 自动重试（失败重试3次）
- 多平台referer适配
- 失败URL记录

运行方式：
```bash
python scripts/download_images.py {url_file} {save_dir}
```

## 注意事项

- **版权提醒**：下载完成后提醒用户图片版权归coser和摄影师所有，仅供个人欣赏
- **付费内容**：舰长壁纸、实体本、付费图集等无法公开获取，需告知用户
- **防盗链**：B站图片可能需要浏览器下载（`bu.download()`），Python直接下载可能失败
- **时间范围**：默认近一年，用户明确要求时可调整
- **平台限制**：部分博主设置微博展示时间限制，需如实告知

## 输出规范

下载完成后向用户报告：
- 总图片数和总大小
- 各平台来源分布
- 保存路径
- 失败/遗漏说明
