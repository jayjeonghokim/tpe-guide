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
import urllib.parse
import urllib.request

API = "https://commons.wikimedia.org/w/api.php"
UA = "tpe-guide/1.0 (jay.jeonghokim@gmail.com)"
THUMB, FULL = 500, 1280  # 화이트리스트 폭. 다른 값 쓰지 말 것.


def api(**params):
    params.setdefault("format", "json")
    params.setdefault("formatversion", "2")
    req = urllib.request.Request(API + "?" + urllib.parse.urlencode(params),
                                 headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def head_ok(url):
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status == 200
    except Exception:
        return False


def strip_html(s):
    s = re.sub(r"<[^>]+>", "", s or "")
    s = urllib.parse.unquote(s)
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
    base = ii["thumburl"].rsplit("/", 1)[0]           # .../thumb/a/ab/Name.jpg
    name = ii["thumburl"].rsplit("/", 1)[1]
    name = re.sub(r"^\d+px-", "", name)
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


def js(x):
    q = lambda s: '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'
    return ("  {t:%s,s:%s,r:%.3f,c:%s,by:%s,l:%s,p:%s}," %
            (q(x["t"]), q(x["s"]), x["r"], q(x["c"]), q(x["by"]), q(x["l"]), q(x["p"])))


def cmd_search(args):
    d = api(action="query", list="search", srsearch=" ".join(args),
            srnamespace="6", srlimit="25")
    for hit in d["query"]["search"]:
        print(hit["title"])


def cmd_show(args):
    for t in args:
        x = info(t)
        print(x["title"])
        for k in ("c", "by", "l", "r"):
            print("  %-3s %s" % (k, x[k]))
        print("  200 %s / %s" % (head_ok(x["t"]), head_ok(x["s"])))


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
        if not (head_ok(x["t"]) and head_ok(x["s"])):
            print("// 건너뜀 — URL 이 200 이 아님: " + x["title"], file=sys.stderr)
            continue
        rows.append(js(x))
    if not rows:
        raise SystemExit("쓸 수 있는 사진이 없습니다.")
    print(" %s:[\n%s\n ]," % (pid, "\n".join(rows)))


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


CMDS = {"search": cmd_search, "show": cmd_show, "entry": cmd_entry, "check": cmd_check}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in CMDS:
        raise SystemExit(__doc__)
    sys.exit(CMDS[sys.argv[1]](sys.argv[2:]) or 0)
