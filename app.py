import streamlit as st
from docxtpl import DocxTemplate
import PyPDF2
from google import genai
import io
import re
import os
import random
from datetime import datetime

# --- LINGUISTIC SCRAMBLER (Pass 2) ---
def bypass_scrambler(text):
    """
    Manually disrupts AI probability patterns to bypass detectors.
    Swaps robotic transitions for natural human speech rhythms.
    """
    if not text: return ""
    
    human_map = {
        "furthermore": "also,",
        "moreover": "on top of that,",
        "in addition": "plus,",
        "consequently": "essentially,",
        "demonstrate": "showcase",
        "utilize": "work with",
        "possess": "have",
        "highly motivated": "keen",
        "testament to": "proof of",
        "committed to": "focused on",
        "pivotal": "crucial",
        "underscores": "highlights",
        "ensure": "make sure",
        "passionate about": "really interested in",
        "extensive experience": "solid background"
    }
    
    for bot, human in human_map.items():
        text = re.sub(rf'\b{bot}\b', human, text, flags=re.IGNORECASE)
    
    # Intentional 'Burstiness': Break a few sentences to vary rhythm
    # Replaces some periods with a more conversational flow
    return text.strip()

# --- DOCUMENT GENERATION ENGINE ---
def render_template(template_input, data_map):
    doc = DocxTemplate(template_input)
    doc.render(data_map)
    output_stream = io.BytesIO()
    doc.save(output_stream)
    output_stream.seek(0)
    return output_stream

def clean_ai_text(text):
    text = re.sub(r'(?i)^(\d+\.\s*)?(\[)?(PART|SUMMARY|SKILLS|SECTION|ITEM|OVERVIEW|LETTER|BODY)(\])?[:\- \t]*', '', text.strip())
    text = re.sub(r'[\*\^#]', '', text)
    return text.strip()

# --- UI CONFIGURATION ---
st.set_page_config(page_title="Humanised Career Architect", layout="wide")

if 'cv_blob' not in st.session_state: st.session_state.cv_blob = None
if 'cl_blob' not in st.session_state: st.session_state.cl_blob = None

cv_template_source = None
cl_template_source = None

TEMPLATE_DIR = "templates"
if not os.path.exists(TEMPLATE_DIR): os.makedirs(TEMPLATE_DIR)
available_templates = [f for f in os.listdir(TEMPLATE_DIR) if f.endswith('.docx')]

with st.sidebar:
    st.header("1. Settings")
    api_key = st.secrets.get("GEMINI_API_KEY") or st.text_input("Gemini API Key", type="password")
    
    cv_mode = st.radio("CV Template Source", ["Folder", "Manual Upload"])
    if cv_mode == "Folder" and available_templates:
        cv_template_source = os.path.join(TEMPLATE_DIR, st.selectbox("Select CV Template", available_templates))
    else:
        cv_template_source = st.file_uploader("Upload CV Template (.docx)", type="docx", key="cv_manual")

    cl_mode = st.radio("Cover Letter Source", ["Folder", "Manual Upload"])
    if cl_mode == "Folder" and available_templates:
        cl_template_source = os.path.join(TEMPLATE_DIR, st.selectbox("Select CL Template", available_templates))
    else:
        cl_template_source = st.file_uploader("Upload CL Template (.docx)", type="docx", key="cl_manual")
    
    if st.button("🗑️ Reset Application"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

st.title("💼 Undetectable AI CV Tailor")

with st.expander("Candidate Details", expanded=True):
    c1, c2, c3 = st.columns(3)
    with c1:
        name = st.text_input("Full Name", "Rimantas Buivydas")
        email = st.text_input("Email", "rimvntas59@gmail.com")
    with c2:
        phone = st.text_input("Phone", "+44 7783 949991")
        company = st.text_input("Target Company", "London Law Firm")
    with c3:
        role = st.text_input("Target Role", "IT Service Desk Analyst")
        linkedin = st.text_input("LinkedIn", "linkedin.com/in/rimantas-buivydas/")

st.markdown("---")
col_a, col_b = st.columns(2)
with col_a:
    uploaded_cv = st.file_uploader("Upload Main CV (PDF)", type="pdf")
with col_b:
    job_desc = st.text_area("2. Paste Job Description", height=200)

if st.button("🚀 Generate Humanised Documents"):
    if not all([api_key, cv_template_source, uploaded_cv, job_desc]):
        st.error("Missing inputs.")
    else:
        client = genai.Client(api_key=api_key)
        pdf_reader = PyPDF2.PdfReader(uploaded_cv)
        cv_raw_text = " ".join([p.extract_text() for p in pdf_reader.pages])

        with st.spinner("Paraphrasing for human-like flow..."):
            prompt = f"""
            Act as a Senior Resume Writer and ATS Expert. 
            Create content for {name} applying for the {role} role at {company}. 
            Use a 'Human-Written' style. 
            STRICT: Do NOT write like an AI. Do NOT use structured formatting.

            STRICT LANGUAGE RULE: 
            Use BRITISH ENGLISH throughout (e.g., 'honours', 'specialised', 'programme', 'organise', 'centre'). 
            Localise all terminology for the UK job market.

            STRICT DETECTION BYPASS INSTRUCTIONS:
            - AVOID perfect grammar. Use slightly conversational, professional British English.
            - BURSTINESS: Mix 5-word sentences with 25-word sentences. 
            - PERPLEXITY: Use specific, technical jargon from my CV. Do not summarize; show.
            - NO AI CLICHES: Never use 'tapestry', 'passion', 'highly motivated', or 'comprehensive'.
            - Start the summary with a specific accomplishment, not a general statement.
            
            DIRECTIONS FOR HUMAN-LIKE FLOW:
            1. Use 'Burstiness': Vary sentence lengths significantly.
            2. Use 'Perplexity': Use a rich, specific vocabulary but avoid AI cliches like 'tapestry', 'unleash', or 'delve'.
            3. Write in FIRST PERSON. Sound confident but not robotic.
            4. Use British English (honours, specialised, programme).

            FORMAT (4 parts separated by '==='):
            PART 1: A professional summary in FIRST PERSON ('I'). 3-4 sentences (natural flow)
            PART 2: A comma-separated list of ATS-optimized technical skills.
            PART 3: A full first-person cover letter (Persuasive, conversational but professional).
            PART 4: ATS Analysis.

            STRICT: Do not include labels like 'PART 1' or 'Summary:' in the content.

            CV: {cv_raw_text}
            JOB: {job_desc}
            """

            
            response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
            parts = response.text.split("===")
            
            # Applying Pass 2 (Manual Scrambler)
            summary = bypass_scrambler(clean_ai_text(parts[0]))
            skills = clean_ai_text(parts[1]) if len(parts) > 1 else ""
            cl_body = bypass_scrambler(clean_ai_text(parts[2])) if len(parts) > 2 else ""
            
            cv_data = {
                'name': name.upper(), 'phone': phone, 'email': email, 
                'linkedin': linkedin, 'github': "github.com/rbuivydas", 
                'summary': summary, 'skills': skills
            }
            st.session_state.cv_blob = render_template(cv_template_source, cv_data)
            
            if cl_template_source:
                cl_data = {
                    'name': name, 'company': company, 'role': role, 
                    'date': datetime.now().strftime("%d %B %Y"), 'letter_body': cl_body
                }
                st.session_state.cl_blob = render_template(cl_template_source, cl_data)

if st.session_state.cv_blob:
    st.success("Human-authentic documents generated!")
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("📥 Download CV", data=st.session_state.cv_blob, file_name=f"{name}_{company}_CV.docx")
    if st.session_state.cl_blob:
        with c2:
            st.download_button("📥 Download Cover Letter", data=st.session_state.cl_blob, file_name=f"{name}_{company}_Letter.docx")
