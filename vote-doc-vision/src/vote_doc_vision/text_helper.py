def is_overlapping(start1, end1, start2, end2):
    return start1 <= end2 and start2 <= end1

def combine_texts_group(detected_texts_group: list[dict], max_horizontal_gap: int = 30) -> list[dict]:
    if not detected_texts_group:
        return []

    # 1. Sort and group into rows securely FIRST
    unassigned = sorted(detected_texts_group, key=lambda x: (x['bbox'][1], x['bbox'][0]))
    rows = []

    while unassigned:
        seed = unassigned.pop(0)
        min_y = seed['bbox'][1]
        max_y = seed['bbox'][3]

        current_row = [seed]
        remaining_bboxes = []

        for bbox in unassigned:
            cy = (bbox['bbox'][1] + bbox['bbox'][3]) / 2

            # Lock word to this row if its center Y falls within the seed's Y range
            if min_y <= cy <= max_y:
                current_row.append(bbox)
            else:
                remaining_bboxes.append(bbox)

        unassigned = remaining_bboxes

        # Sort the completed row horizontally (left to right)
        current_row.sort(key=lambda x: x['bbox'][0])
        rows.append(current_row)

    # 2. Merge words horizontally within their strictly confined rows
    combined_data = []

    for row in rows:
        if not row:
            continue

        merged_row = []

        # Take the first word in the row as our starting block
        # We copy it so we don't accidentally mutate the original data
        current_box = {
            'text': row[0]['text'],
            'bbox': list(row[0]['bbox'])
        }

        for next_box in row[1:]:
            # Calculate horizontal gap (next word's left edge MINUS current word's right edge)
            # Note: If words overlap horizontally, the gap is negative, which is correctly < max_gap
            gap = next_box['bbox'][0] - current_box['bbox'][2]

            if gap <= max_horizontal_gap:
                # Merge the text (I added a space here, remove the +" " if you want them strictly touching)
                current_box['text'] += " " + next_box['text']

                # Expand the bounding box horizontally and vertically (but only for this line's heights)
                current_box['bbox'] = [
                    min(current_box['bbox'][0], next_box['bbox'][0]),
                    min(current_box['bbox'][1], next_box['bbox'][1]),
                    max(current_box['bbox'][2], next_box['bbox'][2]),
                    max(current_box['bbox'][3], next_box['bbox'][3])
                ]
            else:
                # The gap is too large! Save the current box and start a new one
                merged_row.append(current_box)
                current_box = {
                    'text': next_box['text'],
                    'bbox': list(next_box['bbox'])
                }

        # Append the final box of the row
        merged_row.append(current_box)

        # Throw the securely merged row into our final flat list
        combined_data.extend(merged_row)

    return combined_data

def combine_text_in_bboxes(items: list[dict], line_sep: str = "\n", word_sep: str = " ") -> str:
    if not items:
        return ""

    # Sort roughly by top coordinate first
    sorted_items = sorted(items, key=lambda x: (x["bbox"][1], x["bbox"][0]))

    lines = []
    for item in sorted_items:
        _, y1, _, y2 = item["bbox"]
        height = max(1, y2 - y1)

        # Check vertical overlap with existing lines
        matched = False
        for line in lines:
            line_y1 = min(b["bbox"][1] for b in line)
            line_y2 = max(b["bbox"][3] for b in line)
            overlap = max(0, min(y2, line_y2) - max(y1, line_y1))

            # Group together if vertical overlap is significant
            if overlap >= 0.5 * min(height, line_y2 - line_y1):
                line.append(item)
                matched = True
                break

        if not matched:
            lines.append([item])

    # Sort lines vertically, and items within each line horizontally
    lines.sort(key=lambda line: min(b["bbox"][1] for b in line))

    result = [
        word_sep.join(b["text"] for b in sorted(line, key=lambda b: b["bbox"][0]))
        for line in lines
    ]

    return line_sep.join(result)
