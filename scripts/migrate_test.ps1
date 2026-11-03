$ErrorActionPreference = "Stop"

# 기존 환경변수 보관
$previousDatabaseUrl = [Environment]::GetEnvironmentVariable(
    "DATABASE_URL", "Process"
)

try {
    # 테스트 DB 설정
    $env:DATABASE_URL = "postgresql+psycopg://codementor:devpassword@127.0.0.1:5433/codementor_test"

    Write-Host "Applying migrations to codementor_test..."

    python -m alembic upgrade head

    if ($LASTEXITCODE -ne 0) {
        throw "Test database migration failed."
    }

    Write-Host "Test database migration completed."
}
finally {
    # 기존 환경변수 복구
    [Environment]::SetEnvironmentVariable(
        "DATABASE_URL",
        $previousDatabaseUrl,
        "Process"
    )  
}

# 단, 기존에 사용한 방법처럼 alembic/env.py가 DATABASE_URL을 읽는 구조여야 하고, 
# 실제 마이그레이션 대상이 테스트 DB인지 먼저 확인해야 함