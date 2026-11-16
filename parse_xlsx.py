import zipfile
import xml.etree.ElementTree as ET
import csv
import os

excel_path = r"C:\Users\Lenovo\.gemini\antigravity\brain\74c71a91-31f2-443c-82e9-ab3148f8db23\.user_uploaded\media_1793415455254_b5f36252.xlsx"
out_csv = r"C:\Users\Lenovo\.gemini\antigravity\scratch\finguard-india\data\banks_master_dataset.csv"

with zipfile.ZipFile(excel_path, 'r') as z:
    # 1. Read shared strings
    shared_strings = []
    if 'xl/sharedStrings.xml' in z.namelist():
        tree = ET.fromstring(z.read('xl/sharedStrings.xml'))
        # namespace for spreadsheetml
        ns = {'ns': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        for si in tree.findall('ns:si', ns):
            # concatenate all t tags inside si
            t_elems = si.findall('.//ns:t', ns)
            text = "".join([t.text or "" for t in t_elems])
            shared_strings.append(text)

    # 2. Read sheet1.xml
    sheet_xml = z.read('xl/worksheets/sheet1.xml')
    sheet_tree = ET.fromstring(sheet_xml)
    ns = {'ns': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

    rows_data = []
    for row in sheet_tree.findall('.//ns:row', ns):
        row_vals = []
        for c in row.findall('ns:c', ns):
            t = c.get('t')
            v = c.find('ns:v', ns)
            val = v.text if v is not None else ""
            if t == 's':
                idx = int(val)
                val = shared_strings[idx] if idx < len(shared_strings) else ""
            row_vals.append(val)
        if any(row_vals):
            rows_data.append(row_vals)

with open(out_csv, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    for r in rows_data:
        writer.writerow(r)

print(f"SUCCESS! Parsed {len(rows_data)} rows.")
if rows_data:
    print("Header:", rows_data[0])
    print("First data row:", rows_data[1])

