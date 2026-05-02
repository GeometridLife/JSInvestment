from edgar import set_identity, Company

set_identity("Sang Il test@example.com")

# 애플 최신 10-K 가져오기
apple = Company("AAPL")
tenk = apple.get_filings(form="10-K").latest()
print(tenk)

# HTML/텍스트로 변환
print(tenk.text()[:1000])  # 본문 앞 1000자