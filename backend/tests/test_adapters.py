import pytest
from backend.app.integrations import DisabledProvider,FixtureProvider
from backend.app.ai import Narrative,DeterministicExplanation,validate_narrative
from backend.app.engine import benchmark
from backend.app.seed import sample

def test_disabled_source():
    with pytest.raises(PermissionError): DisabledProvider('Fastmarkets').retrieve({})
def test_fixture_is_explicit():
    source=FixtureProvider({'effective_date':'2025-01-01','value':'12'}).retrieve({})[0];assert source.synthetic;assert source.retrieved_at;assert source.source_id.startswith('DEMO')
def test_narrative_grounded():
    result=benchmark(sample(),[]);assert validate_narrative(DeterministicExplanation().explain(result),result)
    with pytest.raises(ValueError): validate_narrative(Narrative(explanation='Invented saving of 87%',evidence_ids=[],provider_status='unverified'),result)
    with pytest.raises(ValueError): validate_narrative(Narrative(explanation=result['explanation'],evidence_ids=['FAKE'],provider_status='unverified'),result)

def test_agent_provider_failure_preserves_numbers():
    from backend.app.agents import NegotiationIntelligenceAgent
    class Unavailable:
        def explain(self,result): raise ConnectionError('Provider unavailable')
    rows=[sample(f'SOURCE-{i}',str(400+i*10),'2024-01-01') for i in range(6)]
    b=NegotiationIntelligenceAgent(Unavailable()).analyze(sample(),rows,[])
    assert b['status']=='supported';assert b['target']=='425.00';assert b['narrative_status'].startswith('unavailable')
