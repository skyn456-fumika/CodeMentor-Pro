from backend.app.services.ai_service import review_code

code = """
def divide(a, b):
    return a / b

print(divide(10, 0))
"""

try:
    result = review_code(code)
    print(result)

except Exception as exc:  # noqa: BLE001
    print(f"AI 리뷰 실패: {exc}")

    if exc.__cause__ is not None:
        print(
            "실제 오류:",
            type(exc.__cause__).__name__,
            str(exc.__cause__)
        )