#!/bin/bash

ENV_NAME="js_env"
PYTHON_VERSION="3.12"

echo "======================================"
echo "  js_env 환경 설정 시작"
echo "======================================"

# conda 또는 python 확인
if command -v conda &> /dev/null; then
    echo "[1/4] conda 감지 → conda 환경으로 생성합니다."

    # 기존 환경 존재 여부 확인
    if conda env list | grep -q "^${ENV_NAME}"; then
        echo "[!] '${ENV_NAME}' 환경이 이미 존재합니다. 삭제 후 재생성합니다."
        conda env remove -n $ENV_NAME -y
    fi

    echo "[2/4] Python ${PYTHON_VERSION} 환경 생성 중..."
    conda create -n $ENV_NAME python=$PYTHON_VERSION -y

    echo "[3/4] 패키지 설치 중..."
    conda run -n $ENV_NAME pip install \
        pandas==2.2.3 \
        numpy==1.26.4 \
        matplotlib==3.9.2 \
        seaborn==0.13.2

    echo "[4/4] 설치 완료!"
    echo ""
    echo "======================================"
    echo "  환경 활성화 방법:"
    echo "  conda activate ${ENV_NAME}"
    echo "======================================"

else
    echo "[1/4] conda 없음 → venv 환경으로 생성합니다."

    # python3.12 존재 확인
    if ! command -v python3.12 &> /dev/null; then
        echo "[ERROR] python3.12 이 설치되어 있지 않습니다."
        echo "  설치 방법 (Mac): brew install python@3.12"
        echo "  설치 방법 (Ubuntu): sudo apt install python3.12 python3.12-venv"
        exit 1
    fi

    # 기존 환경 존재 여부 확인
    if [ -d "$ENV_NAME" ]; then
        echo "[!] '${ENV_NAME}' 폴더가 이미 존재합니다. 삭제 후 재생성합니다."
        rm -rf $ENV_NAME
    fi

    echo "[2/4] Python ${PYTHON_VERSION} venv 환경 생성 중..."
    python3.12 -m venv $ENV_NAME

    echo "[3/4] 패키지 설치 중..."
    ./$ENV_NAME/bin/pip install --upgrade pip
    ./$ENV_NAME/bin/pip install \
        pandas==2.2.3 \
        numpy==1.26.4 \
        matplotlib==3.9.2 \
        seaborn==0.13.2

    echo "[4/4] 설치 완료!"
    echo ""
    echo "======================================"
    echo "  환경 활성화 방법:"
    echo "  source ${ENV_NAME}/bin/activate"
    echo "======================================"
fi

echo ""
echo "설치된 패키지 버전 확인:"
echo "--------------------------------------"

if command -v conda &> /dev/null; then
    conda run -n $ENV_NAME python -c "
import pandas as pd
import numpy as np
import matplotlib
import seaborn as sns
print(f'pandas     : {pd.__version__}')
print(f'numpy      : {np.__version__}')
print(f'matplotlib : {matplotlib.__version__}')
print(f'seaborn    : {sns.__version__}')
"
else
    ./$ENV_NAME/bin/python -c "
import pandas as pd
import numpy as np
import matplotlib
import seaborn as sns
print(f'pandas     : {pd.__version__}')
print(f'numpy      : {np.__version__}')
print(f'matplotlib : {matplotlib.__version__}')
print(f'seaborn    : {sns.__version__}')
"
fi

echo "======================================"
echo "  js_env 설정 완료!"
echo "======================================"