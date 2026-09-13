import hashlib
import re
from pathlib import Path
import fitz
from models import Document, Page

MAX_FILES = 10
MAX_FILE_BYTES = 5 * 1024 * 1024
MAX_PAGES = 60
MAX_CHARS = 90000

class UploadError(ValueError):
    pass

def extract_documents(files: list[tuple[str, bytes]]) -> list[Document]:
    if not files:
        raise UploadError('PDF 파일을 한 개 이상 업로드하세요.')
    if len(files) > MAX_FILES:
        raise UploadError(f'PoC는 최대 {MAX_FILES}개 PDF를 처리합니다.')
    docs, names, total_pages, chars = [], set(), 0, 0
    for raw_name, content in files:
        name = Path(raw_name.replace('\\', '/')).name
        if name in names:
            raise UploadError('같은 파일명이 두 번 있습니다. 파일명을 구분하세요.')
        names.add(name)
        if not name.lower().endswith('.pdf') or not content.startswith(b'%PDF-'):
            raise UploadError(f'{name}: 유효한 PDF 파일이 아닙니다.')
        if len(content) > MAX_FILE_BYTES:
            raise UploadError(f'{name}: 파일당 5 MB를 초과했습니다.')
        try:
            with fitz.open(stream=content, filetype='pdf') as pdf:
                if pdf.needs_pass:
                    raise UploadError(f'{name}: 암호화된 PDF는 지원하지 않습니다.')
                total_pages += len(pdf)
                if total_pages > MAX_PAGES:
                    raise UploadError('전체 PDF는 60페이지 이내로 줄여 주세요.')
                if not len(pdf):
                    raise UploadError(f'{name}: 페이지가 없습니다.')
                pages = []
                for i, p in enumerate(pdf):
                    text = p.get_text('text', sort=True).strip()
                    chars += len(text)
                    if chars > MAX_CHARS:
                        raise UploadError('전체 추출 텍스트가 90,000자를 초과했습니다. 범위를 줄여 주세요.')
                    pages.append(Page(number=i + 1, text=text, unreadable=len(text.strip()) < 20))
        except UploadError:
            raise
        except Exception as exc:
            raise UploadError(f'{name}: PDF를 열 수 없습니다. 손상 여부를 확인하세요.') from exc
        # Explicit header metadata only; document version and design revision differ.
        header = '\n'.join(p.text for p in pages[:2])
        model = re.search(r'^Model\s*:\s*([^\n]+)', header, re.M | re.I)
        rev = re.search(r'^Design revision\s*:\s*([^\n]+)', header, re.M | re.I)
        docs.append(Document(name=name, sha256=hashlib.sha256(content).hexdigest(), pages=pages,
                             model=model.group(1).strip() if model else '',
                             design_revision=rev.group(1).strip() if rev else ''))
    return docs

def normalize(text: str) -> str:
    return re.sub(r'\s+', ' ', text).strip()

def merge_files(old, new, remove):
    merged = {name: data for name, data in old if name not in remove}
    if len({name for name, _ in new}) != len(new):
        raise UploadError('새 파일의 이름이 중복됩니다.')
    # Same-name reupload explicitly replaces the old bytes.
    merged.update(dict(new))
    return list(merged.items())
