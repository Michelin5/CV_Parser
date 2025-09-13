import os
import time
from agents import agent0_validator, agent1_extractor
from src.services.file_parser import FileParser  # Используем ваш оригинальный парсер


def print_header(text):
    """Печатает заголовок с разделителями"""
    print("\n" + "=" * 60)
    print(f" {text} ".center(60))
    print("=" * 60)


def print_section(text):
    """Печатает раздел с подзаголовком"""
    print("\n" + "-" * 40)
    print(f" {text} ")
    print("-" * 40)


def test_resume_processing(file_path):
    """Тестирует обработку резюме и выводит результаты в консоль"""

    # Проверяем существование файла
    if not os.path.exists(file_path):
        print(f"❌ Ошибка: Файл {file_path} не найден")
        print("Пожалуйста, убедитесь, что файл находится в папке data/")
        return

    print_header("НАЧАЛО ОБРАБОТКИ РЕЗЮМЕ")
    print(f"Файл: {file_path}")

    # 1. Парсинг файла
    print_section("1. ПАРСИНГ ФАЙЛА")
    start_time = time.time()

    try:
        parser = FileParser()
        parser.load(file_path)

        parse_time = time.time() - start_time
        print(f"✓ Успешно извлечено {len(parser.text)} символов текста")
        print(f"✓ Найдено {len(parser.links)} ссылок")
        print(f"Время обработки: {parse_time:.2f} сек")
    except Exception as e:
        print(f"✗ Ошибка парсинга: {str(e)}")
        return

    # 2. Валидация резюме
    print_section("2. ВАЛИДАЦИЯ РЕЗЮМЕ")
    start_time = time.time()

    try:
        validation_result = agent0_validator(parser.text)
        validation_time = time.time() - start_time

        if validation_result.get("error"):
            print(f"✗ Ошибка валидации: {validation_result['error']}")

            # Проверяем, связана ли ошибка с API
            if "API" in validation_result["error"]:
                print("\nВОЗМОЖНАЯ ПРИЧИНА:")
                print("API-ключ, вероятно, не работает. Проверьте:")
                print("1. Для Comet API: вы получили блокировку (см. информацию ниже)")
                print("2. Для OpenRouter: убедитесь, что раскомментированы строки в llmclient.py")
                print("   и указано правильное имя модели (не 'api/v1')")
                print("\nИНФОРМАЦИЯ О БЛОКИРОВКЕ:")
                print("Comet API: 'Sorry, you have been blocked'")
                print("OpenRouter: 'The model \"api/v1\" is not available'")
            return
        else:
            print(f"✓ Это {'резюме' if validation_result['is_resume'] else 'НЕ резюме'}")
            print(f"Уверенность: {validation_result['confidence']:.2f}")
            print(f"Обоснование: {validation_result['explain']}")
            print(f"Время обработки: {validation_time:.2f} сек")

            if not validation_result['is_resume']:
                print("\n⚠️ Документ не распознан как резюме.")
                print("Пожалуйста, загрузите корректное резюме.")
                return
    except Exception as e:
        print(f"✗ Неожиданная ошибка валидации: {str(e)}")
        return

    # 3. Извлечение данных
    print_section("3. ИЗВЛЕЧЕНИЕ АТРИБУТОВ")
    start_time = time.time()

    try:
        extraction_result = agent1_extractor(parser.text)
        extraction_time = time.time() - start_time

        if extraction_result.get("error"):
            print(f"✗ Ошибка извлечения: {extraction_result['error']}")

            # Проверяем, связана ли ошибка с API
            if "API" in extraction_result["error"]:
                print("\nВОЗМОЖНАЯ ПРИЧИНА:")
                print("API-ключ, вероятно, не работает. Проверьте:")
                print("1. Для Comet API: вы получили блокировку (см. информацию ниже)")
                print("2. Для OpenRouter: убедитесь, что раскомментированы строки в llmclient.py")
                print("   и указано правильное имя модели (не 'api/v1')")
                print("\nИНФОРМАЦИЯ О БЛОКИРОВКЕ:")
                print("Comet API: 'Sorry, you have been blocked'")
                print("OpenRouter: 'The model \"api/v1\" is not available'")
            return
        else:
            print("✓ Извлечение завершено успешно!")
            print(f"Время обработки: {extraction_time:.2f} сек")
    except Exception as e:
        print(f"✗ Неожиданная ошибка извлечения: {str(e)}")
        return

    # 4. Вывод результатов
    print_section("4. РЕЗУЛЬТАТЫ ОБРАБОТКИ")

    # Личная информация
    print("\n👤 ЛИЧНАЯ ИНФОРМАЦИЯ:")
    print(f"Полное имя: {extraction_result.get('full_name', 'Не найдено')}")
    print(f"Email: {extraction_result.get('email', 'Не найден')}")

    # Образование
    education = extraction_result.get('education', [])
    if education and education[0] is not None:
        print("\n🎓 ОБРАЗОВАНИЕ:")
        for i, edu in enumerate(education):
            print(f"{i + 1}. {edu.get('degree', 'Не указано')} в {edu.get('field', 'Не указано')}")
            print(f"   Учебное заведение: {edu.get('institution', 'Не указано')}")
            print(f"   Период: {edu.get('start_date', 'Не указан')} - {edu.get('end_date', 'Не указан')}")
            if edu.get('grade'):
                print(f"   Оценка: {edu.get('grade')}")

    # Опыт работы
    employment = extraction_result.get('employment_details', [])
    if employment and employment[0] is not None:
        print("\n💼 ОПЫТ РАБОТЫ:")
        for i, emp in enumerate(employment):
            print(f"{i + 1}. {emp.get('title', 'Не указано')} в {emp.get('company', 'Не указано')}")
            print(f"   Местоположение: {emp.get('location', 'Не указано')}")
            print(f"   Период: {emp.get('start_date', 'Не указан')} - {emp.get('end_date', 'Не указан')}")
            print(f"   Описание: {emp.get('description', 'Не указано')}")

    # Навыки
    programming_languages = extraction_result.get('programming_languages', [])
    if programming_languages and programming_languages[0] is not None:
        print("\n💻 ЯЗЫКИ ПРОГРАММИРОВАНИЯ:")
        for lang in programming_languages:
            print(f"- {lang.get('language', 'Не указано')}: {lang.get('proficiency', 'Уровень не указан')}")

    technical_skills = extraction_result.get('technical_skills', [])
    if technical_skills and technical_skills[0] is not None:
        print("\n🛠️ ТЕХНИЧЕСКИЕ НАВЫКИ:")
        for skill in technical_skills:
            print(f"- {skill.get('category', 'Другое')}: {', '.join(skill.get('skills', []))}")

    languages = extraction_result.get('languages', [])
    if languages and languages[0] is not None:
        print("\n🌍 ЯЗЫКИ:")
        for lang in languages:
            print(f"- {lang.get('language', 'Не указано')}: {lang.get('proficiency', 'Уровень не указан')}")

    soft_skills = extraction_result.get('soft_skills', [])
    if soft_skills:
        print("\n🤝 МЯГКИЕ НАВЫКИ:")
        print(", ".join(soft_skills))

    # Общая статистика
    total_time = parse_time + validation_time + extraction_time
    print(f"\n⏱️ ОБЩЕЕ ВРЕМЯ ОБРАБОТКИ: {total_time:.2f} сек")

    print_header("ОБРАБОТКА ЗАВЕРШЕНА")


if __name__ == "__main__":
    # Укажите путь к вашему тестовому файлу
    test_file = "data/Baizak.pdf"

    if not os.path.exists(test_file):
        print(f"❌ Ошибка: Файл {test_file} не найден")
        print("Пожалуйста, поместите тестовый файл в папку data/")
        print("\nДоступные тестовые файлы:")

        # Показать доступные файлы в папке data
        if os.path.exists("data"):
            for file in os.listdir("data"):
                if file.lower().endswith(('.pdf', '.docx', '.doc')):
                    print(f"- data/{file}")
        else:
            print("- Создайте папку data и поместите тестовые файлы туда")
    else:
        test_resume_processing(test_file)
