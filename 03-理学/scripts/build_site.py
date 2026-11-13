# -*- coding: utf-8 -*-
"""
一键构建站点：
  1. 生成课程索引 docs/06-课程索引.md
  2. mkdocs build
  3. 把课程资料复制进 site/files/（跳过超过 24 MB 的文件）

用法（仓库根目录）：
    python scripts/build_site.py

CI 里就是跑这一句。
"""
import os
import shutil
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SITE = os.path.join(ROOT, "site")
MAX_FILE = 24 * 1024 * 1024

SKIP_DIRS = {".git", ".github", "docs", "site", "site-dark", "scripts", "node_modules", "images", "image"}
MEDIA_EXT = {".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx", ".zip",
             ".png", ".jpg", ".jpeg", ".gif", ".webp", ".txt", ".rar", ".7z",
             ".mp4", ".caj", ".epub"}


def run(cmd):
    print("+", " ".join(cmd))
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode != 0:
        sys.exit(result.returncode)


def build_docs():
    run([sys.executable, os.path.join("scripts", "gen_courses.py"), "--root", ROOT])
    run([sys.executable, "-m", "mkdocs", "build"])


def copy_materials():
    dest_root = os.path.join(SITE, "files")
    copied = skipped = 0
    total = 0
    for top in sorted(os.listdir(ROOT)):
        top_path = os.path.join(ROOT, top)
        if not os.path.isdir(top_path):
            continue
        if top in SKIP_DIRS or top.startswith("."):
            continue
        for dirpath, dirnames, filenames in os.walk(top_path):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
            for name in filenames:
                if name.startswith("."):
                    continue
                ext = os.path.splitext(name)[1].lower()
                if ext not in MEDIA_EXT:
                    continue
                src = os.path.join(dirpath, name)
                size = os.path.getsize(src)
                if size > MAX_FILE:
                    print(f"  跳过（>{MAX_FILE // 1024 // 1024}MB）: {os.path.relpath(src, ROOT)}")
                    skipped += 1
                    continue
                rel = os.path.relpath(src, ROOT)
                dst = os.path.join(dest_root, rel)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)
                copied += 1
                total += size
    print(f"复制 {copied} 个文件（{total / 1024 / 1024:.1f} MB），跳过 {skipped} 个超大文件")


def main():
    build_docs()
    copy_materials()
    print("完成 →", SITE)


if __name__ == "__main__":
    main()