"""LLM matching + source validation. Mock mode is a disclosed rule-based fixture runner."""
import json
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from models import (Analysis, DraftPlan, Evidence, EvidenceStatus as ES, Match,
                    MatchBatch, Requirement, Result, ReviewStatus as RS)
from pdf_utils import normalize
from prompts import CHECK_SYSTEM, PREPARE_SYSTEM

ROOT = Path(__file__).parent
DATASET = json.loads((ROOT / 'requirements.json').read_text(encoding='utf-8'))
REQUIREMENTS = [Requirement.model_validate(x) for x in DATASET['requirements']]
REQ_BY_ID = {r.requirement_id: r for r in REQUIREMENTS}

# Only the disclosed mock uses labels. Actual OpenAI mode sends all pages for semantic comparison.
MOCK_LABELS = {
    'maintenance_interval': 'Maintenance interval', 'maintenance_precautions': 'Maintenance precautions',
    'manufacturer': 'Manufacturer', 'product_identity': 'Product identity', 'intended_use': 'Intended use',
    'use_limits': 'Use limits', 'installation': 'Installation', 'controls': 'Controls',
    'test_scope': 'Test scope', 'drawing_configuration': 'Drawing configuration', 'handling': 'Handling',
    'guarding': 'Guarding', 'noise': 'Noise', 'revision_history': 'Revision history',
    'residual_risks': 'Residual risks',
}
FORBIDDEN = re.compile(r'\b(?:COMPLIANT|PASSED|CE\s+APPROVED)\b|규제\s*충족|인증\s*완료|적합\s*판정', re.I)

class AnalysisError(ValueError):
    pass

def _now():
    return datetime.now(timezone.utc).isoformat()

def _client(api_key):
    if not api_key or not api_key.strip():
        raise AnalysisError('OpenAI API 키가 없습니다. Mock 모드를 선택하거나 서버 Secrets에 키를 설정하세요.')
    try:
        from openai import OpenAI
        return OpenAI(api_key=api_key, timeout=90, max_retries=1)
    except Exception as exc:
        raise AnalysisError('API 클라이언트를 초기화하지 못했습니다. 설치 상태와 프록시 설정을 확인하세요.') from exc

def _parse(client, model, system, payload, schema):
    try:
        response = client.responses.parse(
            model=model, store=False, max_output_tokens=12000,
            input=[{'role':'system','content':system},
                   {'role':'user','content':json.dumps(payload, ensure_ascii=False)}],
            text_format=schema,
        )
        if response.output_parsed is None:
            raise AnalysisError('AI가 답변을 거절했거나 응답이 완성되지 않았습니다. 결과를 저장하지 않았습니다.')
        return response.output_parsed
    except AnalysisError:
        raise
    except Exception as exc:
        # Do not put API keys, uploaded text or raw provider error bodies in UI/logs.
        raise AnalysisError('API 분석을 완료하지 못했습니다. 키·사용한도·모델 접근권·네트워크를 확인하세요. '
                            '자동으로 Mock 결과로 바꾸지 않습니다.') from exc

def _mock_matches(documents):
    matches = []
    for req in REQUIREMENTS:
        evidence, missing = [], []
        for field in req.fields:
            found = []
            label = MOCK_LABELS[field.key]
            for doc in documents:
                for p in doc.pages:
                    for line in p.text.splitlines():
                        if line.startswith(label + ':') and line.split(':', 1)[1].strip() not in ('', 'TBD', 'Not specified'):
                            found.append(Evidence(document=doc.name, page=p.number, excerpt=line,
                                                  reason='Mock: 합성자료의 명시적 필드 값을 연결했습니다. 의미 매칭 성능의 증거가 아닙니다.',
                                                  field_key=field.key))
            evidence.extend(found[:4])
            if not found:
                missing.append(field.key)
        unreadable_noise = req.requirement_id == 'REQ-10' and any(
            'noise' in d.name.lower() and any(p.unreadable for p in d.pages) for d in documents)
        status = ES.UNREADABLE if unreadable_noise and not evidence else (
            ES.NOT_FOUND if not evidence else ES.INSUFFICIENT if missing else ES.FOUND)
        matches.append(Match(requirement_id=req.requirement_id,evidence=evidence,evidence_status=status,
                             review_status=RS.EXPERT if req.expert_required else RS.HUMAN,
                             issue='업로드 자료에서 확인되지 않은 정보가 있습니다.' if missing else '',
                             missing_information=missing,
                             next_actions=[f'{f.label}: 담당자에게 확인 후 관련 문서를 보완하세요.' for f in req.fields if f.key in missing]
                             or ['연결된 원문과 대상 모델을 확인하세요.']))
    return MatchBatch(results=matches)

def validate_matches(batch, documents, project):
    ids = [m.requirement_id for m in batch.results]
    if len(ids) != len(REQUIREMENTS) or set(ids) != set(REQ_BY_ID):
        raise AnalysisError('응답의 요구사항 ID가 누락·중복·변경되었습니다. 분석 결과를 저장하지 않았습니다.')
    doc_map = {d.name:d for d in documents}
    results = []
    for m in batch.results:
        req = REQ_BY_ID[m.requirement_id]
        keys = {f.key for f in req.fields}
        if set(m.missing_information) - keys:
            raise AnalysisError('AI가 범위 밖의 정보 필드를 반환했습니다. 다시 분석해주세요.')
        safe, notes = [], []
        if len(m.evidence) > 8:
            raise AnalysisError('근거 수가 고정 범위를 초과했습니다.')
        for e in m.evidence:
            d = doc_map.get(e.document)
            page = next((p for p in d.pages if p.number == e.page), None) if d else None
            if (e.field_key not in keys or not page or len(normalize(e.excerpt)) < 8
                    or normalize(e.excerpt) not in normalize(page.text)):
                notes.append('원문·페이지·필드 검증에 실패한 인용을 제외했습니다. 원문을 직접 확인하세요.')
            elif e not in safe:
                safe.append(e)
        missing = set(m.missing_information) | (keys - {e.field_key for e in safe})
        status = m.evidence_status
        cited_docs = [doc_map[e.document] for e in safe]
        model_mismatch = any(d.model and normalize(d.model).upper() != normalize(project.model).upper() for d in cited_docs)
        version_mismatch = any(d.design_revision and normalize(d.design_revision).upper() != normalize(project.design_revision).upper() for d in cited_docs)
        issue = m.issue.strip()
        if model_mismatch:
            status, issue = ES.MODEL, '관련 자료의 명시적 모델이 프로젝트 모델과 다릅니다. 대상 모델의 자료가 필요합니다.'
        elif version_mismatch:
            status, issue = ES.VERSION, '관련 자료의 설계 버전이 프로젝트와 다릅니다. 현재 버전의 근거를 확인하세요.'
        elif notes:
            status, issue = ES.INSUFFICIENT, '일부 AI 인용의 출처를 검증할 수 없어 확인을 보류했습니다.'
        elif not safe:
            if status != ES.UNREADABLE or not any(p.unreadable for d in documents for p in d.pages):
                status = ES.NOT_FOUND
            issue = '관련 PDF를 판독할 수 없습니다. 텍스트가 있는 자료를 요청하세요.' if status == ES.UNREADABLE else '업로드한 자료에서 관련 근거를 찾지 못했습니다. 실제 자료가 없다는 뜻은 아닙니다.'
        elif missing and status == ES.FOUND:
            status = ES.INSUFFICIENT
        elif status == ES.NOT_FOUND:
            status = ES.INSUFFICIENT
        # Uncertain AI mismatch is retained; its absence is not proof of identity.
        if any(not d.model or not d.design_revision for d in cited_docs):
            notes.append('일부 문서의 명시적 모델·설계 버전 메타데이터가 없습니다. 사람 확인이 필요합니다.')
        review = RS.EXPERT if req.expert_required or m.review_status == RS.EXPERT else RS.HUMAN
        actions = list(m.next_actions)
        if status == ES.MODEL:
            actions.insert(0, f'{project.model} 대상 자료를 담당자에게 요청하고 시험조건을 전문가에게 확인하세요.')
        if status == ES.VERSION:
            actions.insert(0, f'현재 설계 버전 {project.design_revision}의 자료를 요청하세요.')
        if review == RS.EXPERT:
            actions.append('전문가에게 관련 근거의 기술적 충분성과 추가 검토 필요 여부를 확인하세요.')
            if not issue:
                issue = '관련 문장은 있으나 기술적 충분성은 판단하지 않았습니다.'
        if missing and not issue:
            issue = '일부 필수 정보가 업로드 자료에서 확인되지 않았습니다.'
        # Free-form generated text must not contain approval conclusions.
        generated = ' '.join([issue, *actions, *[e.reason for e in safe]])
        if FORBIDDEN.search(generated):
            raise AnalysisError('허용되지 않은 최종 판단 표현이 감지되어 결과를 저장하지 않았습니다.')
        results.append(Result(**m.model_dump(exclude={'evidence','evidence_status','review_status','issue','missing_information','next_actions'}),
                              evidence=safe,evidence_status=status,review_status=review,issue=issue,
                              missing_information=sorted(missing), next_actions=list(dict.fromkeys(actions)),
                              requirement_title=req.requirement_title,requirement_description=req.requirement_description,
                              regulation_reference=req.regulation_reference,source_url=req.source_url,validation_notes=notes))
    return sorted(results, key=lambda r:r.requirement_id)

def analyze(project, documents, mode='mock', api_key='', model='gpt-4.1-mini'):
    start = time.perf_counter()
    if project.market != 'EU' or not project.launch_date.startswith('2026-'):
        raise AnalysisError('이 PoC는 2026년 EU 출시의 사전 확정 범위만 지원합니다.')
    if not documents:
        raise AnalysisError('분석할 문서가 없습니다.')
    if mode == 'mock':
        raw = _mock_matches(documents)
    elif mode == 'openai':
        payload = {'project':project.model_dump(), 'requirements':[r.model_dump() for r in REQUIREMENTS],
                   'documents':[d.model_dump() for d in documents]}
        raw = _parse(_client(api_key),model,CHECK_SYSTEM,payload,MatchBatch)
    else:
        raise AnalysisError('알 수 없는 분석 모드입니다.')
    results = validate_matches(raw,documents,project)
    warnings = [f'{d.name} p.{p.number}: 텍스트 판독 불가(OCR 미지원)' for d in documents for p in d.pages if p.unreadable]
    return Analysis(analysis_id=str(uuid.uuid4()),created_at=_now(),mode=mode,model=model if mode=='openai' else 'mock-rules-v1',
                    project=project,dataset_version=DATASET['dataset_version'],documents=documents,results=results,
                    duration_seconds=round(time.perf_counter()-start,3),warnings=warnings)

def prepare(result, answers, confirmed, mode='mock', api_key='', model='gpt-4.1-mini'):
    if not confirmed:
        raise AnalysisError('인용과 입력한 값의 사실관계를 먼저 확인해주세요.')
    req = REQ_BY_ID[result.requirement_id]
    allowed_keys = {f.key for f in req.fields}
    if set(answers)-allowed_keys:
        raise AnalysisError('범위 밖의 답변 필드입니다.')
    facts = []
    if result.evidence_status not in (ES.MODEL, ES.VERSION, ES.UNREADABLE):
        for e in result.evidence:
            facts.append({'id':f'E{len(facts)+1}','field_key':e.field_key,'value':e.excerpt,
                          'source':f'{e.document} p.{e.page} · 사용자 원문 확인'})
    for key,value in answers.items():
        value = value.strip()
        if value:
            if len(value)>2000 or FORBIDDEN.search(value):
                raise AnalysisError('답변은 2,000자 이내의 제품 사실로 입력하세요. 최종 적합성 결론은 입력할 수 없습니다.')
            facts = [f for f in facts if f['field_key'] != key]
            facts.append({'id':f'U-{key}','field_key':key,'value':value,'source':'사용자 제공·확인 ('+_now()+')'})
    if not facts:
        raise AnalysisError('확인된 사실이 없습니다. 질문에 답변을 입력해주세요.')
    ids = [f['id'] for f in facts]
    if mode == 'openai':
        plan = _parse(_client(api_key), model, PREPARE_SYSTEM, {'requirement':req.model_dump(), 'facts':facts}, DraftPlan)
        if len(plan.ordered_fact_ids)!=len(ids) or set(plan.ordered_fact_ids)!=set(ids):
            raise AnalysisError('초안의 사실 참조가 잘못되었습니다. 초안을 저장하지 않았습니다.')
        facts = sorted(facts,key=lambda f:plan.ordered_fact_ids.index(f['id']))
    elif mode != 'mock':
        raise AnalysisError('알 수 없는 모드입니다.')
    labels = {f.key:f.label for f in req.fields}
    lines=[f'{req.requirement_id} {req.requirement_title} — 문서 보완 초안',
           '사용자 확인 사실만 정리한 검토용 초안입니다. 적용 전 담당자 검토가 필요합니다.','']
    for f in facts:
        lines.extend([f"{labels[f['field_key']]}: {f['value']}",f"출처: {f['source']}",''])
    remaining=[f.question for f in req.fields if f.key not in {x['field_key'] for x in facts}]
    if remaining:
        lines += ['추가 확인 질문']+remaining
    return {'text':'\n'.join(lines),'facts':facts,'remaining_questions':remaining,'created_at':_now(),
            'mode':mode,'requirement_id':req.requirement_id}

def _evidence_signature(result, analysis):
    hashes={d.name:d.sha256 for d in analysis.documents}
    return sorted((e.document,hashes.get(e.document),e.page,e.excerpt,e.field_key) for e in result.evidence)

def compare(before, after):
    old={r.requirement_id:r for r in before.results}
    rows=[]
    for now in after.results:
        prev=old[now.requirement_id]
        changed=_evidence_signature(prev,before)!=_evidence_signature(now,after)
        if prev.has_gap and not now.has_gap:
            change='문서 Gap 보완 후보'
        elif (not prev.has_gap and now.has_gap) or (changed and not prev.has_gap):
            change='재검토 필요'
        elif now.has_gap:
            change='계속 보완 필요'
        elif changed or prev.review_status!=now.review_status:
            change='재검토 필요'
        else:
            change='변화 없음'
        rows.append({'Requirement':now.requirement_id+' '+now.requirement_title,
                     'Before':prev.evidence_status.value,'After':now.evidence_status.value,
                     '이전 검토':prev.review_status.value,'현재 검토':now.review_status.value,
                     '변화':change,'근거 변경':changed,'다음 행동':' / '.join(now.next_actions)})
    return rows
