# JSInvestment
it's for investment

## 환경 설정

Python 3.12 가상환경(`js_env`)을 생성하고 필요한 패키지를 설치합니다.

**설치 패키지:** pandas 2.2.3, numpy 1.26.4, matplotlib 3.9.2, seaborn 0.13.2

### 실행 방법

```bash
# 1. 실행 권한 부여
chmod +x setup_js_env.sh

# 2. 실행
./setup_js_env.sh
```

conda가 설치되어 있으면 conda 환경으로, 없으면 venv 환경으로 자동 생성됩니다.

### 환경 활성화

**conda 사용 시**
```bash
conda activate js_env
```

**venv 사용 시**
```bash
source js_env/bin/activate
```
