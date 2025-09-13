import streamlit as st
import os
import tempfile
from src.workflow import ResumeProcessingWorkflow
import pprint
import datetime
import time
import json


def main():
    st.set_page_config(
        page_title="Resume Key Attributes Extractor",
        page_icon="📄",
        layout="wide"
    )

    st.title("📄 Resume Parser")
    st.markdown("""
    Загрузите ваше резюме (PDF или DOCX) и система извлечет ключевую информацию в структурированном формате.
    """)

    # Инициализация session state
    if 'processing_result' not in st.session_state:
        st.session_state.processing_result = None
    if 'current_file_name' not in st.session_state:
        st.session_state.current_file_name = None

    # Загрузка файла
    uploaded_file = st.file_uploader(
        "Загрузите файл резюме",
        type=["pdf", "docx", "doc"],
        help="Поддерживаемые форматы: PDF, DOC, DOCX"
    )

    # Проверяем, был ли загружен новый файл
    if uploaded_file is not None:
        # Если файл изменился, сбрасываем результаты и обрабатываем заново
        if st.session_state.current_file_name != uploaded_file.name:
            st.session_state.current_file_name = uploaded_file.name
            st.session_state.processing_result = None

            # Сохранение загруженного файла временно
            with st.spinner("Обработка файла..."):
                # Создаем временную директорию
                os.makedirs("temp_uploads", exist_ok=True)

                # Сохраняем файл
                file_path = os.path.join("temp_uploads", uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                # Обрабатываем резюме
                workflow = ResumeProcessingWorkflow()
                result = workflow.process_resume(file_path)

                # Сохраняем результат в session state
                st.session_state.processing_result = result

                # Очистка
                os.remove(file_path)

                # Для отладки (можно убрать в production)
                # st.write("Результат обработки сохранен в session_state")
        else:
            # Используем уже обработанные данные
            result = st.session_state.processing_result
    else:
        # Сбрасываем состояние при удалении файла
        st.session_state.current_file_name = None
        st.session_state.processing_result = None

    # Отображаем результаты, если они есть
    if st.session_state.processing_result is not None:
        result = st.session_state.processing_result

        # Отображение результатов
        if result.get("error"):
            st.error(f"❌ Ошибка: {result['error']}")

            # Проверка на проблемы с API
            if "API" in result["error"]:
                st.warning("""
                **Вероятная причина:** Проблема с API-ключом

                Comet API блокирует запросы с сообщением: "Sorry, you have been blocked"
                OpenRouter возвращает ошибку: "The model 'api/v1' is not available"

                **Решение:**
                1. Для Comet: свяжитесь с поддержкой для снятия блокировки
                2. Для OpenRouter: раскомментируйте соответствующие строки в llmclient.py
                   и укажите правильное имя модели (например, "qwen/qwen-2.5-72b-instruct")
                """)
        else:
            st.success("✅ Резюме успешно обработано!")

            # Показ результатов валидации
            if result.get("validation_result"):
                validation = result["validation_result"]
                st.subheader("🔍 Результаты валидации")

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Это резюме?", "Да" if validation["is_resume"] else "Нет",
                              delta=f"Уверенность, в том что файл - резюме: {validation['confidence']:.2f}")
                    # st.write(f"**Формат:** {validation['primary_format']}")
                    # st.write(f"**Рекомендуемое действие:** {validation['suggested_action']}")

                # Показ результатов извлечения, если это резюме
                if result.get("extraction_result") and result.get("validation_result", {}).get("is_resume", False):
                    st.subheader("📊 Извлеченная информация")

                    extraction = result["extraction_result"]

                    # Личная информация
                    st.markdown("### 👤 Личная информация")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write("**Полное имя:**", extraction["full_name"] or "Не найдено")
                    with col2:
                        st.write("**Email:**", extraction["email"] or "Не найден")
                    with col3:
                        st.write("**Phone:**", extraction["phone_number"] or "Не найдено")

                    # Образование
                    if extraction["education"]:
                        st.markdown("### 🎓 Образование")
                        for edu in extraction["education"]:
                            with st.expander(f"{edu['degree']} в {edu['field']}"):
                                st.write("**Учебное заведение:**", edu["institution"] or "Не указано")
                                period = f"{edu['start_date']} - {edu['end_date']}"
                                st.write("**Период:**", period)
                                if edu["grade"]:
                                    st.write("**Оценка/рейтинг:**", edu["grade"])

                    # Опыт работы
                    if extraction["employment_details"]:
                        st.markdown("### 💼 Опыт работы")
                        for emp in extraction["employment_details"]:
                            with st.expander(f"{emp['title']} в {emp['company']}"):
                                st.write("**Местоположение:**", emp["location"] or "Не указано")
                                period = f"{emp['start_date']} - {emp['end_date']}"
                                st.write("**Период:**", period)
                                st.write("**Описание:**", emp["description"] or "Не указано")

                    # Навыки
                    col1, col2 = st.columns(2)

                    with col1:
                        if extraction["technical_skills"]:
                            st.markdown("### 🛠️ Технические навыки")
                            for skill in extraction["technical_skills"]:
                                st.write(f"**{skill['category'] or 'Другое'}**: {', '.join(skill['skills'])}")

                    with col2:
                        if extraction["languages"]:
                            st.markdown("### 🌍 Языки")
                            for lang in extraction["languages"]:
                                st.write(f"- **{lang['language']}**: {lang['proficiency'] or 'Уровень не указан'}")

                    # Другие разделы
                    if extraction["projects"]:
                        st.markdown("### 📂 Проекты")
                        for project in extraction["projects"]:
                            with st.expander(project["title"] or "Безымянный проект"):
                                st.write("**Описание:**", project["description"] or "Не указано")
                                st.write("**Технологии:**", ", ".join(project["technologies"]) if project[
                                    "technologies"] else "Не указаны")
                                st.write("**Период:**", project["period"] or "Не указан")

                    if extraction["publications"]:
                        st.markdown("### 📚 Публикации")
                        for pub in extraction["publications"]:
                            with st.expander(pub["title"] or "Безымянная публикация"):
                                st.write("**Источник:**", pub["venue"] or "Не указан")
                                st.write("**Год:**", pub["year"] or "Не указан")
                                st.write("**Авторы:**", ", ".join(pub["authors"]) if pub["authors"] else "Не указаны")
                                st.write("**Ссылка:**", pub["link"] or "Не указана")

                    if extraction["soft_skills"]:
                        st.markdown("### 🤝 Soft skills")
                        st.write(", ".join(extraction["soft_skills"]))

                    if extraction["additional_information"]:
                        st.markdown("### ℹ️ Additional information")
                        st.write(extraction["additional_information"])

                    st.markdown("---")
                    st.subheader("📥 Скачать результаты")

                    # Подготовка данных для скачивания
                    full_results = {
                        "metadata": {
                            "processed_at": str(datetime.datetime.now()),
                            "file_name": st.session_state.current_file_name,
                            "file_size": f"{len(result['file_content'])} символов"
                        },
                        "validation": result["validation_result"],
                        "extraction": result["extraction_result"]
                    }

                    # Конвертируем в JSON
                    json_data = json.dumps(full_results, indent=2, ensure_ascii=False)

                    # Кнопка для скачивания полных результатов
                    st.download_button(
                        label="Скачать полные результаты (JSON)",
                        data=json_data,
                        file_name=f"resume_results_{int(time.time())}.json",
                        mime="application/json",
                        help="Скачать все результаты обработки в формате JSON",
                        use_container_width=True
                    )

                    # Опционально: кнопка для скачивания только структурированных данных
                    if result["extraction_result"]:
                        structured_data = json.dumps(result["extraction_result"], indent=2, ensure_ascii=False)
                        st.download_button(
                            label="Скачать только извлеченные данные (JSON)",
                            data=structured_data,
                            file_name=f"resume_data_{int(time.time())}.json",
                            mime="application/json",
                            help="Скачать только структурированные данные резюме",
                            use_container_width=True
                        )

                # Если не резюме
                elif result.get("validation_result") and not result["validation_result"]["is_resume"]:
                    st.warning("⚠️ Загруженный документ не распознан как резюме/CV.")
                    st.write("Пожалуйста, загрузите корректный документ резюме.")

    # Информация в сайдбаре
    st.sidebar.title("ℹ️ Информация")
    st.sidebar.info("""
    Это приложение извлекает ключевые аттрибуты резюме.

    **Как это работает:**
    1. Загрузите резюме (PDF/DOC/DOCX)
    2. Система проверяет, является ли документ резюме
    3. Если да, извлекает структурированную информацию
    4. Отображает извлеченные данные в удобном формате
    """)

    # Добавляем кнопку для сброса и загрузки нового файла
    # if st.sidebar.button("🔄 Загрузить новое резюме"):
    #     st.session_state.current_file_name = None
    #     st.session_state.processing_result = None
    #     st.rerun()


if __name__ == "__main__":
    main()