"""
Google Trends 키워드 추이 수집 스크립트
GitHub Actions에서 매일 자동 실행되어 results/ 폴더에 CSV로 저장됩니다.
"""

import time
import datetime
from pathlib import Path

from pytrends.request import TrendReq

# ── 설정 ──────────────────────────────────────────
KEYWORDS = ["청약", "아파트", "종합소득세", "구독서비스", "AI"]
TIMEFRAME = "now 7-d"   # 최근 7일
GEO = "KR"              # 대한민국
OUTPUT_DIR = Path("results")
# ────────────────────────────────────────────────


def fetch_keyword_group(pytrends, keywords, timeframe, geo):
    """구글 트렌드는 한 번에 최대 5개 키워드까지 비교 가능"""
    pytrends.build_payload(keywords, timeframe=timeframe, geo=geo)
    df = pytrends.interest_over_time()
    if "isPartial" in df.columns:
        df = df.drop(columns=["isPartial"])
    return df


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    pytrends = TrendReq(hl="ko-KR", tz=540)  # tz=540 -> KST(UTC+9)

    # 5개 이하이므로 한 번에 요청
    df = fetch_keyword_group(pytrends, KEYWORDS, TIMEFRAME, GEO)

    today_str = datetime.date.today().isoformat()
    out_path = OUTPUT_DIR / f"trends_{today_str}.csv"
    df.to_csv(out_path, encoding="utf-8-sig")

    # 최신 파일을 가리키는 고정 이름도 함께 저장 (읽기 편하도록)
    latest_path = OUTPUT_DIR / "trends_latest.csv"
    df.to_csv(latest_path, encoding="utf-8-sig")

    print(f"저장 완료: {out_path}")


if __name__ == "__main__":
    main()
