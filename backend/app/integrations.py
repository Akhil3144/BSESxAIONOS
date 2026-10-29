"""Provider-neutral contract. No undocumented URLs or implicit paid access."""
from dataclasses import dataclass
from typing import Protocol
from datetime import datetime, timezone

@dataclass(frozen=True)
class SourceObservation:
    source_id:str
    effective_date:str
    retrieved_at:str
    payload:dict
    synthetic:bool
class Provider(Protocol):
    def retrieve(self, query:dict)->list[SourceObservation]: ...
class DisabledProvider:
    def __init__(self,name): self.name=name
    def retrieve(self,query): raise PermissionError(f'{self.name}: disabled; licensed entitlement, approved scope and tested authentication required')
class FixtureProvider:
    """Test-only provider; never registered as a live data source."""
    def __init__(self,fixture): self.fixture=fixture
    def retrieve(self,query):
        return [SourceObservation('DEMO-FIXTURE',self.fixture['effective_date'],datetime.now(timezone.utc).isoformat(),self.fixture,True)]
