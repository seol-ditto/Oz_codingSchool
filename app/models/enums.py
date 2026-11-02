import enum


class Gender(str, enum.Enum):
    M = "M"   # male
    F = "F"   # female


class Role(str, enum.Enum):
    PENDING = "pending"   # 권한 부여 대기
    STAFF = "staff"       # 폐렴 추적 관련 데이터 CRUD 허용
    ADMIN = "admin"       # 전체 데이터 CRUD 허용


class Department(str, enum.Enum):
    MEDICAL = "medical"     # 의료진
    DEV = "develop"         # 개발팀
    RESEARCH = "research"   # 연구진