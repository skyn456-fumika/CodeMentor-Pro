from sqlalchemy.orm import DeclarativeBase


# 앞으로 작성할 모든 SQLAlchemy 엔티티가 상속할 공통 클래스
class Base(DeclarativeBase):
    pass