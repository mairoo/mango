import os
import time
from collections import defaultdict
from typing import List, Set

import django
from django.apps import apps
from django.db import connections
from django.db import transaction
from django.db.models import Model

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'conf.settings')
django.setup()


class DatabaseMigrator:
    def __init__(self, app_labels: List[str], batch_size=5000, exclude_models: List[str] = None):
        self.app_labels = app_labels
        self.exclude_models = exclude_models or []  # format: ['app_label.model_name', ...]
        self.processed_models: Set[Model] = set()
        self.dependency_graph = defaultdict(set)
        self.batch_size = batch_size
        self.build_dependency_graph()

    def should_migrate_model(self, model: Model) -> bool:
        """주어진 모델이 마이그레이션 대상인지 확인"""
        model_identifier = f"{model._meta.app_label}.{model._meta.model_name}"

        # 제외 목록에 있는 모델은 마이그레이션하지 않음
        if model_identifier in self.exclude_models:
            return False

        # old_db에 테이블이 존재하는지 확인
        with connections['old_db'].cursor() as cursor:
            try:
                cursor.execute(f"""
                    SELECT EXISTS (
                        SELECT 1 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = '{model._meta.db_table}'
                    )
                """)
                exists = cursor.fetchone()[0]
                return exists
            except Exception as e:
                print(f"Warning: Error checking table existence for {model_identifier}: {e}")
                return False

    def run_migration(self):
        """전체 마이그레이션 프로세스를 실행하는 메인 메서드"""
        try:
            print(f"Starting database migration for apps: {', '.join(self.app_labels)}")
            if self.exclude_models:
                print(f"Excluding models: {', '.join(self.exclude_models)}")
            self.migrate_data()
            print("Migration completed successfully!")
        except Exception as e:
            print(f"Error during migration: {str(e)}")
            raise

    def migrate_data(self):
        """의존성 순서에 따라 모든 모델의 데이터를 마이그레이션"""
        migration_order = self.get_migration_order()
        total_start_time = time.time()

        print("\nMigration order:")
        for i, model in enumerate(migration_order, 1):
            status = "SKIP" if not self.should_migrate_model(model) else "MIGRATE"
            print(f"{i}. {model._meta.label} [{status}]")

        for model in migration_order:
            if not self.should_migrate_model(model):
                print(f"\nSkipping migration for {model._meta.label} (excluded or not in old database)")
                continue

            print(f"\nStarting migration for {model._meta.label}...")
            if model.__name__ == 'Profile':
                self.migrate_profile_data(model)
            else:
                self.migrate_model_data(model)

        total_duration = time.time() - total_start_time
        print(f"\nTotal migration time: {total_duration:.2f} seconds")

    def migrate_model_data(self, model):
        """일반 모델의 데이터를 마이그레이션"""
        start_time = time.time()
        total_count = 0
        batch_count = 0

        print(f"Estimating record count for {model._meta.label}...")
        estimated_count = model.objects.using('old_db').count()
        print(f"Found approximately {estimated_count} records to migrate")

        try:
            self.disable_foreign_key_checks('new_db')

            with transaction.atomic(using='new_db'):
                queryset = self.get_optimized_queryset(model)
                new_instances = []
                last_progress = 0

                for instance in queryset:
                    new_instance = model()
                    for field in model._meta.fields:
                        if hasattr(instance, field.name):
                            setattr(new_instance, field.name, getattr(instance, field.name))
                    new_instances.append(new_instance)

                    if len(new_instances) >= self.batch_size:
                        actual_batch_size = min(
                            self.batch_size * 2 if len(model._meta.fields) > 10 else self.batch_size,
                            5000
                        )

                        model.objects.using('new_db').bulk_create(
                            new_instances,
                            batch_size=actual_batch_size,
                            ignore_conflicts=True
                        )
                        total_count += len(new_instances)
                        batch_count += 1

                        progress = (total_count / estimated_count * 100)
                        if progress - last_progress >= 5:
                            print(
                                f"Batch {batch_count} completed: {total_count}/{estimated_count} records migrated ({progress:.1f}%)")
                            last_progress = progress

                        new_instances = []

                if new_instances:
                    model.objects.using('new_db').bulk_create(
                        new_instances,
                        ignore_conflicts=True
                    )
                    total_count += len(new_instances)

                if self.is_auto_field(model._meta.pk):
                    self.prepare_auto_increment(model, 'new_db')

            self.enable_foreign_key_checks('new_db')

        except Exception as e:
            print(f"Error migrating {model._meta.label}: {str(e)}")
            self.enable_foreign_key_checks('new_db')
            raise

        end_time = time.time()
        duration = end_time - start_time
        print(f"Completed migrating {model._meta.label}")
        print(f"Total records: {total_count}")
        print(f"Time taken: {duration:.2f} seconds")
        print(f"Average speed: {total_count / duration:.2f} records/second")
        print("-" * 50)

    def migrate_profile_data(self, model):
        """Profile 전용 마이그레이션 로직"""
        start_time = time.time()
        total_count = 0
        batch_count = 0

        print(f"Estimating record count for {model._meta.label}...")
        estimated_count = model.objects.using('old_db').count()
        print(f"Found approximately {estimated_count} records to migrate")

        try:
            self.disable_foreign_key_checks('new_db')

            # 1. 기본 정보 마이그레이션 (이미지 필드 제외)
            with transaction.atomic(using='new_db'):
                basic_fields = [
                    'id', 'user_id', 'phone', 'address', 'phone_verified',
                    'phone_verified_status', 'document_verified', 'allow_order',
                    'total_order_count', 'first_purchased', 'last_purchased',
                    'not_purchased_months', 'repurchased', 'max_price',
                    'total_list_price', 'total_selling_price', 'average_price',
                    'mileage', 'memo', 'date_of_birth', 'gender', 'domestic',
                    'telecom', 'created', 'modified'
                ]

                queryset = (model.objects.using('old_db')
                            .select_related('user')
                            .only(*basic_fields)
                            .iterator(chunk_size=10000))

                new_instances = []
                last_progress = 0

                for instance in queryset:
                    new_instance = model()
                    for field_name in basic_fields:
                        if hasattr(instance, field_name):
                            setattr(new_instance, field_name, getattr(instance, field_name))
                    new_instances.append(new_instance)

                    if len(new_instances) >= 10000:
                        model.objects.using('new_db').bulk_create(
                            new_instances,
                            batch_size=10000,
                            ignore_conflicts=True
                        )
                        total_count += len(new_instances)
                        batch_count += 1

                        progress = (total_count / estimated_count * 100)
                        if progress - last_progress >= 5:
                            print(
                                f"Batch {batch_count} completed: {total_count}/{estimated_count} records migrated ({progress:.1f}%)")
                            last_progress = progress

                        new_instances = []

                if new_instances:
                    model.objects.using('new_db').bulk_create(
                        new_instances,
                        ignore_conflicts=True
                    )
                    total_count += len(new_instances)

            # 2. 이미지 필드 별도 마이그레이션
            self.migrate_profile_images(model)

            if self.is_auto_field(model._meta.pk):
                self.prepare_auto_increment(model, 'new_db')

            self.enable_foreign_key_checks('new_db')

        except Exception as e:
            print(f"Error migrating {model._meta.label}: {str(e)}")
            self.enable_foreign_key_checks('new_db')
            raise

        end_time = time.time()
        duration = end_time - start_time
        print(f"Completed migrating {model._meta.label}")
        print(f"Total records: {total_count}")
        print(f"Time taken: {duration:.2f} seconds")
        print(f"Average speed: {total_count / duration:.2f} records/second")
        print("-" * 50)

    def migrate_profile_images(self, model):
        """Profile 이미지 필드만 별도로 마이그레이션"""
        print("Starting image field migration...")
        image_fields = ['photo_id', 'card']

        # 이미지가 있는 레코드만 조회
        queryset = (model.objects.using('old_db')
                    .exclude(photo_id='', card='')
                    .only('id', *image_fields))

        total_images = queryset.count()
        if total_images == 0:
            print("No image fields to migrate")
            return

        print(f"Found {total_images} records with image fields")
        processed = 0
        batch_size = 1000

        for instance in queryset.iterator(chunk_size=batch_size):
            try:
                with transaction.atomic(using='new_db'):
                    new_instance = model.objects.using('new_db').get(id=instance.id)
                    updated = False

                    for field in image_fields:
                        if getattr(instance, field):
                            setattr(new_instance, field, getattr(instance, field))
                            updated = True

                    if updated:
                        new_instance.save(update_fields=image_fields)
                        processed += 1

                        if processed % batch_size == 0:
                            print(f"Processed {processed}/{total_images} image records")

            except model.DoesNotExist:
                print(f"Warning: Profile {instance.id} not found in new database")
                continue
            except Exception as e:
                print(f"Error processing image fields for profile {instance.id}: {str(e)}")
                continue

        print(f"Completed image field migration. Processed {processed} records")

    def get_app_models(self) -> List[Model]:
        """지정된 앱의 모델만 반환"""
        models = []
        for app_label in self.app_labels:
            try:
                app_config = apps.get_app_config(app_label)
                for model in app_config.get_models():
                    model_identifier = f"{model._meta.app_label}.{model._meta.model_name}"
                    if model_identifier not in self.exclude_models:
                        models.append(model)
            except LookupError as e:
                print(f"Warning: App '{app_label}' not found: {e}")
        return models

    def build_dependency_graph(self):
        """모델 간의 의존성 그래프를 생성"""
        for model in self.get_app_models():
            if self.should_migrate_model(model):  # 마이그레이션 대상 모델만 의존성 그래프에 포함
                for field in model._meta.fields:
                    if field.is_relation:
                        related_model = field.remote_field.model
                        if (related_model._meta.app_label in self.app_labels and
                                self.should_migrate_model(related_model)):
                            self.dependency_graph[model].add(related_model)

    def get_migration_order(self) -> List[Model]:
        """의존성을 고려한 마이그레이션 순서 반환"""
        migration_order = []

        def process_model(model):
            if model in self.processed_models:
                return

            self.processed_models.add(model)

            for dependent_model in self.dependency_graph[model]:
                process_model(dependent_model)

            migration_order.append(model)

        for model in self.get_app_models():
            process_model(model)

        return migration_order

    def get_primary_key_field(self, model):
        """모델의 primary key 필드 이름을 반환"""
        return model._meta.pk.name

    def prepare_auto_increment(self, model, using):
        """데이터베이스별 AUTO_INCREMENT/시퀀스 값 조정"""
        table_name = model._meta.db_table
        pk_name = self.get_primary_key_field(model)

        if not self.is_auto_field(model._meta.pk):
            return

        with connections[using].cursor() as cursor:
            cursor.execute(f"SELECT MAX({pk_name}) FROM {table_name}")
            max_id = cursor.fetchone()[0] or 0

            if 'postgresql' in connections[using].vendor:
                sequence_name = f"{table_name}_{pk_name}_seq"
                cursor.execute(f"SELECT setval('{sequence_name}', {max_id})")
            elif 'mysql' in connections[using].vendor:
                cursor.execute(f"ALTER TABLE {table_name} AUTO_INCREMENT = {max_id + 1}")

    def disable_foreign_key_checks(self, using):
        """외래키 제약 조건 비활성화"""
        with connections[using].cursor() as cursor:
            if 'mysql' in connections[using].vendor:
                cursor.execute('SET FOREIGN_KEY_CHECKS=0')
            elif 'postgresql' in connections[using].vendor:
                cursor.execute('SET CONSTRAINTS ALL DEFERRED')

    def enable_foreign_key_checks(self, using):
        """외래키 제약 조건 활성화"""
        with connections[using].cursor() as cursor:
            if 'mysql' in connections[using].vendor:
                cursor.execute('SET FOREIGN_KEY_CHECKS=1')
            elif 'postgresql' in connections[using].vendor:
                cursor.execute('SET CONSTRAINTS ALL IMMEDIATE')

    def get_foreign_key_fields(self, model):
        """모델의 모든 외래 키 필드 이름을 반환"""
        fk_fields = []
        for field in model._meta.fields:
            if field.is_relation and field.many_to_one:
                fk_fields.append(field.name)
        return fk_fields

    def get_optimized_queryset(self, model):
        """모델에 맞는 최적화된 쿼리셋 반환"""
        queryset = model.objects.using('old_db')

        fk_fields = self.get_foreign_key_fields(model)

        if fk_fields:
            print(f"Applying select_related for fields: {', '.join(fk_fields)}")
            queryset = queryset.select_related(*fk_fields)

        return queryset.iterator(chunk_size=self.batch_size)

    def is_auto_field(self, field):
        """AutoField나 BigAutoField 등 자동 증가 필드인지 확인"""
        from django.db.models import AutoField, BigAutoField
        return isinstance(field, (AutoField, BigAutoField))


# 마이그레이션 앱
target_apps = [
    'contenttypes',  # 모델의 콘텐츠 타입 정보
    'auth',  # 사용자, 그룹, 권한 관리
    'admin',  # 관리자 인터페이스
    'sessions',  # 세션 관리
    'messages',  # 메시지 프레임워크
    'rakmai',
    'member',
    'shop',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'easy_thumbnails',
]

# 마이그레이션에서 제외할 앱.모델 지정
exclude_models = [
    # 'shop.newmodel1',
    # 'shop.newmodel2',
    # 'member.newprofile'
]

migrator = DatabaseMigrator(app_labels=target_apps, batch_size=5000, exclude_models=exclude_models)
migrator.run_migration()
