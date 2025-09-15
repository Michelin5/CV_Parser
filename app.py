import streamlit as st
import os
import tempfile
from src.workflow import ResumeProcessingWorkflow
from agents import custom_summarizer
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
    Upload your resume in English (PDF or DOCX) and the system extracts the key information in a structured format.
    """)

    # Инициализация session state
    if 'processing_result' not in st.session_state:
        st.session_state.processing_result = None
    if 'current_file_name' not in st.session_state:
        st.session_state.current_file_name = None
    if 'custom_summary' not in st.session_state:
        st.session_state.custom_summary = None

    # Загрузка файла
    uploaded_file = st.file_uploader(
        "Upload resume file",
        type=["pdf", "docx"],
        help="Supported extensions: PDF, DOCX"
    )

    # Проверяем, был ли загружен новый файл
    if uploaded_file is not None:
        # Если файл изменился, сбрасываем результаты и обрабатываем заново
        if st.session_state.current_file_name != uploaded_file.name:
            st.session_state.current_file_name = uploaded_file.name
            st.session_state.processing_result = None
            st.session_state.custom_summary = None

            # Сохранение загруженного файла временно
            with st.spinner("File processing..."):
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
        st.session_state.custom_summary = None

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
            st.success("✅ The resume has been successfully processed!")

            # Показ результатов валидации
            if result.get("validation_result"):
                validation = result["validation_result"]
                st.subheader("🔍 Validation result")

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("### Is this a resume?")
                    if validation["is_resume"]:
                        st.markdown(
                            f"##### :green[YES] (Confidence score, that this file is a resume: {validation['confidence']:.2f})")
                    else:
                        st.markdown(
                            f"##### :red[NO] (Confidence score, that this file is a resume: {validation['confidence']:.2f})")
                    # st.metric("Это резюме?", "Да" if validation["is_resume"] else "Нет",
                    #           delta=f"Уверенность, в том что файл - резюме: {validation['confidence']:.2f}")
                    # st.write(f"**Формат:** {validation['primary_format']}")
                    # st.write(f"**Рекомендуемое действие:** {validation['suggested_action']}")

                # Показ результатов извлечения, если это резюме
                if result.get("extraction_result") and result.get("validation_result", {}).get("is_resume", False):
                    st.subheader("📊 Extracted information")

                    extraction = result["extraction_result"]

                    # Личная информация
                    st.markdown("### 👤 Personal information")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write("**Full name:**", extraction["full_name"] or "Not found")
                    with col2:
                        st.write("**Email:**", extraction["email"] or "Not found")
                    with col3:
                        st.write("**Phone:**", extraction["phone_number"] or "Not found")

                    # Образование
                    if extraction["education"]:
                        st.markdown("### 🎓 Education")
                        for edu in extraction["education"]:
                            with st.expander(f"{edu['degree']} in {edu['field']}"):
                                st.write("**Institution:**", edu["institution"] or "Not stated")
                                period = f"{edu['start_date']} - {edu['end_date']}"
                                st.write("**Date:**", period)
                                if edu["grade"]:
                                    st.write("**Grade/GPA:**", edu["grade"])

                    # Опыт работы
                    if extraction["employment_details"]:
                        st.markdown("### 💼 Working experience")
                        for emp in extraction["employment_details"]:
                            with st.expander(f"{emp['title']} в {emp['company']}"):
                                st.write("**Location:**", emp["location"] or "Not stated")
                                period = f"{emp['start_date']} - {emp['end_date']}"
                                st.write("**Period:**", period)
                                st.write("**Description:**", emp["description"] or "Not stated")

                    # Навыки
                    col1, col2 = st.columns(2)

                    with col1:
                        if extraction["technical_skills"]:
                            st.markdown("### 🛠️ Technical skills")
                            for skill in extraction["technical_skills"]:
                                st.write(f"**{skill['category'] or 'Other'}**: {', '.join(skill['skills'])}")

                    with col2:
                        if extraction["languages"]:
                            st.markdown("### 🌍 Languages")
                            for lang in extraction["languages"]:
                                st.write(f"- **{lang['language']}**: {lang['proficiency'] or 'Proficiency not stated'}")

                    # Другие разделы
                    if extraction["projects"]:
                        st.markdown("### 📂 Projects")
                        for project in extraction["projects"]:
                            with st.expander(project["title"] or "Unnamed project"):
                                st.write("**Description:**", project["description"] or "Not stated")
                                st.write("**Technologies:**", ", ".join(project["technologies"]) if project[
                                    "technologies"] else "Not stated")
                                st.write("**Period:**", project["period"] or "Not stated")

                    if extraction["publications"]:
                        st.markdown("### 📚 Publications")
                        for pub in extraction["publications"]:
                            with st.expander(pub["title"] or "Unnamed publication"):
                                st.write("**Venue:**", pub["venue"] or "Not stated")
                                st.write("**Year:**", pub["year"] or "Not stated")
                                st.write("**Authors:**", ", ".join(pub["authors"]) if pub["authors"] else "Not stated")
                                st.write("**Link:**", pub["link"] or "Not stated")

                    if extraction["soft_skills"]:
                        st.markdown("### 🤝 Soft skills")
                        st.write(", ".join(extraction["soft_skills"]))

                    if extraction["additional_information"]:
                        st.markdown("### ℹ️ Additional information")
                        st.write(extraction["additional_information"])

                    # Краткий пересказ резюме
                    if result.get("summary"):
                        st.markdown("### 📝 Resume Summary")
                        st.write(result["summary"])

                    # Custom Summary section
                    st.markdown("### 🔧 Custom Summary by Parameters")
                    fixed_params = ['experience', 'skills', 'education', 'pros', 'cons', 'projects', 'languages',
                                    'soft_skills', 'certifications']
                    st.info(f"Available parameters: {', '.join(fixed_params)}")
                    params_input = st.text_input(
                        "Enter key parameters (comma-separated):",
                        placeholder="experience, skills, education"
                    )
                    col1, col2 = st.columns(2)
                    generate_btn = col1.button("Generate Custom Summary")
                    clear_btn = col2.button("Clear Summary")

                    if clear_btn:
                        st.session_state.custom_summary = None
                        st.rerun()

                    if generate_btn and params_input.strip():
                        raw_parts = params_input.split(",")
                        parameters = [p.strip().lower() for p in raw_parts if p.strip()]

                        if not parameters:
                            st.warning(
                                "Incorrect format: No valid parameters entered. Please separate parameters with commas.")
                        else:
                            invalid_params = [p for p in parameters if p not in fixed_params]
                            if invalid_params:
                                st.warning(
                                    f"Invalid parameters: {', '.join(invalid_params)}. Please use only from the available list.")
                            elif result.get("file_content"):
                                with st.spinner("Generating custom summary..."):
                                    custom_summary = custom_summarizer(result["file_content"], parameters)
                                    if custom_summary:
                                        st.session_state.custom_summary = custom_summary
                                    else:
                                        st.session_state.custom_summary = None
                                        st.error("Failed to generate custom summary.")
                            else:
                                st.warning("No resume content available for summarization.")
                        st.rerun()

                    # Display the custom summary if it exists
                    if st.session_state.custom_summary:
                        st.markdown("#### Generated Summary")
                        st.write(st.session_state.custom_summary)

                    st.markdown("---")
                    st.subheader("📥 Download results")

                    # Опционально: кнопка для скачивания только структурированных данных
                    if result["extraction_result"]:
                        structured_data = json.dumps(result["extraction_result"], indent=2, ensure_ascii=False)
                        st.download_button(
                            label="Download extracted information (JSON)",
                            data=structured_data,
                            file_name=f"resume_data_{int(time.time())}.json",
                            mime="application/json",
                            help="Download only extracted information (JSON).",
                            use_container_width=True
                        )

                # Если не резюме
                elif result.get("validation_result") and not result["validation_result"]["is_resume"]:
                    st.warning("⚠️ The uploaded document is not recognized as a resume/CV.")
                    st.write("Please upload a valid resume document.")

    # Информация в сайдбаре
    st.sidebar.title("ℹ️ Информация")
    st.sidebar.info("""
    Это приложение извлекает ключевые аттрибуты резюме.

    **Как это работает:**
    1. Загрузите резюме на английском языке (PDF/DOCX)
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