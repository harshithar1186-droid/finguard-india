import json
import pandas as pd

transcript_path = r"C:\Users\Lenovo\.gemini\antigravity\brain\74c71a91-31f2-443c-82e9-ab3148f8db23\.system_generated\logs\transcript_full.jsonl"
with open(transcript_path, "r", encoding="utf-8") as f:
    text = f.read()

idx = text.find("bank_name,year,net_npa_ratio")
raw_sub = text[idx:]

end_pos = len(raw_sub)
for marker in ["Error: Your previous response was cut off", '"}', "</USER_REQUEST>"]:
    p = raw_sub.find(marker)
    if p != -1 and p < end_pos:
        end_pos = p

csv_content = raw_sub[:end_pos]
csv_content = csv_content.replace("\\r\\n", "\n").replace("\\n", "\n").replace('\\"', '"')

with open("data/banks_master_dataset.csv", "w", encoding="utf-8") as out:
    out.write(csv_content.strip())

df = pd.read_csv("data/banks_master_dataset.csv")
print("SUCCESS! Loaded dataframe shape:", df.shape)
print("Unique banks count:", df["bank_name"].nunique())
print("Years span:", df["year"].min(), "to", df["year"].max())
print("Columns:", list(df.columns))
print("Sample banks:", list(df["bank_name"].unique())[:10])

