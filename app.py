from datetime import date, datetime, timezone
from pathlib import Path
import json
import os
import streamlit as st
from dotenv import load_dotenv
import fitz
from ai_engine import REQUIREMENTS, REQ_BY_ID, AnalysisError, analyze, prepare, compare
from models import Project, EvidenceStatus as ES, ReviewStatus as RS
from pdf_utils import extract_documents, merge_files, UploadError
from export_utils import draft_pdf, report_markdown

ROOT=Path(__file__).parent
load_dotenv(ROOT/'.env')
st.set_page_config(page_title='Evidence Desk | 기술문서 준비',page_icon='📑',layout='wide')
st.markdown('''<style>
.block-container{padding-top:2rem;max-width:1450px}
h1{letter-spacing:-1.6px} [data-testid="stMetric"]{border:1px solid #dce4eb;border-radius:10px;padding:14px;background:#f8fafc}
[data-testid="stSidebar"]{background:#f3f6f9} .stTabs [data-baseweb="tab"]{font-weight:600}
</style>''',unsafe_allow_html=True)

def setting(name,default=''):
    value=os.getenv(name)
    if value is not None:return value
    try:return str(st.secrets.get(name,default))
    except (FileNotFoundError,st.errors.StreamlitSecretNotFoundError):return default

def files_from_upload(files):
    return [(f.name,f.getvalue()) for f in (files or [])]

def initial_samples():
    return [(p.name,p.read_bytes()) for p in sorted((ROOT/'sample_data').glob('*.pdf'))]

def show_evidence(result,analysis):
    st.caption(result.regulation_reference)
    st.link_button('공개 법령 원문',result.source_url)
    if not result.evidence:st.info('이 항목에는 검증된 인용이 없습니다.')
    for e in result.evidence:
        st.markdown(f'**{e.document} · p.{e.page}**')
        st.text(e.excerpt)
        st.caption(e.reason)
    for note in result.validation_notes:st.warning(note)
    if result.issue:st.info(result.issue)

def do_analysis(project,files):
    if mode=='openai' and not enabled:
        raise AnalysisError('서버에서 ENABLE_OPENAI=true를 설정해야 API 모드를 사용할 수 있습니다.')
    docs=extract_documents(files)
    return analyze(project,docs,mode=mode,api_key=api_key,model=model)

api_key=setting('OPENAI_API_KEY')
model=setting('OPENAI_MODEL','gpt-4.1-mini')
enabled=setting('ENABLE_OPENAI','false').lower()=='true'
with st.sidebar:
    st.markdown('### Evidence Desk')
    st.caption('EU CONVEYOR · DOCUMENT PREPARATION')
    selected_mode=st.radio('분석 방식',['Mock · API 없이 체험','OpenAI · 실제 의미 매칭'])
    mode='mock' if selected_mode.startswith('Mock') else 'openai'
    if mode=='mock':st.info('Mock는 합성자료의 명시적 필드를 읽는 규칙 기반 시연입니다. AI 성능 검증 결과가 아닙니다.')
    else:
        st.caption('모델: '+model)
        if not enabled:st.warning('실제 API 사용은 서버 설정에서 활성화해야 합니다.')
        elif not api_key:st.warning('서버에 API 키가 없습니다.')
        else:st.info('분석 시 추출된 PDF 텍스트가 OpenAI API로 전송됩니다.')
    st.divider()
    st.caption('범위: 2026년 EU 출시 / 단독 물품이송 벨트 컨베이어 / 사전 정의 문서 항목 12개')
    st.caption('합성·공개자료 시연용입니다. 스캔 OCR과 도면 형상 해석은 지원하지 않습니다.')
    if st.button('프로젝트 초기화',width='stretch'):
        for k in list(st.session_state):del st.session_state[k]
        st.rerun()

st.title('근거를 찾고, 다음 보완을 준비하세요.')
st.caption('UPLOAD → CHECK → TO DO → PREPARE → RE-CHECK')
st.info('문서의 존재와 적합성은 다릅니다. 이 도구는 근거 후보·누락·변경을 정리하며, 최종 판단은 사람이 수행합니다.')
tab_project,tab_check,tab_prepare,tab_recheck=st.tabs(['1 · PROJECT','2 · CHECK','3 · TO DO / PREPARE','4 · RE-CHECK'])

with tab_project:
    st.subheader('검토할 프로젝트와 문서')
    c1,c2=st.columns([2,1])
    with c1:
        with st.form('project_form'):
            project_name=st.text_input('프로젝트명','BC-100 EU 기술문서 준비',max_chars=150)
            product=st.text_input('제품명','Stand-alone general material-handling belt conveyor',max_chars=200)
            a,b,c=st.columns(3)
            product_model=a.text_input('제품 모델','BC-100',max_chars=60)
            revision=b.text_input('현재 설계 버전','B',max_chars=30)
            launch=c.date_input('EU 출시 예정일',date(2026,11,1),min_value=date(2026,1,1),max_value=date(2026,12,31))
            st.caption('목표시장 EU · 문서 v1/v2와 설계 버전 A/B는 다른 값입니다.')
            uploads=st.file_uploader('기술문서 PDF 여러 개 업로드',type=['pdf'],accept_multiple_files=True,key='initial_uploads',max_upload_size=5)
            submit=st.form_submit_button('Analyze · 문서 대조',type='primary',width='stretch')
        if submit:
            try:
                if not all(x.strip() for x in [project_name,product,product_model,revision]):
                    raise UploadError('프로젝트명·제품명·모델·설계 버전을 입력하세요.')
                files=files_from_upload(uploads) or st.session_state.get('sample_files',[])
                project=Project(name=project_name.strip(),product=product.strip(),model=product_model.strip(),design_revision=revision.strip(),launch_date=str(launch))
                with st.spinner('문서 원문과 요구사항을 대조하고 인용을 검증하는 중...'):
                    result=do_analysis(project,files)
                st.session_state.analysis=result
                st.session_state.files=files
                st.session_state.history=[result]
                st.session_state.pop('comparison',None);st.session_state.pop('draft',None)
                st.success(f'분석 완료 · {len(result.results)}개 항목 · {result.mode}. CHECK 탭에서 확인하세요.')
            except (UploadError,AnalysisError,ValueError) as exc:st.error(str(exc))
    with c2:
        st.markdown('#### 1분 데모 준비')
        st.write('샘플에는 다른 모델의 시험자료, 구버전 도면, 유지보수 정보 누락, 읽을 수 없는 소음 자료가 들어 있습니다.')
        if st.button('합성 PDF 6개 불러오기',width='stretch'):
            st.session_state.sample_files=initial_samples()
            st.success('샘플을 준비했습니다. Analyze를 누르세요.')
        staged=files_from_upload(uploads) or st.session_state.get('sample_files',[])
        if staged:
            st.caption('분석할 파일')
            for name,data in staged:st.text(f'{name} ({len(data)//1024} KB)')
        st.caption('직접 업로드한 파일이 있으면 불러온 샘플보다 우선합니다.')
        if st.session_state.get('analysis'):
            st.caption('현재 결과는 마지막 Analyze 시점의 프로젝트·파일 스냅샷입니다. 입력을 바꾼 뒤에는 다시 분석하세요.')

analysis=st.session_state.get('analysis')
with tab_check:
    if not analysis:st.info('PROJECT에서 PDF를 업로드하고 Analyze를 실행하세요.')
    else:
        st.subheader('Requirement–Evidence Gap Matrix')
        st.caption(f'{analysis.project.name} · {analysis.project.model} · 설계 {analysis.project.design_revision} · {analysis.mode} / {analysis.model} · {analysis.created_at}')
        m1,m2,m3,m4=st.columns(4)
        m1.metric('검토 항목',len(analysis.results))
        m2.metric('문서 Gap',sum(r.has_gap for r in analysis.results))
        m3.metric('근거 후보 있음',sum(bool(r.evidence) for r in analysis.results))
        m4.metric('전문가 판단 필요',sum(r.review_status==RS.EXPERT for r in analysis.results))
        for warning in analysis.warnings:st.warning(warning)
        choice=st.radio('결과 필터',['전체','문제 있음','근거 발견','사람 확인 필요','전문가 판단 필요'],horizontal=True)
        predicates={'전체':lambda r:True,'문제 있음':lambda r:r.has_gap,
                    '근거 발견':lambda r:r.evidence_status==ES.FOUND,
                    '사람 확인 필요':lambda r:r.review_status in (RS.UNREVIEWED,RS.HUMAN),
                    '전문가 판단 필요':lambda r:r.review_status==RS.EXPERT}
        visible=[r for r in analysis.results if predicates[choice](r)]
        rows=[{'Requirement':r.requirement_id+' '+r.requirement_title,
               'Evidence':' / '.join(dict.fromkeys(e.document for e in r.evidence)) or '—',
               'Page':', '.join(f'{e.document}: {e.page}' for e in r.evidence) or '—',
               'Evidence Status':r.evidence_status.value,'Review Status':r.review_status.value,
               'Issue':r.issue or '원문 및 사실관계 확인 대기','Next Action':' / '.join(r.next_actions)} for r in visible]
        st.dataframe(rows,width='stretch',hide_index=True)
        if visible:
            rid=st.selectbox('항목 상세보기',[r.requirement_id for r in visible],format_func=lambda x:x+' · '+REQ_BY_ID[x].requirement_title)
            row=next(r for r in analysis.results if r.requirement_id==rid)
            with st.expander('근거 원문 및 검토',expanded=True):
                show_evidence(row,analysis)
                if row.evidence:
                    source=st.selectbox('PDF 페이지 보기',list(range(len(row.evidence))),format_func=lambda i:row.evidence[i].document+' · p.'+str(row.evidence[i].page))
                    e=row.evidence[source]
                    with st.expander('해당 PDF 페이지 열기'):
                        data=dict(st.session_state.files)[e.document]
                        with fitz.open(stream=data,filetype='pdf') as pdf:
                            st.image(pdf[e.page-1].get_pixmap(matrix=fitz.Matrix(1.1,1.1)).tobytes('png'),width=650)
                st.caption('사용자 확인은 인용·문서 사실관계 확인만 의미합니다. 전문가 판단 항목에는 적용할 수 없습니다.')
                if st.button('문서 사실관계 확인 기록',disabled=row.has_gap or row.review_status==RS.EXPERT):
                    row.review_status=RS.CONFIRMED;row.confirmed_at=datetime.now(timezone.utc).isoformat()
                    st.rerun()
        d1,d2=st.columns(2)
        d1.download_button('결과 JSON 다운로드',analysis.model_dump_json(indent=2),file_name='evidence-analysis.json',mime='application/json',width='stretch')
        d2.download_button('검토 보고서 다운로드',report_markdown(analysis),file_name='document-review.md',mime='text/markdown',width='stretch')

with tab_prepare:
    if not analysis:st.info('먼저 분석을 실행하세요.')
    else:
        st.subheader('다음 보완 작업과 확인된 사실의 초안')
        st.caption('현재 분석 방식: '+analysis.mode+' · 초안 생성도 같은 방식으로 수행합니다.')
        todo=[r for r in analysis.results if r.has_gap or r.review_status==RS.EXPERT]
        with st.expander('TO DO · 항목별 작업 목록',expanded=True):
            for r in todo:
                st.markdown('**'+r.requirement_id+' · '+r.requirement_title+'**')
                for action in r.next_actions:st.write('• '+action)
        ids=[r.requirement_id for r in (todo or analysis.results)]
        rid=st.selectbox('보완할 Requirement',ids,format_func=lambda x:x+' · '+REQ_BY_ID[x].requirement_title,key='prepare_req')
        row=next(r for r in analysis.results if r.requirement_id==rid);req=REQ_BY_ID[rid]
        left,right=st.columns(2)
        with left:
            st.markdown('#### 현재 확인할 근거')
            show_evidence(row,analysis)
            st.markdown('#### 부족한 정보')
            missing=[f for f in req.fields if f.key in row.missing_information]
            if missing:
                for f in missing:st.write('• '+f.label)
            elif row.has_gap:st.write('모델·설계 버전·자료 충분성의 확인이 필요합니다.')
            else:st.write('문서 필드의 누락은 탐지되지 않았습니다. 기술적 충분성은 별도 검토입니다.')
        with right:
            st.markdown('#### 담당자에게 확인한 답변')
            answers={}
            for f in req.fields:
                answers[f.key]=st.text_area(f.question,key=f'answer_{analysis.analysis_id}_{rid}_{f.key}',max_chars=2000,height=90)
            ack=st.checkbox('인용 원문과 입력값의 사실관계를 확인했습니다.',key=f'ack_{analysis.analysis_id}_{rid}')
            signature=json.dumps([analysis.analysis_id,rid,answers,ack],ensure_ascii=False,sort_keys=True)
            if st.button('확인된 정보로 보완 초안 생성',type='primary'):
                try:
                    with st.spinner('확인된 사실로 초안을 구성하는 중...'):
                        draft=prepare(row,answers,ack,mode=analysis.mode,api_key=api_key,model=analysis.model)
                    st.session_state.draft=(signature,draft)
                except AnalysisError as exc:st.error(str(exc))
            saved=st.session_state.get('draft')
            if saved and saved[0]==signature:
                draft=saved[1]
                st.text_area('문서 보완 초안',draft['text'],height=280,disabled=True)
                st.caption('입력한 값만 정리한 초안입니다. Gap은 자동 해소되지 않습니다. 담당자 검토 후 수정 문서를 RE-CHECK에 업로드하세요.')
                st.download_button('보완 초안 TXT 다운로드',draft['text'],file_name=f'{rid}_draft.txt')
                st.download_button('재업로드용 보완 PDF 다운로드',draft_pdf(analysis.project,draft),file_name=f'BC100_Prepared_{rid}.pdf',mime='application/pdf')

with tab_recheck:
    if not analysis:st.info('최초 분석 후 수정된 PDF를 업로드하세요.')
    else:
        st.subheader('변경 후에도 근거가 유효한가요?')
        st.caption('현재 분석 방식 '+analysis.mode+'를 유지합니다. 다른 방식으로 비교하려면 새 프로젝트 분석을 시작하세요.')
        current_files=st.session_state.files
        with st.form('recheck_form'):
            remove=st.multiselect('교체하거나 제외할 기존 파일',options=[n for n,_ in current_files])
            updates=st.file_uploader('수정·추가 PDF 업로드',type=['pdf'],accept_multiple_files=True,key='updated_uploads',max_upload_size=5)
            st.caption('파일명이 다르면 기존 파일은 남습니다. 구버전을 교체할 때는 위에서 기존 파일을 제외하세요. 같은 파일명은 새 내용으로 교체됩니다.')
            recheck=st.form_submit_button('RE-CHECK · 변경 비교',type='primary')
        if recheck:
            try:
                if not updates and not remove:raise UploadError('수정 PDF를 업로드하거나 제외할 파일을 선택하세요.')
                files=merge_files(current_files,files_from_upload(updates),remove)
                docs=extract_documents(files)
                with st.spinner('변경된 문서 묶음을 재검토하는 중...'):
                    after=analyze(analysis.project,docs,mode=analysis.mode,api_key=api_key,model=analysis.model)
                previous=analysis.model_copy(deep=True)
                st.session_state.comparison=compare(previous,after)
                st.session_state.analysis=after;st.session_state.files=files
                st.session_state.history.append(after)
                st.session_state.history=st.session_state.history[-5:]
                st.session_state.pop('draft',None)
                st.rerun()
            except (UploadError,AnalysisError,ValueError) as exc:st.error(str(exc))
        changes=st.session_state.get('comparison')
        if changes:
            st.caption('직전 분석과 현재 분석의 비교입니다. “보완 후보”는 문서 Gap의 변화이며 최종 적합성이나 전문가 승인 의미가 아닙니다.')
            c1,c2,c3=st.columns(3)
            c1.metric('문서 Gap 보완 후보',sum(x['변화']=='문서 Gap 보완 후보' for x in changes))
            c2.metric('계속 보완 필요',sum(x['변화']=='계속 보완 필요' for x in changes))
            c3.metric('재검토 필요',sum(x['변화']=='재검토 필요' for x in changes))
            st.dataframe(changes,width='stretch',hide_index=True)
            st.download_button('Before / After JSON 다운로드',json.dumps(changes,ensure_ascii=False,indent=2),file_name='recheck-diff.json',mime='application/json')
            st.caption('재분석 시 사람의 확인 상태는 다시 확인 대기로 바뀝니다. 세션에는 최근 분석 5회가 유지되며 새로고침·세션 종료 시 사라질 수 있습니다.')
