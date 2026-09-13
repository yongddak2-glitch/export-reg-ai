"""Actual SDK parsing over a fake HTTP transport, not a live model test."""
import json
import httpx2 as httpx
import pytest
from openai import OpenAI
import ai_engine
from models import Project
from pdf_utils import extract_documents

def client_for(payload,requests):
    def handler(request):
        requests.append(json.loads(request.content))
        response={'id':'resp_fixture','object':'response','created_at':1,'status':'completed','model':'gpt-4.1-mini',
                  'output':[{'id':'msg_fixture','type':'message','status':'completed','role':'assistant',
                             'content':[{'type':'output_text','text':json.dumps(payload),'annotations':[]}]}]}
        return httpx.Response(200,json=response)
    return OpenAI(api_key='test-key-not-a-real-secret',http_client=httpx.Client(transport=httpx.MockTransport(handler)))

def test_real_sdk_structured_parse(monkeypatch,files):
    docs=extract_documents(files);payload=ai_engine._mock_matches(docs).model_dump(mode='json');requests=[]
    client=client_for(payload,requests);monkeypatch.setattr(ai_engine,'_client',lambda key:client)
    result=ai_engine.analyze(Project(),docs,mode='openai',api_key='test')
    assert len(result.results)==12 and result.mode=='openai'
    request=requests[0]
    assert request['store'] is False
    assert request['text']['format']['type']=='json_schema'
    assert request['text']['format']['strict'] is True
    assert len(json.loads(request['input'][1]['content'])['documents'])==6
    client.close()

def test_api_failure_never_silently_mock(monkeypatch,files):
    class Failing:
        @property
        def responses(self):raise RuntimeError('private provider details')
    monkeypatch.setattr(ai_engine,'_client',lambda key:Failing())
    with pytest.raises(ai_engine.AnalysisError) as error:
        ai_engine.analyze(Project(),extract_documents(files),mode='openai',api_key='test')
    assert 'private provider details' not in str(error.value)

def test_prepare_uses_only_supplied_fact_ids(monkeypatch,files):
    result=ai_engine.analyze(Project(),extract_documents(files)).results[0]
    requests=[];client=client_for({'ordered_fact_ids':['E1','U-maintenance_interval']},requests)
    monkeypatch.setattr(ai_engine,'_client',lambda key:client)
    draft=ai_engine.prepare(result,{'maintenance_interval':'30 days'},True,mode='openai',api_key='test')
    assert {f['value'] for f in draft['facts']}=={result.evidence[0].excerpt,'30 days'}
    client.close()
