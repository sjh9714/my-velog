# Velog Thumbnails

Velog 시리즈와 게시글에 사용할 썸네일 이미지 모음입니다.

## 생성 방법

썸네일은 시리즈별 공통 AI 배경 위에 로컬 Markdown 제목을 HTML/CSS 포스터 템플릿으로 얹은 뒤, Playwright CLI와 설치된 Google Chrome으로 PNG 캡처합니다.

루트 디렉터리에서 아래 명령을 실행합니다.

```bash
python3 tools/generate_thumbnails.py
```

생성된 이미지가 모두 올바른 크기인지 확인하려면 아래 명령을 실행합니다.

```bash
python3 tools/generate_thumbnails.py --check
```

## 이미지 규칙

- 크기: 1080x565
- 형식: PNG
- 비율: Velog 썸네일에 맞춘 약 1.91:1
- 배경: 시리즈별 공통 AI 이미지
- 텍스트: HTML/CSS + Google Chrome headless
- 글꼴: macOS 시스템 한글 글꼴 우선 사용
- AI 배경에는 글자, 숫자, 로고, 워터마크를 넣지 않습니다.
- 게시글별 배경 이미지는 따로 만들지 않고, 같은 시리즈의 게시글은 같은 배경을 공유합니다.

## 폴더 구조

- `series/`: 시리즈 커버 썸네일
- `posts/realtime-chat/`: 실시간 채팅 백엔드 게시글 썸네일
- `posts/concert-booking/`: 콘서트 예매 시스템 게시글 썸네일
- `posts/open-source/`: 오픈소스 기여 게시글 썸네일
- `posts/programmers-python/`: 프로그래머스 Python 코딩테스트 게시글 썸네일
- `posts/hana-finance-ai/`: 하나 청년 금융인재 프로젝트 게시글 썸네일
- `ai-backgrounds/series/`: 텍스트가 없는 시리즈별 공통 AI 배경 원본

## 배경 재생성 순서

1. `ai-backgrounds/series/` 아래에 시리즈별 배경을 준비합니다.
2. `python3 tools/generate_thumbnails.py --check-backgrounds`로 배경 파일 존재 여부를 확인합니다.
3. `python3 tools/generate_thumbnails.py`로 게시글/시리즈 썸네일을 다시 렌더링합니다.
4. `python3 tools/generate_thumbnails.py --check`로 최종 PNG 크기를 확인합니다.

## Velog에 적용하기

Velog 글 수정 화면에서 썸네일 이미지를 직접 업로드하면 됩니다.
본문 Markdown은 이 작업에서 변경하지 않습니다.
