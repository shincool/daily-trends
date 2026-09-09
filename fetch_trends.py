"""
Google Trends 수집 스크립트

1) interest_over_time : 5개 주제어 자체의 7일 추이 (참고용)
2) related_queries     : 각 주제 "안에서" 뜨고 있는 세부 검색어
                          예) "AI" 안에서 챗지피티/클로드/제미나이 등
                          - top    : 꾸준히 검색량 많은 연관어
                          - rising : 최근 급상승한 연관어 (신조어/이슈 포착에 유용)

매일 GitHub Actions가 이 스크립트를 실행해 results/ 에 CSV로 쌓습니다.
"""

import time
import datetime
from pathlib import Path

import pandas as pd
from pytrends.request import TrendReq

# ── 설정 ──────────────────────────────────────────
KEYWORDS = ["청약", "아파트", "종합소득세", "구독서비스", "AI"]
TIMEFRAME = "now 7-d"   # 최근 7일
GEO = "KR"
OUTPUT_DIR = Path("results")
# ────────────────────────────────────────────────


def fetch_interest_over_time(pytrends, keywords, timeframe, geo):
    """5개 키워드 그룹의 상대적 추이 (참고용, 큰 그림만 파악)"""
    pytrends.build_payload(keywords, timeframe=timeframe, geo=geo)
    df = pytrends.interest_over_time()
    if "isPartial" in df.columns:
        df = df.drop(columns=["isPartial"])
    return df


def fetch_related_for_keyword(pytrends, keyword, timeframe, geo):
    """키워드 1개에 대한 top / rising 연관 검색어를 가져온다."""
    pytrends.build_payload([keyword], timeframe=timeframe, geo=geo)
    related = pytrends.related_queries()
    data = related.get(keyword, {})

    rows = []

    top_df = data.get("top")
    if top_df is not None and not top_df.empty:
        for _, r in top_df.iterrows():
            rows.append({
                "topic": keyword,
                "type": "top",
                "query": r["query"],
                "value": r["value"],
            })

    rising_df = data.get("rising")
    if rising_df is not None and not rising_df.empty:
        for _, r in rising_df.iterrows():
            rows.append({
                "topic": keyword,
                "type": "rising",
                "query": r["query"],
                "value": r["value"],
            })

    return rows


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    pytrends = TrendReq(hl="ko-KR", tz=540)  # tz=540 -> KST(UTC+9)
    today_str = datetime.date.today().isoformat()

    # 1) 참고용: 5개 주제어 자체의 추이
    try:
        iot_df = fetch_interest_over_time(pytrends, KEYWORDS, TIMEFRAME, GEO)
        iot_df.to_csv(OUTPUT_DIR / f"trends_{today_str}.csv", encoding="utf-8-sig")
        iot_df.to_csv(OUTPUT_DIR / "trends_latest.csv", encoding="utf-8-sig")
        print("주제어 추이(trends) 저장 완료")
    except Exception as e:
        print(f"[경고] 주제어 추이 수집 실패: {e}")

    time.sleep(2)

    # 2) 핵심: 각 주제 안의 연관/급상승 검색어
    all_rows = []
    for kw in KEYWORDS:
        try:
            rows = fetch_related_for_keyword(pytrends, kw, TIMEFRAME, GEO)
            all_rows.extend(rows)
        except Exception as e:
            print(f"[경고] '{kw}' 연관 검색어 수집 실패: {e}")
        time.sleep(2)  # 구글 트렌드 요청 간격 (429 방지)

    related_df = pd.DataFrame(all_rows, columns=["topic", "type", "query", "value"])
    related_df.to_csv(OUTPUT_DIR / f"related_{today_str}.csv", index=False, encoding="utf-8-sig")
    related_df.to_csv(OUTPUT_DIR / "related_latest.csv", index=False, encoding="utf-8-sig")
    print(f"연관 검색어(related) 저장 완료 ({len(related_df)}행)")


if __name__ == "__main__":
    main()
