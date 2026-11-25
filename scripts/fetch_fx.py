"""관세청 관세환율정보(GW) → site/data/fx_usd.csv

수입 과세환율(주간, 일요일 적용 시작) 중 '매월 첫 공표분'(그 달 첫 일요일부터 적용되는 USD 환율)을 월별로 저장합니다.
인증키는 KCS_SERVICE_KEY(공공데이터포털)를 같이 씁니다. 공공데이터포털에서 '관세청_관세환율정보(GW)' 활용신청이 필요합니다.
이 스크립트가 실패해도 대시보드 수집은 계속되도록 항상 정상 종료합니다.
"""
import csv
import os
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta, timezone

ENDPOINT = "https://apis.data.go.kr/1220000/retrieveTrifFxrtInfo/getRetrieveTrifFxrtInfo"
BASE = os.path.join(os.path.dirname(__file__), "..", "site", "data")
DATA_CSV = os.path.join(BASE, "salt_import_data.csv")
FX_CSV = os.path.join(BASE, "fx_usd.csv")
HEADER = ["month", "aply_date", "usd_krw"]
KST = timezone(timedelta(hours=9))


def first_sunday(y, m):
    d = date(y, m, 1)
    return d + timedelta(days=(6 - d.weekday()) % 7)


def fetch(key, d):
    qs = urllib.parse.urlencode({"serviceKey": key, "aplyBgnDt": d.strftime("%Y%m%d"), "weekFxrtTpcd": "2"})
    last = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(f"{ENDPOINT}?{qs}", timeout=30) as r:
                body = r.read()
            break
        except Exception as e:
            last = e
            time.sleep(2 * (attempt + 1))
    else:
        raise RuntimeError(f"요청 실패: {last}")
    root = ET.fromstring(body)
    code = root.findtext(".//resultCode")
    if code and code not in ("00", "0"):
        raise RuntimeError(f"resultCode {code} {root.findtext('.//resultMsg')}")
    for it in root.iter("item"):
        cur = (it.findtext("currSgn") or "").strip().upper()
        if cur == "USD":
            rate = float((it.findtext("fxrt") or "0").replace(",", ""))
            ad = (it.findtext("aplyBgnDt") or d.strftime("%Y%m%d")).strip()
            if rate > 0:
                return f"{ad[:4]}-{ad[4:6]}-{ad[6:8]}", rate
    raise RuntimeError("USD 환율 없음")


def main():
    key = os.environ.get("KCS_SERVICE_KEY", "").strip()
    if not key:
        print("KCS_SERVICE_KEY 없음 → 환율 건너뜀"); return
    months = set()
    if os.path.exists(DATA_CSV):
        with open(DATA_CSV, encoding="utf-8") as f:
            months = {r["month"] for r in csv.DictReader(f)}
    now = datetime.now(KST)
    months.add(f"{now.year:04d}-{now.month:02d}")
    have = {}
    if os.path.exists(FX_CSV):
        with open(FX_CSV, encoding="utf-8") as f:
            have = {r["month"]: r for r in csv.DictReader(f)}
    cur_m = f"{now.year:04d}-{now.month:02d}"
    errors, got = [], 0
    for m in sorted(months):
        if m in have and m != cur_m:
            continue
        y, mo = int(m[:4]), int(m[5:7])
        d = first_sunday(y, mo)
        if d > now.date():
            continue  # 이번 달 첫 적용일이 아직 안 옴
        try:
            ad, rate = fetch(key, d)
            have[m] = {"month": m, "aply_date": ad, "usd_krw": f"{rate:.2f}"}
            got += 1
        except Exception as e:
            errors.append(f"{m}: {e}")
        time.sleep(0.3)
    if have:
        with open(FX_CSV, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=HEADER, lineterminator="\n")
            w.writeheader()
            for m in sorted(have):
                w.writerow({k: have[m][k] for k in HEADER})
    print(f"환율 새로 받음 {got}건, 저장 {len(have)}개월, 오류 {len(errors)}건")
    for e in errors[:5]:
        print("  오류:", e)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("환율 수집 실패(무시):", e)
