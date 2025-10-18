# JYP mk2

~~~md
공개 미러 안내
이 리포는 내부 프로젝트의 공개용 미러입니다.
실데이터(특가/밴리스트), 키/토큰, .env 등은 포함되어 있지 않습니다.
동작 예시는 gas_sample/와 문서로 제공합니다.
~~~

장수레저 예약 문자/특가 관리 자동화 툴  
**Python + Tkinter GUI** / 모듈형 구조

## 🚀 빠른 실행
~~~bash
pip install -r requirements.txt
python app.py
~~~
## 📁 폴더 구조
~~~
jyp/            # 패키지 소스
views/          # 템플릿/리소스
assets/         # 이미지/아이콘 등
특가모음/       # 데이터(원본 미포함, 샘플만)
app.py          # 진입점
launcher.py     # 런처/배포 스크립트
~~~
## 🧩 주요 모듈
`jyp.banlist` : 금지목록 관리
`jyp.specials` : 특가 로직 (달력: jyp.ui.datepickers)
`jyp.utils.*` : 공용 유틸
모듈 관계는 각 파일 헤더의 `Depends on / Used by` 참고

## 🧰 환경(필수)
Python 3.10+ (권장: 3.11.x)
OS: Windows 10/11 (Tkinter GUI)

## 필수 패키지
`pyperclip >= 1.8`
(Pillow는 프로젝트에 vendoring 되어 있어 추가 설치 없이 동작합니다. 외부 설치를 선호한다면 `Pillow>=10`를 `requirements.txt`에 유지하세요.)

## 버전 확인
~~~bash
python --version    # 3.10 이상이어야 함
pip install -r requirements.txt
python app.py
~~~
