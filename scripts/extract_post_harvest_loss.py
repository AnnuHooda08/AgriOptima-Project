"""Extract numeric state/crop/stage loss estimates from NABCONS 2022 Appendix 6.

The PDF has irregular tables. Ambiguous cells are omitted rather than guessed.
"""

import csv
import re
from collections import Counter, defaultdict
from pathlib import Path

import pdfplumber


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/raw/nabcons_post_harvest_loss_2022.pdf"
DEST = ROOT / "data/processed/post_harvest_loss_2022_state_stage.csv"

STATES = [
    "Andhra Pradesh", "Assam", "Andaman and Nicobar Islands", "Bihar",
    "Chhattisgarh", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
    "Jammu & Kashmir", "Karnataka", "Kerala", "Madhya Pradesh",
    "Maharashtra", "Meghalaya", "Nagaland", "Odisha", "Punjab",
    "Rajasthan", "Tamil Nadu", "Telangana", "Uttarakhand",
    "Uttar Pradesh", "West Bengal",
]


def number(cell):
    value = (cell or "").strip().replace("\n", " ")
    if not value or value.startswith(("±", "+/-", "-")):
        return None
    match = re.match(r"^(?:0|[1-9]\d*)(?:\.\d+)?", value)
    if not match:
        return None
    result = float(match.group())
    return result if 0 <= result <= 100 else None


def metric(header, col, count):
    offset = count - col
    fixed = {
        1: ("Total", "Overall total loss"),
        2: ("Market Operations", "Total loss in market operations"),
        3: ("Market Operations", "Transport"),
        4: ("Market Operations", "Processing unit"),
        5: ("Market Operations", "Retailers"),
        6: ("Market Operations", "Wholesalers"),
        7: ("Market Operations", "Godown"),
        8: ("Farm Operations", "Total loss in farm operations"),
    }
    if offset in fixed:
        return fixed[offset]
    h = re.sub(r"[^a-z]", "", header.lower())
    for term, label in [
        ("harvest", "Harvesting"), ("collect", "Collection"),
        ("sort", "Sorting/Grading"), ("trim", "Trimming"),
        ("thresh", "Threshing"), ("winnow", "Winnowing/Cleaning"),
        ("dry", "Drying"), ("pack", "Packaging"),
        ("storage", "Farm level storage"), ("trans", "Transport"),
    ]:
        if term in h:
            return "Farm Operations", label
    return None


def candidate_rows(table, index):
    # The crop label is often on the line below the means; uncertainties follow it.
    for row_i in (index - 1, index):
        if row_i < 0:
            continue
        row = table[row_i]
        score = sum(number(c) is not None for c in row[1:])
        if score >= 4:
            yield score, row_i, row


def main():
    result = []
    state = None
    with pdfplumber.open(SOURCE) as pdf:
        for page_index in range(266, 286):  # printed Appendix 6, PDF pages 267–286
            page = pdf.pages[page_index]
            for table_index, found in enumerate(page.find_tables()):
                x0, y0, x1, _ = found.bbox
                if x1 - x0 < 700:
                    continue
                table = found.extract()
                if not table or not 17 <= len(table[0]) <= 22:
                    continue  # PDF table grid is too broken to align safely.
                above = page.crop((0, 0, page.width, y0)).extract_text() or ""
                for line in above.splitlines():
                    stripped = line.strip()
                    if stripped in STATES:
                        state = stripped
                if not state:
                    continue
                crop_positions = [
                    i for i, row in enumerate(table)
                    if row and row[0] and row[0].strip()
                    and row[0].strip().lower() not in {"crop", "crop/ commodity"}
                    and not re.search(r"\d", row[0])
                    and not row[0].strip().startswith(("Farm", "Market", "Overall"))
                ]
                if not crop_positions:
                    continue
                first = crop_positions[0]
                header = [" ".join((table[i][j] or "").replace("\n", " ")
                                   for i in range(max(0, first - 1)))
                          for j in range(len(table[0]))]
                for crop_i in crop_positions:
                    crop = re.sub(r"\s+", " ", table[crop_i][0]).strip()
                    options = list(candidate_rows(table, crop_i))
                    if not options:
                        continue
                    _, mean_i, means = max(options)
                    for col in range(1, len(means)):
                        loss = number(means[col])
                        if loss is None:
                            continue
                        label = metric(header[col], col, len(means))
                        if label is None:
                            continue
                        result.append({
                            "year": 2022, "state": state, "crop": crop,
                            "loss_type": label[0], "stage": label[1],
                            "loss_percentage": loss,
                            "source_pdf_page": page_index + 1,
                            "source_table": table_index + 1,
                            "source_row": mean_i + 1,
                        })
    groups = defaultdict(list)
    for row in result:
        groups[(row["state"], row["crop"])].append(row)
    rejected = set()
    for key, rows in groups.items():
        values = {(r["loss_type"], r["stage"]): r["loss_percentage"] for r in rows}
        farm = values.get(("Farm Operations", "Total loss in farm operations"))
        market = values.get(("Market Operations", "Total loss in market operations"))
        overall = values.get(("Total", "Overall total loss"))
        if all(x is not None for x in (farm, market, overall)) and abs(farm + market - overall) > 0.15:
            rejected.add(key)
            continue
        for kind, total in (("Farm Operations", farm), ("Market Operations", market)):
            if total is None:
                continue
            parts = [v for (part_kind, stage), v in values.items()
                     if part_kind == kind and not stage.startswith("Total loss")]
            if len(parts) >= (7 if kind == "Farm Operations" else 4) and sum(parts) > total + 0.25:
                rejected.add(key)
    result = [row for row in result if (row["state"], row["crop"]) not in rejected
              and row["crop"].lower() != "nut"]
    DEST.parent.mkdir(parents=True, exist_ok=True)
    with DEST.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(result[0]))
        writer.writeheader()
        writer.writerows(result)
    print("rows", len(result))
    print("rejected groups", len(rejected), sorted(rejected))
    print("states", Counter(r["state"] for r in result))
    print("haryana crops", Counter(r["crop"] for r in result if r["state"] == "Haryana"))
    print("punjab crops", Counter(r["crop"] for r in result if r["state"] == "Punjab"))


if __name__ == "__main__":
    main()
