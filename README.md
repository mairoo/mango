# mango

pincoin django project

# django 용도

- 데이터베이스 마이그레이션 관리 도구

# 서비스 이관 방안

1. `default`, `old_db`, `new_db` 데이터 소스 연결 설정
2. 스키마 복사: `python manage.py migrate`
3. 데이터 복사: `python manage.py shell < scripts/migrate_db.py`
4. 마이그레이션 초기화: `django_migrations` 테이블 레코드 모두 삭제 후 `python manage.py migrate --fake`
5. 신규 모델 생성 및 마이그레이션: `python manage.py makemigrations; python manage.py migrate`
6. 스프링부트 JPA 도메인 개발 완료
7. 신규 모델 마이그레이션 끊기: `managed=False`
8. 새 데이터베이스 준비: `CREATE DATABASE`
9. 스키마 복사: `python manage.py migrate`
10. 데이터 복사: `python manage.py shell < scripts/migrate_db.py`
11. 마이그레이션 초기화: `django_migrations` 테이블 레코드 모두 삭제 후 `python manage.py migrate --fake`
12. 신규 모델 마이그레이션 연결: `managed=True`
14. 신규 모델 생성 및 마이그레이션: `python manage.py makemigrations; python manage.py migrate`

# 이관 후 할 일

- 기존 서비스 의존성 django-mptt, easy_thumbnails 삭제 처리 (단, django-model-utils 유지)
- `rakmai`, `member`, `shop` 앱 통합 후 모델 패키지로 관리