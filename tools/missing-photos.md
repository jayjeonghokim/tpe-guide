# 사진이 없는 장소 — Commons 후보 조사 목록

현재 57곳 중 18곳에만 자유 라이선스 사진이 있습니다. 나머지 39곳은
`galHtml()`이 구글 사진 / 이미지 검색 / 인스타 링크로 대체하고 있습니다.

Wikimedia 로 나가는 네트워크가 열린 환경에서 아래를 돌리세요.
`entry` 가 출력하는 블록을 `index.html` 의 `const PHOTOS={ ... }` 안에 붙여넣으면 끝입니다.

```bash
./tools/commons-photos.py search "赤峰街 Taipei"
./tools/commons-photos.py show File:후보.jpg          # 캡션이 실제 사진과 맞는지 눈으로 확인
./tools/commons-photos.py entry zhongshan File:후보.jpg
```

## 1순위 — Commons 에 있을 가능성이 높은 곳

| id | 검색어 | 비고 |
|---|---|---|
| `zhongshan` | `赤峰街 Taipei`, `Chifeng Street Taipei`, `Zhongshan District Taipei street` | 일정 포함(9/2)인데 사진이 없는 유일한 볼거리 |
| `fuhang` | `阜杭豆漿`, `Fuhang Soy Milk`, `華山市場 Taipei` | 화산시장 건물 사진이라도 |
| `ayzong` | `阿宗麵線`, `Ay-Chung Flour-Rice Noodle` | 시먼딩 사진에 간판이 잡힌 것 포함 |
| `amba` | `西門町意舍酒店`, `Ximending hotel` | 없으면 넘어가세요 |

## 2순위 — 기존 사진이 얇은 곳 (3장)

| id | 검색어 |
|---|---|
| `dadaocheng` | `迪化街`, `Dihua Street`, `Dadaocheng Taipei` |
| `tpemain` | `台北車站`, `Taipei Main Station concourse` |

## 3순위 — 사실상 없음

식당·카페·바 33곳은 개인 업장이라 Commons 에 자유 라이선스 사진이 거의 없습니다.
`search` 로 한 번 확인해보고 안 나오면 그대로 두세요 —
카드가 구글 사진 / 이미지 검색 / 인스타 링크로 대체합니다.

## 규칙 (CLAUDE.md 요약)

- Wikimedia Commons 자유 라이선스만. 구글 이미지·지도 사용자 사진·인스타 이미지 **직접 임베드 금지**.
- 캡션은 `ImageDescription` 메타데이터 그대로. 사진을 안 보고 캡션을 쓰면 내용이 어긋납니다.
- 썸네일 폭은 화이트리스트: 120·250·330·500·960·1280·1920. 스크립트는 500/1280 만 씁니다.
- 커밋 전 `./tools/commons-photos.py check` 로 전체 URL 200 확인.
