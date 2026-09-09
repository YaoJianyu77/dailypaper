#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
论文图片提取脚本 - 支持从arXiv源码包优先提取
优先级：
1. arXiv源码包中的pics/或figures/目录（真正的论文图片）
2. 源码包中的PDF图片（架构图、实验图等）
3. PDF直接提取的图片（最后备选）
"""

import os
import json
import sys
import re
import shutil
import tarfile
import tempfile
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

IMAGE_EXTS = {'.png', '.jpg', '.jpeg', '.pdf', '.eps', '.svg'}
RASTER_EXTS = {'.png', '.jpg', '.jpeg', '.svg'}
FIGURE_DIR_HINTS = {'pics', 'figures', 'figure', 'fig', 'images', 'img'}
IGNORE_FILE_HINTS = {'logo', 'icon', 'favicon', 'avatar'}

try:
    import fitz  # PyMuPDF
    HAS_FITZ = True
except ImportError:
    fitz = None
    HAS_FITZ = False
    logger.warning("PyMuPDF not found, PDF-based image extraction will be skipped")

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    import urllib.request
    HAS_REQUESTS = False
    logger.warning("requests not found, using urllib")


def download_url(url, output_path, timeout=60):
    """下载URL到指定路径"""
    try:
        if HAS_REQUESTS:
            response = requests.get(url, timeout=timeout)
            content = response.content if response.status_code == 200 else None
            status = response.status_code
        else:
            req = urllib.request.urlopen(url, timeout=timeout)
            content = req.read()
            status = req.status

        if status == 200 and content:
            with open(output_path, 'wb') as f:
                f.write(content)
            return True
        print(f"下载失败: HTTP {status}")
        return False
    except Exception as e:
        logger.error("下载失败 (%s): %s", url, e)
        return False


def extract_arxiv_source(arxiv_id, temp_dir):
    """下载并提取arXiv源码包"""
    source_url = f"https://arxiv.org/e-print/{arxiv_id}"
    print(f"正在下载arXiv源码包: {source_url}")
    tar_path = os.path.join(temp_dir, f"{arxiv_id}.src")

    if not download_url(source_url, tar_path, timeout=60):
        return False

    print(f"源码包已下载: {tar_path}")

    try:
        with tarfile.open(tar_path, 'r:*') as tar:
            safe_members = []
            for member in tar.getmembers():
                if member.name.startswith('/') or '..' in Path(member.name).parts:
                    continue
                safe_members.append(member)
            tar.extractall(path=temp_dir, members=safe_members)
        print(f"源码已提取到: {temp_dir}")
        return True
    except tarfile.TarError as e:
        logger.error("解压源码包失败: %s", e)
        return False


def download_arxiv_pdf(arxiv_id, output_path):
    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    print(f"正在下载PDF: {pdf_url}")
    return download_url(pdf_url, output_path, timeout=60)


def normalize_ref_token(value):
    token = str(value or '').replace('\\', '/').strip()
    token = re.sub(r'^\./', '', token)
    return token


def resolve_graphics_ref(base_dir, ref):
    raw_ref = normalize_ref_token(ref)
    if not raw_ref:
        return None
    raw_path = Path(raw_ref)
    candidates = []
    if raw_path.suffix:
        candidates.append(base_dir / raw_path)
    else:
        candidates.append(base_dir / raw_path)
        for ext in ['.png', '.jpg', '.jpeg', '.pdf', '.eps', '.svg']:
            candidates.append(base_dir / f"{raw_ref}{ext}")

    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate.resolve()
    return None


def find_graphics_refs(temp_dir):
    refs = []
    seen = set()
    tex_files = sorted(Path(temp_dir).rglob('*.tex'))
    pattern = re.compile(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}')

    for tex_file in tex_files:
        try:
            text = tex_file.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue
        for ref in pattern.findall(text):
            resolved = resolve_graphics_ref(tex_file.parent, ref)
            if not resolved:
                continue
            key = str(resolved)
            if key in seen:
                continue
            seen.add(key)
            refs.append({
                'type': 'source',
                'source': 'latex-figure-ref',
                'path': str(resolved),
                'filename': resolved.name,
            })
    return refs


def should_ignore_file(path):
    lowered = path.name.lower()
    return any(token in lowered for token in IGNORE_FILE_HINTS)


def find_figures_from_source(temp_dir):
    """从源码目录中递归查找图片，优先 LaTeX 明确引用的 figure 文件"""
    figures = []
    seen_paths = set()

    for item in find_graphics_refs(temp_dir):
        key = item['path']
        if key in seen_paths:
            continue
        seen_paths.add(key)
        figures.append(item)

    ranked = []
    root_path = Path(temp_dir)
    for path in root_path.rglob('*'):
        if not path.is_file():
            continue
        if path.suffix.lower() not in IMAGE_EXTS:
            continue
        if should_ignore_file(path):
            continue
        lowered_parts = {part.lower() for part in path.parts}
        dir_score = 3 if lowered_parts & FIGURE_DIR_HINTS else 0
        if path.suffix.lower() == '.pdf':
            dir_score -= 1
        ranked.append((dir_score, len(path.parts), path))

    for _, _, path in sorted(ranked, key=lambda item: (-item[0], item[1], item[2].name.lower())):
        key = str(path.resolve())
        if key in seen_paths:
            continue
        seen_paths.add(key)
        figures.append({
            'type': 'source',
            'source': 'arxiv-source',
            'path': str(path.resolve()),
            'filename': path.name,
        })

    return figures


def unique_output_path(output_dir, filename):
    path = Path(output_dir) / filename
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    counter = 2
    while True:
        candidate = Path(output_dir) / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def extract_pdf_figures(pdf_path, output_dir):
    """从PDF中提取图片（备选方案）"""
    if not HAS_FITZ:
        logger.warning("跳过PDF图片提取：PyMuPDF 不可用")
        return []
    print("从PDF直接提取图片（备选方案）...")

    pdf_doc = fitz.open(pdf_path)
    image_list = []

    for page_num in range(len(pdf_doc)):
        page = pdf_doc[page_num]
        image_list_page = page.get_images(full=True)

        if image_list_page:
            for img_index, img in enumerate(image_list_page):
                xref = img[0]
                try:
                    base_image = pdf_doc.extract_image(xref)
                except Exception as e:
                    logger.warning("  跳过无法提取的图片 (page %d, xref %d): %s", page_num + 1, xref, e)
                    continue

                if base_image:
                    image_bytes = base_image['image']
                    image_ext = base_image['ext']

                    filename = f'page{page_num + 1}_fig{img_index + 1}.{image_ext}'
                    filepath = os.path.join(output_dir, filename)

                    with open(filepath, 'wb') as img_file:
                        img_file.write(image_bytes)

                    image_list.append({
                        'page': page_num + 1,
                        'index': img_index + 1,
                        'filename': filename,
                        'path': f'images/{filename}',
                        'size': len(image_bytes),
                        'ext': image_ext
                    })

    pdf_doc.close()
    return image_list


def extract_from_pdf_figures(figures_pdf, output_dir):
    """从PDF格式图片文件中提取图片"""
    if not HAS_FITZ:
        logger.warning("跳过PDF figure 提取：PyMuPDF 不可用")
        return []
    print(f"从PDF图片文件提取: {os.path.basename(figures_pdf)}")

    extracted = []
    doc = fitz.open(figures_pdf)
    filename = os.path.splitext(os.path.basename(figures_pdf))[0]

    for i in range(len(doc)):
        page = doc[i]
        pix = page.get_pixmap(dpi=150)
        output_name = f'{filename}_page{i+1}.png'
        output_path = os.path.join(output_dir, output_name)
        pix.save(output_path)

        extracted.append({
            'filename': output_name,
            'path': f'images/{output_name}',
            'size': len(pix.tobytes()),
            'ext': 'png'
        })

    doc.close()
    return extracted


def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S',
        stream=sys.stderr,
    )

    if len(sys.argv) < 4:
        print("Usage: python extract_images.py <paper_id> <output_dir> <index_file>")
        print("  paper_id: arXiv ID (如: 2510.24701) 或本地PDF路径")
        print("  output_dir: 输出目录")
        print("  index_file: 索引文件路径")
        sys.exit(1)

    paper_input = sys.argv[1]
    output_dir = sys.argv[2]
    index_file = sys.argv[3]

    os.makedirs(output_dir, exist_ok=True)

    is_pdf_file = os.path.isfile(paper_input)
    arxiv_id = None
    pdf_path = None

    if is_pdf_file:
        pdf_path = paper_input
        filename = os.path.basename(pdf_path)
        match = re.search(r'(\d{4}\.\d+)', filename)
        if match:
            arxiv_id = match.group(1)
            print(f"检测到arXiv ID: {arxiv_id}")
    else:
        arxiv_id = paper_input

    with tempfile.TemporaryDirectory() as temp_dir:
        all_figures = []

        # 步骤1: 尝试从arXiv源码包提取
        if arxiv_id:
            if extract_arxiv_source(arxiv_id, temp_dir):
                source_figures = find_figures_from_source(temp_dir)
                if source_figures:
                    print(f"\n从arXiv源码找到 {len(source_figures)} 个图片文件")
                    for fig in source_figures:
                        output_file = unique_output_path(output_dir, fig['filename'])
                        shutil.copy2(fig['path'], output_file)

                        all_figures.append({
                            'filename': output_file.name,
                            'path': f'images/{output_file.name}',
                            'size': os.path.getsize(output_file),
                            'ext': output_file.suffix[1:].lower(),
                            'source': fig['source']
                        })
                        print(f"  - {output_file.name}")

        # 步骤2: 如果源码包中没有找到足够的图片，从PDF中提取
        if len(all_figures) < 3 and not pdf_path and arxiv_id:
            candidate_pdf = os.path.join(temp_dir, f'{arxiv_id}.pdf')
            if download_arxiv_pdf(arxiv_id, candidate_pdf):
                pdf_path = candidate_pdf

        if len(all_figures) < 3 and pdf_path:
            print(f"\n找到的图片数量较少，从PDF直接提取...")
            pdf_figures = extract_pdf_figures(pdf_path, output_dir)
            for fig in pdf_figures:
                fig['source'] = 'pdf-extraction'
                all_figures.append(fig)

        # 步骤3: 检查源码包中的PDF图片文件并提取
        if arxiv_id and os.path.exists(temp_dir):
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    pdf_fig_path = os.path.join(root, file)
                    if (
                        file.endswith('.pdf')
                        and 'logo' not in file.lower()
                        and file != f'{arxiv_id}.tar.gz'
                        and os.path.abspath(pdf_fig_path) != os.path.abspath(pdf_path or '')
                    ):
                        try:
                            extracted = extract_from_pdf_figures(pdf_fig_path, output_dir)
                            for fig in extracted:
                                fig['source'] = 'pdf-figure'
                                all_figures.append(fig)
                        except Exception as e:
                            logger.warning("  跳过无法处理的PDF: %s (%s)", file, e)

    # 生成索引文件
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write('# 图片索引\n\n')
        f.write(f'总计：{len(all_figures)} 张图片\n\n')

        sources = {}
        for fig in all_figures:
            source = fig.get('source', 'unknown')
            if source not in sources:
                sources[source] = []
            sources[source].append(fig)

        for source, figs in sources.items():
            f.write(f'\n## 来源: {source}\n')
            for fig in figs:
                f.write(f'- 文件名：{fig["filename"]}\n')
                f.write(f'- 路径：{fig["path"]}\n')
                f.write(f'- 大小：{fig["size"] / 1024:.1f} KB\n')
                f.write(f'- 格式：{fig["ext"]}\n\n')

    print(f'\n成功提取 {len(all_figures)} 张图片')
    print(f'保存目录：{output_dir}')
    print(f'索引文件：{index_file}')
    print('\n图片列表：')
    for fig in all_figures:
        print(f'  - {fig["path"]} ({fig.get("source", "unknown")})')

    print('\nImage paths:')
    for fig in all_figures:
        print(fig["path"])


if __name__ == '__main__':
    main()
