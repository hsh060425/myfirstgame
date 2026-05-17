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
파이인스톨러를 에셋파일을 넣어서 사용할려면 어떻게 해야해
--add-data "엣셋폴더이름;만든 파일안의 명칭"으로  하면됩니다
pyinstaller에서 옵션들은 뭐가있어
-F,D,W,C,i,name,add data,add birary 등등 여러가지 있습니다
빌드를  하면  spec이 생기는데 거기서 무엇을 할수있어?
-여러 개의 파일을 한꺼번에 포함 ,특정 파일이나 라이브러리 제외,코드 실행 전후에 작업 추가,실행 파일에 여러 개의 파이썬 파일 포함,실행 환경에 따른 커스터마이징