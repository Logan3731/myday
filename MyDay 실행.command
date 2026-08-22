#!/bin/bash
# MyDay 실행 스크립트
# 파인더에서 이 파일을 더블클릭하면 앱이 열립니다.

# 이 파일이 있는 폴더로 이동 (어디서 실행하든 동작하도록)
cd "$(dirname "$0")" || exit 1

# 처음 실행이면 준비 작업부터 (가상환경 + 라이브러리 설치)
if [ ! -x "venv/bin/streamlit" ]; then
    echo "처음 실행이라 준비 중이에요. 1~2분 걸립니다..."
    echo

    if ! python3 -m venv venv; then
        echo
        echo "❌ python3 을 찾지 못했어요. 파이썬을 먼저 설치해주세요."
        read -n 1 -s -r -p "아무 키나 누르면 창이 닫힙니다."
        exit 1
    fi

    ./venv/bin/pip install -q -r requirements.txt
    echo "✅ 준비 끝!"
    echo
fi

echo "MyDay 를 켜는 중이에요. 잠시 후 브라우저가 열립니다."
echo "끄려면 이 검은 창에서 Control + C 를 누르거나, 창을 닫으세요."
echo

./venv/bin/streamlit run app.py
