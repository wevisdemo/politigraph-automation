from typing import Any
import re
from .scraper import scrape_bill_data
from .utilities import get_status_from_raw
from .events import (
    BillEvent, 
    BillVoteEvent, 
    BillMergeEvent,
    BillRoyalAssentEvent,
    BillEnactEvent,
    BillRejectEvent
)


class Bill():
    
    def __init__(
        self,
        title: str,
        acceptance_number: str,
        lis_id: int,
        url: str,
        status: str='IN_PROGRESS',
        status_text: str='อยู่ระหว่างการพิจารณา',
        classification: str='NORMAL_BILL',
    ) -> None:
        
        self.title = title
        self.acceptance_number = re.sub(r"\s+", "", acceptance_number)
        self.lis_id = lis_id
        self.url = url
        self.classification = classification
        
        self.status = status
        self.status_raw = status_text
        
        # General info
        self.parliament_term = None
        self.creator_type = None
        self.proposer_name = None
        self.prime_minister_name = None
        self.proposal_date = None
        self.recipient = None
        self.co_proposer = []
        
        # Events
        self.events: list[BillEvent] = []
        
        # Politigraph info
        self.id = None
        
    def get_lis_status(self) -> str:
        return get_status_from_raw(self.status_raw)
        
    def get_parliament_term(self) -> int:
        if self.parliament_term is None:
            self.scrape_events()
        return self.parliament_term # type: ignore
    
    def get_proposer_name(self) -> str:
        if self.proposer_name is None:
            self.scrape_events()
        return self.proposer_name # type: ignore
        
    def get_prime_minister_name(self) -> str:
        if self.prime_minister_name is None:
            self.scrape_events()
        return self.prime_minister_name # type: ignore
        
    def scrape_events(self) -> None:
        
        # Scrape bill event data
        events_data = scrape_bill_data(url=self.url)
        
        # Get general info
        general_info = next(
            (ev for ev in events_data if ev.get('event_type', '') == 'GENERAL_INFO'),
            None
        )
        if general_info:
            self.parliament_term = general_info.get('parliament_term', None)
            self.creator_type = general_info.get('creator_type', None)
            self.proposer_name = general_info.get('proposer', None)
            self.prime_minister_name = general_info.get('prime_minister', None)
            self.proposal_date = general_info.get('proposal_date', None)
            self.recipient = general_info.get('recipient', None)
            
            # print(self.parliament_term)
            # print(self.creator_type)
            # print(self.proposer_name)
            # print(self.prime_minister_name)
            # print(self.proposal_date)
            # print(self.recipient)
            
        # Get co-proposer
        co_proposer_info = next(
            (ev for ev in events_data if ev.get('event_type', '') == 'CO_PROPOSER'),
            None
        )
        if co_proposer_info:
            self.co_proposer = co_proposer_info.get('co_proposer', [])
            
        _added_events: list[tuple[str, str|None]] = []
        for event in events_data[::-1]: # reverse so newest event go first
            event_type = event.get('event_type')
            classification = event.get('classification')
            if (event_type, classification) not in _added_events:
                match event_type:
                    case 'VOTE_EVENT':
                        self.events.append(BillVoteEvent(event))
                        _added_events.append((event_type, classification))
                    case 'MERGE':
                        self.events.append(BillMergeEvent(event))
                        _added_events.append((event_type, None))
                    case 'ROYAL_ASSENT':
                        self.events.append(BillRoyalAssentEvent(event))
                        _added_events.append((event_type, None))
                    case 'ENACT':
                        self.events.append(BillEnactEvent(event))
                        _added_events.append((event_type, None))
                    case 'REJECT':
                        self.events.append(BillRejectEvent(event))
                        _added_events.append((event_type, None))
            
    def to_dict(self) -> dict[str, Any]:
        
        bill_dict = {
            "id": self.id,
            "title": self.title,
            "acceptance_number": self.acceptance_number,
            "lis_id": self.lis_id,
            "proposer_name": self.proposer_name,
            "proposal_date": self.proposal_date,
            "classification": self.classification,
            "status": self.status,
            "events": [
                event.to_dict() for event in self.events
            ],
        }
        
        return bill_dict
    