import streamlit as st
from docxtpl import DocxTemplate
import PyPDF2
from google import genai
import io
import re
import os
from datetime import datetime

# --- DOCUMENT GENERATION ENGINE ---
def render_template(template_file, data_map):
    """Fills a .docx template and returns the stream."""
    temp_path = "temp_render.docx"
    with open(temp_path, "wb") as f:
        f.write(template_file.getbuffer())
    
    doc = DocxTemplate(temp_path)
    doc.render(data_map)
    
    output_stream = io.BytesIO()
    doc.save(output_stream)
    output_stream.seek(0)
    
    if os.path.exists(temp_path):
        os.remove(temp_path)
    return output_stream

# --- CLEANING LOGIC ---
def clean_ai_text(text):
    """Removes common AI headers and markdown artifacts."""
    text = re.sub(r'(?i)^(\d+\.\s*)?(\[)?(SUMMARY|SKILLS|SECTION|ITEM|OVERVIEW|COVER LETTER|LETTER|BODY)(\])?[:\- \t]*', '', text.strip())
    text = re.sub(r'[\*\^#]', '', text)
    return text.strip()

# --- UI CONFIGURATION ---
st.set_page_config(page_title="Career Suite Architect", layout="wide")

# Initialize Session State to keep files persistent
if 'cv_blob' not in st.session_state:
    st.session_state.cv_blob = None
if 'cl_blob' not in st.session_state:
    st.session_state.cl_blob = None
if 'file_base' not in st.session_state:
    st.session_state.file_base = ""
if 'match_details' not in st.session_state:
    st.session_state.match_details = None

with st.sidebar:
    st.header("1. API & Templates")
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
    else:
        api_key = st.text_input("Gemini API Key", type="password")
    
    cv_template_file = st.file_uploader("Upload CV Template (.docx)", type="docx")
    cl_template_file = st.file_uploader("Upload Cover Letter Template (.docx)", type="docx")

st.title("💼 AI Career Suite Architect")

with st.expander("Application Identity", expanded=True):
    c1, c2, c3 = st.columns(3)
    with c1:
        name = st.text_input("Full Name", "Rimantas Buivydas")
        email = st.text_input("Email", "rimvntas59@gmail.com")
    with c2:
        phone = st.text_input("Phone", "+44 7783 949991")
        company_name = st.text_input("Target Company", "e.g. London Law Firm")
    with c3:
        target_role = st.text_input("Target Role", "IT Service Desk Analyst")
        linkedin = st.text_input("LinkedIn URL", "linkedin.com/in/rimantas-buivydas/")

st.markdown("---")
col_a, col_b = st.columns(2)
with col_a:
    uploaded_cv = st.file_uploader("Upload Master CV (PDF)", type="pdf")
with col_b:
    job_desc = st.text_area("2. Paste Job Description", height=200)

if st.button("🚀 Generate Professional Suite"):
    if not all([api_key, cv_template_file, uploaded_cv, job_desc]):
        st.error("Please provide API Key, CV Template, Master CV, and Job Description.")
    else:
        client = genai.Client(api_key=api_key)
        pdf_reader = PyPDF2.PdfReader(uploaded_cv)
        cv_raw_text = " ".join([p.extract_text() for p in pdf_reader.pages])

        with st.spinner("Optimizing and Generating..."):
            prompt = f"""
            Act as a Senior Career Consultant and ATS Expert. 
            Create content for {name} applying for {target_role} at {company_name}.
            
            STRICT RULES:
            - Split with '==='.
            - Part 1 (Summary): 1st person ('I', 'My'), 3-4 sentences. No titles.
            - Part 2 (Skills): Comma-separated technical keywords found in both the job and CV. No titles.
            - Part 3 (Cover Letter): Full 1st person letter.
            - Part 4 (Match Analysis): List 5 key matched keywords and an ATS % score.
            
            CV: {cv_raw_text}
            JOB: {job_desc}
            """
            
            response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
            parts = response.text.split("===")
            
            # Store everything in session state
            summary = clean_ai_text(parts[0])
            skills = clean_ai_text(parts[1])
            cl_body = clean_ai_text(parts[2])
            st.session_state.match_details = parts[3] if len(parts) > 3 else "N/A"

            # Prepare Files
            st.session_state.file_base = f"{name.replace(' ', '_')}_{company_name.replace(' ', '_')}"
            
            cv_data = {
                'name': name.upper(), 'phone': phone, 'email': email,
                'linkedin': linkedin, 'github': "github.com/rbuivydas",
                'summary': summary, 'skills': skills
            }
            st.session_state.cv_blob = render_template(cv_template_file, cv_data)

            if cl_template_file:
                cl_data = {
                    'name': name, 'company': company_name, 'role': target_role,
                    'date': datetime.now().strftime("%B %d, %Y"), 'letter_body': cl_body
                }
                st.session_state.cl_blob = render_template(cl_template_file, cl_data)

# --- DISPLAY PERSISTENT RESULTS ---
if st.session_state.cv_blob:
    st.success(f"Tailored documents for {company_name} are ready!")
    
    # Keyword Match Analysis Section
    with st.expander("📊 ATS Keyword Match Analysis", expanded=True):
        st.write(st.session_state.match_details)

    res_col, cl_col = st.columns(2)
    with res_col:
        st.download_button(
            label="📥 Download CV (.docx)",
            data=st.session_state.cv_blob,
            file_name=f"{st.session_state.file_base}_CV.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            key="cv_download"
        )
    
    if st.session_state.cl_blob:
        with cl_col:
            st.download_button(
                label="📥 Download Cover Letter (.docx)",
                data=st.session_state.cl_blob,
                file_name=f"{st.session_state.file_base}_CoverLetter.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key="cl_download"
            )
