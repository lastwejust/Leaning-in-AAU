# -*- coding: utf-8 -*-
"""
扫描仓库里的课程资料，生成 docs/06-课程索引.md

用法（在仓库根目录执行）：
    python scripts/gen_courses.py
    python scripts/gen_courses.py --root . --out docs/06-课程索引.md
"""
import argparse
import os
import re
import urllib.parse

OWNER = "lastwejust"
REPO = "Leaning-in-AAU"
BRANCH = "main"
GH_BLOB = f"https://github.com/{OWNER}/{REPO}/blob/{BRANCH}"

# 超过这个大小的文件不复制进站点，只给 GitHub 链接
MAX_SITE_FILE = 24 * 1024 * 1024

SKIP_DIRS = {".git", ".github", "docs", "site", "site-dark", "scripts", "node_modules", "images", "image"}
MEDIA_EXT = {".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx", ".zip",
             ".png", ".jpg", ".jpeg", ".gif", ".webp", ".txt", ".rar", ".7z",
             ".mp4", ".caj", ".epub"}

CATEGORY_NAMES = {
    "00": "公共与平台课",
    "01": "农学",
    "02": "工学",
    "03": "理学",
    "04": "经济管理学院",
    "05": "人文社会科学学院",
    "06": "马克思主义学院",
    "07": "外国语学院与国际教育学院",
}


def enc(path):
    return "/".join(urllib.parse.quote(seg) for seg in path.split("/"))


def human(n):
    if n is None:
        return "—"
    size = float(n)
    for unit in ("B", "KB", "MB"):
        if size < 1024:
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} GB"


def scan(root):
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = os.path.relpath(dirpath, root)
        if rel_dir == ".":
            rel_dir = ""
        else:
            top = rel_dir.split(os.sep)[0]
            if top in SKIP_DIRS or top.startswith("."):
                dirnames[:] = []
                continue
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for name in filenames:
            if name.startswith("."):
                continue
            ext = os.path.splitext(name)[1].lower()
            if ext not in MEDIA_EXT or name.lower() == 'readme.md':
                continue
            if not rel_dir:
                continue  # 仓库根目录的 README 等不算资料
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, root).replace("\\", "/")
            files.append({"path": rel, "size": os.path.getsize(full)})
    files.sort(key=lambda x: x["path"])
    return files


def group(files):
    groups = {}
    for f in files:
        parts = f["path"].split("/")
        cat = parts[0]
        course = "/".join(parts[:-1])
        groups.setdefault(cat, {}).setdefault(course, []).append(f)
    return groups


def cat_label(cat):
    m = re.match(r"^(\d{2})", cat)
    return CATEGORY_NAMES.get(m.group(1), cat) if m else cat


def render(groups, total):
    out = []
    out.append("# 课程索引\n")
    out.append("这一页由脚本在构建时自动生成，列出仓库里**所有可以下载的文件**。\n")
    out.append(f"共 **{len(groups)}** 个分类、**{total}** 个文件。\n")
    out.append("!!! tip \"怎么下载\"\n"
               "    点表格里的 **下载** 直接取文件（来自本站，国内一般能直连）。\n"
               "    标注 **大文件** 的超过 24 MB，站点不托管，点 **GitHub** 到仓库页下载。\n")
    out.append("!!! note \"找不到课程？\"\n"
               "    页面内按 `Ctrl + F` 搜课程名。仓库里没有的课，就是还没人上传。\n")
    out.append("---\n")

    out.append("## 一览\n")
    out.append("| 分类 | 课程 / 目录 | 文件数 | 大小 |")
    out.append("| :--- | ---: | ---: | ---: |")
    for cat in sorted(groups):
        n_course = len(groups[cat])
        n_file = sum(len(v) for v in groups[cat].values())
        size = sum(f["size"] or 0 for v in groups[cat].values() for f in v)
        out.append(f"| **{cat_label(cat)}** | {n_course} | {n_file} | {human(size)} |")
    out.append("")

    for cat in sorted(groups):
        out.append(f"## {cat_label(cat)}\n")
        for course in sorted(groups[cat]):
            files = groups[cat][course]
            name = course.split("/")[-1]
            size = sum(f["size"] or 0 for f in files)
            out.append(f'??? note "{name}（{len(files)} 个文件，{human(size)}）"\n')
            out.append(f"    目录：`{course}`\n")
            out.append("    | 文件 | 大小 | 下载 |")
            out.append("    | :--- | ---: | :---: |")
            for f in files:
                label = f["path"].split("/")[-1].replace("|", "\\|")
                enc_path = enc(f["path"])
                if (f["size"] or 0) <= MAX_SITE_FILE:
                    link = f"[下载](../files/{enc_path})"
                else:
                    link = f"[GitHub 大文件]({GH_BLOB}/{enc_path})"
                out.append(f"    | {label} | {human(f['size'])} | {link} |")
            out.append("")

    out.append("---\n")
    out.append(f"仓库地址：<https://github.com/{OWNER}/{REPO}>\n")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    out = args.out or os.path.join(root, "docs", "06-课程索引.md")

    files = scan(root)
    groups = group(files)
    md = render(groups, len(files))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(md)
    print(f"写入 {out}")
    print(f"文件 {len(files)} 个，分类 {len(groups)} 个")


if __name__ == "__main__":
    main()