"""관세청 품목별 국가별 수출입실적(GW) → site/data/salt_import_data.csv

GitHub Actions가 매일 실행합니다. 인증키는 저장소 Secrets의 KCS_SERVICE_KEY(Decoding 형태)에서 읽습니다.
- 기존 CSV가 없거나 비어 있으면 최근 24개월을, 있으면 최근 13개월을 다시 받아 덮어씁니다(수정치 반영).
- 월·국가·세번이 같은 줄은 최신 값으로 바꾸고, 새 줄은 추가합니다.
"""
import csv
import os
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

ENDPOINT = "https://apis.data.go.kr/1220000/nitemtrade/getNitemtradeList"
COUNTRIES = {"PK": "파키스탄", "CN": "중국", "AU": "호주"}
ITEMS = {
    "2501001020": "천일염",
    "2501001010": "암염",
    "2501009010": "식염",
    "2501009020": "순염화나트륨",
    "2501009090": "기타 소금",
}
BACKFILL_MONTHS = 24
REFRESH_MONTHS = 13
CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "site", "data", "salt_import_data.csv")
HEADER = ["month", "country_code", "country", "hs_code", "item", "weight_kg", "value_usd", "updated_at"]
KST = timezone(timedelta(hours=9))


def month_ranges(n):
    """지난달까지 최근 n개월을 12개월 이하 구간으로 나눔 → [("YYYYMM","YYYYMM"), ...]"""
    now = datetime.now(KST)
    y, m = now.year, now.month
    months = []
    for i in range(n, 0, -1):
        mm = m - i
        yy = y + (mm - 1) // 12
        mm = (mm - 1) % 12 + 1
        months.append(f"{yy:04d}{mm:02d}")
    return [(months[i], months[min(i + 11, len(months) - 1)]) for i in range(0, len(months), 12)]


def fetch(key, cc, hs, strt, end):
    qs = urllib.parse.urlencode({"serviceKey": key, "strtYymm": strt, "endYymm": end, "cntyCd": cc, "hsSgn": hs})
    last = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(f"{ENDPOINT}?{qs}", timeout=30) as r:
                body = r.read()
            break
        except Exception as e:  # 네트워크 일시 오류 재시도
            last = e
            time.sleep(2 * (attempt + 1))
    else:
        raise RuntimeError(f"요청 실패: {last}")
    root = ET.fromstring(body)
    code = root.findtext("header/resultCode")
    if code and code != "00":
        raise RuntimeError(f"resultCode {code} {root.findtext('header/resultMsg')}")
    rows = []
    for it in root.iter("item"):
        year = (it.findtext("year") or "").strip()  # '2025.11' 또는 '총계'
        if len(year) != 7 or year[4] != ".":
            continue
        hs_cd = (it.findtext("hsCd") or "").strip()
        if hs_cd not in ("", "-", hs):
            continue
        rows.append({
            "month": year.replace(".", "-"),
            "country_code": cc,
            "country": COUNTRIES[cc],
            "hs_code": hs,
            "item": ITEMS[hs],
            "weight_kg": int(float(it.findtext("impWgt") or 0)),
            "value_usd": int(float(it.findtext("impDlr") or 0)),
        })
    return rows


def main():
    key = os.environ.get("KCS_SERVICE_KEY", "").strip()
    if not key:
        sys.exit("KCS_SERVICE_KEY가 없습니다. 저장소 Settings → Secrets and variables → Actions에 등록하세요.")

    existing = {}
    if os.path.exists(CSV_PATH):
        with open(CSV_PATH, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                existing[(r["month"], r["country_code"], r["hs_code"])] = r
    months_back = REFRESH_MONTHS if len(existing) > 50 else BACKFILL_MONTHS

    stamp = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")
    fetched, errors = 0, []
    for cc in COUNTRIES:
        for hs in ITEMS:
            for strt, end in month_ranges(months_back):
                try:
                    for r in fetch(key, cc, hs, strt, end):
                        r["updated_at"] = stamp
                        existing[(r["month"], r["country_code"], r["hs_code"])] = r
                        fetched += 1
                except Exception as e:
                    errors.append(f"{cc} {hs} {strt}-{end}: {e}")
                time.sleep(0.3)

    if fetched == 0:
        sys.exit("수집 실패: " + (errors[0] if errors else "응답 없음"))

    rows = sorted(existing.values(), key=lambda r: (r["month"], r["country_code"], r["hs_code"]))
    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=HEADER, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in HEADER})
    latest = rows[-1]["month"] if rows else "-"
    print(f"받은 행 {fetched}, 전체 {len(rows)}행, 최신 {latest}, 오류 {len(errors)}건")
    for e in errors[:10]:
        print("  오류:", e)


if __name__ == "__main__":
    main()
