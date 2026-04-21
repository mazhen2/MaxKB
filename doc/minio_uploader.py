r"""
MinIO Markdown 转录工具
将 md 文件中的本地图片/视频上传到 MinIO，生成「原名_转录版.md」，路径替换为 MinIO URL。
"""

import re
import os
import sys
import argparse
import urllib.parse
from pathlib import Path
from urllib.parse import unquote

try:
    from minio import Minio
except ImportError:
    print("Error: minio package not found. Install it with: pip install minio")
    sys.exit(1)


# =====================  默认 MinIO 配置  =====================
DEFAULT_ENDPOINT = "127.0.0.1:9000"
DEFAULT_ACCESS_KEY = "root"
DEFAULT_SECRET_KEY = "Root123.com"
DEFAULT_BUCKET = "media"
DEFAULT_SECURE = False
DEFAULT_BASE_URL = "http://127.0.0.1:9000/media"

# 支持的文件扩展名
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".ico"}
VIDEO_EXTS = {".mp4", ".webm", ".avi", ".mov", ".mkv", ".flv", ".wmv"}
SUPPORTED_EXTS = IMAGE_EXTS | VIDEO_EXTS


class MinIOClient:
    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        secure: bool,
        base_url: str,
    ):
        self.endpoint = endpoint
        self.access_key = access_key
        self.secret_key = secret_key
        self.bucket = bucket
        self.secure = secure
        self.base_url = base_url
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
        )
        self._ensure_bucket()

    def _ensure_bucket(self):
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)
            print(f"  [MinIO] Bucket '{self.bucket}' created.")
        else:
            print(f"  [MinIO] Bucket '{self.bucket}' already exists.")

    def upload_file(self, local_path: str, object_name: str) -> str:
        object_name = object_name.lstrip("/")
        self.client.fput_object(self.bucket, object_name, local_path)
        return f"{self.base_url}/{object_name}"

    def object_exists(self, object_name: str) -> bool:
        object_name = object_name.lstrip("/")
        try:
            self.client.stat_object(self.bucket, object_name)
            return True
        except Exception:
            return False


class MarkdownUploader:
    SUFFIX = "_转录版"

    def __init__(
        self,
        root_dir: str,
        minio_client: MinIOClient,
        dry_run: bool = False,
    ):
        self.root_dir = Path(root_dir).resolve()
        self.minio = minio_client
        self.dry_run = dry_run
        self.stats = {
            "md_files_found": 0,
            "md_files_generated": 0,
            "resources_found": 0,
            "resources_uploaded": 0,
            "resources_skipped": 0,
            "errors": 0,
        }

    # ---- 路径解析 ----

    def _resolve_resource_path(self, md_file: Path, rel_path: str) -> Path | None:
        rel_path = rel_path.strip()
        rel_path = unquote(rel_path)

        if rel_path.startswith("/"):
            return self.root_dir / rel_path.lstrip("/")

        md_dir = md_file.parent
        return (md_dir / rel_path).resolve()

    # ---- 内容解析 ----

    def _extract_markdown_images(self, content: str) -> list[tuple[str, str, int]]:
        pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        results = []
        for m in re.finditer(pattern, content):
            path = m.group(2).strip()
            if self._is_local_media(path):
                results.append((m.group(0), path, m.start()))
        return results

    def _extract_html_images(self, content: str) -> list[tuple[str, str, int]]:
        results = []
        for m in re.finditer(r'<img\s+[^>]*src=["\']([^"\']+)["\'][^>]*>', content, re.IGNORECASE):
            path = m.group(1).strip()
            if self._is_local_media(path):
                results.append((m.group(0), path, m.start()))
        for m in re.finditer(r'<source\s+[^>]*src=["\']([^"\']+)["\'][^>]*>', content, re.IGNORECASE):
            path = m.group(1).strip()
            if self._is_local_media(path):
                results.append((m.group(0), path, m.start()))
        for m in re.finditer(r'<(?:video|audio)\s+[^>]*src=["\']([^"\']+)["\'][^>]*>', content, re.IGNORECASE):
            path = m.group(1).strip()
            if self._is_local_media(path):
                results.append((m.group(0), path, m.start()))
        return results

    def _is_local_media(self, path: str) -> bool:
        path = path.strip()
        if path.startswith(("http://", "https://", "//", "data:")):
            return False
        ext = os.path.splitext(path)[1].lower()
        return ext in SUPPORTED_EXTS

    def _get_object_name(self, md_file: Path, local_path: Path) -> str:
        md_rel = md_file.parent.relative_to(self.root_dir) if md_file.parent != self.root_dir else Path(".")
        try:
            resource_rel = local_path.relative_to(self.root_dir)
        except ValueError:
            resource_rel = local_path

        md_subpath = str(md_rel).replace("\\", "/")
        if md_subpath == ".":
            md_subpath = ""
        res_subpath = str(resource_rel).replace("\\", "/")

        if md_subpath:
            return f"{md_subpath}/{res_subpath}"
        return res_subpath

    def _iter_encoded_variants(self, path: str) -> list[str]:
        variants = []
        for safe in ["/:", "/", ""]:
            try:
                encoded = urllib.parse.quote(path, safe=safe)
                if encoded != path:
                    variants.append(encoded)
            except Exception:
                pass
        return variants

    def _output_path(self, md_file: Path) -> Path:
        stem = md_file.stem
        suffix = md_file.suffix
        return md_file.parent / f"{stem}{self.SUFFIX}{suffix}"

    # ---- 核心处理 ----

    def process(self):
        md_files = list(self.root_dir.rglob("*.md"))
        if not md_files:
            print(f"\nNo .md files found in {self.root_dir}")
            return

        self.stats["md_files_found"] = len(md_files)
        print(f"\nFound {len(md_files)} .md file(s). Scanning for media resources...\n")

        for md_file in sorted(md_files):
            self._process_md_file(md_file)

        self._print_summary()

    def _process_md_file(self, md_file: Path):
        try:
            content = md_file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            try:
                content = md_file.read_text(encoding="gbk")
            except Exception as e:
                print(f"  [ERROR] Cannot read {md_file}: {e}")
                self.stats["errors"] += 1
                return

        all_refs = []
        for full_match, path, pos in self._extract_markdown_images(content):
            all_refs.append((pos, "md", full_match, path))
        for full_match, path, pos in self._extract_html_images(content):
            all_refs.append((pos, "html", full_match, path))

        all_refs.sort(key=lambda x: x[0], reverse=True)

        if not all_refs:
            print(f"  [SKIP] No local media references: {md_file.name}")
            return

        seen_paths = {}

        for pos, ref_type, full_match, rel_path in all_refs:
            local_path = self._resolve_resource_path(md_file, rel_path)
            if local_path is None or not local_path.exists():
                print(f"  [SKIP] Not found: {rel_path} (in {md_file.name})")
                self.stats["resources_skipped"] += 1
                continue

            if not local_path.is_file():
                print(f"  [SKIP] Not a file: {rel_path}")
                self.stats["resources_skipped"] += 1
                continue

            ext = local_path.suffix.lower()
            if ext not in SUPPORTED_EXTS:
                print(f"  [SKIP] Unsupported extension: {rel_path}")
                self.stats["resources_skipped"] += 1
                continue

            self.stats["resources_found"] += 1
            key = str(local_path.resolve())
            object_name = self._get_object_name(md_file, local_path.resolve())

            if key in seen_paths:
                minio_url = seen_paths[key]
                print(f"  [REUSE] {local_path.name} -> {minio_url}")
            else:
                if self.dry_run:
                    minio_url = f"{self.minio.base_url}/{object_name}"
                    print(f"  [DRY] Would upload: {local_path} -> {minio_url}")
                else:
                    if self.minio.object_exists(object_name):
                        minio_url = f"{self.minio.base_url}/{object_name}"
                        print(f"  [EXISTS] {local_path.name} -> {minio_url}")
                    else:
                        try:
                            minio_url = self.minio.upload_file(str(local_path), object_name)
                            print(f"  [UPLOADED] {local_path.name} -> {minio_url}")
                            self.stats["resources_uploaded"] += 1
                        except Exception as e:
                            print(f"  [ERROR] Upload failed for {local_path}: {e}")
                            self.stats["errors"] += 1
                            continue

                seen_paths[key] = minio_url

            # 检查文件类型，决定使用视频标签还是图片标签
            file_ext = local_path.suffix.lower()
            is_video = file_ext in VIDEO_EXTS

            if ref_type == "md":
                # Markdown 格式 ![alt](path)
                if is_video:
                    # 视频：使用 <video> HTML 标签
                    new_match = f'<video src="{minio_url}" controls width="100%"></video>'
                else:
                    # 图片：保持 Markdown 语法
                    new_match = full_match.replace(f"({rel_path})", f"({minio_url})", 1)
                    for enc_path in self._iter_encoded_variants(rel_path):
                        new_match = new_match.replace(f"({enc_path})", f"({minio_url})", 1)
            else:
                # HTML 格式 <img src="path" /> 或 <video src="path" />
                if is_video:
                    # 转换为 <video> 标签
                    new_match = f'<video src="{minio_url}" controls width="100%"></video>'
                else:
                    # 保持原 HTML 格式，更新 src
                    new_match = re.sub(
                        r'(src=["\'])([^"\']+)',
                        lambda m: m.group(1) + minio_url,
                        full_match,
                        count=1,
                    )

            content = content[:pos] + new_match + content[pos + len(full_match):]

        out_path = self._output_path(md_file)
        self.stats["md_files_generated"] += 1
        if not self.dry_run:
            out_path.write_text(content, encoding="utf-8")
        print(f"  [GENERATED] -> {out_path}" + (" (dry-run)" if self.dry_run else ""))

    def _print_summary(self):
        print("\n" + "=" * 50)
        print("  Summary")
        print("=" * 50)
        print(f"  .md files found        : {self.stats['md_files_found']}")
        print(f"  .md files generated   : {self.stats['md_files_generated']}")
        print(f"  Resources found        : {self.stats['resources_found']}")
        print(f"  Resources uploaded    : {self.stats['resources_uploaded']}")
        print(f"  Resources skipped    : {self.stats['resources_skipped']}")
        print(f"  Errors                : {self.stats['errors']}")
        print("=" * 50)


def main():
    epilog = """
Examples:
  python minio_uploader.py
  python minio_uploader.py --dry-run
  python minio_uploader.py --endpoint 192.168.1.100:9000 --bucket mybucket
  python minio_uploader.py --endpoint 192.168.1.100:9000 --base-url http://192.168.1.100:9000/media
"""
    parser = argparse.ArgumentParser(
        description="Upload local media from .md files to MinIO and generate translated copies.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=epilog,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be uploaded without uploading or writing files",
    )
    parser.add_argument(
        "--endpoint",
        default=DEFAULT_ENDPOINT,
        help=f"MinIO endpoint (default: {DEFAULT_ENDPOINT})",
    )
    parser.add_argument(
        "--bucket",
        default=DEFAULT_BUCKET,
        help=f"MinIO bucket name (default: {DEFAULT_BUCKET})",
    )
    parser.add_argument(
        "--access-key",
        default=DEFAULT_ACCESS_KEY,
        help=f"MinIO access key (default: {DEFAULT_ACCESS_KEY})",
    )
    parser.add_argument(
        "--secret-key",
        default=DEFAULT_SECRET_KEY,
        help=f"MinIO secret key (default: ***)",
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"Public base URL (default: {DEFAULT_BASE_URL})",
    )

    args = parser.parse_args()

    script_path = Path(__file__).resolve()
    root_dir = script_path.parent.resolve()

    print(f"\nWorking directory : {root_dir}")
    print(f"MinIO endpoint    : {args.endpoint}")
    print(f"MinIO bucket      : {args.bucket}")
    print(f"Base URL          : {args.base_url}")
    if args.dry_run:
        print("Mode              : DRY RUN")

    minio_client = MinIOClient(
        endpoint=args.endpoint,
        access_key=args.access_key,
        secret_key=args.secret_key,
        bucket=args.bucket,
        secure=DEFAULT_SECURE,
        base_url=args.base_url,
    )

    uploader = MarkdownUploader(str(root_dir), minio_client, dry_run=args.dry_run)
    uploader.process()


if __name__ == "__main__":
    main()
