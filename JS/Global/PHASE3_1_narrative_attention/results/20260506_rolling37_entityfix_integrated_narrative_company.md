# Integrated Narrative x Company Analysis

- 생성 시각: 2026-05-06T00:56:17
- 분석 행 수: 224
- 해석 원칙: theme attention score로 내러티브 열기를 보고, company support score로 실제 기업 연결 품질을 검증한다.
- beneficiary map 후보는 뉴스 직접 연결이 없으면 watchlist로만 본다.

## 통합 우선순위

| theme | attention_score | theme_adjusted_confidence | theme_narrative_type | company_support_score | investability_score | verdict | news_linked_companies | mapped_pure_play_watch |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Data Center Capex | 75.84 | very_high | sustained_narrative | 100.00 | 90.34 | Core Candidate | ORCL, META, AMD, NVDA, INTC | SMCI, VRT, DELL, ANET |
| Stablecoin And Crypto Policy | 70.16 | very_high | sustained_narrative | 100.00 | 88.06 | Core Candidate | V, MSTR, COIN, INTC, META | CLSK, RIOT, MARA |
| Earnings And Buybacks | 70.09 | very_high | sustained_narrative | 100.00 | 88.04 | Core Candidate | AAPL, META, LLY, XOM, AMD |  |
| Robotics And Automation | 77.34 | high | sustained_narrative | 100.00 | 86.44 | Core Candidate | META, MSFT, AMZN, GOOG, NVDA | TER, ROK, SYM, ZBRA, ISRG |
| Tariffs And Supply Chain | 42.84 | very_high | sustained_narrative | 100.00 | 77.14 | Core Candidate | AAPL, AMZN, INTC, NVDA, MSFT |  |
| Regulatory And Legal Risk | 53.41 | high | sustained_narrative | 100.00 | 76.86 | Core Candidate | TSLA, INTC, AAPL, XOM, META |  |
| AI Infrastructure | 39.78 | very_high | sustained_narrative | 100.00 | 75.91 | Core Candidate | AVGO, NVDA, INTC, AMD, MU | ARM, ASML, TSM |
| Quantum Computing | 82.84 | high | sustained_narrative | 56.00 | 73.24 | Active Watch | INTC, NVDA, GOOG | RGTI, IONQ, QBTS, QUBT |
| GLP-1 And Obesity Drugs | 58.28 | high | emerging_watch | 78.40 | 66.25 | Active Watch | LLY, INTC, WMT | NVO, VKTX |
| Smartphone And Devices | 49.41 | medium | emerging_watch | 100.00 | 65.26 | Active Watch | AAPL, META, INTC, MSFT, XOM |  |

## Data Center Capex
- attention: 75.84, company_support: 100.00, investability: 90.34, verdict: Core Candidate
- confidence: very_high, type: sustained_narrative

| ticker | company_narrative_role | company_narrative_score | article_count_7d | source_breadth_7d | explicit_mention_count_7d | bucket_type | price_return_1m | relative_return_1m_spy | price_state | interpretation_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ORCL | explicit_news_linked | 91.65 | 10 | 3 | 2 | explicit_news_linked | 26.18 | 16.43 | confirming | normal |
| META | explicit_news_linked | 88.81 | 16 | 3 | 10 | explicit_news_linked | 5.22 | -4.52 | neutral | normal |
| AMD | explicit_news_linked | 84.32 | 8 | 2 | 6 | explicit_news_linked | 61.31 | 51.57 | overheated | normal;price_risk |
| NVDA | explicit_news_linked | 72.94 | 3 | 1 | 1 | explicit_news_linked | 11.03 | 1.29 | neutral | normal |
| INTC | api_related_indirect | 71.63 | 8 | 1 | 0 | api_related_news | 114.59 | 104.86 | overheated | normal;price_risk |
| AMZN | api_related_indirect | 69.99 | 4 | 3 | 0 | api_related_news | 29.65 | 19.91 | extended | normal;price_risk |
| JPM | api_related_indirect | 66.81 | 5 | 1 | 0 | api_related_news | 4.78 | -4.97 | neutral | normal |
| AVGO | api_related_indirect | 65.23 | 3 | 2 | 0 | api_related_news | 35.99 | 26.25 | overheated | normal;price_risk |
| MU | api_related_indirect | 59.52 | 2 | 2 | 0 | api_related_news | 70.81 | 61.07 | overheated | normal;price_risk |
| MSFT | api_related_indirect | 58.32 | 2 | 2 | 0 | api_related_news | 9.84 | 0.09 | neutral | normal |
| GOOG | api_related_indirect | 58.10 | 2 | 1 | 0 | api_related_news | 29.25 | 19.51 | extended | normal;price_risk |
| LLY | api_related_indirect | 55.72 | 2 | 2 | 0 | api_related_news | 5.77 | -3.98 | neutral | normal |

- 뉴스가 실제 연결한 기업: ORCL, META, AMD, NVDA, INTC
- 뉴스 확인이 더 필요한 테마 후보: 없음

## Stablecoin And Crypto Policy
- attention: 70.16, company_support: 100.00, investability: 88.06, verdict: Core Candidate
- confidence: very_high, type: sustained_narrative

| ticker | company_narrative_role | company_narrative_score | article_count_7d | source_breadth_7d | explicit_mention_count_7d | bucket_type | price_return_1m | relative_return_1m_spy | price_state | interpretation_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| V | explicit_news_linked | 89.05 | 10 | 3 | 8 | explicit_news_linked | 5.62 | -4.12 | neutral | normal |
| MSTR | explicit_news_linked | 87.92 | 6 | 3 | 5 | explicit_news_linked | 46.50 | 36.75 | overheated | normal;price_risk |
| COIN | explicit_news_linked | 81.40 | 3 | 2 | 2 | explicit_news_linked | 12.94 | 3.19 | neutral | normal |
| INTC | api_related_indirect | 73.96 | 6 | 1 | 0 | api_related_news | 114.59 | 104.86 | overheated | normal;price_risk |
| META | explicit_news_linked | 69.82 | 2 | 1 | 1 | explicit_news_linked | 5.22 | -4.52 | neutral | normal |
| TSLA | api_related_indirect | 68.85 | 3 | 1 | 0 | api_related_news | 11.38 | 1.64 | neutral | normal |
| CRCL | explicit_news_linked | 65.80 | 1 | 1 | 1 | explicit_news_linked | 27.33 | 17.58 | confirming | normal |
| AMD | api_related_indirect | 64.07 | 2 | 2 | 0 | api_related_news | 61.31 | 51.57 | overheated | normal;price_risk |
| NVDA | api_related_indirect | 60.78 | 2 | 1 | 0 | api_related_news | 11.03 | 1.29 | neutral | normal |
| AAPL | api_related_indirect | 60.30 | 2 | 1 | 0 | api_related_news | 8.15 | -1.58 | neutral | normal |
| JPM | api_related_indirect | 59.74 | 2 | 1 | 0 | api_related_news | 4.78 | -4.97 | neutral | normal |
| GOOG | api_related_indirect | 53.12 | 1 | 1 | 0 | api_related_news | 29.25 | 19.51 | extended | normal;price_risk |

- 뉴스가 실제 연결한 기업: V, MSTR, COIN, INTC, META
- 뉴스 확인이 더 필요한 테마 후보: 없음

## Earnings And Buybacks
- attention: 70.09, company_support: 100.00, investability: 88.04, verdict: Core Candidate
- confidence: very_high, type: sustained_narrative

| ticker | company_narrative_role | company_narrative_score | article_count_7d | source_breadth_7d | explicit_mention_count_7d | bucket_type | price_return_1m | relative_return_1m_spy | price_state | interpretation_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AAPL | explicit_news_linked | 87.95 | 60 | 6 | 5 | explicit_news_linked | 8.15 | -1.58 | neutral | normal |
| META | explicit_news_linked | 87.46 | 61 | 5 | 16 | explicit_news_linked | 5.22 | -4.52 | neutral | normal |
| LLY | explicit_news_linked | 81.97 | 47 | 7 | 8 | explicit_news_linked | 5.77 | -3.98 | neutral | normal |
| XOM | explicit_news_linked | 79.59 | 56 | 5 | 6 | explicit_news_linked | -5.55 | -15.28 | lagging | normal |
| AMD | explicit_news_linked | 78.27 | 36 | 4 | 17 | explicit_news_linked | 61.31 | 51.57 | overheated | normal;price_risk |
| AMZN | explicit_news_linked | 76.72 | 25 | 4 | 1 | explicit_news_linked | 29.65 | 19.91 | extended | normal;price_risk |
| INTC | api_related_indirect | 70.00 | 51 | 3 | 0 | api_related_news | 114.59 | 104.86 | overheated | normal;price_risk |
| MSFT | explicit_news_linked | 69.76 | 18 | 4 | 2 | explicit_news_linked | 9.84 | 0.09 | neutral | normal |
| V | explicit_news_linked | 69.35 | 20 | 3 | 2 | explicit_news_linked | 5.62 | -4.12 | neutral | normal |
| NVDA | explicit_news_linked | 66.79 | 20 | 3 | 1 | explicit_news_linked | 11.03 | 1.29 | neutral | normal |
| GOOG | explicit_news_linked | 63.68 | 15 | 3 | 1 | explicit_news_linked | 29.25 | 19.51 | extended | normal;price_risk |
| ORCL | api_related_indirect | 61.46 | 16 | 4 | 0 | api_related_news | 26.18 | 16.43 | confirming | normal |

- 뉴스가 실제 연결한 기업: AAPL, META, LLY, XOM, AMD
- 뉴스 확인이 더 필요한 테마 후보: 없음

## Robotics And Automation
- attention: 77.34, company_support: 100.00, investability: 86.44, verdict: Core Candidate
- confidence: high, type: sustained_narrative

| ticker | company_narrative_role | company_narrative_score | article_count_7d | source_breadth_7d | explicit_mention_count_7d | bucket_type | price_return_1m | relative_return_1m_spy | price_state | interpretation_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| META | explicit_news_linked | 87.22 | 5 | 3 | 5 | explicit_news_linked | 5.22 | -4.52 | neutral | normal |
| MSFT | api_related_indirect | 77.45 | 5 | 2 | 0 | api_related_news | 9.84 | 0.09 | neutral | normal |
| AMZN | api_related_indirect | 74.62 | 3 | 1 | 0 | api_related_news | 29.65 | 19.91 | extended | normal;price_risk |
| GOOG | api_related_indirect | 69.68 | 2 | 1 | 0 | api_related_news | 29.25 | 19.51 | extended | normal;price_risk |
| NVDA | api_related_indirect | 67.13 | 2 | 1 | 0 | api_related_news | 11.03 | 1.29 | neutral | normal |
| ORCL | api_related_indirect | 64.41 | 1 | 1 | 0 | api_related_news | 26.18 | 16.43 | confirming | normal |
| TSLA | api_related_indirect | 60.47 | 1 | 1 | 0 | api_related_news | 11.38 | 1.64 | neutral | normal |
| OKLO | api_related_indirect | 59.76 | 1 | 1 | 0 | api_related_news | nan | nan | nan | normal |
| TER | mapped_pure_play_watch | 49.10 | 0 | 0 | 0 | pure_play | 15.41 | 5.66 | confirming | mapped_only_needs_news_confirmation |
| ROK | mapped_pure_play_watch | 46.95 | 0 | 0 | 0 | pure_play | 20.54 | 10.80 | extended | mapped_only_needs_news_confirmation;price_risk |
| SYM | mapped_pure_play_watch | 46.40 | 0 | 0 | 0 | pure_play | 8.12 | -1.62 | neutral | mapped_only_needs_news_confirmation |
| ZBRA | mapped_pure_play_watch | 46.19 | 0 | 0 | 0 | pure_play | 6.85 | -2.89 | neutral | mapped_only_needs_news_confirmation |

- 뉴스가 실제 연결한 기업: META, MSFT, AMZN, GOOG, NVDA
- 뉴스 확인이 더 필요한 테마 후보: TER, ROK, SYM, ZBRA

## Tariffs And Supply Chain
- attention: 42.84, company_support: 100.00, investability: 77.14, verdict: Core Candidate
- confidence: very_high, type: sustained_narrative

| ticker | company_narrative_role | company_narrative_score | article_count_7d | source_breadth_7d | explicit_mention_count_7d | bucket_type | price_return_1m | relative_return_1m_spy | price_state | interpretation_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AAPL | explicit_news_linked | 83.57 | 6 | 2 | 1 | explicit_news_linked | 8.15 | -1.58 | neutral | normal |
| AMZN | api_related_indirect | 79.50 | 14 | 3 | 0 | api_related_news | 29.65 | 19.91 | extended | normal;price_risk |
| INTC | api_related_indirect | 60.04 | 3 | 2 | 0 | api_related_news | 114.59 | 104.86 | overheated | normal;price_risk |
| NVDA | api_related_indirect | 53.21 | 2 | 2 | 0 | api_related_news | 11.03 | 1.29 | neutral | normal |
| MSFT | api_related_indirect | 48.56 | 2 | 1 | 0 | api_related_news | 9.84 | 0.09 | neutral | normal |
| AMD | api_related_indirect | 38.09 | 1 | 1 | 0 | api_related_news | 61.31 | 51.57 | overheated | normal;price_risk |
| TSLA | api_related_indirect | 37.15 | 1 | 1 | 0 | api_related_news | 11.38 | 1.64 | neutral | normal |
| JPM | api_related_indirect | 36.06 | 1 | 1 | 0 | api_related_news | 4.78 | -4.97 | neutral | normal |
| WMT | api_related_indirect | 35.75 | 1 | 1 | 0 | api_related_news | 2.89 | -6.84 | neutral | normal |

- 뉴스가 실제 연결한 기업: AAPL, AMZN, INTC, NVDA, MSFT
- 뉴스 확인이 더 필요한 테마 후보: 없음

## Regulatory And Legal Risk
- attention: 53.41, company_support: 100.00, investability: 76.86, verdict: Core Candidate
- confidence: high, type: sustained_narrative

| ticker | company_narrative_role | company_narrative_score | article_count_7d | source_breadth_7d | explicit_mention_count_7d | bucket_type | price_return_1m | relative_return_1m_spy | price_state | interpretation_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TSLA | api_related_indirect | 80.21 | 6 | 4 | 0 | api_related_news | 11.38 | 1.64 | neutral | normal |
| INTC | api_related_indirect | 70.44 | 4 | 2 | 0 | api_related_news | 114.59 | 104.86 | overheated | normal;price_risk |
| AAPL | api_related_indirect | 57.18 | 2 | 2 | 0 | api_related_news | 8.15 | -1.58 | neutral | normal |
| XOM | api_related_indirect | 52.67 | 2 | 2 | 0 | api_related_news | -5.55 | -15.28 | lagging | normal |
| META | explicit_news_linked | 44.19 | 1 | 1 | 1 | explicit_news_linked | 5.22 | -4.52 | neutral | normal |
| AMZN | api_related_indirect | 36.72 | 1 | 1 | 0 | api_related_news | 29.65 | 19.91 | extended | normal;price_risk |
| JPM | api_related_indirect | 29.83 | 1 | 1 | 0 | api_related_news | 4.78 | -4.97 | neutral | normal |

- 뉴스가 실제 연결한 기업: TSLA, INTC, AAPL, XOM, META
- 뉴스 확인이 더 필요한 테마 후보: 없음

## AI Infrastructure
- attention: 39.78, company_support: 100.00, investability: 75.91, verdict: Core Candidate
- confidence: very_high, type: sustained_narrative

| ticker | company_narrative_role | company_narrative_score | article_count_7d | source_breadth_7d | explicit_mention_count_7d | bucket_type | price_return_1m | relative_return_1m_spy | price_state | interpretation_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AVGO | explicit_news_linked | 80.95 | 4 | 1 | 2 | explicit_news_linked | 35.99 | 26.25 | overheated | normal;price_risk |
| NVDA | api_related_indirect | 79.72 | 14 | 3 | 0 | api_related_news | 11.03 | 1.29 | neutral | normal |
| INTC | api_related_indirect | 75.50 | 8 | 1 | 0 | api_related_news | 114.59 | 104.86 | overheated | normal;price_risk |
| AMD | api_related_indirect | 73.11 | 4 | 3 | 0 | api_related_news | 61.31 | 51.57 | overheated | normal;price_risk |
| MU | api_related_indirect | 69.30 | 3 | 3 | 0 | api_related_news | 70.81 | 61.07 | overheated | normal;price_risk |
| GOOG | api_related_indirect | 61.22 | 4 | 1 | 0 | api_related_news | 29.25 | 19.51 | extended | normal;price_risk |
| ORCL | api_related_indirect | 59.91 | 3 | 1 | 0 | api_related_news | 26.18 | 16.43 | confirming | normal |
| MSFT | explicit_news_linked | 59.63 | 1 | 1 | 1 | explicit_news_linked | 9.84 | 0.09 | neutral | normal |
| AMZN | api_related_indirect | 59.22 | 1 | 1 | 0 | api_related_news | 29.65 | 19.91 | extended | normal;price_risk |
| OKLO | api_related_indirect | 57.00 | 1 | 1 | 0 | api_related_news | nan | nan | nan | normal |
| META | api_related_indirect | 54.63 | 2 | 2 | 0 | api_related_news | 5.22 | -4.52 | neutral | normal |
| TSLA | api_related_indirect | 49.88 | 1 | 1 | 0 | api_related_news | 11.38 | 1.64 | neutral | normal |

- 뉴스가 실제 연결한 기업: AVGO, NVDA, INTC, AMD, MU
- 뉴스 확인이 더 필요한 테마 후보: 없음

## Quantum Computing
- attention: 82.84, company_support: 56.00, investability: 73.24, verdict: Active Watch
- confidence: high, type: sustained_narrative

| ticker | company_narrative_role | company_narrative_score | article_count_7d | source_breadth_7d | explicit_mention_count_7d | bucket_type | price_return_1m | relative_return_1m_spy | price_state | interpretation_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| INTC | explicit_news_linked | 81.92 | 6 | 3 | 2 | explicit_news_linked | 114.59 | 104.86 | overheated | normal;price_risk |
| NVDA | explicit_news_linked | 74.38 | 1 | 1 | 1 | explicit_news_linked | 11.03 | 1.29 | neutral | normal |
| GOOG | api_related_indirect | 68.58 | 3 | 1 | 0 | api_related_news | 29.25 | 19.51 | extended | normal;price_risk |
| RGTI | mapped_pure_play_watch | 60.10 | 0 | 0 | 0 | pure_play | 25.85 | 16.10 | confirming | mapped_only_needs_news_confirmation |
| IONQ | mapped_pure_play_watch | 57.16 | 0 | 0 | 0 | pure_play | 59.82 | 50.07 | overheated | mapped_only_needs_news_confirmation;price_risk |
| QBTS | mapped_pure_play_watch | 57.16 | 0 | 0 | 0 | pure_play | 50.11 | 40.36 | overheated | mapped_only_needs_news_confirmation;price_risk |
| QUBT | mapped_pure_play_watch | 56.76 | 0 | 0 | 0 | pure_play | 37.39 | 27.65 | overheated | mapped_only_needs_news_confirmation;price_risk |
| GOOGL | mapped_watch | 53.71 | 0 | 0 | 0 | enabler | 29.53 | 19.78 | extended | mapped_only_needs_news_confirmation;price_risk |
| AMZN | mapped_watch | 48.73 | 0 | 0 | 0 | adopter | 29.65 | 19.91 | extended | mapped_only_needs_news_confirmation;price_risk |
| MSFT | mapped_watch | 46.96 | 0 | 0 | 0 | adopter | 9.84 | 0.09 | neutral | mapped_only_needs_news_confirmation |
| IBM | mapped_watch | 46.84 | 0 | 0 | 0 | enabler | -7.55 | -17.29 | lagging | mapped_only_needs_news_confirmation |
| HON | mapped_watch | 46.84 | 0 | 0 | 0 | enabler | -7.56 | -17.30 | lagging | mapped_only_needs_news_confirmation |

- 뉴스가 실제 연결한 기업: INTC, NVDA, GOOG
- 뉴스 확인이 더 필요한 테마 후보: RGTI, IONQ, QBTS, QUBT, GOOGL

## GLP-1 And Obesity Drugs
- attention: 58.28, company_support: 78.40, investability: 66.25, verdict: Active Watch
- confidence: high, type: emerging_watch

| ticker | company_narrative_role | company_narrative_score | article_count_7d | source_breadth_7d | explicit_mention_count_7d | bucket_type | price_return_1m | relative_return_1m_spy | price_state | interpretation_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LLY | explicit_news_linked | 89.28 | 20 | 5 | 1 | explicit_news_linked | 5.77 | -3.98 | neutral | normal |
| INTC | api_related_indirect | 73.20 | 1 | 1 | 0 | api_related_news | 114.59 | 104.86 | overheated | normal;price_risk |
| WMT | api_related_indirect | 61.76 | 1 | 1 | 0 | api_related_news | 2.89 | -6.84 | neutral | normal |
| NVO | mapped_pure_play_watch | 57.14 | 0 | 0 | 0 | pure_play | 21.87 | 12.13 | confirming | mapped_only_needs_news_confirmation |
| HIMS | mapped_watch | 49.30 | 0 | 0 | 0 | adopter | 28.92 | 19.18 | confirming | mapped_only_needs_news_confirmation |
| VKTX | mapped_pure_play_watch | 48.13 | 0 | 0 | 0 | pure_play | -9.99 | -19.73 | lagging | mapped_only_needs_news_confirmation |
| AMGN | mapped_watch | 44.79 | 0 | 0 | 0 | enabler | -6.01 | -15.76 | lagging | mapped_only_needs_news_confirmation |
| PFE | mapped_watch | 44.77 | 0 | 0 | 0 | enabler | -6.13 | -15.87 | lagging | mapped_only_needs_news_confirmation |
| MRK | mapped_watch | 44.76 | 0 | 0 | 0 | enabler | -6.19 | -15.94 | lagging | mapped_only_needs_news_confirmation |
| TNDM | mapped_watch | 39.01 | 0 | 0 | 0 | sympathetic | -0.13 | -9.87 | neutral | mapped_only_needs_news_confirmation |
| DXCM | mapped_watch | 35.71 | 0 | 0 | 0 | sympathetic | -6.52 | -16.26 | lagging | mapped_only_needs_news_confirmation |

- 뉴스가 실제 연결한 기업: LLY, INTC, WMT
- 뉴스 확인이 더 필요한 테마 후보: NVO, HIMS, VKTX, AMGN, PFE

## Smartphone And Devices
- attention: 49.41, company_support: 100.00, investability: 65.26, verdict: Active Watch
- confidence: medium, type: emerging_watch

| ticker | company_narrative_role | company_narrative_score | article_count_7d | source_breadth_7d | explicit_mention_count_7d | bucket_type | price_return_1m | relative_return_1m_spy | price_state | interpretation_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AAPL | explicit_news_linked | 89.68 | 34 | 5 | 3 | explicit_news_linked | 8.15 | -1.58 | neutral | normal |
| META | api_related_indirect | 66.19 | 2 | 2 | 0 | api_related_news | 5.22 | -4.52 | neutral | normal |
| INTC | api_related_indirect | 42.15 | 1 | 1 | 0 | api_related_news | 114.59 | 104.86 | overheated | normal;price_risk |
| MSFT | api_related_indirect | 40.95 | 1 | 1 | 0 | api_related_news | 9.84 | 0.09 | neutral | normal |
| XOM | api_related_indirect | 36.17 | 1 | 1 | 0 | api_related_news | -5.55 | -15.28 | lagging | normal |

- 뉴스가 실제 연결한 기업: AAPL, META, INTC, MSFT, XOM
- 뉴스 확인이 더 필요한 테마 후보: 없음
