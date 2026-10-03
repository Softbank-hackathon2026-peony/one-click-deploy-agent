"""S4 서비스 유형별 순위(knowledge/ranking.yaml, 설계 2026-10-03-infrafit-service-type-ranking-design.md).

유형 판정, 기준 값 계산 도우미, 비용 동률, decided_by. 순위는 사전식이고 유형마다 기준 순서만 다르다.
"""

from __future__ import annotations

# 계산 함수가 있는 기준. ranking.yaml criteria 는 이 안에서만 고른다(kb_lint)
CRITERIA = ("certainty", "cost", "always_on", "request_headroom", "scaling", "data_safety", "config_burden")
