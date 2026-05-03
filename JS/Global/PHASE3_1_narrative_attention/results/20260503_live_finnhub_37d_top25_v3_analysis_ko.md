# Finnhub Top25 37일 Narrative Attention v3 신뢰도 분석

기준일: 2026-05-03  
수집 소스: Finnhub `company-news`  
수집 대상: PHASE0 universe market cap 상위 25개  
수집 기간: 최근 37일  
분석 원문: URL 중복 제거 후 4,822건  
테마 매칭 기사: 1,053건

## v3에서 추가한 것

기존 `attention_score`는 "최근 7일 관심이 직전 30일 대비 얼마나 뛰었는가"를 잘 잡지만, single event와 지속 narrative를 구분하지 못했다.

v3에서는 다음 신뢰도 컬럼을 추가했다.

| 컬럼 | 의미 |
|---|---|
| `adjusted_confidence` | article count, active days, source/ticker breadth, event concentration을 반영한 보정 신뢰도 |
| `narrative_type` | `sustained_narrative`, `emerging_watch`, `derivative_mention`, `single_event`, `noise_possible` |
| `daily_active_days_7d` | 최근 7일 중 실제로 기사가 나온 날짜 수 |
| `unique_ticker_count_7d` | 최근 7일 매칭 기사에 포함된 고유 ticker 수 |
| `top_ticker_share_7d` | 특정 ticker 하나에 쏠린 비율 |
| `top_headline_cluster_share_7d` | 유사 headline cluster 하나에 쏠린 비율 |
| `pure_play_ratio_7d` | 해당 theme의 pure-play ticker가 차지하는 비율 |
| `event_concentration_score` | ticker/headline 쏠림 중 큰 값 |

## v3 핵심 결론

attention score만 보면 Quantum이 1위지만, 신뢰도 레이어를 붙이면 해석이 달라진다.

| Theme | Attention | Adjusted Confidence | Type | 해석 |
|---|---:|---|---|---|
| Quantum Computing | 80.63 | medium | derivative_mention | spike는 맞지만 NVDA/AI narrative의 부산물 가능성 |
| Robotics And Automation | 78.78 | medium | emerging_watch | Meta 이벤트 영향이 크지만 watch 필요 |
| Data Center Capex | 77.31 | very_high | sustained_narrative | 가장 신뢰도 높은 sustained narrative |
| Grid And Power Equipment | 72.25 | low | noise_possible | 기사 수 4건이라 아직 약함 |
| Reshoring And Manufacturing | 66.19 | low | noise_possible | 1건짜리 spike |
| Earnings And Buybacks | 65.88 | very_high | sustained_narrative | 강하지만 earnings season effect |
| AI Infrastructure | 36.38 | very_high | sustained_narrative | 관심은 높지만 최근 acceleration은 약함 |

## 해석 업데이트

### 1. Data Center Capex가 가장 신뢰도 높은 결과

- attention score: 77.31
- adjusted confidence: very_high
- narrative type: sustained_narrative
- 최근 7일 기사 수: 58건
- active days: 6일
- unique ticker count: 15개
- top ticker share: 27.6%
- pure-play ratio: 79.3%

이 테마는 기사 수, 날짜 지속성, ticker breadth, pure-play ratio가 모두 좋다. v3 기준으로는 "가장 믿을 수 있는 narrative shift"다.

### 2. Quantum은 1위지만 derivative mention

- attention score: 80.63
- adjusted confidence: medium
- narrative type: derivative_mention
- 최근 7일 기사 수: 8건
- active days: 4일
- pure-play ratio: 0%

Quantum은 7일 변화율이 커서 attention score는 높지만, pure-play ticker 기반 신호가 없다. 즉 IONQ/RGTI/QBTS 같은 pure-play narrative라기보다 NVDA/AI narrative에 quantum 키워드가 붙은 derivative mention으로 보는 게 맞다.

### 3. Robotics는 emerging watch

- attention score: 78.78
- adjusted confidence: medium
- narrative type: emerging_watch
- 최근 7일 기사 수: 11건
- active days: 4일
- top ticker share: 54.5%
- pure-play ratio: 63.6%

Meta 관련 이벤트 영향이 크지만, pure-play/관련 ticker 비율과 active days가 나쁘지 않다. single-event로 단정하기보다는 emerging watch가 적절하다.

### 4. Grid / Reshoring / Nuclear는 noise 가능성

Grid는 attention score 4위지만 기사 수가 4건뿐이라 `noise_possible`로 내려갔다. Reshoring과 Nuclear는 각각 1건 기반이라 아직 narrative로 볼 수 없다.

### 5. AI Infrastructure는 falling이지만 죽은 테마가 아님

- attention score: 36.38
- adjusted confidence: very_high
- narrative type: sustained_narrative
- 최근 7일 기사 수: 33건
- active days: 7일
- unique ticker count: 11개

AI Infrastructure는 sustained narrative지만 최근 7일 acceleration이 약하다. 이건 "AI 관심이 사라졌다"가 아니라, 이미 baseline이 높아진 상위 narrative가 Data Center Capex, Robotics, Quantum, Power 같은 하위 narrative로 분화되고 있다는 뜻에 가깝다.

## 다음 개선

1. `narrative_type`을 최종 리포트의 1차 정렬 기준으로 함께 사용한다.
2. `attention_score`가 높아도 `noise_possible`이면 ranking에서는 별도 alert bucket으로 뺀다.
3. Quantum처럼 `derivative_mention`인 경우 pure-play basket을 별도로 수집해 검증한다.
4. Robotics처럼 `emerging_watch`인 경우 daily trend를 시각화해 single event인지 지속 관심인지 확인한다.
5. Data Center Capex처럼 `sustained_narrative`이면서 `very_high`인 테마를 실제 투자 리서치 후보로 우선 넘긴다.
