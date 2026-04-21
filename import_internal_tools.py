"""
更新「提取上传到MaxKB后文档中的图片」工具代码，
使其同时支持 Markdown ![](url) 和 HTML <img src="..."> 两种格式
用法：D:\conda\envs\GCode\python.exe import_internal_tools.py
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'maxkb.settings')

import django
django.setup()

from django.db import connection

NEW_CODE = r'''# coding=utf-8
import re
import time
from typing import Any, Dict, List


def extract_images_from_markdown(markdown_text: str) -> List[Dict[str, Any]]:
    """
    从 Markdown/HTML 文本中提取图片引用，返回 MAXKB 工作流可直接使用的图片数组。
    支持：
    - Markdown 格式：![alt](url)
    - HTML 格式：<img src="url" ...> 或 <image src="url" ...>
    """
    images_info: List[Dict[str, Any]] = []
    index = 0

    # 1. Markdown 格式：![alt](url)
    md_pattern = re.compile(r'!\[(.*?)\]\(([^)]+)\)')
    for match in md_pattern.finditer(markdown_text or ""):
        index += 1
        alt_text = match.group(1)
        url = str(match.group(2) or "").strip().strip('"').strip("'")
        if not url:
            continue
        filename = _derive_filename(url, alt_text, index)
        file_id = _extract_file_id_from_url(url)
        uid = int(time.time() * 1000) + index * 100
        images_info.append({
            "name": filename,
            "percentage": 0,
            "status": "ready",
            "size": 0,
            "raw": {"uid": uid},
            "uid": uid,
            "url": url,
            "file_id": file_id,
        })

    # 2. HTML 格式：<img src="url"> 或 <image src="url">
    html_pattern = re.compile(
        r'<(?:img|image)\b[^>]*?\bsrc\s*=\s*["\']?\s*([^"\'>\s]+)["\']?[^>]*/?>',
        re.IGNORECASE
    )
    for match in html_pattern.finditer(markdown_text or ""):
        index += 1
        url = match.group(1).strip().strip('"').strip("'")
        if not url:
            continue
        # 尝试从标签中提取 alt 属性
        alt_match = re.search(r'\balt\s*=\s*["\']([^"\']*)["\']', match.group(0), re.IGNORECASE)
        alt_text = alt_match.group(1) if alt_match else ""
        filename = _derive_filename(url, alt_text, index)
        file_id = _extract_file_id_from_url(url)
        uid = int(time.time() * 1000) + index * 100
        images_info.append({
            "name": filename,
            "percentage": 0,
            "status": "ready",
            "size": 0,
            "raw": {"uid": uid},
            "uid": uid,
            "url": url,
            "file_id": file_id,
        })

    return images_info


def _derive_filename(url: str, alt_text: str, index: int) -> str:
    if "/" in url:
        filename = url.split("/")[-1].split("?")[0]
        if "." not in filename:
            if alt_text and "." in alt_text:
                for candidate in alt_text.split():
                    if "." in candidate:
                        filename = candidate
                        break
            if "." not in filename:
                filename = f"{filename}.png"
        return filename

    if alt_text and "." in alt_text:
        for candidate in alt_text.split():
            if "." in candidate:
                return candidate

    return f"image{index}.png"


def _extract_file_id_from_url(url: str) -> str:
    if not url:
        return ""
    if "./oss/file/" in url:
        return url.split("./oss/file/")[-1].strip()
    if "/oss/file/" in url:
        return url.split("/oss/file/")[-1].strip()
    return ""


def handler(markdown_text: str) -> List[Dict[str, Any]]:
    return extract_images_from_markdown(markdown_text)
'''

TOOL_ID = '00474ff5-79f6-5b4d-b5a7-64a9acfbce8b'

with connection.cursor() as cursor:
    cursor.execute(
        'UPDATE tool SET code = %s WHERE id = %s',
        [NEW_CODE, TOOL_ID]
    )
    print(f'更新了 {cursor.rowcount} 条记录')
    if cursor.rowcount == 0:
        print('警告：未找到工具，请确认 TOOL_ID 是否正确')
