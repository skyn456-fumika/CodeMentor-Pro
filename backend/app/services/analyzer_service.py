import json
import subprocess
import sys


class AnalyzerError(Exception):
    pass

# Ruff는 -로 표준 입력의 코드를 분석하고 JSON 형식으로 결과를 반환
def analyze_code(code: str) -> list[dict]:
    if not code.strip():
        raise ValueError("분석할 코드가 비어 있습니다.")

    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m", "ruff",
                "check",
                "--output-format", "json",
                "--isolated",
                "--stdin-filename", "input.py",
                "-"
            ],
            input=code,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=10,
            check=False,
        )

    except (OSError, subprocess.TimeoutExpired) as exc:
        raise AnalyzerError("Ruff 실행에 실패했습니다.") from exc

    if result.returncode not in (0, 1):
        raise AnalyzerError(result.stderr or "Ruff 분석 오류")

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise AnalyzerError("Ruff 결과를 해석할 수 없습니다.") from exc

    return [
        {
            "line": issue["location"]["row"],
            "column": issue["location"]["column"],
            "code": issue["code"],
            "message": issue["message"]
        }
        for issue in data
    ]