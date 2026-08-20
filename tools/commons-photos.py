#!/usr/bin/env python3
"""index.html 의 PHOTOS 블록을 만들고 검증하는 보조 스크립트.

파이썬 표준 라이브러리만 씁니다. 사이트 빌드와는 무관하고, 손으로 돌리는 도구입니다.
Wikimedia 에 나가는 네트워크가 열린 곳에서 실행하세요. 저장소를 클론할 필요는 없습니다 —
이 파일 하나만 받으면 됩니다:

  curl -sSLO https://raw.githubusercontent.com/jayjeonghokim/tpe-guide/main/tools/commons-photos.py
  python3 commons-photos.py search "赤峰街 Taipei"

  ./tools/commons-photos.py search "赤峰街 Taipei"      후보 파일 찾기
  ./tools/commons-photos.py show File:Foo.jpg            캡션·촬영자·라이선스 확인
  ./tools/commons-photos.py entry zhongshan File:Foo.jpg File:Bar.jpg
                                                         index.html 에 붙여넣을 JS 출력
  ./tools/commons-photos.py check                        PHOTOS 안의 모든 URL 이 200 인지 검사
                                                         (클론 없이 돌리면 라이브 사이트를 받아서 검사)
  ./tools/commons-photos.py harvest out/ zhongshan="赤峰街 台北" ...
                                                         검색 + 메타데이터 + 썸네일 다운로드를
                                                         한 번에. 사람이 눈으로 고르라고 만든 모드.

CLAUDE.md 의 사진 규칙을 그대로 강제합니다.
 - Wikimedia Commons 자유 라이선스만
 - 캡션은 ImageDescription 메타데이터 그대로. 지어내지 않습니다.
 - 썸네일 폭은 화이트리스트(500 / 1280)만
 - 출력 전에 실제 URL 이 200 인지 확인
"""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

API = "https://commons.wikimedia.org/w/api.php"
UA = "tpe-guide/1.0 (jay.jeonghokim@gmail.com)"
THUMB, FULL = 500, 1280  # 화이트리스트 폭. 다른 값 쓰지 말 것.
THROTTLE = 0.4           # 요청 간 최소 간격(초). wikimedia 가 클라우드 IP 를 조인다.


def api(**params):
    params.setdefault("format", "json")
    params.setdefault("formatversion", "2")
    req = urllib.request.Request(API + "?" + urllib.parse.urlencode(params),
                                 headers={"User-Agent": UA})
    time.sleep(THROTTLE)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def check_url(url, tries=4):
    """URL 이 200 이면 "" 를, 아니면 사유 문자열을 돌려준다.

    upload.wikimedia.org 는 클라우드 IP 에서 연속 요청을 던지면 429/503 을 준다.
    (Actions 러너에서 이것 때문에 후보가 통째로 걸러진 적이 있다.)
    429/503/네트워크 오류는 지수 백오프로 재시도하고, 404 는 즉시 실패로 본다.
    """
    reason = "알 수 없음"
    for i in range(tries):
        time.sleep(THROTTLE)
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                if r.status == 200:
                    return ""
                reason = "status %d" % r.status
        except urllib.error.HTTPError as e:
            reason = "HTTP %d" % e.code
            if e.code not in (429, 503):
                return reason
        except Exception as e:
            reason = type(e).__name__ + ": " + str(e)
        if i < tries - 1:
            time.sleep(2 ** i)
    return reason


def head_ok(url):
    return check_url(url) == ""


ZERO_WIDTH = "\u200b\u200c\u200d\u200e\u200f\ufeff"


def strip_html(s):
    s = re.sub(r"<[^>]+>", "", s or "")
    s = urllib.parse.unquote(s)
    # Commons 설명문은 제로폭 공백으로 시작하는 경우가 흔하다. 그대로 두면
    # 캡션 앞에 보이지 않는 문자가 박힌다.
    s = s.translate({ord(c): None for c in ZERO_WIDTH})
    return " ".join(s.split()).strip()


def info(title):
    """한 파일의 캡션·촬영자·라이선스·썸네일 URL 을 가져온다."""
    if not title.startswith("File:"):
        title = "File:" + title
    d = api(action="query", titles=title, prop="imageinfo",
            iiprop="url|extmetadata|size", iiurlwidth=FULL)
    pages = d.get("query", {}).get("pages", [])
    if not pages or "imageinfo" not in pages[0]:
        raise SystemExit("없는 파일이거나 이미지가 아닙니다: " + title)
    ii = pages[0]["imageinfo"][0]
    em = ii.get("extmetadata", {})
    g = lambda k: strip_html(em.get(k, {}).get("value", ""))
    # thumburl 에 utm_* 추적 파라미터가 붙어서 온다. 그대로 쓰면 PHOTOS 에
    # 쿼리스트링이 박히므로 잘라낸다.
    thumb = urllib.parse.urlsplit(ii["thumburl"])._replace(query="", fragment="").geturl()
    base = thumb.rsplit("/", 1)[0]                    # .../thumb/a/ab/Name.jpg
    name = re.sub(r"^\d+px-", "", thumb.rsplit("/", 1)[1])
    return {
        "title": pages[0]["title"],
        "t": f"{base}/{THUMB}px-{name}",
        "s": f"{base}/{FULL}px-{name}",
        "r": round(ii["width"] / ii["height"], 3),
        "c": g("ImageDescription"),
        "by": g("Artist"),
        "l": g("LicenseShortName"),
        "p": ii["descriptionurl"],
    }


def srch(q, limit="15"):
    """파일 검색. 스캔본(pdf·djvu)이 결과를 뒤덮으므로 비트맵으로 제한한다.
    incategory:"..." 같은 CirrusSearch 연산자를 그대로 쓸 수 있다."""
    if "filetype:" not in q:
        q = q + " filetype:bitmap"
    d = api(action="query", list="search", srsearch=q, srnamespace="6", srlimit=limit)
    return [h["title"] for h in d.get("query", {}).get("search", [])]


def js(x):
    q = lambda s: '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'
    return ("  {t:%s,s:%s,r:%.3f,c:%s,by:%s,l:%s,p:%s}," %
            (q(x["t"]), q(x["s"]), x["r"], q(x["c"]), q(x["by"]), q(x["l"]), q(x["p"])))


def cmd_search(args):
    for t in srch(" ".join(args), "25"):
        print(t)


def cmd_show(args):
    for t in args:
        x = info(t)
        print(x["title"])
        for k in ("c", "by", "l", "r"):
            print("  %-3s %s" % (k, x[k]))
        print("  url %s" % (check_url(x["t"]) or check_url(x["s"]) or "200 OK"))


def cmd_entry(args):
    if len(args) < 2:
        raise SystemExit("사용법: entry <placeId> <File:...> [File:...]")
    pid, titles = args[0], args[1:]
    rows = []
    for t in titles:
        x = info(t)
        if not x["c"]:
            print("// 건너뜀 — ImageDescription 이 비어 있음: " + x["title"], file=sys.stderr)
            continue
        err = check_url(x["t"]) or check_url(x["s"])
        if err:
            print("// 건너뜀 — URL 확인 실패 (%s): %s" % (err, x["title"]), file=sys.stderr)
            continue
        rows.append(js(x))
    if not rows:
        raise SystemExit("쓸 수 있는 사진이 없습니다.")
    print(" %s:[\n%s\n ]," % (pid, "\n".join(rows)))


PER_PLACE = 8  # 장소당 내려받을 후보 수. 눈으로 넘겨볼 수 있는 정도로.


def safe(s):
    return re.sub(r"[^A-Za-z0-9._-]+", "_", s)[:80]


def cmd_harvest(args):
    """검색 → 메타데이터 → 썸네일 다운로드를 한 번에.

        harvest <outdir> <placeId>="<질의어>" [<placeId>="<질의어>" ...]

    같은 placeId 를 여러 번 줘도 됩니다 — 질의어별 결과를 합치고 중복은 제거합니다.
    outdir/<placeId>/NN-<파일명>.jpg 로 썸네일을 받고, outdir/manifest.json 에
    캡션·촬영자·라이선스·종횡비를 적습니다. 고르는 건 사람이 합니다.
    """
    if len(args) < 2:
        raise SystemExit('사용법: harvest <outdir> <placeId>="<질의어>" [...]')
    outdir, pairs = args[0], args[1:]

    queries = {}
    for pair in pairs:
        if "=" not in pair:
            raise SystemExit("placeId=질의어 형식이어야 합니다: " + pair)
        pid, q = pair.split("=", 1)
        queries.setdefault(pid, []).append(q)

    manifest = {}
    for pid, qs in queries.items():
        titles, seen = [], set()
        for q in qs:
            try:
                found = srch(q)
            except Exception as e:
                print("  검색 실패 [%s] %s: %s" % (pid, q, e))
                continue
            for t in found:
                if t.lower().endswith((".jpg", ".jpeg", ".png")) and t not in seen:
                    seen.add(t)
                    titles.append(t)

        print("\n=== %s === 질의 %s · 후보 %d개" % (pid, qs, len(titles)))
        rows = []
        for t in titles:
            if len(rows) >= PER_PLACE:
                break
            try:
                x = info(t)
            except Exception as e:
                print("  건너뜀 %s (%s)" % (t, e))
                continue
            if not x["c"]:
                print("  건너뜀 %s — ImageDescription 비어 있음" % t)
                continue
            err = check_url(x["t"]) or check_url(x["s"])
            if err:
                print("  건너뜀 %s — URL 확인 실패 (%s)" % (t, err))
                continue
            n = len(rows)
            rel = "%s/%02d-%s" % (pid, n, safe(t[5:]))
            path = os.path.join(outdir, rel)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            try:
                req = urllib.request.Request(x["t"], headers={"User-Agent": UA})
                with urllib.request.urlopen(req, timeout=60) as r, open(path, "wb") as f:
                    f.write(r.read())
            except Exception as e:
                print("  건너뜀 %s — 썸네일 다운로드 실패 (%s)" % (t, e))
                continue
            x["file"] = rel
            rows.append(x)
            print("  [%02d] %s\n       %s\n       %s · %s · r=%.3f"
                  % (n, t, x["c"][:110], x["by"], x["l"], x["r"]))
        manifest[pid] = rows

    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)

    print("\n\n===== 붙여넣기용 초안 (고르기 전) =====")
    for pid, rows in manifest.items():
        if not rows:
            continue
        print(" %s:[" % pid)
        for x in rows:
            print(js(x) + "   // " + x["file"])
        print(" ],")
    print("\n총 %d개 장소 · 사진 %d장 내려받음"
          % (len(manifest), sum(len(v) for v in manifest.values())))
    return 0


LIVE = "https://jayjeonghokim.github.io/tpe-guide/"


def cmd_check(args):
    """index.html 안의 Wikimedia URL 이 전부 200 인지 검사.

    인자로 로컬 경로나 URL 을 줄 수 있습니다. 아무것도 안 주면 현재 폴더의
    index.html 을 보고, 그것도 없으면 라이브 사이트를 내려받아 검사합니다.
    (저장소를 클론하지 않았을 때 이 경로로 떨어집니다.)
    """
    target = args[0] if args else ("index.html" if os.path.exists("index.html") else LIVE)
    if target.startswith(("http://", "https://")):
        print("대상: " + target)
        req = urllib.request.Request(target, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=30) as r:
            src = r.read().decode("utf-8")
    else:
        print("대상: " + target)
        src = open(target, encoding="utf-8").read()
    urls = re.findall(r'[ts]:"(https://upload\.wikimedia\.org[^"]+)"', src)
    bad = [u for u in urls if not head_ok(u)]
    print("검사 %d개 · 실패 %d개" % (len(urls), len(bad)))
    for u in bad:
        print("  X " + u)
    return 1 if bad else 0


CMDS = {"search": cmd_search, "show": cmd_show, "entry": cmd_entry,
        "check": cmd_check, "harvest": cmd_harvest}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in CMDS:
        raise SystemExit(__doc__)
    sys.exit(CMDS[sys.argv[1]](sys.argv[2:]) or 0)
