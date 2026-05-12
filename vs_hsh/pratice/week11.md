# Week 11 실습
## 오늘 한 것
- PyInstaller 설치 및 빌드
- resource_path() 함수 추가
- --add-data 옵션으로 에셋 포함
- .exe 실행 확인
## resource_path() 를 써야 하는 이유
리소스 패스를 쓰는이유는 pyinstaller에서 실행파일을 만들때 에셋폴더나 이미지 같은 폴더를 저장한 위치를 임시 파일로 저장을 하는데 그저장한 파일의 위치를 찾아오고 적용시키기위해서 쓰는것이다
## 빌드 명령어
pyinstaller spaceshootercopy2.py
pyinstaller --onefile --noconsole --add-data "assets;assets" spaceshootercopy2.py
## AI 활용 
