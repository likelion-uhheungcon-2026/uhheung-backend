

import argparse
import json
import re
import sys
from pathlib import Path

import openpyxl

BASE_DIR = Path(__file__).resolve().parent.parent
SEED_FILE = BASE_DIR / "data" / "booths.seed.json"

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
COL_COLLAB = 17

RETROSPECT_COLUMNS = {"refactoring": COL_REFACTORING, "collab": COL_COLLAB}

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


def first_url(text, domain=None):
    for url in urls(text):
        if domain is None or domain in url:
            return url
    return None


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


def build_booth(row, retrospect_column):
    team = cell(row, COL_TEAM)
    booth_id = BOOTH_ID_BY_TEAM[team_key(team)]
    warnings = []

    project_links = cell(row, COL_PROJECT_LINKS)
    service_url_cell = cell(row, COL_SERVICE_URL)

    servicelink = first_url(service_url_cell)
    if len(urls(service_url_cell)) > 1:
        warnings.append(f"서비스 URL 여러 개 중 첫 번째만 사용: {servicelink}")
    if servicelink is None:
        warnings.append("서비스 URL 없음")

    githublink = first_url(project_links, "github.com")
    if githublink is None:
        warnings.append("GitHub 링크 없음")
    elif len([url for url in urls(project_links) if "github.com" in url]) > 1:
        warnings.append(f"GitHub 링크 여러 개 중 첫 번째만 사용: {githublink}")

    booth = {
        "id": booth_id,
        "name": cell(row, COL_NAME),
        "team": team,
        "tag": TRACK_TO_TAG[cell(row, COL_TRACK)],
        "serviceimage": None,
        "servicelink": servicelink,
        "githublink": githublink,
        "figmalink": first_url(project_links, "figma.com"),
        "maincontent": cell(row, COL_MAIN_CONTENT),
        "content": cell(row, COL_CONTENT),
        "function": parse_functions(cell(row, COL_FUNCTIONS), warnings),
        "techstack": parse_tech_stack(cell(row, COL_TECH_STACK)),
        "retrospect": cell(row, retrospect_column) if retrospect_column is not None else "",
    }
    booth.update(OVERRIDES.get(booth_id, {}))

    return booth, warnings


def load_booths(xlsx_path, retrospect_column):
    rows = list(openpyxl.load_workbook(xlsx_path, read_only=True).worksheets[0].iter_rows(values_only=True))

    booths, report = {}, []
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

        booth, warnings = build_booth(row, retrospect_column)
        if booth["id"] in booths:
            raise SystemExit(f"{booth['id']}번 부스 응답이 두 개입니다: {team}")

        booths[booth["id"]] = booth
        for warning in warnings:
            report.append(f"  {booth['id']}번 {booth['name']}: {warning}")

    missing = sorted(set(BOOTH_ID_BY_TEAM.values()) - set(booths))
    if missing:
        raise SystemExit(f"응답이 없는 부스가 있습니다: {missing}")

    return [booths[booth_id] for booth_id in sorted(booths)], report


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
    parser.add_argument(
        "--retrospect",
        choices=sorted(RETROSPECT_COLUMNS),
        help="retrospect 에 넣을 열 (refactoring: 서비스 리팩토링 내용, collab: 우리 팀의 협업 이야기)",
    )
    args = parser.parse_args()

    retrospect_column = RETROSPECT_COLUMNS.get(args.retrospect)
    booths, report = load_booths(args.xlsx, retrospect_column)

    SEED_FILE.write_text(json.dumps(booths, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"백엔드 시드 {len(booths)}건 → {SEED_FILE}")

    if args.frontend:
        write_frontend(args.frontend, booths)
        print(f"프론트 데이터 {len(booths)}건 → {args.frontend}")

    if retrospect_column is None:
        report.append("  retrospect: 넣을 열이 정해지지 않아 전부 비워 둠 (--retrospect 로 지정)")

    if report:
        print("\n확인 필요:")
        print("\n".join(report))


if __name__ == "__main__":
    sys.exit(main())
