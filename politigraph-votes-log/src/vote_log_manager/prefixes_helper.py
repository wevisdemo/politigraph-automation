def get_thai_name_prefixes():
    prefixes = [
        "นาย", "นาง", "นางสาว", "ไนาย",
        "ดร.", "ศาสตราจารย์", "ศาสตราจารย์ ดร.", "ศ.ดร.",
        "รองศาสตราจารย์", "รศ.", "ผู้ช่วยศาสตราจารย์", "ผศ.",
        "รองศาสตราจารย์พิเศษ", "รศ.พิเศษ",
        "นายแพทย์", "นพ.", "แพทย์หญิง", "พญ."
    ]

    full_bases = [
        "พล", "พัน", "ร้อย", "จ่าสิบ", "สิบ", # Army
        "พลเรือ", "นาวา", "เรือ", "พันจ่า", "จ่า", # Navy
        "พลอากาศ", "นาวาอากาศ", "เรืออากาศ", "พันจ่าอากาศ", "จ่าอากาศ", # Air Force
        "พลตำรวจ", "พันตำรวจ", "ร้อยตำรวจ", "สิบตำรวจ" # Police
    ]
    
    abbr_bases = [
        "พล.", "พ.", "ร.", "จ.ส.", "ส.", # Army
        "พล.ร.", "น.", "พ.จ.", "จ.", # Navy (ร. shared with Army)
        "พล.อ.", "พ.อ.", # Air Force (น., ร., จ. shared)
        "พล.ต.", "พ.ต.", "ร.ต.", "ส.ต." # Police
    ]

    # Specific ranks that don't take เอก/โท/ตรี suffixes
    ranks = ["จ่าสิบตำรวจ", "จ.ส.ต."] 
    
    # Combine bases with rank levels
    ranks += [f"{b}{lvl}" for b in full_bases for lvl in ["เอก", "โท", "ตรี"]]
    ranks += [f"{b}{lvl}" for b in abbr_bases for lvl in ["อ.", "ท.", "ต."]]

    # Apply combinations for female and acting variants
    for rank in ranks:
        acting = "ว่าที่ " if "." in rank else "ว่าที่"
        
        prefixes.extend([
            rank,
            f"{rank}หญิง",
            f"{acting}{rank}",
            f"{acting}{rank}หญิง"
        ])

    # Remove overlaps (e.g. shared abbreviations across branches) while maintaining order
    return list(dict.fromkeys(prefixes))