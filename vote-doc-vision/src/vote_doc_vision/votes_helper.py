import re
from typing import Any

from .utilities import correct_typo


def extract_votes_data(bbox_data: list[dict[str, Any]]) -> list[dict[str, str]]:
    if not bbox_data:
        return []

    # 1. Group items into rows using the Top-Left Bounding Box method
    unassigned = bbox_data.copy()
    rows = []

    while unassigned:
        # Sort remaining boxes by y1 (top-to-bottom), then by x1 (left-to-right)
        unassigned.sort(key=lambda x: (x['bbox'][1], x['bbox'][0]))

        # Pick the top-left bbox as the "seed" for this row
        seed = unassigned.pop(0)
        min_y = seed['bbox'][1]
        max_y = seed['bbox'][3]

        current_row = [seed]
        remaining_bboxes = []

        # Scan EVERY other unassigned bbox
        for bbox in unassigned:
            cy = (bbox['bbox'][1] + bbox['bbox'][3]) / 2

            # If the center Y falls within the seed's Y range, it belongs to this row
            if min_y <= cy <= max_y:
                current_row.append(bbox)
            else:
                remaining_bboxes.append(bbox)

        unassigned = remaining_bboxes

        # Sort the completed row from left to right
        current_row.sort(key=lambda x: x['bbox'][0])
        rows.append(current_row)

    # 2. Determine global column gaps by curating rows with exactly 5 columns
    x_centers = []
    for row in rows:
        if len(row) == 5:
            for item in row:
                x_centers.append((item['bbox'][0] + item['bbox'][2]) / 2)

    # Fallback: if no perfect 5-column rows exist, try using rows with 4+ items
    if not x_centers:
        for row in rows:
            if len(row) >= 4:
                for item in row:
                    x_centers.append((item['bbox'][0] + item['bbox'][2]) / 2)

    x_centers.sort()
    boundaries = []

    if len(x_centers) > 4:
        # Calculate distances between adjacent x-centers
        gaps = [(x_centers[i+1] - x_centers[i], i) for i in range(len(x_centers)-1)]
        # Sort by gap width descending
        gaps.sort(reverse=True, key=lambda x: x[0])

        # The top 4 largest horizontal gaps are the walls separating our 5 columns
        top_4_gaps = gaps[:4]
        boundaries = sorted([(x_centers[idx] + x_centers[idx+1]) / 2 for gap, idx in top_4_gaps])

    def get_column_index(item: dict[str, Any]) -> int:
        if not boundaries:
            return 0
        xc = (item['bbox'][0] + item['bbox'][2]) / 2
        for i, boundary in enumerate(boundaries):
            if xc < boundary:
                return i
        return len(boundaries)

    # 3. Construct dictionaries by assigning items to the determined columns
    structured_data = []
    keys = ['order', 'member_num', 'voter_name', 'party_name', 'vote_option']

    for row in rows:
        # Ignore obvious noise rows (like page numbers or headers).
        # A valid table row should have at least a few columns of data.
        if len(row) < 3:
            continue

        # Create 5 empty "buckets" for the 5 columns
        mapped_cols = {0: [], 1: [], 2: [], 3: [], 4: []}

        # Throw every bounding box in this row into its respective bucket
        for item in row:
            col_idx = get_column_index(item)
            # Safety cap to ensure we don't exceed the 5th column (index 4)
            col_idx = min(col_idx, 4)
            mapped_cols[col_idx].append(item)

        row_dict = {}

        # Process each bucket
        for i in range(5):
            if mapped_cols[i]:
                # If there are items (e.g., 2 parts of a name), sort them left-to-right
                mapped_cols[i].sort(key=lambda x: x['bbox'][0])
                # Merge them with a space
                row_dict[keys[i]] = " ".join([x['text'] for x in mapped_cols[i]])
            else:
                # If the bucket is completely empty (missing column)
                row_dict[keys[i]] = "-"

        structured_data.append(row_dict)

    return structured_data

def clean_votes(votes: list[dict], full_text: str) -> list[dict]:

    texts_list = full_text.split("\n")

    for vote in votes:
        order = vote.get('order', '0')
        order = re.sub(r"\D", "", order)
        if re.search(r"^\d+$", order):
            vote['order'] = order
        else:
            vote['order'] = '0'

        member_num = vote.get('member_num', '0')
        vote['member_num'] = re.sub(r"\D", "", member_num)

        # Clean name
        voter_name = vote.get('voter_name', '')
        voter_name = re.sub(r"\d|\s", "", voter_name).strip()
        vote['voter_name'] = correct_typo(voter_name, texts_list)

    return sorted(votes, key=lambda v: v['order'])
