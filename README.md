# 💼 AI CV Tailoring Application

**CV Tailor** is a Streamlit-based application that automatically tailors a professional CV and cover letter to a specific job description using generative AI. It is designed to optimise applications for **ATS (Applicant Tracking Systems)** while maintaining a polished, human-written tone aligned with the **UK job market**.

The tool analyses a master CV (PDF), a job description, and user-selected Word templates to generate:
- A tailored CV summary
- ATS-optimised skills list
- A full first-person cover letter
- A keyword match analysis with percentage score

---

## ✨ Features

- 📄 **CV Tailoring from PDF**  
  Extracts and analyses content from an uploaded master CV (PDF).

- 🧠 **AI-Powered Content Generation**  
  Uses Google Gemini to generate role-specific summaries, skills, and cover letters.

- 🧩 **ATS Optimisation**  
  Produces keyword-rich skills lists and a match analysis for ATS screening.

- 📝 **DOCX Template Engine**  
  Supports reusable `.docx` templates with placeholder variables.

- 📊 **Keyword Match Analysis**  
  Displays extracted keywords and an estimated ATS match score.

- 🔁 **Reusable & Resettable Workflow**  
  Session-based state management with one-click reset.

---

## 🏗️ Application Architecture

### Core Technologies

| Technology | Purpose |
|----------|--------|
| Streamlit | Web UI and session state management |
| PyPDF2 | Extracts text from uploaded CV PDFs |
| docxtpl | Renders Word templates using dynamic data |
| Google Gemini API | AI-driven CV & cover letter generation |
| Regex Cleaning Engine | Removes AI artefacts and formatting noise |

---

## 📂 Folder Structure

cv_tailor/
│
├── app.py # Main Streamlit application
├── README.md # Project documentation
├── requirements.txt # Python dependencies
│
├── templates/ # Reusable Word templates
│ ├── cv_template.docx # CV template with placeholders
│ └── cover_letter_template.docx # Cover letter template
│
├── .streamlit/
│ ├── secrets.toml # Gemini API key (not committed)
│ └── config.toml # Streamlit UI configuration
│
├── assets/ # Optional static assets
│ ├── screenshots/ # App screenshots for README
│ └── icons/ # Logos or UI icons
│
└── .gitignore # Git ignore rules
