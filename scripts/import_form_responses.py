

import argparse
import json
import re
import sys
from pathlib import Path

import openpyxl

BASE_DIR = Path(__file__).resolve().parent.parent
SEED_FILE = BASE_DIR / "data" / "booths.seed.json"
RETROSPECT_FILE = BASE_DIR / "data" / "retrospects.json"
LINKS_FILE = BASE_DIR / "data" / "links.json"

# 엑셀 열 위치
COL_TEAM = 2
COL_TRACK = 4
COL_NAME = 5
COL_MAIN_CONTENT = 6
COL_PROJECT_LINKS = 7
COL_SERVICE_URL = 8
COL_TECH_STACK = 11
COL_CONTENT = 12
COL_FUNCTIONS = 14
COL_REFACTORING = 16
COL_COLLABORATION = 17
COL_MESSAGE = 18

TRACK_TO_TAG = {
    "LIKELION Track": "멋사",
    "SJF Track": "SJF",
    "AAC Track": "AAC",
    "Open Track": "OPEN",
}

BOOTH_ID_BY_TEAM = {
    "국경없는사자들": 1,
    "말랑이": 2,
    "시원쿨쿨멋터밤": 3,
    "꽃보다사자": 4,
    "하이파이브": 5,
    "금연한사자처럼": 6,
    "삶이순탄쿠나": 7,
    "왕꿈트리": 8,
    "이리저리": 9,
    "수상한아기사자들": 10,
    "더버버": 11,
    "skinearth": 12,
    "영크크말고봉크크": 13,
    "aura": 14,
    "오리스웰": 15,
    "초코숭이": 16,
    "독수리6형제": 17,
    "tagonai": 18,
    "되면천재안되면쩔수": 19,
    "멋크크": 20,
    "가천미인": 21,
}


IGNORED_TEAMS = {"숭실대학교": "18번 중복 제출 중 앞선 응답"}
OVERRIDES = {18: {"team": "사춘기온사자", "name": "TagonAI"}}

URL_PATTERN = re.compile(r"https?://[^\s|,]+")
NUMBERED_LINE = re.compile(r"^\s*\d+[.)]\s*")
BULLET = re.compile(r"^\s*(?:[-*•·]|\d+[.)])\s*")

FRONTEND_PLACEHOLDER_IMAGE = "../features/Onboarding/assets/lion-logo.svg"


def cell(row, index):
    value = row[index] if index < len(row) else None
    return str(value).strip() if value is not None else ""


def team_key(name):
    return re.sub(r"\s+", "", name).lower()


def urls(text):
    return [url.rstrip(".)") for url in URL_PATTERN.findall(text)]


def lines(text):
    return [line.strip() for line in text.replace("\t", " ").splitlines() if line.strip()]


def parse_functions(text, warnings):
    """번호 목록이면 번호가 붙은 줄만 항목으로, 아니면 모든 줄을 항목으로 쓴다."""
    all_lines = lines(text)
    numbered = [line for line in all_lines if NUMBERED_LINE.match(line)]

    if numbered:
        if len(numbered) != len(all_lines):
            warnings.append(f"기능: 번호 아래 설명 {len(all_lines) - len(numbered)}줄은 제외함")
        items = numbered
    else:
        items = all_lines

    return [BULLET.sub("", item).strip() for item in items]


def parse_tech_stack(text):
    return [line.rstrip(" ,") for line in lines(text)]


def build_booth(row):
    team = cell(row, COL_TEAM)
    booth_id = BOOTH_ID_BY_TEAM[team_key(team)]
    warnings = []

    project_links = cell(row, COL_PROJECT_LINKS)
    service_url_cell = cell(row, COL_SERVICE_URL)

    servicelinks = urls(service_url_cell)
    githublinks = [url for url in urls(project_links) if "github.com" in url]
    figmalinks = [url for url in urls(project_links) if "figma.com" in url]
    etclinks = [
        url for url in urls(project_links) if url not in githublinks and url not in figmalinks
    ]

    if not servicelinks:
        warnings.append("서비스 URL 없음")
    if not githublinks:
        warnings.append("GitHub 링크 없음")

    booth = {
        "id": booth_id,
        "name": cell(row, COL_NAME),
        "team": team,
        "tag": TRACK_TO_TAG[cell(row, COL_TRACK)],
        "serviceimage": None,
        "servicelink": next(iter(servicelinks), None),
        "githublink": next(iter(githublinks), None),
        "figmalink": next(iter(figmalinks), None),
        "maincontent": cell(row, COL_MAIN_CONTENT),
        "content": cell(row, COL_CONTENT),
        "function": parse_functions(cell(row, COL_FUNCTIONS), warnings),
        "techstack": parse_tech_stack(cell(row, COL_TECH_STACK)),
    }
    booth.update(OVERRIDES.get(booth_id, {}))

    retrospect = {
        "id": booth_id,
        "refactoring": cell(row, COL_REFACTORING),
        "collaboration": cell(row, COL_COLLABORATION),
        "message": cell(row, COL_MESSAGE),
    }

    links = {
        "id": booth_id,
        "servicelinks": servicelinks,
        "githublinks": githublinks,
        "figmalinks": figmalinks,
        "etclinks": etclinks,
    }

    return booth, retrospect, links, warnings


def load_booths(xlsx_path):
    rows = list(openpyxl.load_workbook(xlsx_path, read_only=True).worksheets[0].iter_rows(values_only=True))

    booths, retrospects, links, report = {}, {}, {}, []
    for row in rows[1:]:
        if not any(row):
            continue

        team = cell(row, COL_TEAM)
        if team in IGNORED_TEAMS:
            report.append(f"  제외: {team} / {cell(row, COL_NAME)} ({IGNORED_TEAMS[team]})")
            continue
        if team_key(team) not in BOOTH_ID_BY_TEAM:
            raise SystemExit(f"배치표에 없는 팀입니다: {team}")
        if cell(row, COL_TRACK) not in TRACK_TO_TAG:
            raise SystemExit(f"알 수 없는 트랙입니다: {team} / {cell(row, COL_TRACK)}")

        booth, retrospect, link, warnings = build_booth(row)
        if booth["id"] in booths:
            raise SystemExit(f"{booth['id']}번 부스 응답이 두 개입니다: {team}")

        booths[booth["id"]] = booth
        retrospects[booth["id"]] = retrospect
        links[booth["id"]] = link
        for warning in warnings:
            report.append(f"  {booth['id']}번 {booth['name']}: {warning}")

    missing = sorted(set(BOOTH_ID_BY_TEAM.values()) - set(booths))
    if missing:
        raise SystemExit(f"응답이 없는 부스가 있습니다: {missing}")

    ordered = sorted(booths)
    return (
        [booths[i] for i in ordered],
        [retrospects[i] for i in ordered],
        [links[i] for i in ordered],
        report,
    )


def write_frontend(path, booths):
    body = []
    for booth in booths:
        text = json.dumps(booth, ensure_ascii=False, indent=2)
        text = text.replace('"serviceimage": null', '"serviceimage": none')
        body.append("  " + text.replace("\n", "\n  "))

    path.write_text(
        f'import none from "{FRONTEND_PLACEHOLDER_IMAGE}";\n\n'
        "// 구글 폼 응답을 uhheung-backend/scripts/import_form_responses.py 로 변환한 데이터.\n"
        "// 직접 고치지 말고 스크립트를 다시 실행한다.\n"
        "export const booths = [\n" + ",\n".join(body) + ",\n];\n",
        encoding="utf-8",
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("xlsx", type=Path, help="구글 폼 응답 엑셀 파일")
    parser.add_argument("--frontend", type=Path, help="함께 덮어쓸 프론트 src/data/booths.js 경로")
    args = parser.parse_args()

    booths, retrospects, links, report = load_booths(args.xlsx)

    SEED_FILE.write_text(json.dumps(booths, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"백엔드 시드 {len(booths)}건 → {SEED_FILE}")

    RETROSPECT_FILE.write_text(
        json.dumps(retrospects, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"회고 {len(retrospects)}건 → {RETROSPECT_FILE} (깃에 올리지 않음, 릴리즈로 업로드)")

    LINKS_FILE.write_text(json.dumps(links, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"링크 {len(links)}건 → {LINKS_FILE} (깃에 올리지 않음, 릴리즈로 업로드)")

    if args.frontend:
        write_frontend(args.frontend, booths)
        print(f"프론트 데이터 {len(booths)}건 → {args.frontend}")

    if report:
        print("\n확인 필요:")
        print("\n".join(report))


if __name__ == "__main__":
    sys.exit(main())
