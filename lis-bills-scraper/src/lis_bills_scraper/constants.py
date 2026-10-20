LIS_ENDPOINT = "https://lis.parliament.go.th/index/search_advance_detail.php"

BILLS_TYPE_SYSTEM_INDEX: dict[str, int] = {
    'ร่างพระราชบัญญัติ': 3,
    'ร่างพระราชบัญญัติงบประมาณรายจ่ายประจำปีงบประมาณ': 4,
    'พระราชกำหนด': 5,
}

BIll_TYPE_CLASS_INDEX: dict[str, str] = {
    'ร่างพระราชบัญญัติ': 'NORMAL_BILL',
    'ร่างพระราชบัญญัติงบประมาณรายจ่ายประจำปีงบประมาณ': 'BUDGET_BILL',
    'พระราชกำหนด': 'EMERGENCY_DECREE',
}

OFFSET_STEP = 50