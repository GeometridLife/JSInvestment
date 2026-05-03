# Narrative x Company Analysis

- 생성 시각: 2026-05-03T17:31:48
- 분석 행 수: 199
- 해석 원칙: 기사에서 실제 연결된 ticker를 우선하고, beneficiary map 후보는 보조 watchlist로만 본다.

## 1. Quantum Computing
- attention: 80.62, confidence: medium, type: derivative_mention

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

## 2. Robotics And Automation
- attention: 78.78, confidence: medium, type: emerging_watch

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

## 3. Data Center Capex
- attention: 77.31, confidence: very_high, type: sustained_narrative

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

## 4. Grid And Power Equipment
- attention: 72.25, confidence: low, type: noise_possible

| ticker | company_narrative_role | company_narrative_score | article_count_7d | source_breadth_7d | bucket_type | price_return_1m | relative_return_1m_spy | price_state | interpretation_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GOOGL | news_linked_unmapped | 84.41 | 1 | 1 | news_linked | 29.69 | 19.71 | extended | normal;price_risk |
| ORCL | news_linked_unmapped | 78.37 | 2 | 1 | news_linked | 18.73 | 8.75 | confirming | normal |
| JPM | news_linked_unmapped | 72.06 | 1 | 1 | news_linked | 6.33 | -3.66 | neutral | normal |
| GEV | mapped_pure_play_watch | 59.23 | 0 | 0 | pure_play | 18.79 | 8.81 | confirming | mapped_only_needs_news_confirmation |
| VRT | mapped_pure_play_watch | 57.52 | 0 | 0 | pure_play | 26.58 | 16.60 | extended | mapped_only_needs_news_confirmation;price_risk |
| BE | mapped_pure_play_watch | 57.48 | 0 | 0 | pure_play | 119.34 | 109.36 | overheated | mapped_only_needs_news_confirmation;price_risk |
| ETN | mapped_pure_play_watch | 55.84 | 0 | 0 | pure_play | 16.41 | 6.43 | extended | mapped_only_needs_news_confirmation;price_risk |
| CEG | mapped_watch | 52.31 | 0 | 0 | enabler | 10.14 | 0.16 | neutral | mapped_only_needs_news_confirmation |
| FSLR | mapped_watch | 51.65 | 0 | 0 | enabler | 6.16 | -3.82 | neutral | mapped_only_needs_news_confirmation |
| FLNC | mapped_pure_play_watch | 51.33 | 0 | 0 | pure_play | -6.37 | -16.36 | lagging | mapped_only_needs_news_confirmation |
| VST | mapped_watch | 50.78 | 0 | 0 | enabler | 0.86 | -9.13 | neutral | mapped_only_needs_news_confirmation |
| GOOG | mapped_watch | 49.08 | 0 | 0 | adopter | 29.95 | 19.97 | extended | mapped_only_needs_news_confirmation;price_risk |

- 뉴스가 실제 연결한 기업: GOOGL, ORCL, JPM
- 뉴스 확인이 더 필요한 테마 후보: GEV, VRT, BE, ETN, CEG

## 5. Reshoring And Manufacturing
- attention: 66.19, confidence: low, type: noise_possible

| ticker | company_narrative_role | company_narrative_score | article_count_7d | source_breadth_7d | bucket_type | price_return_1m | relative_return_1m_spy | price_state | interpretation_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| JNJ | news_linked_unmapped | 85.50 | 1 | 1 | news_linked | nan | nan | nan | normal |

- 뉴스가 실제 연결한 기업: JNJ
- 뉴스 확인이 더 필요한 테마 후보: 없음

## 6. Earnings And Buybacks
- attention: 65.88, confidence: very_high, type: sustained_narrative

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

## 7. Stablecoin And Crypto Policy
- attention: 63.62, confidence: very_high, type: sustained_narrative

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

## 8. Smartphone And Devices
- attention: 59.75, confidence: medium, type: emerging_watch

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

## 9. Nuclear Renaissance
- attention: 59.69, confidence: low, type: noise_possible

| ticker | company_narrative_role | company_narrative_score | article_count_7d | source_breadth_7d | bucket_type | price_return_1m | relative_return_1m_spy | price_state | interpretation_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| NVDA | news_linked_unmapped | 86.43 | 1 | 1 | news_linked | 12.92 | 2.93 | neutral | normal |

- 뉴스가 실제 연결한 기업: NVDA
- 뉴스 확인이 더 필요한 테마 후보: 없음

## 10. Tariffs And Supply Chain
- attention: 46.88, confidence: high, type: emerging_watch

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
