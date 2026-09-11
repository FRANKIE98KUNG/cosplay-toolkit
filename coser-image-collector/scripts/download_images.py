"""
Coser图片批量下载脚本
用法: python download_images.py <url_file> <save_dir>
"""
import os
import sys
import urllib.request
import time
from urllib.parse import urlparse


def download_images(url_file, save_dir):
    # 确保保存目录存在
    os.makedirs(save_dir, exist_ok=True)

    # 读取URL列表
    with open(url_file, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip()]

    print(f"共 {len(urls)} 张图片待下载")

    # 基础请求头
    base_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }

    success = 0
    failed = 0
    skipped = 0
    failed_urls = []

    for i, url in enumerate(urls, 1):
        # 从URL提取文件名
        parsed = urlparse(url)
        filename = os.path.basename(parsed.path)
        if not filename or '.' not in filename:
            filename = f"image_{i}.jpg"
        save_path = os.path.join(save_dir, filename)

        # 跳过已存在的文件
        if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
            skipped += 1
            if i % 50 == 0:
                print(f"[{i}/{len(urls)}] 成功={success}, 跳过={skipped}, 失败={failed}")
            continue

        # 根据域名设置referer
        headers = base_headers.copy()
        if 'bilibili.com' in url or 'hdslb.com' in url:
            headers['Referer'] = 'https://www.bilibili.com/'
        elif 'sinaimg.cn' in url or 'weibo' in url:
            headers['Referer'] = 'https://weibo.com/'

        # 重试机制
        downloaded = False
        for retry in range(3):
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=30) as response:
                    data = response.read()
                with open(save_path, 'wb') as f:
                    f.write(data)
                success += 1
                downloaded = True
                break
            except Exception as e:
                if retry < 2:
                    time.sleep(1)
                else:
                    failed += 1
                    failed_urls.append(url)

        if i % 50 == 0:
            print(f"[{i}/{len(urls)}] 成功={success}, 跳过={skipped}, 失败={failed}")

        # 避免请求过快
        time.sleep(0.1)

    print(f"\n下载完成！成功: {success}, 失败: {failed}, 跳过: {skipped}")

    # 保存失败的URL
    if failed_urls:
        failed_file = os.path.join(save_dir, "failed_urls.txt")
        with open(failed_file, "w", encoding="utf-8") as f:
            for url in failed_urls:
                f.write(url + "\n")
        print(f"失败的URL已保存到 {failed_file}")

    return success, failed, skipped


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("用法: python download_images.py <url_file> <save_dir>")
        sys.exit(1)

    url_file = sys.argv[1]
    save_dir = sys.argv[2]
    download_images(url_file, save_dir)
