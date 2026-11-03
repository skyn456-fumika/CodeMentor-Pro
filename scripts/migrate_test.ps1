$ErrorActionPreference = "Stop"

# 기존 DATABASE_URL 백업
$previousDatabaseUrl = [Environment]::GetEnvironmentVariable(
    "DATABASE_URL", "Process"
)

# 테스트 DB 환경변수 확인
$testDatabaseUrl = [Environment]::GetEnvironmentVariable(
    "TEST_DATABASE_URL", "Process"
)

if ([string]::IsNullOrWhiteSpace($testDatabaseUrl)) {
    throw "TEST_DATABASE_URL environment variable is required."
}

try {
    # Alembic이 테스트 DB를 사용하도록 설정
    $env:DATABASE_URL = $testDatabaseUrl

    Write-Host "Applying migrations to test database..."

    python -m alembic upgrade head

    if ($LASTEXITCODE -ne 0) {
        throw "Test database migration failed."
    }

    Write-Host "Test database migration completed."
}
finally {
    # 기존 DATABASE_URL 복원
    [Environment]::SetEnvironmentVariable(
        "DATABASE_URL",
        $previousDatabaseUrl,
        "Process"
    )
}
