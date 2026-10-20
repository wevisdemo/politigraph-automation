from typing import Any

class PrettyType(type):
    def __repr__(self):
        return self.__name__

class BillEvent(metaclass=PrettyType):
    
    classification: str | None = None
    date:  str | None = None
    
    def to_dict(self) -> dict[str, Any]:
        return {}

class BillVoteEvent(BillEvent):
    
    def __init__(
        self,
        vote_event_data: dict[str, Any]
    ) -> None:
        
        # Main info
        self.classification = vote_event_data.get('classification')
        self.date = vote_event_data.get('date')
        self.result = vote_event_data.get('result')
        
        # Session info
        self.msbis_id = vote_event_data.get('msbis_id')
        self.parliament_term = vote_event_data.get('parliament_term')
        self.session_year = vote_event_data.get('session_year')
        self.session_number = vote_event_data.get('session_number')
        self.session_type = vote_event_data.get('session_type')
        
        # Links
        self.links = vote_event_data.get('links', [])
        
        vote_count = vote_event_data.get('vote_count', vote_event_data)
        # Vote count
        self.agree_count = vote_count.get('agree_count', -1)
        self.disagree_count = vote_count.get('disagree_count', -1)
        self.abstain_count = vote_count.get('abstain_count', -1)
        self.novote_count = vote_count.get('novote_count', -1)
        
    def to_dict(self) -> dict[str, Any]:
        
        vote_event_dict = {
            "id": None,
            "classification": self.classification,
            "msbis_id": self.msbis_id,
            "start_date": self.date,
            "result": self.result,
            "agree_count": self.agree_count,
            "disagree_count": self.disagree_count,
            "abstain_count": self.abstain_count,
            "novote_count": self.novote_count,
        }
        
        return vote_event_dict
    
class BillMergeEvent(BillEvent):
    
    merged_bills: list[dict[str, str]] = []
    
    def __init__(
        self,
        merge_event_data: dict[str, Any]
    ) -> None:
        
        self.merged_bills = merge_event_data.get('merged_bills', [])
        self.total_merged_bills = merge_event_data.get('total_merged_bills')
        
    def to_dict(self) -> dict[str, Any]:
            
        merge_event_dict = {
            "id": None,
            "merged_bills": self.merged_bills,
            "total_merged_bills": self.total_merged_bills,
        }
        
        return merge_event_dict
    
class BillRoyalAssentEvent(BillEvent):
    
    def __init__(
        self,
        royal_assent_event_data: dict[str, Any]
    ) -> None:
        
        self.result = royal_assent_event_data.get('result')
    
    def to_dict(self) -> dict[str, Any]:
                
        royal_assent_event_dict = {
            "id": None,
            "result": self.result
        }
        
        return royal_assent_event_dict
    
class BillEnactEvent(BillEvent):
    
    def __init__(
        self,
        enact_event_data: dict[str, Any]
    ) -> None:
        
        self.title = enact_event_data.get('title')
        self.date = enact_event_data.get('start_date')
        self.announcement_report_link = enact_event_data.get('announcement_report_link')
        
    def to_dict(self) -> dict[str, Any]:
            
        enact_event_dict = {
            "id": None,
            "title": self.title,
            "start_date": self.date,
            "end_date": self.date,
            "announcement_report_link": self.announcement_report_link,
        }
        
        return enact_event_dict
    
class BillRejectEvent(BillEvent):
    
    def __init__(
        self,
        reject_event_data: dict[str, Any]
    ) -> None:
        
        self.reject_reason = reject_event_data.get('reject_reason')
    
    def to_dict(self) -> dict[str, Any]:
                
        reject_event_dict = {
            "id": None,
            "reject_reason": self.reject_reason
        }
        
        return reject_event_dict
    