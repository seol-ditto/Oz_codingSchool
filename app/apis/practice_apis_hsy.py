from fastapi import APIRouter

router = APIRouter(prefix="/practice_api")

user_list = [
    {
        "id": 1,
        "name": "홍길동",
        "age": 24,
        "email": "gildong24@example.com",
        "password": "Password1234!!"
    },
    {
        "id": 2,
        "name": "장문복",
        "age": 21,
        "email": "moonluck12@example.com",
        "password": "Check1321!"
    },
    {
        "id": 3,
        "name": "임우진",
        "age": 31,
        "email": "limousine33@example.com",
        "password": "lwsPAssword12@"
    }
]


# 모든 회원의 정보를 목록으로 조회하는 API
# endpoint: practice_api/users
# 조회 가능한 항목: id, name, age, email

@router.get("/users")
def get_users():
    # password는 빼고 id, name, age, email만 반환
    return [
        {
            "id": user["id"],
            "name": user["name"],
            "age": user["age"],
            "email": user["email"],
        }
        for user in user_list
    ]
