# Integrated Narrative x Company Analysis

- 생성 시각: 2026-05-06T01:08:21
- 분석 행 수: 205
- 해석 원칙: theme attention score로 내러티브 열기를 보고, company support score로 실제 기업 연결 품질을 검증한다.
- beneficiary map 후보는 뉴스 직접 연결이 없으면 watchlist로만 본다.

## 통합 우선순위

| theme | attention_score | theme_adjusted_confidence | theme_narrative_type | company_support_score | investability_score | verdict | news_linked_companies | mapped_pure_play_watch |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Stablecoin And Crypto Policy | 70.16 | very_high | sustained_narrative | 100.00 | 88.06 | Core Candidate | MSTR, V, COIN, CRCL, META | CLSK, RIOT, MARA |
| Earnings And Buybacks | 70.09 | very_high | sustained_narrative | 100.00 | 88.04 | Core Candidate | AAPL, LLY, META, XOM, AMD |  |
| Data Center Capex | 75.84 | very_high | sustained_narrative | 86.00 | 85.44 | Core Candidate | META, ORCL, AMD, NVDA | SMCI, VRT, DELL, ANET |
| Robotics And Automation | 77.34 | high | sustained_narrative | 26.00 | 60.54 | Watch / Validate | META | TER, ROK, SYM, ZBRA, ISRG |
| Quantum Computing | 82.84 | high | emerging_watch | 31.60 | 59.70 | Watch / Validate | INTC, NVDA | RGTI, IONQ, QBTS, QUBT |
| Smartphone And Devices | 49.41 | medium | emerging_watch | 64.00 | 52.66 | Watch / Validate | AAPL |  |
| AI Infrastructure | 39.78 | very_high | sustained_narrative | 28.80 | 50.99 | Watch / Validate | AVGO, MSFT | ARM, ASML, TSM |
| Tariffs And Supply Chain | 42.84 | very_high | sustained_narrative | 23.20 | 50.26 | Watch / Validate | AAPL |  |
| GLP-1 And Obesity Drugs | 58.28 | medium | emerging_watch | 42.00 | 48.51 | Watch / Validate | LLY | NVO, VKTX |
| Regulatory And Legal Risk | 53.41 | high | sustained_narrative | 13.20 | 46.48 | Low Priority | META |  |

## Stablecoin And Crypto Policy
- attention: 70.16, company_support: 100.00, investability: 88.06, verdict: Core Candidate
- confidence: very_high, type: sustained_narrative

| ticker | company_narrative_role | company_narrative_score | article_count_7d | source_breadth_7d | explicit_mention_count_7d | bucket_type | price_return_1m | relative_return_1m_spy | price_state | interpretation_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MSTR | explicit_news_linked | 88.53 | 6 | 3 | 5 | explicit_news_linked | 46.18 | 36.38 | overheated | normal;price_risk |
| V | explicit_news_linked | 88.53 | 9 | 2 | 8 | explicit_news_linked | 5.58 | -4.22 | neutral | normal |
| COIN | explicit_news_linked | 84.50 | 3 | 2 | 2 | explicit_news_linked | 12.89 | 3.09 | neutral | normal |
| CRCL | explicit_news_linked | 75.96 | 1 | 1 | 1 | explicit_news_linked | 27.10 | 17.29 | confirming | normal |
| META | explicit_news_linked | 70.83 | 1 | 1 | 1 | explicit_news_linked | 5.08 | -4.72 | neutral | normal |
| CLSK | mapped_pure_play_watch | 47.47 | 0 | 0 | 0 | pure_play | 46.59 | 36.79 | overheated | mapped_only_needs_news_confirmation;price_risk |
| RIOT | mapped_pure_play_watch | 47.47 | 0 | 0 | 0 | pure_play | 45.12 | 35.31 | overheated | mapped_only_needs_news_confirmation;price_risk |
| MARA | mapped_pure_play_watch | 46.79 | 0 | 0 | 0 | pure_play | 35.76 | 25.96 | overheated | mapped_only_needs_news_confirmation;price_risk |
| HOOD | mapped_watch | 42.50 | 0 | 0 | 0 | enabler | 11.28 | 1.47 | neutral | mapped_only_needs_news_confirmation |
| SQ | mapped_watch | 41.82 | 0 | 0 | 0 | enabler | nan | nan | neutral | mapped_only_needs_news_confirmation |
| PYPL | mapped_watch | 40.82 | 0 | 0 | 0 | enabler | 1.06 | -8.75 | neutral | mapped_only_needs_news_confirmation |
| MA | mapped_watch | 38.19 | 0 | 0 | 0 | enabler | -1.21 | -11.01 | lagging | mapped_only_needs_news_confirmation |

- 뉴스가 실제 연결한 기업: MSTR, V, COIN, CRCL, META
- 뉴스 확인이 더 필요한 테마 후보: CLSK, RIOT, MARA, HOOD, SQ

## Earnings And Buybacks
- attention: 70.09, company_support: 100.00, investability: 88.04, verdict: Core Candidate
- confidence: very_high, type: sustained_narrative

| ticker | company_narrative_role | company_narrative_score | article_count_7d | source_breadth_7d | explicit_mention_count_7d | bucket_type | price_return_1m | relative_return_1m_spy | price_state | interpretation_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AAPL | explicit_news_linked | 89.26 | 53 | 6 | 5 | explicit_news_linked | 8.15 | -1.58 | neutral | normal |
| LLY | explicit_news_linked | 85.53 | 38 | 7 | 8 | explicit_news_linked | 5.80 | -4.01 | neutral | normal |
| META | explicit_news_linked | 81.25 | 20 | 5 | 16 | explicit_news_linked | 5.08 | -4.72 | neutral | normal |
| XOM | explicit_news_linked | 81.00 | 41 | 5 | 6 | explicit_news_linked | -5.55 | -15.28 | lagging | normal |
| AMD | explicit_news_linked | 79.48 | 19 | 3 | 17 | explicit_news_linked | 60.83 | 51.02 | overheated | normal;price_risk |
| AMZN | explicit_news_linked | 77.71 | 16 | 3 | 1 | explicit_news_linked | 29.35 | 19.55 | extended | normal;price_risk |
| MSFT | explicit_news_linked | 74.53 | 14 | 4 | 2 | explicit_news_linked | 9.83 | 0.03 | neutral | normal |
| GOOG | explicit_news_linked | 70.76 | 7 | 3 | 1 | explicit_news_linked | 28.94 | 19.13 | extended | normal;price_risk |
| V | explicit_news_linked | 69.66 | 10 | 2 | 2 | explicit_news_linked | 5.58 | -4.22 | neutral | normal |
| TSLA | explicit_news_linked | 53.57 | 2 | 1 | 1 | explicit_news_linked | 11.60 | 1.80 | neutral | normal |
| NVDA | explicit_news_linked | 53.50 | 2 | 1 | 1 | explicit_news_linked | 11.16 | 1.35 | neutral | normal |
| ASML | explicit_news_linked | 40.17 | 1 | 1 | 1 | explicit_news_linked | 11.20 | 1.40 | neutral | normal |

- 뉴스가 실제 연결한 기업: AAPL, LLY, META, XOM, AMD
- 뉴스 확인이 더 필요한 테마 후보: 없음

## Data Center Capex
- attention: 75.84, company_support: 86.00, investability: 85.44, verdict: Core Candidate
- confidence: very_high, type: sustained_narrative

| ticker | company_narrative_role | company_narrative_score | article_count_7d | source_breadth_7d | explicit_mention_count_7d | bucket_type | price_return_1m | relative_return_1m_spy | price_state | interpretation_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| META | explicit_news_linked | 89.16 | 13 | 3 | 10 | explicit_news_linked | 5.08 | -4.72 | neutral | normal |
| ORCL | explicit_news_linked | 87.57 | 5 | 1 | 2 | explicit_news_linked | 26.34 | 16.53 | confirming | normal |
| AMD | explicit_news_linked | 86.75 | 6 | 1 | 6 | explicit_news_linked | 60.83 | 51.02 | overheated | normal;price_risk |
| NVDA | explicit_news_linked | 71.46 | 1 | 1 | 1 | explicit_news_linked | 11.16 | 1.35 | neutral | normal |
| SMCI | mapped_pure_play_watch | 51.12 | 0 | 0 | 0 | pure_play | 26.05 | 16.25 | confirming | mapped_only_needs_news_confirmation |
| VRT | mapped_pure_play_watch | 48.81 | 0 | 0 | 0 | pure_play | 30.23 | 20.42 | extended | mapped_only_needs_news_confirmation;price_risk |
| DELL | mapped_pure_play_watch | 47.88 | 0 | 0 | 0 | pure_play | 24.59 | 14.79 | extended | mapped_only_needs_news_confirmation;price_risk |
| ANET | mapped_pure_play_watch | 47.82 | 0 | 0 | 0 | pure_play | 37.85 | 28.05 | overheated | mapped_only_needs_news_confirmation;price_risk |
| ARM | mapped_watch | 44.07 | 0 | 0 | 0 | enabler | 39.34 | 29.54 | overheated | mapped_only_needs_news_confirmation;price_risk |
| AVGO | mapped_watch | 43.54 | 0 | 0 | 0 | enabler | 36.18 | 26.38 | overheated | mapped_only_needs_news_confirmation;price_risk |
| ASML | mapped_watch | 43.17 | 0 | 0 | 0 | enabler | 11.20 | 1.40 | neutral | mapped_only_needs_news_confirmation |
| TSM | mapped_watch | 42.50 | 0 | 0 | 0 | enabler | 16.22 | 6.42 | extended | mapped_only_needs_news_confirmation;price_risk |

- 뉴스가 실제 연결한 기업: META, ORCL, AMD, NVDA
- 뉴스 확인이 더 필요한 테마 후보: SMCI, VRT, DELL, ANET, ARM

## Robotics And Automation
- attention: 77.34, company_support: 26.00, investability: 60.54, verdict: Watch / Validate
- confidence: high, type: sustained_narrative

| ticker | company_narrative_role | company_narrative_score | article_count_7d | source_breadth_7d | explicit_mention_count_7d | bucket_type | price_return_1m | relative_return_1m_spy | price_state | interpretation_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| META | explicit_news_linked | 88.61 | 5 | 3 | 5 | explicit_news_linked | 5.08 | -4.72 | neutral | normal |
| TER | mapped_pure_play_watch | 52.07 | 0 | 0 | 0 | pure_play | 15.61 | 5.81 | confirming | mapped_only_needs_news_confirmation |
| ROK | mapped_pure_play_watch | 50.00 | 0 | 0 | 0 | pure_play | 21.22 | 11.42 | extended | mapped_only_needs_news_confirmation;price_risk |
| SYM | mapped_pure_play_watch | 49.39 | 0 | 0 | 0 | pure_play | 8.44 | -1.36 | neutral | mapped_only_needs_news_confirmation |
| ZBRA | mapped_pure_play_watch | 49.19 | 0 | 0 | 0 | pure_play | 7.22 | -2.59 | neutral | mapped_only_needs_news_confirmation |
| AMD | mapped_watch | 46.82 | 0 | 0 | 0 | enabler | 60.83 | 51.02 | overheated | mapped_only_needs_news_confirmation;price_risk |
| AVGO | mapped_watch | 46.22 | 0 | 0 | 0 | enabler | 36.18 | 26.38 | overheated | mapped_only_needs_news_confirmation;price_risk |
| TSLA | mapped_watch | 45.91 | 0 | 0 | 0 | enabler | 11.60 | 1.80 | neutral | mapped_only_needs_news_confirmation |
| ISRG | mapped_pure_play_watch | 45.64 | 0 | 0 | 0 | pure_play | -0.63 | -10.43 | lagging | mapped_only_needs_news_confirmation |
| GOOGL | mapped_watch | 42.31 | 0 | 0 | 0 | adopter | 29.19 | 19.39 | extended | mapped_only_needs_news_confirmation;price_risk |
| ABBNY | mapped_watch | 37.55 | 0 | 0 | 0 | sympathetic | 24.55 | 14.74 | extended | mapped_only_needs_news_confirmation;price_risk |
| IRBT | mapped_watch | 36.17 | 0 | 0 | 0 | sympathetic | nan | nan | neutral | mapped_only_needs_news_confirmation |

- 뉴스가 실제 연결한 기업: META
- 뉴스 확인이 더 필요한 테마 후보: TER, ROK, SYM, ZBRA, AMD

## Quantum Computing
- attention: 82.84, company_support: 31.60, investability: 59.70, verdict: Watch / Validate
- confidence: high, type: emerging_watch

| ticker | company_narrative_role | company_narrative_score | article_count_7d | source_breadth_7d | explicit_mention_count_7d | bucket_type | price_return_1m | relative_return_1m_spy | price_state | interpretation_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| INTC | explicit_news_linked | 81.92 | 2 | 2 | 2 | explicit_news_linked | 114.59 | 104.86 | overheated | normal;price_risk |
| NVDA | explicit_news_linked | 75.74 | 1 | 1 | 1 | explicit_news_linked | 11.16 | 1.35 | neutral | normal |
| RGTI | mapped_pure_play_watch | 60.15 | 0 | 0 | 0 | pure_play | 26.16 | 16.36 | confirming | mapped_only_needs_news_confirmation |
| IONQ | mapped_pure_play_watch | 57.16 | 0 | 0 | 0 | pure_play | 60.02 | 50.22 | overheated | mapped_only_needs_news_confirmation;price_risk |
| QBTS | mapped_pure_play_watch | 57.16 | 0 | 0 | 0 | pure_play | 50.85 | 41.04 | overheated | mapped_only_needs_news_confirmation;price_risk |
| QUBT | mapped_pure_play_watch | 56.74 | 0 | 0 | 0 | pure_play | 37.32 | 27.52 | overheated | mapped_only_needs_news_confirmation;price_risk |
| GOOGL | mapped_watch | 53.65 | 0 | 0 | 0 | enabler | 29.19 | 19.39 | extended | mapped_only_needs_news_confirmation;price_risk |
| AMZN | mapped_watch | 48.67 | 0 | 0 | 0 | adopter | 29.35 | 19.55 | extended | mapped_only_needs_news_confirmation;price_risk |
| MSFT | mapped_watch | 46.95 | 0 | 0 | 0 | adopter | 9.83 | 0.03 | neutral | mapped_only_needs_news_confirmation |
| IBM | mapped_watch | 46.85 | 0 | 0 | 0 | enabler | -7.48 | -17.29 | lagging | mapped_only_needs_news_confirmation |
| HON | mapped_watch | 46.82 | 0 | 0 | 0 | enabler | -7.65 | -17.45 | lagging | mapped_only_needs_news_confirmation |
| ARQQ | mapped_watch | 42.53 | 0 | 0 | 0 | sympathetic | 7.28 | -2.52 | neutral | mapped_only_needs_news_confirmation |

- 뉴스가 실제 연결한 기업: INTC, NVDA
- 뉴스 확인이 더 필요한 테마 후보: RGTI, IONQ, QBTS, QUBT, GOOGL

## Smartphone And Devices
- attention: 49.41, company_support: 64.00, investability: 52.66, verdict: Watch / Validate
- confidence: medium, type: emerging_watch

| ticker | company_narrative_role | company_narrative_score | article_count_7d | source_breadth_7d | explicit_mention_count_7d | bucket_type | price_return_1m | relative_return_1m_spy | price_state | interpretation_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AAPL | explicit_news_linked | 89.68 | 32 | 5 | 3 | explicit_news_linked | 8.15 | -1.58 | neutral | normal |

- 뉴스가 실제 연결한 기업: AAPL
- 뉴스 확인이 더 필요한 테마 후보: 없음

## AI Infrastructure
- attention: 39.78, company_support: 28.80, investability: 50.99, verdict: Watch / Validate
- confidence: very_high, type: sustained_narrative

| ticker | company_narrative_role | company_narrative_score | article_count_7d | source_breadth_7d | explicit_mention_count_7d | bucket_type | price_return_1m | relative_return_1m_spy | price_state | interpretation_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AVGO | explicit_news_linked | 85.44 | 3 | 1 | 2 | explicit_news_linked | 36.18 | 26.38 | overheated | normal;price_risk |
| MSFT | explicit_news_linked | 66.68 | 1 | 1 | 1 | explicit_news_linked | 9.83 | 0.03 | neutral | normal |
| ARM | mapped_pure_play_watch | 49.77 | 0 | 0 | 0 | pure_play | 39.34 | 29.54 | overheated | mapped_only_needs_news_confirmation;price_risk |
| ASML | mapped_pure_play_watch | 48.87 | 0 | 0 | 0 | pure_play | 11.20 | 1.40 | neutral | mapped_only_needs_news_confirmation |
| SMCI | mapped_watch | 48.82 | 0 | 0 | 0 | enabler | 26.05 | 16.25 | confirming | mapped_only_needs_news_confirmation |
| TSM | mapped_pure_play_watch | 48.20 | 0 | 0 | 0 | pure_play | 16.22 | 6.42 | extended | mapped_only_needs_news_confirmation;price_risk |
| VRT | mapped_watch | 46.51 | 0 | 0 | 0 | enabler | 30.23 | 20.42 | extended | mapped_only_needs_news_confirmation;price_risk |
| MRVL | mapped_watch | 45.85 | 0 | 0 | 0 | enabler | 56.69 | 46.88 | overheated | mapped_only_needs_news_confirmation;price_risk |
| MU | mapped_watch | 45.85 | 0 | 0 | 0 | enabler | 70.74 | 60.94 | overheated | mapped_only_needs_news_confirmation;price_risk |
| DELL | mapped_watch | 45.58 | 0 | 0 | 0 | enabler | 24.59 | 14.79 | extended | mapped_only_needs_news_confirmation;price_risk |
| ANET | mapped_watch | 45.52 | 0 | 0 | 0 | enabler | 37.85 | 28.05 | overheated | mapped_only_needs_news_confirmation;price_risk |
| ORCL | mapped_watch | 43.87 | 0 | 0 | 0 | adopter | 26.34 | 16.53 | confirming | mapped_only_needs_news_confirmation |

- 뉴스가 실제 연결한 기업: AVGO, MSFT
- 뉴스 확인이 더 필요한 테마 후보: ARM, ASML, SMCI, TSM, VRT

## Tariffs And Supply Chain
- attention: 42.84, company_support: 23.20, investability: 50.26, verdict: Watch / Validate
- confidence: very_high, type: sustained_narrative

| ticker | company_narrative_role | company_narrative_score | article_count_7d | source_breadth_7d | explicit_mention_count_7d | bucket_type | price_return_1m | relative_return_1m_spy | price_state | interpretation_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AAPL | explicit_news_linked | 81.82 | 6 | 2 | 1 | explicit_news_linked | 8.15 | -1.58 | neutral | normal |
| AMZN | api_related_indirect | 30.42 | 13 | 3 | 0 | api_related_news | 29.35 | 19.55 | extended | normal;price_risk |
| INTC | api_related_indirect | 26.69 | 3 | 2 | 0 | api_related_news | 114.59 | 104.86 | overheated | normal;price_risk |
| NVDA | api_related_indirect | 24.45 | 2 | 2 | 0 | api_related_news | 11.16 | 1.35 | neutral | normal |
| TSLA | api_related_indirect | 20.95 | 1 | 1 | 0 | api_related_news | 11.60 | 1.80 | neutral | normal |
| MSFT | api_related_indirect | 20.66 | 1 | 1 | 0 | api_related_news | 9.83 | 0.03 | neutral | normal |
| WMT | api_related_indirect | 19.52 | 1 | 1 | 0 | api_related_news | 2.89 | -6.84 | neutral | normal |

- 뉴스가 실제 연결한 기업: AAPL, AMZN, INTC, NVDA, TSLA
- 뉴스 확인이 더 필요한 테마 후보: 없음

## GLP-1 And Obesity Drugs
- attention: 58.28, company_support: 42.00, investability: 48.51, verdict: Watch / Validate
- confidence: medium, type: emerging_watch

| ticker | company_narrative_role | company_narrative_score | article_count_7d | source_breadth_7d | explicit_mention_count_7d | bucket_type | price_return_1m | relative_return_1m_spy | price_state | interpretation_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LLY | explicit_news_linked | 89.28 | 15 | 4 | 1 | explicit_news_linked | 5.80 | -4.01 | neutral | normal |
| NVO | mapped_pure_play_watch | 62.15 | 0 | 0 | 0 | pure_play | 21.98 | 12.18 | confirming | mapped_only_needs_news_confirmation |
| HIMS | mapped_watch | 54.49 | 0 | 0 | 0 | adopter | 30.10 | 20.30 | confirming | mapped_only_needs_news_confirmation |
| VKTX | mapped_pure_play_watch | 53.17 | 0 | 0 | 0 | pure_play | -9.74 | -19.54 | lagging | mapped_only_needs_news_confirmation |
| AMGN | mapped_watch | 49.78 | 0 | 0 | 0 | enabler | -6.00 | -15.81 | lagging | mapped_only_needs_news_confirmation |
| MRK | mapped_watch | 49.77 | 0 | 0 | 0 | enabler | -6.06 | -15.86 | lagging | mapped_only_needs_news_confirmation |
| PFE | mapped_watch | 49.77 | 0 | 0 | 0 | enabler | -6.07 | -15.88 | lagging | mapped_only_needs_news_confirmation |
| TNDM | mapped_watch | 44.00 | 0 | 0 | 0 | sympathetic | -0.16 | -9.96 | neutral | mapped_only_needs_news_confirmation |
| DXCM | mapped_watch | 40.67 | 0 | 0 | 0 | sympathetic | -6.66 | -16.46 | lagging | mapped_only_needs_news_confirmation |

- 뉴스가 실제 연결한 기업: LLY
- 뉴스 확인이 더 필요한 테마 후보: NVO, HIMS, VKTX, AMGN, MRK

## Regulatory And Legal Risk
- attention: 53.41, company_support: 13.20, investability: 46.48, verdict: Low Priority
- confidence: high, type: sustained_narrative

| ticker | company_narrative_role | company_narrative_score | article_count_7d | source_breadth_7d | explicit_mention_count_7d | bucket_type | price_return_1m | relative_return_1m_spy | price_state | interpretation_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| META | explicit_news_linked | 48.80 | 1 | 1 | 1 | explicit_news_linked | 5.08 | -4.72 | neutral | normal |
| INTC | api_related_indirect | 32.04 | 4 | 2 | 0 | api_related_news | 114.59 | 104.86 | overheated | normal;price_risk |
| AAPL | api_related_indirect | 27.62 | 2 | 2 | 0 | api_related_news | 8.15 | -1.58 | neutral | normal |
| XOM | api_related_indirect | 23.11 | 2 | 2 | 0 | api_related_news | -5.55 | -15.28 | lagging | normal |
| AMZN | api_related_indirect | 22.83 | 1 | 1 | 0 | api_related_news | 29.35 | 19.55 | extended | normal;price_risk |
| TSLA | api_related_indirect | 21.40 | 1 | 1 | 0 | api_related_news | 11.60 | 1.80 | neutral | normal |
| JPM | api_related_indirect | 18.85 | 1 | 1 | 0 | api_related_news | 4.81 | -4.99 | neutral | normal |

- 뉴스가 실제 연결한 기업: META, INTC, AAPL, XOM, AMZN
- 뉴스 확인이 더 필요한 테마 후보: 없음
