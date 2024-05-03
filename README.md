# 서울시 스트레스 데이터 분석 프로젝트

이 프로젝트는 스마트인재개발원 과정의 첫 번째 프로젝트로, 서울시 각 자치구별 스트레스 데이터를 분석하여 원인을 식별하고 인사이트를 도출하는 것을 목표로 합니다.

## 프로젝트 개요

- **목적**: 서울시 각 자치구의 스트레스 원인 분석 및 인사이트 도출
- **기술 스택**: 
  - 백엔드: FastAPI
  - 프론트엔드: Node.js
  - 데이터 처리: Python, CSV, Excel, JSON Server

## 설치 방법

1. 이 저장소를 클론합니다.
    ```bash
    git clone https://github.com/yourusername/seoul-stress-analysis.git
    ```
2. 필요한 라이브러리를 설치합니다.
    ```bash
    pip install -r requirements.txt
    ```
3. JSON Server를 설치합니다 (Node.js 필요).
    ```bash
    npm install -g json-server
    ```

## 로컬에서 사용 방법

1. JSON Server를 시작합니다 (데이터베이스 파일 지정).
    ```bash
    json-server --watch db.json
    ```
2. 백엔드 서버를 시작합니다 (로컬 주소 사용).
    ```bash
    uvicorn main:app --reload --host 127.0.0.1 --port 8000
    ```
3. 프론트엔드 서버를 실행합니다.
    ```bash
    npm start
    ```

## 데이터 구조

- 데이터는 CSV 및 Excel 파일에서 로드되어 JSON Server를 통해 API로 제공됩니다.
- 이 구조는 비정형 데이터를 다루는 API 호출을 모방하기 위해 설계되었습니다.

## 주요 결과

- 스트레스 데이터는 파이썬의 시각화 도구를 사용하여 stacked bar 그래프로 표현되었습니다.
 /* - 분석 결과, 특정 자치구에서 스트레스 원인과 그 영향력에 대한 중요한 인사이트를 제공하였습니다. */
