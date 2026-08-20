# 사진 현황과 남은 후보

**23곳 97장**에 자유 라이선스 사진이 있습니다. 나머지 34곳은 `galHtml()`이
구글 사진 / 이미지 검색 / 인스타 링크로 대체합니다.

남은 34곳의 내역: 카페 18 · 바 11 · 식당 3 · 숙소 2.
**전부 개인 업장입니다.** Commons 에 자유 라이선스 사진이 있을 가능성은 낮습니다.

## 이미 확인해서 없는 것으로 판명된 곳

아래는 Commons 검색에서 사진이 0건이었습니다. 다시 찾지 마세요.

`興波咖啡`(simplekaffa) · `FIKA FIKA CAFE`(fika) · `伊良可樂`(iyoshi) ·
`金峰滷肉飯`(jinfeng) · `雙月食品社`(moonq/moonj) · `RUFOUS COFFEE`(rufous) ·
`BAR MOOD`(barmood) · `西門町意舍酒店`(amba)

전문 검색은 고서 스캔본(pdf·djvu)이 결과를 뒤덮으므로 `search` 가
`filetype:bitmap` 을 자동으로 붙입니다.

## 다시 시도해볼 만한 곳

주소·상호가 확정되면 중국어 상호로 다시 찾아볼 값어치가 있습니다.
지금은 상호 자체가 미확인이라 검색이 안 됩니다.

`oasis` · `oddoneout` · `astea`(芏) · `yiyi` · `wangtealab`(Lab 지점 쪽) ·
`thenormal` · `moonshine` · `paperst` · `congrats` · `kor`

## 쓰는 법

**저장소를 클론할 필요 없습니다** — 스크립트 파일 하나만 받으면 됩니다.

```bash
curl -sSLO https://raw.githubusercontent.com/jayjeonghokim/tpe-guide/main/tools/commons-photos.py

python3 commons-photos.py search 'incategory:"Dihua Street"'   # 카테고리가 전문검색보다 정확
python3 commons-photos.py search '赤峰街 台北'
python3 commons-photos.py show   File:후보.jpg                  # 캡션이 실제 사진과 맞는지 눈으로
python3 commons-photos.py entry  zhongshan File:후보.jpg        # 붙여넣을 JS 출력
python3 commons-photos.py check                                # 전체 URL 200 검사
```

`entry` 출력을 `index.html` 의 `const PHOTOS={ ... }` 안에 붙여넣으면 끝입니다.
클론이 없으면 GitHub 웹 편집기(저장소에서 `.` 키)로 붙여넣어도 됩니다.

여러 곳을 한꺼번에 보려면 `harvest` 가 썸네일까지 내려받습니다.

```bash
python3 commons-photos.py harvest out/ \
  zhongshan='incategory:"Chifeng Street"' fuhang='阜杭豆漿'
```

`out/<placeId>/` 의 이미지를 **직접 열어보고** 고르세요. 캡션만 믿으면 안 됩니다 —
실제로 桃園공항 출국장이 王有記茶行 후보에, 松山역이 台北車站 후보에,
士林 분점이 阿宗麵線 후보에 섞여 들어왔습니다.

## 규칙 (CLAUDE.md 요약)

- Wikimedia Commons 자유 라이선스만. 구글·인스타 이미지 **직접 임베드 금지**.
- 캡션은 `ImageDescription` 그대로. 스크립트가 강제합니다.
- 썸네일 폭 화이트리스트: 120·250·330·500·960·1280·1920. 스크립트는 500/1280 만.
- 커밋 전 `check` 로 200 확인. `429`/`503` 만 남으면 통과입니다 —
  upload.wikimedia.org 가 연속 요청을 조이는 것이지 링크가 깨진 게 아닙니다.
