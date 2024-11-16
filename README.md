# mango

pincoin django project

# django 용도

- 데이터베이스 마이그레이션 관리 도구

# 서비스 이관 방안

## 1. `default`, `old_db`, `new_db` 데이터 소스 연결 설정

PostgreSQL에 정의된 앱/모델 설정 파이썬 코드 그대로 복사

## 2. 기존 모델 신규 데이터베이스에 스키마 생성

```
python manage.py migrate
```

## 3. 데이터 이관 복사 (현재 약 25분 소요)

```
python manage.py shell < scripts/migrate_db.py
```

# 이관 후 할 일

- 기존 서비스 의존성 django-mptt, easy_thumbnails 삭제 처리 (단, django-model-utils 유지)
- migrations 파일 동기화 처리 방안
- 신규 테이블 생성 관리 방안
