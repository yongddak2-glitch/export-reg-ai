from io import BytesIO
import fitz
from ai_engine import MOCK_LABELS


def draft_pdf(project, draft):
    """Exact confirmed fact values; fixed labels make both real + mock re-ingestion possible."""
    doc=fitz.open()
    lines=['SYNTHETIC / USER-CONFIRMED DRAFT - REVIEW REQUIRED',
           f'Model: {project.model}',f'Design revision: {project.design_revision}',
           'Document version: prepared-1',f"Requirement: {draft['requirement_id']}",'']
    for f in draft['facts']:
        label=MOCK_LABELS[f['field_key']]
        value=f['value']
        if value.startswith(label+':'):
            lines.append(value)
        else:
            lines.append(label+': '+value)
        lines += ['Source: '+f['source'],'']
    if draft['remaining_questions']:
        lines += ['UNRESOLVED QUESTIONS']+draft['remaining_questions']
    # Measure glyph widths; CJK fonts can render Latin with different widths.
    page=doc.new_page();y=45
    for line in lines:
        fontname='helv' if line.isascii() else 'FactFont'
        font=fitz.Font('helv' if line.isascii() else 'korea')
        chunks=[]
        while line:
            end=0
            while end<len(line) and font.text_length(line[:end+1],fontsize=10)<=520:
                end+=1
            end=max(1,end)
            if end<len(line):
                space=line.rfind(' ',0,end)
                if space>0:end=space
            chunks.append(line[:end]);line=line[end:].lstrip()
        chunks=chunks or ['']
        for part in chunks:
            if y>780:page=doc.new_page();y=45
            if fontname=='FactFont':page.insert_font(fontname=fontname,fontbuffer=font.buffer)
            page.insert_text((35,y),part,fontname=fontname,fontsize=10);y+=17
    doc.subset_fonts()
    data=doc.tobytes(garbage=4,deflate=True);doc.close();return data

def report_markdown(analysis):
    lines=['# 기술문서 준비 검토 결과',f'프로젝트: {analysis.project.name}',
           f'모델: {analysis.project.model} / 설계 버전: {analysis.project.design_revision}',
           f'분석 방식: {analysis.mode} ({analysis.model})',f'분석 ID: {analysis.analysis_id}',
           f'생성 시각: {analysis.created_at}',f'요구사항 버전: {analysis.dataset_version}',
           '근거 후보와 문서 보완용 결과입니다. 최종 적합성 판정이 아닙니다.',
           'Mock 결과는 AI 성능의 증거가 아닙니다.' if analysis.mode=='mock' else 'AI 인용은 원문과의 문자열 대조를 거쳤으며 의미의 정확성은 사람 확인이 필요합니다.']
    for r in analysis.results:
        lines += ['',f'## {r.requirement_id} {r.requirement_title}',r.regulation_reference,r.source_url,
                  f'자료 상태: {r.evidence_status.value}',f'검토 상태: {r.review_status.value}',r.issue]
        for e in r.evidence:lines += [f'- {e.document} p.{e.page}: {e.excerpt}',f'  연결 이유: {e.reason}']
        lines += [f'- 다음 행동: {a}' for a in r.next_actions]
        lines += [f'- 검증 참고: {a}' for a in r.validation_notes]
    return '\n'.join(lines)
