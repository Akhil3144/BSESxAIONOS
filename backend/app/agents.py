"""One coordinated negotiation agent. Financial authority stays in the engine."""
from .engine import benchmark, digest
from .ai import DeterministicExplanation, validate_narrative, configured_provider

class NegotiationIntelligenceAgent:
    def __init__(self,narrative_provider=None):
        self.narrative_provider=narrative_provider or configured_provider()
    def analyze(self,quote,reference_rows,supplier_records,rule=None):
        result=benchmark(quote,reference_rows,rule)
        result['supplier_context']=[r for r in supplier_records if r['supplier']==quote['supplier']]
        # Default contract accepts only exact engine explanation and existing sources.
        # No confidential content is transmitted by the default adapter.
        try:
            result['narrative']=validate_narrative(self.narrative_provider.explain(result),result).model_dump()
        except Exception:
            result['narrative']=DeterministicExplanation().explain(result).model_dump()
            result['narrative']['provider_status']='deterministic fallback; optional provider unavailable or rejected'
            result['narrative_status']='unavailable; numerical benchmark remains valid'
        if result['narrative'].get('strategy_codes'):result['narrative_status']=result['narrative']['provider_status']
        result['fingerprint']=digest({k:v for k,v in result.items() if k!='fingerprint'})
        return result
