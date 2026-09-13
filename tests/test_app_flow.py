"""Streamlit's official UI harness: real PDF bytes through uploader widgets, no state injection."""
from pathlib import Path
from streamlit.testing.v1 import AppTest
from models import EvidenceStatus as ES
ROOT=Path(__file__).resolve().parents[1]

def button(at,label):return next(b for b in at.button if b.label==label)
def assert_clean(at):assert not list(at.exception), str(list(at.exception))

def test_upload_check_prepare_recheck(files):
    at=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run();assert_clean(at)
    at.file_uploader(key='initial_uploads').set_value([(n,b,'application/pdf') for n,b in files])
    button(at,'Analyze · 문서 대조').click().run();assert_clean(at)
    assert not list(at.error)
    assert len(at.dataframe[0].value)==12
    assert len(at.session_state['analysis'].documents)==6
    assert 'MODEL_MISMATCH' in set(at.dataframe[0].value['Evidence Status'])
    filt=next(r for r in at.radio if r.label=='결과 필터')
    filt.set_value('문제 있음').run();assert_clean(at)
    assert len(at.dataframe[0].value)==6
    next(r for r in at.radio if r.label=='결과 필터').set_value('전체').run()
    question=next(t for t in at.text_area if '주기' in t.label)
    question.input('Every 30 days (synthetic demonstration only).')
    next(c for c in at.checkbox if c.label=='인용 원문과 입력값의 사실관계를 확인했습니다.').check()
    button(at,'확인된 정보로 보완 초안 생성').click().run();assert_clean(at)
    assert not list(at.error)
    assert any(t.label=='문서 보완 초안' and 'Every 30 days' in t.value for t in at.text_area)
    assert any(d.label=='재업로드용 보완 PDF 다운로드' for d in at.get('download_button'))
    updates=[(p.name,p.read_bytes(),'application/pdf') for p in sorted((ROOT/'sample_data/revised').glob('*.pdf'))]
    at.multiselect[0].set_value(['BC100_User_Manual_v1.pdf','BC100_Drawing_Summary.pdf'])
    at.file_uploader(key='updated_uploads').set_value(updates)
    button(at,'RE-CHECK · 변경 비교').click().run();assert_clean(at)
    assert not list(at.error)
    a=at.session_state['analysis']
    assert a.results[0].evidence_status==ES.FOUND
    assert a.results[3].evidence_status==ES.NOT_FOUND
    assert len(at.dataframe[-1].value)==12
    assert at.session_state['comparison'][3]['변화']=='재검토 필요'
    assert len(at.session_state['history'])==2
    # Input changes cannot leave the previous draft visible after a new analysis.
    assert not any(t.label=='문서 보완 초안' for t in at.text_area)
