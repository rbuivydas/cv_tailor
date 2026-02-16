import streamlit as st
from docxtpl import DocxTemplate
import PyPDF2
from google import genai
import io
import re
import os
from datetime import datetime

# --- DOCUMENT GENERATION ENGINE ---
def render_template(template_input, data_map):
    """Fills a .docx template and returns the stream. Handles both file objects and paths."""
    doc = None
    if isinstance(template_input, str):
        # If it's a file path from the templates folder
        doc = DocxTemplate(template_input)
    else:
        # If it's a file uploader object
        temp_path = "temp_render.docx"
        with open(temp_path, "wb") as f:
            f.write(template_input.getbuffer())
        doc = DocxTemplate(temp_path)
    
    doc.render(data_map)
    
    output_stream = io.BytesIO()
    doc.save(output_stream)
    output_stream.seek(0)
    
    # Cleanup if temp file was created
    if not isinstance(template_input, str) and os.path.exists("temp_render.docx"):
        os.remove("temp_render.docx")
        
    return output_stream

# --- CLEANING LOGIC ---
def clean_ai_text(text):
    """Removes common AI headers and markdown artifacts."""
    if not text:
        return ""
    text = re.sub(r'(?i)^(\d+\.\s*)?(\[)?(SUMMARY|SKILLS|SECTION|ITEM|OVERVIEW|COVER LETTER|LETTER|BODY)(\])?[:\- \t]*', '', text.strip())
    text = re.sub(r'[\*\^#]', '', text)
    return text.strip()

# --- UI CONFIGURATION ---
st.set_page_config(page_title="Career Suite Architect", layout="wide")

# Initialize Session State
if 'cv_blob' not in st.session_state:
    st.session_state.cv_blob = None
if 'cl_blob' not in st.session_state:
    st.session_state.cl_blob = None
if 'file_base' not in st.session_state:
    st.session_state.file_base = ""
if 'match_details' not in st.session_state:
    st.session_state.match_details = None

# --- TEMPLATE FOLDER LOGIC ---
TEMPLATE_DIR = "templates"
if not os.path.exists(TEMPLATE_DIR):
    os.makedirs(TEMPLATE_DIR)

available_templates = [f for f in os.listdir(TEMPLATE_DIR) if f.endswith('.docx')]

with st.sidebar:
    st.header("1. API & Templates")
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
    else:
        api_key = st.text_input("Gemini API Key", type="password")

    st.subheader("Template Selection")
    
    # Selection logic for CV
    cv_mode = st.radio("CV Template Source", ["Folder", "Manual Upload"])
    cv_template_source = None
    if cv_mode == "Folder" and available_templates:
        cv_selection = st.selectbox("Select CV Template", available_templates)
        cv_template_source = os.path.join(TEMPLATE_DIR, cv_selection)
    else:
        cv_template_source = st.file_uploader("Upload CV Template (.docx)", type="docx", key="cv_manual")

    # Selection logic for Cover Letter
    cl_mode = st.radio("Cover Letter Source", ["Folder", "Manual Upload"])
    cl_template_source = None
    if cl_mode == "Folder" and available_templates:
        cl_selection = st.selectbox("Select CL Template", available_templates)
        cl_template_source = os.path.join(TEMPLATE_DIR, cl_selection)
    else:
        cl_template_source = st.file_uploader("Upload Cover Letter Template (.docx)", type="docx", key="cl_manual")
    
    if st.button("🗑️ Reset Application"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

st.title("💼 CV Tailoring Program")

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
    uploaded_cv = st.file_uploader("Upload Main CV (PDF)", type="pdf")
with col_b:
    job_desc = st.text_area("2. Paste Job Description", height=200)

if st.button("🚀 Generate Tailored CV"):
    if not all([api_key, cv_template_source, uploaded_cv, job_desc]):
        st.error("Please provide API Key, CV Template, Master CV, and Job Description.")
    else:
        client = genai.Client(api_key=api_key)
        pdf_reader = PyPDF2.PdfReader(uploaded_cv)
        cv_raw_text = " ".join([p.extract_text() for p in pdf_reader.pages])

        with st.spinner("Analyzing and segmenting content correctly..."):
            prompt = f"""
            Act as a Senior Resume Writer and ATS Expert. 
            Create content for {name} applying for the {target_role} role at {company_name}.

            STRICT LANGUAGE RULE: 
            Use BRITISH ENGLISH throughout (e.g., 'honours', 'specialised', 'programme', 'organise', 'centre'). 
            Localise all terminology for the UK job market.
            
            YOU MUST PROVIDE EXACTLY 4 PARTS SEPARATED BY '===':
            PART 1: A professional summary in FIRST PERSON ('I'). 3-4 sentences.
            PART 2: A comma-separated list of ATS-optimized technical skills.
            PART 3: A full first-person cover letter.
            PART 4: A brief ATS match analysis (Keywords & % Score).
            
            STRICT: Do not include labels like 'PART 1' or 'Summary:' in the content.
            CV: {cv_raw_text}
            JOB: {job_desc}
            """
            
            response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
            parts = [p.strip() for p in response.text.split("===")]
            
            summary = clean_ai_text(parts[0]) if len(parts) > 0 else ""
            skills = clean_ai_text(parts[1]) if len(parts) > 1 else ""
            cl_body = clean_ai_text(parts[2]) if len(parts) > 2 else ""
            st.session_state.match_details = clean_ai_text(parts[3]) if len(parts) > 3 else "Analysis unavailable."

            st.session_state.file_base = f"{name.replace(' ', '_')}_{company_name.replace(' ', '_')}"
            
            cv_data = {
                'name': name.upper(), 'phone': phone, 'email': email,
                'linkedin': linkedin, 'github': "github.com/rbuivydas",
                'summary': summary, 'skills': skills
            }
            st.session_state.cv_blob = render_template(cv_template_source, cv_data)

            if cl_template_source:
                cl_data = {
                    'name': name, 'company': company_name, 'role': target_role,
                    'date': datetime.now().strftime("%d %B %Y"), 'letter_body': cl_body
                }
                st.session_state.cl_blob = render_template(cl_template_source, cl_data)

# --- PERSISTENT DISPLAY ---
if st.session_state.cv_blob:
    st.success(f"Tailored documents for {company_name} are ready!")
    
    with st.expander("📊 ATS Keyword Match Analysis", expanded=True):
        st.write(st.session_state.match_details)

    res_col, cl_col = st.columns(2)
    with res_col:
        st.download_button(
            label="📥 Download Tailored CV (.docx)",
            data=st.session_state.cv_blob,
            file_name=f"{st.session_state.file_base}_CV.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    
    if st.session_state.cl_blob:
        with cl_col:
            st.download_button(
                label="📥 Download Cover Letter (.docx)",
                data=st.session_state.cl_blob,
                file_name=f"{st.session_state.file_base}_CoverLetter.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
