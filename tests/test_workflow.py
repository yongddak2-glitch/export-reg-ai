from pathlib import Path
import json
import fitz
import pytest
from pydantic import ValidationError
from ai_engine import analyze, prepare, compare, validate_matches, _mock_matches, AnalysisError
from models import Project, EvidenceStatus as ES, ReviewStatus as RS, MatchBatch
from pdf_utils import extract_documents, merge_files, UploadError, normalize
from export_utils import draft_pdf
ROOT=Path(__file__).resolve().parents[1]

def test_initial_gaps_and_source_quotes(files):
    docs=extract_documents(files);a=analyze(Project(),docs)
    assert [r.evidence_status for r in a.results]==[ES.INSUFFICIENT,ES.FOUND,ES.FOUND,ES.FOUND,ES.FOUND,ES.MODEL,ES.VERSION,ES.NOT_FOUND,ES.VERSION,ES.UNREADABLE,ES.FOUND,ES.FOUND]
    assert a.results[0].missing_information==['maintenance_interval']
    assert a.results[11].review_status==RS.EXPERT
    assert all(r.review_status!=RS.CONFIRMED for r in a.results)
    for r in a.results:
        assert r.next_actions
        for e in r.evidence:
            doc=next(d for d in docs if d.name==e.document)
            assert normalize(e.excerpt) in normalize(doc.pages[e.page-1].text)

def test_prepare_exact_values_pdf_and_reingest(files):
    a=analyze(Project(),extract_documents(files));r=a.results[0]
    with pytest.raises(AnalysisError):prepare(r,{},False)
    value='Every 30 days (synthetic demonstration only).'
    draft=prepare(r,{'maintenance_interval':value},True)
    assert value in draft['text'] and '1,000' not in draft['text']
    assert not draft['remaining_questions']
    raw=draft_pdf(a.project,draft)
    pdfdocs=extract_documents([('prepared.pdf',raw)])
    text=normalize(' '.join(p.text for p in pdfdocs[0].pages))
    for fact in draft['facts']:assert normalize(fact['value']) in text
    after=analyze(a.project,extract_documents(files+[('prepared.pdf',raw)]))
    assert after.results[0].evidence_status==ES.FOUND
    assert after.results[0].review_status==RS.HUMAN
    with pytest.raises(AnalysisError):prepare(a.results[7],{},True)

def test_recheck_recovers_and_reopens(files):
    before=analyze(Project(),extract_documents(files))
    updates=[(p.name,p.read_bytes()) for p in sorted((ROOT/'sample_data/revised').glob('*.pdf'))]
    merged=merge_files(files,updates,['BC100_User_Manual_v1.pdf','BC100_Drawing_Summary.pdf'])
    after=analyze(before.project,extract_documents(merged))
    assert after.results[0].evidence_status==ES.FOUND
    assert after.results[3].evidence_status==ES.NOT_FOUND
    assert after.results[6].evidence_status==ES.FOUND
    assert after.results[8].review_status==RS.EXPERT
    assert after.results[5].evidence_status==ES.MODEL
    diffs=compare(before,after)
    assert diffs[0]['변화']=='문서 Gap 보완 후보'
    assert diffs[3]['변화']=='재검토 필요'
    assert diffs[6]['변화']=='문서 Gap 보완 후보'
    assert len(diffs)==12
    assert dict(merge_files(files,[(files[0][0],b'new bytes')],[]))[files[0][0]]==b'new bytes'

def test_fabricated_quote_and_ids_fail_closed(files):
    docs=extract_documents(files);batch=_mock_matches(docs)
    batch.results[1].evidence[0].excerpt='Invented engineering fact absent from every page'
    results=validate_matches(batch,docs,Project())
    assert results[1].evidence_status==ES.INSUFFICIENT
    assert results[1].validation_notes
    batch.results[0].requirement_id='REQ-XX'
    with pytest.raises(AnalysisError):validate_matches(batch,docs,Project())

def test_schema_and_approval_guard(files):
    docs=extract_documents(files);batch=_mock_matches(docs)
    raw=batch.model_dump(mode='json');raw['results'][0]['evidence_status']='COMPLIANT'
    with pytest.raises(ValidationError):MatchBatch.model_validate(raw)
    batch.results[1].review_status=RS.CONFIRMED
    assert validate_matches(batch,docs,Project())[1].review_status==RS.HUMAN
    batch.results[1].next_actions=['CE APPROVED']
    with pytest.raises(AnalysisError):validate_matches(batch,docs,Project())

def test_upload_rejections(files):
    for invalid in ([], [('bad.pdf',b'not pdf')], [files[0],files[0]], [('huge.pdf',b'%PDF-'+b'x'*(5*1024*1024))]):
        with pytest.raises(UploadError):extract_documents(invalid)
    pdf=fitz.open();pdf.new_page()
    encrypted=pdf.tobytes(encryption=fitz.PDF_ENCRYPT_AES_256,owner_pw='owner',user_pw='test');pdf.close()
    with pytest.raises(UploadError):extract_documents([('locked.pdf',encrypted)])
    pdf=fitz.open()
    for _ in range(61):pdf.new_page()
    with pytest.raises(UploadError):extract_documents([('too-many-pages.pdf',pdf.tobytes())])
    pdf.close()

def test_long_korean_draft_preserves_facts(files):
    a=analyze(Project(),extract_documents(files))
    value='담당자가 확인한 점검 일정입니다. ' * 40
    draft=prepare(a.results[0],{'maintenance_interval':value},True)
    docs=extract_documents([('long.pdf',draft_pdf(a.project,draft))])
    text=normalize(' '.join(p.text for p in docs[0].pages))
    assert normalize(value) in text
