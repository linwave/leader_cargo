from celery import shared_task
import pandas as pd
from django.utils import timezone
from .models import Calls, CallsFile
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

# Размер пакета для batch_create
BATCH_SIZE = 5000

# Функция для нахождения ближайшего совпадения по названию колонки
def find_best_matches(column_name, possible_names):
    column_name_lower = ''.join(column_name.split()).lower()
    best_match = None
    max_similarity = 0

    for possible_name in possible_names:
        possible_name_lower = ''.join(possible_name.split()).lower()
        intersection = len(set(column_name_lower) & set(possible_name_lower))
        union = len(set(column_name_lower) | set(possible_name_lower))
        if union == 0:
            continue
        similarity = intersection / union
        if similarity > max_similarity and similarity >= 0.9:
            max_similarity = similarity
            best_match = possible_name

    return best_match

@shared_task
def process_excel_file(file_id):
    calls_file = CallsFile.objects.get(id=file_id)
    try:
        excel_file = calls_file.file

        # Чтение файла Excel с использованием pandas
        df = pd.read_excel(excel_file)

        # Определение возможных вариантов имен колонок
        column_mapping = {
            'client_name': ['название лида', 'имя', 'фамилия', 'имя клиента', 'компания'],
            'client_phone': ['телефон', 'номер телефона', 'контактный номер', 'рабочий телефон'],
        }

        # Нормализация имен колонок и сбор данных
        normalized_columns = {key: [] for key in column_mapping.keys()}
        for col in df.columns:
            for key, possible_names in column_mapping.items():
                best_match = find_best_matches(col, possible_names)
                if best_match:
                    normalized_columns[key].append(col)
                    break

        # Проверка наличия хотя бы одной колонки для каждого поля
        required_columns = set(column_mapping.keys())
        missing_columns = []
        for key in required_columns:
            if not normalized_columns[key]:
                missing_columns.append(key)
        if missing_columns:
            logger.error(f'Отсутствуют необходимые колонки: {", ".join(missing_columns)}.')
            return f'Отсутствуют необходимые колонки: {", ".join(missing_columns)}.'

        # Получение всех операторов и установка начального индекса
        operators = list(User.objects.filter(role='Оператор'))  # Фильтрация по роли Оператор
        current_operator_index = 0

        # Процесс создания объектов Calls
        total_rows = len(df)
        processed_rows = 0
        created_calls_count = 0
        duplicate_phone_count = 0

        logger.info(f'Начало обработки файла {calls_file.file.name}. Всего строк: {total_rows}')

        calls_to_create = []
        existing_phones = Calls.get_existing_phones()

        for index, row in df.iterrows():
            processed_rows += 1

            # Выбор следующего оператора по очереди
            if operators:
                current_operator = operators[current_operator_index]
                current_operator_index = (current_operator_index + 1) % len(operators)
            else:
                current_operator = None  # Если нет операторов, оставляем поле operator пустым

            # Создание объекта Calls
            call = Calls.create_from_row(row, normalized_columns, current_operator, calls_file)
            if call:
                if call.client_phone in existing_phones:
                    logger.warning(f'Пропущена строка {processed_rows}: client_phone={call.client_phone} уже существует.')
                    duplicate_phone_count += 1
                    continue
                calls_to_create.append(call)
                existing_phones.add(call.client_phone)

            # Массовое создание объектов Calls с пакетным созданием
            if len(calls_to_create) >= BATCH_SIZE:
                created_calls = Calls.objects.bulk_create(calls_to_create)
                created_calls_count += len(created_calls)
                logger.info(f'Создано {created_calls_count} новых объектов Calls.')
                calls_to_create = []

        # Создание оставшихся объектов Calls
        if calls_to_create:
            created_calls = Calls.objects.bulk_create(calls_to_create)
            created_calls_count += len(created_calls)
            logger.info(f'Создано {created_calls_count} новых объектов Calls.')

        logger.info(f'Файл {calls_file.file.name} успешно обработан. Всего строк: {total_rows}, обработано: {processed_rows}, создано заявок: {created_calls_count}, дублирующихся номеров: {duplicate_phone_count}')
        return 'Файл успешно обработан.'
    except Exception as e:
        logger.error(f'Ошибка при обработке файла {calls_file.file.name}: {e}')
        return str(e)