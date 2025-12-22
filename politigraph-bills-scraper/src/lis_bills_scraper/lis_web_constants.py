from typing import Dict

LIS_ENDPOINT = "https://lis.parliament.go.th/index/search_advance_detail.php"

BILLS_TYPE_SYSTEM_INDEX: Dict[str, int] = {
    'ร่างพระราชบัญญัติ': 3,
    'ร่างพระราชบัญญัติงบประมาณรายจ่ายประจำปีงบประมาณ': 4,
    'พระราชกำหนด': 5,
}

BIll_TYPE_CLASS_INDEX: Dict[str, str] = {
    'ร่างพระราชบัญญัติ': 'NORMAL_BILL',
    'ร่างพระราชบัญญัติงบประมาณรายจ่ายประจำปีงบประมาณ': 'BUDGET_BILL',
    'พระราชกำหนด': 'EMERGENCY_DECREE',
}

BILL_EVENT_TYPENAME_INDEX = {
    'MERGE': 'BillMergeEvent',
    'ROYAL_ASSENT': 'BillRoyalAssentEvent',
    'REJECT': 'BillRejectEvent',
    'ENACT': 'BillEnactEvent',
    'VOTE_EVENT_MP_1': 'BillVoteEvent',
    'VOTE_EVENT_MP_2': 'BillVoteEvent',
    'VOTE_EVENT_MP_3': 'BillVoteEvent',
    'VOTE_EVENT_SENATE_1': 'BillVoteEvent',
    'VOTE_EVENT_SENATE_3': 'BillVoteEvent',
}

OFFSET_STEP = 50