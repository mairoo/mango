# mango
pincoin django project

# django 용도
- 데이터베이스 마이그레이션 관리 도구

# 서비스 이관 방안
`default`, `old_db`, `new_db` 데이터 소스 연결 설정

```
python manage.py migrate
python manage.py shell < scripts/migrate_db.py
```

# 이관 후 할 일
- 기존 서비스 의존성 django-mptt, easy_thumbnails 삭제 처리
- django-model-utils 유지
- migrations 파일 동기화 처리
