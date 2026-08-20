# tpe-guide

타이베이 여행 필드 가이드. **`index.html` 한 장짜리 정적 사이트**입니다.
빌드 도구, 의존성, 패키지 매니저 없음. 이 파일을 직접 편집합니다.

라이브: https://jayjeonghokim.github.io/tpe-guide/
여행 기간: 2026-08-29(토) ~ 09-02(수)

## 배포

GitHub Pages **legacy 방식**(Actions 워크플로 없음). `main` 브랜치 루트를 그대로 서빙합니다.
**`main`에 푸시하면 곧바로 공개 사이트에 반영됩니다.** 별도 배포 단계 없음.

푸시 후 확인:

```bash
gh api repos/jayjeonghokim/tpe-guide/pages/builds/latest --jq '{status,commit,error:.error.message}'
curl -sS -o /dev/null -w "%{http_code} %{size_download}\n" -L https://jayjeonghokim.github.io/tpe-guide/
```

빌드는 보통 30~60초. `status`가 `built`이고 `commit`이 방금 푸시한 SHA와 같아야 합니다.

## 편집 후 반드시 검증

`index.html` 안에 JS가 인라인이라 문법 오류가 나면 페이지 전체가 죽습니다. 커밋 전에:

```bash
python3 -c "h=open('index.html').read();open('/tmp/b.js','w').write(h.split('<script>',1)[1].rsplit('</script>',1)[0])"
node --check /tmp/b.js
```

## 파일 구조

`index.html` 단일 파일. 순서대로:

1. `<head>` — 메타, Google Fonts, `<style>` 전체 CSS (라이트/다크 양쪽 정의)
2. `<body>` — 마스트헤드, PID 시계 패널, 탭 6개, 각 탭 pane, 라이트박스/확대 오버레이
3. `<script>` — 데이터 상수 → 렌더 함수 → 초기화

탭: 일정 / 동선 / 장소 / 필담 / 실전 / 긴급

## 데이터 형식

### `PLACES`
```js
{id, nm, zh, cat, area, sch, addr, hours, pid, ll, nomap, tip}
```
- `cat`: `base`(숙소) `sight`(볼거리) `food`(먹거리) `cafe`(커피·차) `bar`(바·재즈) `move`(교통) `trip`(별도 검토)
- `sch: 1` — 확정 일정에 포함된 곳. 장소 탭의 "일정 포함만" 토글이 이걸 봅니다.
- `pid` — Google place_id. 있으면 지도/사진 링크가 정확해집니다.
- `ll` — `"위도,경도"` 문자열. **확실하지 않으면 빈 문자열로 두세요.** 비어 있으면 지도 링크가 이름 검색으로 대체됩니다. 추측 좌표로 잘못된 핀을 찍는 것보다 낫습니다.
- `nomap: 1` — 동선 지도 범위에서 제외(예: 타오위안공항. 넣으면 시내가 뭉개집니다).

### `hours`
요일별 영업시간. **0=일요일 … 6=토요일**, 값은 `null`(휴무) 또는 `[시작분, 종료분]` 구간 배열.
분은 자정 기준. `종료 > 1440`이면 익일(예: `[1080,1500]` = 18:00–01:00).
`[[0,1440]]`은 24시간 — `isAllDay()`가 따로 처리해 "24시간 · 상시"로 표시합니다.
헬퍼: `ALLDAY`, `EVERYDAY(a,b)`, `EXCEPT(a,b,[휴무요일])`.
영업시간을 모르면 `hours: null` → UI가 "시간 확인 필요"로 처리합니다. **모르는 시간을 지어내지 마세요.**

### `DAYS`
```js
{d:'08.29', w:'토', stay, est, note, stops:[{t, n, zh, cat, p, est, leg, d, opt, warn}]}
```
- `t` — `'HH:MM'`. 시간순 정렬 유지 필수.
- `p` — `PLACES`의 `id` 참조.
- `est: 1` — **추정 시각**. `~14:00`처럼 흐리게 표시됩니다. 8/30 이후는 패키지 공식 일정이라 시각이 확정 전이므로 전부 `est`입니다. 확정 시각표를 받으면 `est`를 떼세요.
- `warn` — 일정상 문제 경고(붉은 박스). 예: 고궁박물원 17:00 폐관인데 17:00 도착으로 잡혀 있음.
- `opt` — 선택 사항 제안.
- `leg` — **직전 지점에서 이 지점까지의 이동**:
  ```js
  {m, line, from, to, stops, min, walk, dist, fare, note, alt}
  ```
  `m`: `walk|mrt|taxi|arex|air|bus` · `line`: `BL|R|G|O|BR|A` (MRT 노선 색 배지)
  `alt`: 대안 경로 문자열. 택시 구간에 MRT 대안을 적어두면 유용합니다.

### `TALK`
```js
{k, g, items: [[한자, 한국어발음, 뜻], ...]}
```
3요소 배열 고정. 발음은 한글 표기(예: `請問` → `칭원`).

### `PHOTOS`
```js
{ placeId: [{t, s, r, c, by, l, p}] }
```
`t`=500px 썸네일 · `s`=1280px 원본 · `r`=가로세로비 · `c`=캡션 · `by`=촬영자 · `l`=라이선스 · `p`=Commons 파일 페이지

## 사진 규칙 — 중요

**Wikimedia Commons의 자유 라이선스 사진만 씁니다.**

- 구글 이미지·구글 지도 사용자 사진은 **금지**. 저작권 문제이고, Places Photo API는 정적 공개 페이지에 노출되는 API 키가 필요합니다.
- 자유 라이선스 사진이 없는 곳(대부분의 식당·카페·바)은 사진을 넣지 말고, 카드가 구글 지도 사진 갤러리로 링크하게 두세요. `galHtml()`이 자동 처리합니다.
- **캡션은 Commons의 `ImageDescription` 메타데이터를 그대로 씁니다.** 사진을 보지 않고 캡션을 지어내면 내용과 어긋납니다(실제로 한 번 발생해 전량 교체했습니다).
- 라이트박스에 촬영자·라이선스·Commons 링크를 반드시 표기합니다. CC BY/BY-SA 요건입니다.
- **Wikimedia 썸네일 폭은 화이트리스트입니다: 120, 250, 330, 500, 960, 1280, 1920.** 그 외 폭은 400을 반환합니다. 다른 값 쓰지 마세요.
- 새 사진 추가 시 URL이 실제로 200인지 확인하고 커밋하세요.

메타데이터 조회:
```bash
curl -sS -A "tpe-guide/1.0 (연락처)" \
 "https://commons.wikimedia.org/w/api.php?action=query&titles=File:NAME.jpg&prop=imageinfo&iiprop=url%7Cextmetadata&iiurlwidth=1280&format=json"
```

## 정확성 원칙

이 가이드는 실제 여행에 쓰입니다. 틀린 정보가 빈칸보다 나쁩니다.

- 영업시간·주소·좌표를 모르면 **모른다고 표시**하세요(`hours:null`, `ll:''`, tip에 "미확인" 명시).
- 8/30 이후 시각은 전부 추정치입니다. 확정된 것처럼 쓰지 마세요.
- 주소 미확인 업장(OASIS, ODD ONE OUT, Astēa, Wangtea Lab, YiYi, inhouse Hotel 등)은 패키지 확정서의 주소가 우선입니다.
- 일정상 물리적으로 불가능한 구간을 발견하면 `warn`으로 표시하세요.

## 동선 지도

`mapSvg()`가 `ll` 좌표를 등거리 원통도법으로 투영해 SVG를 그립니다. 외부 지도 API 없음.
가까운 지점은 번호가 겹치지 않도록 자동으로 밀어냅니다(`SEP=25`) — 위치가 약간 왜곡되므로 그 사실을 지도 아래 표기합니다.
색은 CSS 변수라 다크 모드에서 자동으로 맞습니다.

## 주의

- CSS 셀렉터에 자식 결합자를 빠뜨리지 마세요. `.sum div`는 손자까지 잡습니다 (`.sum>div`가 맞습니다).
- `escape` 처리된 문자열을 `onclick` 속성에 직접 넣지 말고 인덱스를 넘기세요(`openBig(i)`, `lbOpen(id,i)`).
- 시계·영업상태는 `Asia/Taipei` 기준입니다(`taipeiNow()`). 로컬 시간대를 쓰지 마세요.
