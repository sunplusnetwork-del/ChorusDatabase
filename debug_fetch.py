import requests
from bs4 import BeautifulSoup

url = "https://jcanet.or.jp/Public/meikyoku/meikyoku-No51.htm"
resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
text_raw = resp.content.decode("cp932", errors="replace")
soup = BeautifulSoup(text_raw, "html.parser")
for br in soup.find_all("br"):
    br.replace_with("\n")
lines = soup.get_text("\n").split("\n")
for i, line in enumerate(lines):
    s = line.strip()
    if s:
        print(f"{i:4d}: {repr(s[:120])}")
