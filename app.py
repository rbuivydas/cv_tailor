import streamlit as st
from docxtpl import DocxTemplate
import PyPDF2
from google import genai
import io
import re
import os
from datetime import datetime

# --- DOCUMENT GENERATION ENGINE ---
def render_template(template_path, data_map):
    """Fills a .docx template from a local path and returns the stream."""
    doc = DocxTemplate(template_path)
    doc.render(data_map)
    
    output_stream = io.BytesIO()
    doc.save(output_stream)
    output_stream.seek(0)
    return output_stream

def clean_ai_text(text):
    """Removes common AI headers and markdown artifacts."""
    if not text: return ""
    text = re.sub(r'(?i)^(\d+\.\s*)?(\[)?(SUMMARY|SKILLS|SECTION|ITEM|OVERVIEW|COVER LETTER|LETTER|BODY)(\])?[:\- \t]*', '', text.strip())
    text = re.sub(r'[\*\^#]', '', text)
    return text.strip()

# --- UI CONFIGURATION ---
st.set_page_config(page_title="Career Suite Architect (UK)", layout="wide")

# Persistent Session State
if 'cv_blob' not in st.session_state: st.session_state.cv_blob = None
if 'cl_blob' not in st.session_state: st.session_state.cl_blob = None
if 'file_base' not in st.session_state: st.session_state.file_base = ""
if 'match_details' not in st.session_state: st.session_state.match_details = None

# --- TEMPLATE SELECTION LOGIC ---
TEMPLATE_DIR = "templates"
# Ensure directory exists for local testing
if not os.path.exists(TEMPLATE_DIR):
    os.makedirs(TEMPLATE_DIR)

# Get list of .docx files in the templates folder
available_templates = [f for f in os.listdir(TEMPLATE_DIR) if f.endswith('.docx')]

with st.sidebar:
    st.header("🎨 Template Library")
    
    if not available_templates:
        st.warning("No templates found in /templates folder. Please upload manually below.")
        cv_template_path = st.file_uploader("Upload CV Template", type="docx")
        cl_template_path = st.file_uploader("Upload Cover Letter Template", type="docx")
    else:
        cv_choice = st.selectbox("Select CV Style", available_templates)
        cl_choice = st.selectbox("Select Cover Letter Style", available_templates)
        cv_template_path = os.path.join(TEMPLATE_DIR, cv_choice)
        cl_template_path = os.path.join(TEMPLATE_DIR, cl_choice)

    st.markdown("---")
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
    else:
        api_key = st.text_input("Gemini API Key", type="password")
    
    if st.button("🗑️ Reset Application"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

st.title("💼 AI Career Suite Architect (UK)")

# Application Identity
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
    uploaded_cv = st.file_uploader("1. Upload Master CV (PDF)", type="pdf")
with col_b:
    job_desc = st.text_area("2. Paste Job Description", height=200)

if st.button("🚀 Generate Tailored Suite"):
    if not all([api_key, cv_template_path, uploaded_cv, job_desc]):
        st.error("Missing requirements: API Key, Templates, or Documents.")
    else:
        client = genai.Client(api_key=api_key)
        pdf_reader = PyPDF2.PdfReader(uploaded_cv)
        cv_raw_text = " ".join([p.extract_text() for p in pdf_reader.pages])

        with st.spinner("British English Tailoring in Progress..."):
            prompt = f"""
            Act as a Senior British Recruitment Consultant. 
            Tailor content for {name} applying for {target_role} at {company_name}.
            
            STRICT RULES:
            - Use BRITISH ENGLISH spelling (honours, specialised).
            - Use FIRST PERSON ('I', 'My').
            - Split sections using '==='.
            - Part 1: Professional Summary (prose). No titles.
            - Part 2: ATS-Optimized Skills (comma-list). No titles.
            - Part 3: Full Cover Letter.
            - Part 4: ATS Match Analysis.
            
            CV: {cv_raw_text}
            JOB: {job_desc}
            """
            
            response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
            parts = [p.strip() for p in response.text.split("===")]
            
            summary = clean_ai_text(parts[0]) if len(parts) > 0 else ""
            skills = clean_ai_text(parts[1]) if len(parts) > 1 else ""
            cl_body = clean_ai_text(parts[2]) if len(parts) > 2 else ""
            st.session_state.match_details = clean_ai_text(parts[3]) if len(parts) > 3 else "N/A"

            st.session_state.file_base = f"{name.replace(' ', '_')}_{company_name.replace(' ', '_')}"
            
            cv_data = {
                'name': name.upper(), 'phone': phone, 'email': email,
                'linkedin': linkedin, 'github': "github.com/rbuivydas",
                'summary': summary, 'skills': skills
            }
            # Handles both local paths from selection and uploaded files
            st.session_state.cv_blob = render_template(cv_template_path, cv_data)

            if cl_template_path:
                cl_data = {
                    'name': name, 'company': company_name, 'role': target_role,
                    'date': datetime.now().strftime("%d %B %Y"),
                    'letter_body': cl_body
                }
                st.session_state.cl_blob = render_template(cl_template_path, cl_data)

# --- PERSISTENT DISPLAY ---
if st.session_state.cv_blob:
    st.success(f"Tailored documents for {company_name} are ready!")
    with st.expander("📊 ATS Keyword Match Analysis", expanded=True):
        st.write(st.session_state.match_details)

    res_col, cl_col = st.columns(2)
    with res_col:
        st.download_button(label="📥 Download CV (.docx)", data=st.session_state.cv_blob, 
                           file_name=f"{st.session_state.file_base}_CV.docx")
    
    if st.session_state.cl_blob:
        with cl_col:
            st.download_button(label="📥 Download Cover Letter (.docx)", data=st.session_state.cl_blob, 
                               file_name=f"{st.session_state.file_base}_CoverLetter.docx")
