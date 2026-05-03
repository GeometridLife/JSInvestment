# Integrated Narrative x Company Analysis

- 생성 시각: 2026-05-03T17:33:57
- 분석 행 수: 199
- 해석 원칙: theme attention score로 내러티브 열기를 보고, company support score로 실제 기업 연결 품질을 검증한다.
- beneficiary map 후보는 뉴스 직접 연결이 없으면 watchlist로만 본다.

## 통합 우선순위

| theme | attention_score | theme_adjusted_confidence | theme_narrative_type | company_support_score | investability_score | verdict | news_linked_companies | mapped_pure_play_watch |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Data Center Capex | 77.31 | very_high | sustained_narrative | 100.00 | 90.92 | Core Candidate | ORCL, AMD, GOOG, AVGO, AMZN | SMCI, VRT, ANET, DELL |
| Earnings And Buybacks | 65.88 | very_high | sustained_narrative | 100.00 | 86.35 | Core Candidate | AAPL, XOM, LLY, V, META |  |
| Stablecoin And Crypto Policy | 63.62 | very_high | sustained_narrative | 100.00 | 85.45 | Core Candidate | V, INTC, TSLA, AMD, META | CLSK, MARA, MSTR, RIOT, COIN |
| Robotics And Automation | 78.78 | medium | emerging_watch | 93.20 | 74.63 | Active Watch | META, GOOG, AMZN, ORCL, GOOGL | TER, ROK, ZBRA, SYM, ISRG |
| AI Infrastructure | 36.38 | very_high | sustained_narrative | 100.00 | 74.55 | Active Watch | NVDA, AVGO, AMD, GOOGL, MU | ARM, TSM, ASML |
| Smartphone And Devices | 59.75 | medium | emerging_watch | 100.00 | 69.40 | Active Watch | AAPL, GOOG, GOOGL, AVGO, META |  |
| Tariffs And Supply Chain | 46.88 | high | emerging_watch | 100.00 | 69.25 | Active Watch | AAPL, NVDA, AMZN, COST, MSFT |  |
| Regulatory And Legal Risk | 46.84 | medium | emerging_watch | 90.80 | 61.02 | Watch / Validate | INTC, AAPL, XOM, TSLA, LLY |  |
| Quantum Computing | 80.62 | medium | derivative_mention | 85.60 | 59.71 | Watch / Validate | JPM, GOOG, GOOGL, MU, NVDA | RGTI, IONQ, QBTS, QUBT |
| GLP-1 And Obesity Drugs | 43.00 | medium | emerging_watch | 66.40 | 50.94 | Watch / Validate | LLY, INTC | NVO, VKTX |

## Data Center Capex
- attention: 77.31, company_support: 100.00, investability: 90.92, verdict: Core Candidate
- confidence: very_high, type: sustained_narrative

| ticker | company_narrative_role | company_narrative_score | article_count_7d | source_breadth_7d | bucket_type | price_return_1m | relative_return_1m_spy | price_state | interpretation_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ORCL | news_linked_unmapped | 88.52 | 16 | 3 | news_linked | 18.73 | 8.75 | confirming | normal |
| AMD | news_linked_unmapped | 84.74 | 11 | 3 | news_linked | 71.51 | 61.53 | overheated | normal;price_risk |
| GOOG | news_linked_unmapped | 80.15 | 6 | 1 | news_linked | 29.95 | 19.97 | extended | normal;price_risk |
| AVGO | news_linked_unmapped | 79.40 | 3 | 3 | news_linked | 34.38 | 24.40 | extended | normal;price_risk |
| AMZN | news_linked_unmapped | 78.43 | 4 | 2 | news_linked | 27.40 | 17.41 | extended | normal;price_risk |
| MSFT | news_linked_unmapped | 74.83 | 3 | 2 | news_linked | 12.20 | 2.22 | neutral | normal |
| INTC | news_linked_unmapped | 71.80 | 3 | 1 | news_linked | nan | nan | nan | normal |
| MU | news_linked_unmapped | 66.69 | 2 | 1 | news_linked | 47.40 | 37.42 | overheated | normal;price_risk |
| NVDA | news_linked_unmapped | 65.97 | 2 | 1 | news_linked | 12.92 | 2.93 | neutral | normal |
| JPM | news_linked_unmapped | 64.88 | 2 | 1 | news_linked | 6.33 | -3.66 | neutral | normal |
| AAPL | news_linked_unmapped | 62.07 | 2 | 1 | news_linked | nan | nan | nan | normal |
| GOOGL | news_linked_unmapped | 59.09 | 1 | 1 | news_linked | 29.69 | 19.71 | extended | normal;price_risk |

- 뉴스가 실제 연결한 기업: ORCL, AMD, GOOG, AVGO, AMZN
- 뉴스 확인이 더 필요한 테마 후보: 없음

## Earnings And Buybacks
- attention: 65.88, company_support: 100.00, investability: 86.35, verdict: Core Candidate
- confidence: very_high, type: sustained_narrative

| ticker | company_narrative_role | company_narrative_score | article_count_7d | source_breadth_7d | bucket_type | price_return_1m | relative_return_1m_spy | price_state | interpretation_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AAPL | news_linked_unmapped | 85.08 | 59 | 6 | news_linked | nan | nan | nan | normal |
| XOM | news_linked_unmapped | 81.96 | 55 | 5 | news_linked | nan | nan | nan | normal |
| LLY | news_linked_unmapped | 78.41 | 43 | 7 | news_linked | 0.92 | -9.06 | neutral | normal |
| V | news_linked_unmapped | 77.60 | 46 | 4 | news_linked | 9.89 | -0.09 | neutral | normal |
| META | news_linked_unmapped | 74.73 | 28 | 5 | news_linked | 5.10 | -4.89 | neutral | normal |
| AMZN | news_linked_unmapped | 72.95 | 27 | 4 | news_linked | 27.40 | 17.41 | extended | normal;price_risk |
| ORCL | news_linked_unmapped | 69.93 | 23 | 3 | news_linked | 18.73 | 8.75 | confirming | normal |
| GOOGL | news_linked_unmapped | 67.28 | 22 | 5 | news_linked | 29.69 | 19.71 | extended | normal;price_risk |
| MU | news_linked_unmapped | 67.15 | 22 | 4 | news_linked | 47.40 | 37.42 | overheated | normal;price_risk |
| GOOG | news_linked_unmapped | 62.95 | 22 | 3 | news_linked | 29.95 | 19.97 | extended | normal;price_risk |
| AMD | news_linked_unmapped | 61.11 | 21 | 3 | news_linked | 71.51 | 61.53 | overheated | normal;price_risk |
| TSLA | news_linked_unmapped | 56.17 | 20 | 4 | news_linked | 2.51 | -7.48 | neutral | normal |

- 뉴스가 실제 연결한 기업: AAPL, XOM, LLY, V, META
- 뉴스 확인이 더 필요한 테마 후보: 없음

## Stablecoin And Crypto Policy
- attention: 63.62, company_support: 100.00, investability: 85.45, verdict: Core Candidate
- confidence: very_high, type: sustained_narrative

| ticker | company_narrative_role | company_narrative_score | article_count_7d | source_breadth_7d | bucket_type | price_return_1m | relative_return_1m_spy | price_state | interpretation_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| V | news_linked_unmapped | 85.93 | 14 | 4 | news_linked | 9.89 | -0.09 | neutral | normal |
| INTC | news_linked_unmapped | 79.88 | 4 | 1 | news_linked | nan | nan | nan | normal |
| TSLA | news_linked_unmapped | 78.09 | 4 | 1 | news_linked | 2.51 | -7.48 | neutral | normal |
| AMD | news_linked_unmapped | 77.03 | 2 | 2 | news_linked | 71.51 | 61.53 | overheated | normal;price_risk |
| META | news_linked_unmapped | 73.52 | 2 | 1 | news_linked | 5.10 | -4.89 | neutral | normal |
| GOOG | news_linked_unmapped | 70.62 | 1 | 1 | news_linked | 29.95 | 19.97 | extended | normal;price_risk |
| JPM | news_linked_unmapped | 68.22 | 1 | 1 | news_linked | 6.33 | -3.66 | neutral | normal |
| MSTR | mapped_pure_play_watch | 50.10 | 0 | 0 | pure_play | 44.30 | 34.32 | overheated | mapped_only_needs_news_confirmation;price_risk |
| RIOT | mapped_pure_play_watch | 50.10 | 0 | 0 | pure_play | 47.41 | 37.43 | overheated | mapped_only_needs_news_confirmation;price_risk |
| MARA | mapped_pure_play_watch | 50.10 | 0 | 0 | pure_play | 42.54 | 32.55 | overheated | mapped_only_needs_news_confirmation;price_risk |
| CLSK | mapped_pure_play_watch | 50.10 | 0 | 0 | pure_play | 41.18 | 31.20 | overheated | mapped_only_needs_news_confirmation;price_risk |
| COIN | mapped_pure_play_watch | 48.99 | 0 | 0 | pure_play | 10.56 | 0.57 | neutral | mapped_only_needs_news_confirmation |

- 뉴스가 실제 연결한 기업: V, INTC, TSLA, AMD, META
- 뉴스 확인이 더 필요한 테마 후보: MSTR, RIOT, MARA, CLSK, COIN

## Robotics And Automation
- attention: 78.78, company_support: 93.20, investability: 74.63, verdict: Active Watch
- confidence: medium, type: emerging_watch

| ticker | company_narrative_role | company_narrative_score | article_count_7d | source_breadth_7d | bucket_type | price_return_1m | relative_return_1m_spy | price_state | interpretation_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| META | news_linked_unmapped | 85.14 | 6 | 3 | news_linked | 5.10 | -4.89 | neutral | normal |
| GOOG | news_linked_unmapped | 78.04 | 1 | 1 | news_linked | 29.95 | 19.97 | extended | normal;price_risk |
| AMZN | news_linked_unmapped | 77.62 | 1 | 1 | news_linked | 27.40 | 17.41 | extended | normal;price_risk |
| ORCL | news_linked_unmapped | 76.25 | 1 | 1 | news_linked | 18.73 | 8.75 | confirming | normal |
| GOOGL | news_linked_unmapped | 75.05 | 1 | 1 | news_linked | 29.69 | 19.71 | extended | normal;price_risk |
| TSLA | news_linked_unmapped | 72.07 | 1 | 1 | news_linked | 2.51 | -7.48 | neutral | normal |
| TER | mapped_pure_play_watch | 49.20 | 0 | 0 | pure_play | 10.64 | 0.66 | neutral | mapped_only_needs_news_confirmation |
| ROK | mapped_pure_play_watch | 49.17 | 0 | 0 | pure_play | 10.44 | 0.46 | neutral | mapped_only_needs_news_confirmation |
| ZBRA | mapped_pure_play_watch | 49.02 | 0 | 0 | pure_play | 9.55 | -0.43 | neutral | mapped_only_needs_news_confirmation |
| SYM | mapped_pure_play_watch | 48.67 | 0 | 0 | pure_play | 7.42 | -2.56 | neutral | mapped_only_needs_news_confirmation |
| AVGO | mapped_watch | 47.62 | 0 | 0 | enabler | 34.38 | 24.40 | extended | mapped_only_needs_news_confirmation;price_risk |
| AMD | mapped_watch | 46.29 | 0 | 0 | enabler | 71.51 | 61.53 | overheated | mapped_only_needs_news_confirmation;price_risk |

- 뉴스가 실제 연결한 기업: META, GOOG, AMZN, ORCL, GOOGL
- 뉴스 확인이 더 필요한 테마 후보: TER, ROK, ZBRA, SYM, AVGO

## AI Infrastructure
- attention: 36.38, company_support: 100.00, investability: 74.55, verdict: Active Watch
- confidence: very_high, type: sustained_narrative

| ticker | company_narrative_role | company_narrative_score | article_count_7d | source_breadth_7d | bucket_type | price_return_1m | relative_return_1m_spy | price_state | interpretation_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| NVDA | news_linked_unmapped | 86.43 | 8 | 3 | news_linked | 12.92 | 2.93 | neutral | normal |
| AVGO | news_linked_unmapped | 83.02 | 5 | 1 | news_linked | 34.38 | 24.40 | extended | normal;price_risk |
| AMD | news_linked_unmapped | 80.67 | 4 | 2 | news_linked | 71.51 | 61.53 | overheated | normal;price_risk |
| GOOGL | news_linked_unmapped | 78.04 | 4 | 1 | news_linked | 29.69 | 19.71 | extended | normal;price_risk |
| MU | news_linked_unmapped | 74.76 | 3 | 2 | news_linked | 47.40 | 37.42 | overheated | normal;price_risk |
| ORCL | news_linked_unmapped | 74.23 | 3 | 1 | news_linked | 18.73 | 8.75 | confirming | normal |
| LLY | news_linked_unmapped | 63.43 | 1 | 1 | news_linked | 0.92 | -9.06 | neutral | normal |
| GOOG | news_linked_unmapped | 62.52 | 2 | 1 | news_linked | 29.95 | 19.97 | extended | normal;price_risk |
| MSFT | news_linked_unmapped | 57.11 | 1 | 1 | news_linked | 12.20 | 2.22 | neutral | normal |
| INTC | news_linked_unmapped | 56.30 | 1 | 1 | news_linked | nan | nan | nan | normal |
| META | news_linked_unmapped | 55.94 | 1 | 1 | news_linked | 5.10 | -4.89 | neutral | normal |
| ARM | mapped_pure_play_watch | 46.27 | 0 | 0 | pure_play | 36.18 | 26.20 | overheated | mapped_only_needs_news_confirmation;price_risk |

- 뉴스가 실제 연결한 기업: NVDA, AVGO, AMD, GOOGL, MU
- 뉴스 확인이 더 필요한 테마 후보: ARM

## Smartphone And Devices
- attention: 59.75, company_support: 100.00, investability: 69.40, verdict: Active Watch
- confidence: medium, type: emerging_watch

| ticker | company_narrative_role | company_narrative_score | article_count_7d | source_breadth_7d | bucket_type | price_return_1m | relative_return_1m_spy | price_state | interpretation_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AAPL | news_linked_unmapped | 85.50 | 31 | 4 | news_linked | nan | nan | nan | normal |
| GOOG | news_linked_unmapped | 75.96 | 2 | 2 | news_linked | 29.95 | 19.97 | extended | normal;price_risk |
| GOOGL | news_linked_unmapped | 68.77 | 2 | 1 | news_linked | 29.69 | 19.71 | extended | normal;price_risk |
| AVGO | news_linked_unmapped | 47.40 | 1 | 1 | news_linked | 34.38 | 24.40 | extended | normal;price_risk |
| META | news_linked_unmapped | 44.07 | 1 | 1 | news_linked | 5.10 | -4.89 | neutral | normal |
| TSLA | news_linked_unmapped | 43.64 | 1 | 1 | news_linked | 2.51 | -7.48 | neutral | normal |
| LLY | news_linked_unmapped | 43.38 | 1 | 1 | news_linked | 0.92 | -9.06 | neutral | normal |

- 뉴스가 실제 연결한 기업: AAPL, GOOG, GOOGL, AVGO, META
- 뉴스 확인이 더 필요한 테마 후보: 없음

## Tariffs And Supply Chain
- attention: 46.88, company_support: 100.00, investability: 69.25, verdict: Active Watch
- confidence: high, type: emerging_watch

| ticker | company_narrative_role | company_narrative_score | article_count_7d | source_breadth_7d | bucket_type | price_return_1m | relative_return_1m_spy | price_state | interpretation_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AAPL | news_linked_unmapped | 84.79 | 6 | 2 | news_linked | nan | nan | nan | normal |
| NVDA | news_linked_unmapped | 67.86 | 2 | 2 | news_linked | 12.92 | 2.93 | neutral | normal |
| AMZN | news_linked_unmapped | 57.32 | 1 | 1 | news_linked | 27.40 | 17.41 | extended | normal;price_risk |
| COST | news_linked_unmapped | 55.50 | 1 | 1 | news_linked | nan | nan | nan | normal |
| MSFT | news_linked_unmapped | 47.74 | 1 | 1 | news_linked | 12.20 | 2.22 | neutral | normal |
| JPM | news_linked_unmapped | 46.77 | 1 | 1 | news_linked | 6.33 | -3.66 | neutral | normal |
| TSLA | news_linked_unmapped | 46.14 | 1 | 1 | news_linked | 2.51 | -7.48 | neutral | normal |

- 뉴스가 실제 연결한 기업: AAPL, NVDA, AMZN, COST, MSFT
- 뉴스 확인이 더 필요한 테마 후보: 없음

## Regulatory And Legal Risk
- attention: 46.84, company_support: 90.80, investability: 61.02, verdict: Watch / Validate
- confidence: medium, type: emerging_watch

| ticker | company_narrative_role | company_narrative_score | article_count_7d | source_breadth_7d | bucket_type | price_return_1m | relative_return_1m_spy | price_state | interpretation_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| INTC | news_linked_unmapped | 84.67 | 3 | 2 | news_linked | nan | nan | nan | normal |
| AAPL | news_linked_unmapped | 75.50 | 2 | 2 | news_linked | nan | nan | nan | normal |
| XOM | news_linked_unmapped | 49.25 | 1 | 1 | news_linked | nan | nan | nan | normal |
| TSLA | news_linked_unmapped | 48.47 | 1 | 1 | news_linked | 2.51 | -7.48 | neutral | normal |
| LLY | news_linked_unmapped | 48.20 | 1 | 1 | news_linked | 0.92 | -9.06 | neutral | normal |
| JPM | news_linked_unmapped | 42.43 | 1 | 1 | news_linked | 6.33 | -3.66 | neutral | normal |

- 뉴스가 실제 연결한 기업: INTC, AAPL, XOM, TSLA, LLY
- 뉴스 확인이 더 필요한 테마 후보: 없음

## Quantum Computing
- attention: 80.62, company_support: 85.60, investability: 59.71, verdict: Watch / Validate
- confidence: medium, type: derivative_mention

| ticker | company_narrative_role | company_narrative_score | article_count_7d | source_breadth_7d | bucket_type | price_return_1m | relative_return_1m_spy | price_state | interpretation_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| JPM | derivative_news_linked | 82.18 | 2 | 1 | news_linked | 6.33 | -3.66 | neutral | news_linked_but_derivative_theme |
| GOOG | derivative_news_linked | 76.58 | 2 | 2 | news_linked | 29.95 | 19.97 | extended | news_linked_but_derivative_theme;price_risk |
| GOOGL | derivative_news_linked | 67.53 | 1 | 1 | news_linked | 29.69 | 19.71 | extended | news_linked_but_derivative_theme;price_risk |
| MU | derivative_news_linked | 66.98 | 1 | 1 | news_linked | 47.40 | 37.42 | overheated | news_linked_but_derivative_theme;price_risk |
| NVDA | derivative_news_linked | 66.27 | 1 | 1 | news_linked | 12.92 | 2.93 | neutral | news_linked_but_derivative_theme |
| INTC | derivative_news_linked | 65.33 | 1 | 1 | news_linked | nan | nan | nan | news_linked_but_derivative_theme |
| RGTI | mapped_pure_play_watch | 52.89 | 0 | 0 | pure_play | 29.63 | 19.65 | confirming | mapped_only_needs_news_confirmation |
| IONQ | mapped_pure_play_watch | 49.35 | 0 | 0 | pure_play | 66.25 | 56.26 | overheated | mapped_only_needs_news_confirmation;price_risk |
| QBTS | mapped_pure_play_watch | 49.35 | 0 | 0 | pure_play | 49.56 | 39.58 | overheated | mapped_only_needs_news_confirmation;price_risk |
| QUBT | mapped_pure_play_watch | 49.14 | 0 | 0 | pure_play | 38.70 | 28.72 | overheated | mapped_only_needs_news_confirmation;price_risk |
| AMZN | mapped_watch | 40.52 | 0 | 0 | adopter | 27.40 | 17.41 | extended | mapped_only_needs_news_confirmation;price_risk |
| MSFT | mapped_watch | 39.52 | 0 | 0 | adopter | 12.20 | 2.22 | neutral | mapped_only_needs_news_confirmation |

- 뉴스가 실제 연결한 기업: JPM, GOOG, GOOGL, MU, NVDA
- 뉴스 확인이 더 필요한 테마 후보: RGTI, IONQ, QBTS, QUBT, AMZN

## GLP-1 And Obesity Drugs
- attention: 43.00, company_support: 66.40, investability: 50.94, verdict: Watch / Validate
- confidence: medium, type: emerging_watch

| ticker | company_narrative_role | company_narrative_score | article_count_7d | source_breadth_7d | bucket_type | price_return_1m | relative_return_1m_spy | price_state | interpretation_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LLY | news_linked_unmapped | 84.45 | 21 | 5 | news_linked | 0.92 | -9.06 | neutral | normal |
| INTC | news_linked_unmapped | 79.00 | 1 | 1 | news_linked | nan | nan | nan | normal |
| NVO | mapped_pure_play_watch | 58.60 | 0 | 0 | pure_play | 20.29 | 10.30 | confirming | mapped_only_needs_news_confirmation |
| VKTX | mapped_pure_play_watch | 50.02 | 0 | 0 | pure_play | -8.98 | -18.96 | lagging | mapped_only_needs_news_confirmation |
| HIMS | mapped_watch | 47.30 | 0 | 0 | adopter | 38.16 | 28.17 | overheated | mapped_only_needs_news_confirmation;price_risk |
| AMGN | mapped_watch | 46.41 | 0 | 0 | enabler | -6.64 | -16.62 | lagging | mapped_only_needs_news_confirmation |
| MRK | mapped_watch | 46.32 | 0 | 0 | enabler | -7.18 | -17.17 | lagging | mapped_only_needs_news_confirmation |
| PFE | mapped_watch | 46.22 | 0 | 0 | enabler | -7.78 | -17.76 | lagging | mapped_only_needs_news_confirmation |
| TNDM | mapped_watch | 41.29 | 0 | 0 | sympathetic | 3.24 | -6.74 | neutral | mapped_only_needs_news_confirmation |
| DXCM | mapped_watch | 38.23 | 0 | 0 | sympathetic | -1.64 | -11.62 | lagging | mapped_only_needs_news_confirmation |

- 뉴스가 실제 연결한 기업: LLY, INTC
- 뉴스 확인이 더 필요한 테마 후보: NVO, VKTX, HIMS, AMGN, MRK
