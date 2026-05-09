# Integrated Narrative x Company Analysis

- 생성 시각: 2026-05-06T00:41:07
- 분석 행 수: 201
- 해석 원칙: theme attention score로 내러티브 열기를 보고, company support score로 실제 기업 연결 품질을 검증한다.
- beneficiary map 후보는 뉴스 직접 연결이 없으면 watchlist로만 본다.

## 통합 우선순위

| theme | attention_score | theme_adjusted_confidence | theme_narrative_type | company_support_score | investability_score | verdict | news_linked_companies | mapped_pure_play_watch |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Data Center Capex | 75.84 | very_high | sustained_narrative | 100.00 | 90.34 | Core Candidate | ORCL, META, AMD, INTC, AMZN | SMCI, VRT, DELL, ANET |
| Stablecoin And Crypto Policy | 70.16 | very_high | sustained_narrative | 100.00 | 88.06 | Core Candidate | V, INTC, TSLA, AMD, NVDA | MARA, CLSK, MSTR, RIOT, COIN |
| Earnings And Buybacks | 70.09 | very_high | sustained_narrative | 100.00 | 88.04 | Core Candidate | AAPL, META, LLY, XOM, INTC |  |
| Robotics And Automation | 77.34 | high | sustained_narrative | 100.00 | 86.44 | Core Candidate | MSFT, META, AMZN, GOOG, NVDA | TER, ROK, SYM, ZBRA, ISRG |
| Tariffs And Supply Chain | 42.84 | very_high | sustained_narrative | 100.00 | 77.14 | Core Candidate | AMZN, AAPL, INTC, NVDA, MSFT |  |
| Regulatory And Legal Risk | 53.41 | high | sustained_narrative | 100.00 | 76.86 | Core Candidate | TSLA, INTC, AAPL, XOM, AMZN |  |
| AI Infrastructure | 39.78 | very_high | sustained_narrative | 100.00 | 75.91 | Core Candidate | NVDA, INTC, AMD, AVGO, MU | ARM, ASML, TSM |
| Quantum Computing | 82.84 | high | sustained_narrative | 56.00 | 73.24 | Active Watch | INTC, GOOG, NVDA | RGTI, IONQ, QBTS, QUBT |
| GLP-1 And Obesity Drugs | 58.28 | high | emerging_watch | 78.40 | 66.25 | Active Watch | LLY, INTC, WMT | NVO, VKTX |
| Smartphone And Devices | 49.41 | medium | emerging_watch | 100.00 | 65.26 | Active Watch | AAPL, META, INTC, MSFT, XOM |  |

## Data Center Capex
- attention: 75.84, company_support: 100.00, investability: 90.34, verdict: Core Candidate
- confidence: very_high, type: sustained_narrative

| ticker | company_narrative_role | company_narrative_score | article_count_7d | source_breadth_7d | bucket_type | price_return_1m | relative_return_1m_spy | price_state | interpretation_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ORCL | news_linked_unmapped | 87.61 | 10 | 3 | news_linked | 25.94 | 16.19 | confirming | normal |
| META | news_linked_unmapped | 84.84 | 16 | 3 | news_linked | 5.42 | -4.33 | neutral | normal |
| AMD | news_linked_unmapped | 80.32 | 8 | 2 | news_linked | 60.92 | 51.17 | overheated | normal;price_risk |
| INTC | news_linked_unmapped | 77.63 | 8 | 1 | news_linked | 114.59 | 104.86 | overheated | normal;price_risk |
| AMZN | news_linked_unmapped | 76.02 | 4 | 3 | news_linked | 29.80 | 20.06 | extended | normal;price_risk |
| JPM | news_linked_unmapped | 72.82 | 5 | 1 | news_linked | 4.83 | -4.92 | neutral | normal |
| AVGO | news_linked_unmapped | 71.26 | 3 | 2 | news_linked | 36.19 | 26.45 | overheated | normal;price_risk |
| NVDA | news_linked_unmapped | 68.94 | 3 | 1 | news_linked | 11.04 | 1.29 | neutral | normal |
| MU | news_linked_unmapped | 65.52 | 2 | 2 | news_linked | 69.21 | 59.46 | overheated | normal;price_risk |
| MSFT | news_linked_unmapped | 64.37 | 2 | 2 | news_linked | 10.15 | 0.41 | neutral | normal |
| GOOG | news_linked_unmapped | 64.11 | 2 | 1 | news_linked | 29.29 | 19.54 | extended | normal;price_risk |
| LLY | news_linked_unmapped | 61.71 | 2 | 2 | news_linked | 5.69 | -4.06 | neutral | normal |

- 뉴스가 실제 연결한 기업: ORCL, META, AMD, INTC, AMZN
- 뉴스 확인이 더 필요한 테마 후보: 없음

## Stablecoin And Crypto Policy
- attention: 70.16, company_support: 100.00, investability: 88.06, verdict: Core Candidate
- confidence: very_high, type: sustained_narrative

| ticker | company_narrative_role | company_narrative_score | article_count_7d | source_breadth_7d | bucket_type | price_return_1m | relative_return_1m_spy | price_state | interpretation_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| V | news_linked_unmapped | 85.29 | 10 | 3 | news_linked | 5.79 | -3.95 | neutral | normal |
| INTC | news_linked_unmapped | 82.37 | 6 | 1 | news_linked | 114.59 | 104.86 | overheated | normal;price_risk |
| TSLA | news_linked_unmapped | 79.12 | 3 | 1 | news_linked | 11.92 | 2.18 | neutral | normal |
| AMD | news_linked_unmapped | 74.76 | 2 | 2 | news_linked | 60.92 | 51.17 | overheated | normal;price_risk |
| NVDA | news_linked_unmapped | 71.80 | 2 | 1 | news_linked | 11.04 | 1.29 | neutral | normal |
| AAPL | news_linked_unmapped | 71.33 | 2 | 1 | news_linked | 8.15 | -1.58 | neutral | normal |
| META | news_linked_unmapped | 70.88 | 2 | 1 | news_linked | 5.42 | -4.33 | neutral | normal |
| JPM | news_linked_unmapped | 70.78 | 2 | 1 | news_linked | 4.83 | -4.92 | neutral | normal |
| GOOG | news_linked_unmapped | 64.95 | 1 | 1 | news_linked | 29.29 | 19.54 | extended | normal;price_risk |
| MU | news_linked_unmapped | 64.43 | 1 | 1 | news_linked | 69.21 | 59.46 | overheated | normal;price_risk |
| MARA | mapped_pure_play_watch | 51.56 | 0 | 0 | pure_play | 34.86 | 25.11 | confirming | mapped_only_needs_news_confirmation |
| RIOT | mapped_pure_play_watch | 47.13 | 0 | 0 | pure_play | 43.97 | 34.23 | overheated | mapped_only_needs_news_confirmation;price_risk |

- 뉴스가 실제 연결한 기업: V, INTC, TSLA, AMD, NVDA
- 뉴스 확인이 더 필요한 테마 후보: MARA, RIOT

## Earnings And Buybacks
- attention: 70.09, company_support: 100.00, investability: 88.04, verdict: Core Candidate
- confidence: very_high, type: sustained_narrative

| ticker | company_narrative_role | company_narrative_score | article_count_7d | source_breadth_7d | bucket_type | price_return_1m | relative_return_1m_spy | price_state | interpretation_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AAPL | news_linked_unmapped | 83.80 | 60 | 6 | news_linked | 8.15 | -1.58 | neutral | normal |
| META | news_linked_unmapped | 83.35 | 61 | 5 | news_linked | 5.42 | -4.33 | neutral | normal |
| LLY | news_linked_unmapped | 77.35 | 47 | 7 | news_linked | 5.69 | -4.06 | neutral | normal |
| XOM | news_linked_unmapped | 75.13 | 56 | 5 | news_linked | -5.55 | -15.28 | lagging | normal |
| INTC | news_linked_unmapped | 75.07 | 51 | 3 | news_linked | 114.59 | 104.86 | overheated | normal;price_risk |
| AMD | news_linked_unmapped | 73.19 | 36 | 4 | news_linked | 60.92 | 51.17 | overheated | normal;price_risk |
| AMZN | news_linked_unmapped | 71.50 | 25 | 4 | news_linked | 29.80 | 20.06 | extended | normal;price_risk |
| ORCL | news_linked_unmapped | 65.53 | 16 | 4 | news_linked | 25.94 | 16.19 | confirming | normal |
| MSFT | news_linked_unmapped | 64.13 | 18 | 4 | news_linked | 10.15 | 0.41 | neutral | normal |
| V | news_linked_unmapped | 63.72 | 20 | 3 | news_linked | 5.79 | -3.95 | neutral | normal |
| NVDA | news_linked_unmapped | 60.84 | 20 | 3 | news_linked | 11.04 | 1.29 | neutral | normal |
| MU | news_linked_unmapped | 59.55 | 15 | 4 | news_linked | 69.21 | 59.46 | overheated | normal;price_risk |

- 뉴스가 실제 연결한 기업: AAPL, META, LLY, XOM, INTC
- 뉴스 확인이 더 필요한 테마 후보: 없음

## Robotics And Automation
- attention: 77.34, company_support: 100.00, investability: 86.44, verdict: Core Candidate
- confidence: high, type: sustained_narrative

| ticker | company_narrative_role | company_narrative_score | article_count_7d | source_breadth_7d | bucket_type | price_return_1m | relative_return_1m_spy | price_state | interpretation_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MSFT | news_linked_unmapped | 83.37 | 5 | 2 | news_linked | 10.15 | 0.41 | neutral | normal |
| META | news_linked_unmapped | 83.14 | 5 | 3 | news_linked | 5.42 | -4.33 | neutral | normal |
| AMZN | news_linked_unmapped | 80.53 | 3 | 1 | news_linked | 29.80 | 20.06 | extended | normal;price_risk |
| GOOG | news_linked_unmapped | 75.30 | 2 | 1 | news_linked | 29.29 | 19.54 | extended | normal;price_risk |
| NVDA | news_linked_unmapped | 72.68 | 2 | 1 | news_linked | 11.04 | 1.29 | neutral | normal |
| ORCL | news_linked_unmapped | 71.08 | 1 | 1 | news_linked | 25.94 | 16.19 | confirming | normal |
| TSLA | news_linked_unmapped | 67.27 | 1 | 1 | news_linked | 11.92 | 2.18 | neutral | normal |
| TER | mapped_pure_play_watch | 48.56 | 0 | 0 | pure_play | 14.30 | 4.55 | neutral | mapped_only_needs_news_confirmation |
| ROK | mapped_pure_play_watch | 48.07 | 0 | 0 | pure_play | 20.44 | 10.69 | extended | mapped_only_needs_news_confirmation;price_risk |
| SYM | mapped_pure_play_watch | 47.60 | 0 | 0 | pure_play | 8.50 | -1.25 | neutral | mapped_only_needs_news_confirmation |
| ZBRA | mapped_pure_play_watch | 47.29 | 0 | 0 | pure_play | 6.62 | -3.12 | neutral | mapped_only_needs_news_confirmation |
| ISRG | mapped_pure_play_watch | 46.23 | 0 | 0 | pure_play | 0.17 | -9.57 | neutral | mapped_only_needs_news_confirmation |

- 뉴스가 실제 연결한 기업: MSFT, META, AMZN, GOOG, NVDA
- 뉴스 확인이 더 필요한 테마 후보: TER, ROK, SYM, ZBRA, ISRG

## Tariffs And Supply Chain
- attention: 42.84, company_support: 100.00, investability: 77.14, verdict: Core Candidate
- confidence: very_high, type: sustained_narrative

| ticker | company_narrative_role | company_narrative_score | article_count_7d | source_breadth_7d | bucket_type | price_return_1m | relative_return_1m_spy | price_state | interpretation_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AMZN | news_linked_unmapped | 85.53 | 14 | 3 | news_linked | 29.80 | 20.06 | extended | normal;price_risk |
| AAPL | news_linked_unmapped | 79.57 | 6 | 2 | news_linked | 8.15 | -1.58 | neutral | normal |
| INTC | news_linked_unmapped | 66.04 | 3 | 2 | news_linked | 114.59 | 104.86 | overheated | normal;price_risk |
| NVDA | news_linked_unmapped | 59.21 | 2 | 2 | news_linked | 11.04 | 1.29 | neutral | normal |
| MSFT | news_linked_unmapped | 54.62 | 2 | 1 | news_linked | 10.15 | 0.41 | neutral | normal |
| AMD | news_linked_unmapped | 44.09 | 1 | 1 | news_linked | 60.92 | 51.17 | overheated | normal;price_risk |
| TSLA | news_linked_unmapped | 43.24 | 1 | 1 | news_linked | 11.92 | 2.18 | neutral | normal |
| JPM | news_linked_unmapped | 42.07 | 1 | 1 | news_linked | 4.83 | -4.92 | neutral | normal |
| WMT | news_linked_unmapped | 41.75 | 1 | 1 | news_linked | 2.89 | -6.84 | neutral | normal |

- 뉴스가 실제 연결한 기업: AMZN, AAPL, INTC, NVDA, MSFT
- 뉴스 확인이 더 필요한 테마 후보: 없음

## Regulatory And Legal Risk
- attention: 53.41, company_support: 100.00, investability: 76.86, verdict: Core Candidate
- confidence: high, type: sustained_narrative

| ticker | company_narrative_role | company_narrative_score | article_count_7d | source_breadth_7d | bucket_type | price_return_1m | relative_return_1m_spy | price_state | interpretation_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TSLA | news_linked_unmapped | 86.30 | 6 | 4 | news_linked | 11.92 | 2.18 | neutral | normal |
| INTC | news_linked_unmapped | 76.44 | 4 | 2 | news_linked | 114.59 | 104.86 | overheated | normal;price_risk |
| AAPL | news_linked_unmapped | 63.18 | 2 | 2 | news_linked | 8.15 | -1.58 | neutral | normal |
| XOM | news_linked_unmapped | 58.67 | 2 | 2 | news_linked | -5.55 | -15.28 | lagging | normal |
| AMZN | news_linked_unmapped | 42.75 | 1 | 1 | news_linked | 29.80 | 20.06 | extended | normal;price_risk |
| META | news_linked_unmapped | 40.22 | 1 | 1 | news_linked | 5.42 | -4.33 | neutral | normal |
| JPM | news_linked_unmapped | 35.84 | 1 | 1 | news_linked | 4.83 | -4.92 | neutral | normal |

- 뉴스가 실제 연결한 기업: TSLA, INTC, AAPL, XOM, AMZN
- 뉴스 확인이 더 필요한 테마 후보: 없음

## AI Infrastructure
- attention: 39.78, company_support: 100.00, investability: 75.91, verdict: Core Candidate
- confidence: very_high, type: sustained_narrative

| ticker | company_narrative_role | company_narrative_score | article_count_7d | source_breadth_7d | bucket_type | price_return_1m | relative_return_1m_spy | price_state | interpretation_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| NVDA | news_linked_unmapped | 85.70 | 14 | 3 | news_linked | 11.04 | 1.29 | neutral | normal |
| INTC | news_linked_unmapped | 81.47 | 8 | 1 | news_linked | 114.59 | 104.86 | overheated | normal;price_risk |
| AMD | news_linked_unmapped | 78.74 | 4 | 3 | news_linked | 60.92 | 51.17 | overheated | normal;price_risk |
| AVGO | news_linked_unmapped | 76.78 | 4 | 1 | news_linked | 36.19 | 26.45 | overheated | normal;price_risk |
| MU | news_linked_unmapped | 74.76 | 3 | 3 | news_linked | 69.21 | 59.46 | overheated | normal;price_risk |
| GOOG | news_linked_unmapped | 67.44 | 4 | 1 | news_linked | 29.29 | 19.54 | extended | normal;price_risk |
| ORCL | news_linked_unmapped | 65.91 | 3 | 1 | news_linked | 25.94 | 16.19 | confirming | normal |
| AMZN | news_linked_unmapped | 65.70 | 1 | 1 | news_linked | 29.80 | 20.06 | extended | normal;price_risk |
| META | news_linked_unmapped | 60.45 | 2 | 2 | news_linked | 5.42 | -4.33 | neutral | normal |
| TSLA | news_linked_unmapped | 56.53 | 1 | 1 | news_linked | 11.92 | 2.18 | neutral | normal |
| MSFT | news_linked_unmapped | 56.23 | 1 | 1 | news_linked | 10.15 | 0.41 | neutral | normal |
| ARM | mapped_pure_play_watch | 47.25 | 0 | 0 | pure_play | 39.22 | 29.48 | overheated | mapped_only_needs_news_confirmation;price_risk |

- 뉴스가 실제 연결한 기업: NVDA, INTC, AMD, AVGO, MU
- 뉴스 확인이 더 필요한 테마 후보: ARM

## Quantum Computing
- attention: 82.84, company_support: 56.00, investability: 73.24, verdict: Active Watch
- confidence: high, type: sustained_narrative

| ticker | company_narrative_role | company_narrative_score | article_count_7d | source_breadth_7d | bucket_type | price_return_1m | relative_return_1m_spy | price_state | interpretation_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| INTC | news_linked_unmapped | 77.92 | 6 | 3 | news_linked | 114.59 | 104.86 | overheated | normal;price_risk |
| GOOG | news_linked_unmapped | 74.59 | 3 | 1 | news_linked | 29.29 | 19.54 | extended | normal;price_risk |
| NVDA | news_linked_unmapped | 70.38 | 1 | 1 | news_linked | 11.04 | 1.29 | neutral | normal |
| RGTI | mapped_pure_play_watch | 60.06 | 0 | 0 | pure_play | 25.56 | 15.82 | confirming | mapped_only_needs_news_confirmation |
| IONQ | mapped_pure_play_watch | 57.16 | 0 | 0 | pure_play | 59.99 | 50.24 | overheated | mapped_only_needs_news_confirmation;price_risk |
| QBTS | mapped_pure_play_watch | 57.16 | 0 | 0 | pure_play | 49.96 | 40.22 | overheated | mapped_only_needs_news_confirmation;price_risk |
| QUBT | mapped_pure_play_watch | 56.65 | 0 | 0 | pure_play | 36.73 | 26.99 | overheated | mapped_only_needs_news_confirmation;price_risk |
| GOOGL | mapped_watch | 53.72 | 0 | 0 | enabler | 29.59 | 19.84 | extended | mapped_only_needs_news_confirmation;price_risk |
| AMZN | mapped_watch | 48.76 | 0 | 0 | adopter | 29.80 | 20.06 | extended | mapped_only_needs_news_confirmation;price_risk |
| MSFT | mapped_watch | 47.01 | 0 | 0 | adopter | 10.15 | 0.41 | neutral | mapped_only_needs_news_confirmation |
| IBM | mapped_watch | 46.86 | 0 | 0 | enabler | -7.45 | -17.19 | lagging | mapped_only_needs_news_confirmation |
| HON | mapped_watch | 46.81 | 0 | 0 | enabler | -7.74 | -17.48 | lagging | mapped_only_needs_news_confirmation |

- 뉴스가 실제 연결한 기업: INTC, GOOG, NVDA
- 뉴스 확인이 더 필요한 테마 후보: RGTI, IONQ, QBTS, QUBT, GOOGL

## GLP-1 And Obesity Drugs
- attention: 58.28, company_support: 78.40, investability: 66.25, verdict: Active Watch
- confidence: high, type: emerging_watch

| ticker | company_narrative_role | company_narrative_score | article_count_7d | source_breadth_7d | bucket_type | price_return_1m | relative_return_1m_spy | price_state | interpretation_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LLY | news_linked_unmapped | 85.27 | 20 | 5 | news_linked | 5.69 | -4.06 | neutral | normal |
| INTC | news_linked_unmapped | 79.20 | 1 | 1 | news_linked | 114.59 | 104.86 | overheated | normal;price_risk |
| WMT | news_linked_unmapped | 67.76 | 1 | 1 | news_linked | 2.89 | -6.84 | neutral | normal |
| NVO | mapped_pure_play_watch | 57.14 | 0 | 0 | pure_play | 21.87 | 12.12 | confirming | mapped_only_needs_news_confirmation |
| HIMS | mapped_watch | 49.51 | 0 | 0 | adopter | 30.15 | 20.41 | confirming | mapped_only_needs_news_confirmation |
| VKTX | mapped_pure_play_watch | 48.21 | 0 | 0 | pure_play | -9.50 | -19.25 | lagging | mapped_only_needs_news_confirmation |
| AMGN | mapped_watch | 44.80 | 0 | 0 | enabler | -5.93 | -15.68 | lagging | mapped_only_needs_news_confirmation |
| PFE | mapped_watch | 44.79 | 0 | 0 | enabler | -6.02 | -15.76 | lagging | mapped_only_needs_news_confirmation |
| MRK | mapped_watch | 44.74 | 0 | 0 | enabler | -6.28 | -16.03 | lagging | mapped_only_needs_news_confirmation |
| TNDM | mapped_watch | 36.74 | 0 | 0 | sympathetic | -0.26 | -10.01 | lagging | mapped_only_needs_news_confirmation |
| DXCM | mapped_watch | 35.75 | 0 | 0 | sympathetic | -6.26 | -16.01 | lagging | mapped_only_needs_news_confirmation |

- 뉴스가 실제 연결한 기업: LLY, INTC, WMT
- 뉴스 확인이 더 필요한 테마 후보: NVO, HIMS, VKTX, AMGN, PFE

## Smartphone And Devices
- attention: 49.41, company_support: 100.00, investability: 65.26, verdict: Active Watch
- confidence: medium, type: emerging_watch

| ticker | company_narrative_role | company_narrative_score | article_count_7d | source_breadth_7d | bucket_type | price_return_1m | relative_return_1m_spy | price_state | interpretation_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AAPL | news_linked_unmapped | 85.68 | 34 | 5 | news_linked | 8.15 | -1.58 | neutral | normal |
| META | news_linked_unmapped | 72.22 | 2 | 2 | news_linked | 5.42 | -4.33 | neutral | normal |
| INTC | news_linked_unmapped | 48.15 | 1 | 1 | news_linked | 114.59 | 104.86 | overheated | normal;price_risk |
| MSFT | news_linked_unmapped | 47.01 | 1 | 1 | news_linked | 10.15 | 0.41 | neutral | normal |
| XOM | news_linked_unmapped | 42.17 | 1 | 1 | news_linked | -5.55 | -15.28 | lagging | normal |

- 뉴스가 실제 연결한 기업: AAPL, META, INTC, MSFT, XOM
- 뉴스 확인이 더 필요한 테마 후보: 없음
