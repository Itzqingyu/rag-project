"""檔案格式轉換服務模組 (Document Converter)。

提供將不同格式的原始檔案 (PDF, DOCX, TXT, MD) 統一解析並轉換為標準 Markdown 格式的功能。
轉換後的 Markdown 檔案一律託管並儲存於 python/data/markdown/ 目錄中。
"""

import os
import shutil
from typing import Optional
from pypdf import PdfReader
from docx import Document as DocxDocument

# 定義預設的 Markdown 儲存目錄 (python/data/markdown/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DEFAULT_MARKDOWN_DIR = os.path.join(BASE_DIR, "data", "markdown")
os.makedirs(DEFAULT_MARKDOWN_DIR, exist_ok=True)


def _convert_txt_to_markdown(raw_path: str) -> str:
    """讀取 TXT 純文字檔案並包裹標題生成 Markdown 文字內容。"""
    filename = os.path.basename(raw_path)
    title = os.path.splitext(filename)[0]
    
    content = ""
    # 嘗試不同的文字編碼讀取 TXT
    for encoding in ("utf-8", "utf-8-sig", "big5", "gbk", "cp950", "latin1"):
        try:
            with open(raw_path, "r", encoding=encoding) as f:
                content = f.read()
            break
        except (UnicodeDecodeError, Exception):
            continue
            
    markdown_text = f"# {title}\n\n{content}"
    return markdown_text


def _convert_pdf_to_markdown(raw_path: str) -> str:
    """使用 pypdf 逐頁提取 PDF 內文並格式化為 Markdown 文字內容。"""
    filename = os.path.basename(raw_path)
    title = os.path.splitext(filename)[0]
    
    reader = PdfReader(raw_path)
    pages_text = []
    
    for i, page in enumerate(reader.pages, 1):
        extracted = page.extract_text()
        if extracted and extracted.strip():
            pages_text.append(f"## 頁碼 {i}\n\n{extracted.strip()}")
            
    combined_body = "\n\n---\n\n".join(pages_text)
    markdown_text = f"# {title}\n\n{combined_body}"
    return markdown_text


def _convert_docx_to_markdown(raw_path: str) -> str:
    """使用 python-docx 解析 Word 檔案之標題與段落，轉為 Markdown 文字內容。"""
    filename = os.path.basename(raw_path)
    title = os.path.splitext(filename)[0]
    
    doc = DocxDocument(raw_path)
    lines = [f"# {title}\n"]
    
    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        if not text:
            continue
            
        style_name = paragraph.style.name.lower() if paragraph.style else ""
        if "heading 1" in style_name:
            lines.append(f"\n# {text}")
        elif "heading 2" in style_name:
            lines.append(f"\n## {text}")
        elif "heading 3" in style_name:
            lines.append(f"\n### {text}")
        elif "list" in style_name or "bullet" in style_name:
            lines.append(f"* {text}")
        else:
            lines.append(text)
            
    markdown_text = "\n\n".join(lines)
    return markdown_text


def convert_to_markdown(file_path: str, output_dir: Optional[str] = None) -> str:
    """將傳入的檔案 (MD, TXT, PDF, DOCX) 統一轉換並儲存為 Markdown (.md) 實體檔案。
    
    :param file_path: 原始檔案實體路徑
    :param output_dir: 可選的輸出目錄 (預設為 python/data/markdown/)
    :return: 轉換完成後的 Markdown 檔案絕對路徑
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"找不到檔案: {file_path}")
        
    target_dir = output_dir or DEFAULT_MARKDOWN_DIR
    os.makedirs(target_dir, exist_ok=True)
    
    base_name = os.path.basename(file_path)
    file_stem, ext = os.path.splitext(base_name)
    ext = ext.lower()
    
    target_md_path = os.path.join(target_dir, f"{file_stem}.md")
    
    # 1. 若本身就是 .md 檔案，直接複製備份至 target_dir 託管
    if ext == ".md":
        if os.path.abspath(file_path) != os.path.abspath(target_md_path):
            shutil.copyfile(file_path, target_md_path)
        return target_md_path
        
    # 2. .txt 檔案轉換
    elif ext == ".txt":
        md_text = _convert_txt_to_markdown(file_path)
        
    # 3. .pdf 檔案轉換
    elif ext == ".pdf":
        md_text = _convert_pdf_to_markdown(file_path)
        
    # 4. .docx 檔案轉換
    elif ext in (".docx", ".doc"):
        if ext == ".doc":
            raise ValueError("目前暫不支援舊版 .doc 格式，請先存為 .docx 後再上傳")
        md_text = _convert_docx_to_markdown(file_path)
        
    else:
        raise ValueError(f"不支援的檔案格式: {ext}，目前僅支援 .md, .txt, .pdf, .docx")
        
    # 將轉換後的 Markdown 寫入目標檔案
    with open(target_md_path, "w", encoding="utf-8") as f:
        f.write(md_text)
        
    return target_md_path
