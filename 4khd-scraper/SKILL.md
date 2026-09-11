---
name: 4khd-scraper
description: 从4KHD网站（fjjdu.uuss.uk / 4khd.com类镜像站）搜索并批量下载指定coser/模特的图集预览图。支持按图集名称自动建文件夹归类，自动去重，断点续传。当用户要求"去4KHD爬取XX的图"、"下载4KHD上XX的全部图片"、"从4KHD保存XX图集"时使用。
---

# 4KHD 图集批量爬取 Skill

## 适用场景
用户要求从 4KHD 网站（域名可能为 `fjjdu.uuss.uk`、`4khd.com` 或其他镜像）下载指定 coser / 模特的全部图集图片。

## 网站结构说明
- 搜索 URL：`https://<domain>/?s=<关键词>` 或 `https://<domain>/search/<关键词>/page/<N>`
- 图集详情页：`https://<domain>/content/<NN>/<slug>.html`
- 每个图集页面提供约 20-30 张 **1300px 宽 webp 预览图**
- 完整无水印高清图存储在 TeraBox 网盘，网站页面不直接提供
- 图片 CDN 域名有两个（不同图集可能用不同CDN）：
  - `img.uuss.uk` — URL 含 `/w1300-rw/` 路径段
  - `i0.wp.com/pic.4khd.com` — WordPress.com CDN，URL 也含 `/w1300-rw/`
- **重要**：图集详情页可以直接用 HTTP 请求获取（不需要浏览器渲染），图片URL在HTML源码中

## 执行流程

### 第一步：确定域名和搜索
1. 用户给出的 URL 中提取域名（如 `fjjdu.uuss.uk`）
2. 若用户未给 URL，使用 `https://fjjdu.uuss.uk` 作为默认域名
3. 用浏览器（computer_use_tool / mac_computer_use_tool）打开搜索页

### 第二步：收集所有图集链接（遍历分页）
1. 访问 `https://<domain>/?s=<关键词>`（第1页）
2. 等待页面加载（至少5秒）
3. 用 JS 提取所有 `/content/` 链接：
   ```javascript
   const links = document.querySelectorAll('a');
   const albums = {};
   links.forEach(link => {
       if (link.href && link.href.includes('/content/') && link.href.includes('.html')) {
           const text = link.textContent.trim();
           if (text && text.length > 5 && text.length < 150) {
               albums[link.href] = text;
           }
       }
   });
   ```
4. 只保留标题含目标关键词的图集
5. 翻页：`https://<domain>/search/<关键词>/page/<N>`，直到无新结果
6. **注意**：该站分页可能有重复内容，需用 URL 去重
7. 将图集列表保存为 JSON 文件（含 url 和 title）

### 第三步：逐图集提取图片URL（推荐HTTP方法，更可靠）

**方法A：直接HTTP请求（推荐，避免浏览器导航问题）**

用 Python urllib 直接请求图集页面HTML，正则提取图片URL：
```python
import re, urllib.request

def extract_images(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
    with urllib.request.urlopen(req, timeout=20) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
    # 匹配两个CDN域名的webp图片
    pattern = r'https?://(?:i0\.wp\.com/pic\.4khd\.com|img\.uuss\.uk)/[^\s"\'<>]+?\.webp'
    urls = re.findall(pattern, html)
    # 去重，过滤站点装饰图
    unique = []
    seen = set()
    for u in urls:
        clean = u.split('?')[0]
        if clean not in seen and '4khd-beautifulGirls' not in clean and 'logo' not in clean.lower():
            seen.add(clean)
            unique.append(clean)
    return unique
```
- 注意：部分URL可能不完整（以 `/w1300-rw` 结尾无文件名），下载时会失败，属正常现象

**方法B：浏览器提取（备用，HTTP失败时用）**
1. `bu.navigate(album.url)`，等待加载（4-8秒）
2. 提取 `a.imageLink` 的 href：
   ```javascript
   const links = document.querySelectorAll('a.imageLink');
   const urls = [];
   links.forEach(link => {
       if (link.href && link.href.includes('uuss')) urls.push(link.href);
   });
   ```
3. 若返回0张，等待5秒后重试
4. 该站浏览器导航可能异常（页面不跳转/重定向），优先用方法A

记录每张图所属图集名称（用于建文件夹）。

### 第四步：按图集建文件夹并下载
1. 根目录：`<工作目录>/<关键词>_4KHD/`
2. 每个图集建子文件夹，文件夹名从图集标题提取（去掉 `[xxxMB-xxphotos]` 后缀）
3. 文件名：从 URL 最后一段提取（如 `ion-part-2-4khd.com-001.webp`）
4. 下载脚本（PowerShell）：
   ```powershell
   $savePath = Join-Path $albumDir $filename
   if (-not (Test-Path $savePath)) {
       Invoke-WebRequest -Uri $url -OutFile $savePath -UseBasicParsing -TimeoutSec 20 -Headers @{"Referer"="https://<domain>/"}
   }
   ```
5. 每张间隔 300ms，避免被限流
6. 后台运行下载，定期检查进度

### 第五步：验证和清理
1. 检查 0 字节文件和异常小文件（<10KB）
2. 统计总数和总大小
3. 删除临时 JSON / TXT 文件

## 关键注意事项
- **必须用浏览器操作**：网站有反爬，直接 HTTP 请求搜索页可能失败
- **图片是预览图**：1300px webp，非原图。完整图在 TeraBox，需用户自行下载
- **分页重复**：第2-5页可能内容重复，务必 URL 去重
- **超时处理**：浏览器单次调用不超过120秒，分批处理图集
- **编码问题**：PowerShell 读 JSON 可能乱码，用 Python 处理中文 JSON
- **Referer 头**：下载图片时需带 Referer，否则可能 403
- **断点续传**：下载前检查文件是否已存在，跳过已下载的

## 输出给用户
- 保存路径
- 图集数量、图片总数、总大小
- 涵盖的图集名称列表
- 说明是1300px预览图，完整高清图在TeraBox
