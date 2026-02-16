import streamlit as st
from docxtpl import DocxTemplate
import PyPDF2
from google import genai
import io
import re
import os
from datetime import datetime

# --- HUMANISATION & DETECTION LOGIC ---
def calculate_human_score(text):
    """
    Heuristic-based check to estimate human-written quality.
    Checks for sentence length variance and typical 'AI-isms'.
    """
    if not text: return 0
    sentences = re.split(r'[.!?]+', text)
    lengths = [len(s.split()) for s in sentences if len(s.split()) > 0]
    
    if not lengths: return 0
    
    # Calculate variance (Humans have high variance/burstiness)
    mean = sum(lengths) / len(lengths)
    variance = sum((x - mean) ** 2 for x in lengths) / len(lengths)
    
    # Penalize common AI transition words
    ai_cliches = ['furthermore', 'moreover', 'tapestry', 'delve', 'comprehensive', 'testament']
    cliche_count = sum(1 for word in ai_cliches if word in text.lower())
    
    # Heuristic Score: Base 80 + variance bonus - penalty for cliches
    score = 75 + (min(variance, 20)) - (cliche_count * 5)
    return min(max(score, 15), 98) # Cap between 15% and 98%

# --- DOCUMENT GENERATION ENGINE ---
def render_template(template_input, data_map):
    doc = None
    if isinstance(template_input, str):
        doc = DocxTemplate(template_input)
    else:
        temp_path = "temp_render.docx"
        with open(temp_path, "wb") as f:
            f.write(template_input.getbuffer())
        doc = DocxTemplate(temp_path)
    
    doc.render(data_map)
    output_stream = io.BytesIO()
    doc.save(output_stream)
    output_stream.seek(0)
    
    if not isinstance(template_input, str) and os.path.exists("temp_render.docx"):
        os.remove("temp_render.docx")
    return output_stream

def clean_ai_text(text):
    if not text: return ""
    text = re.sub(r'(?i)^(\d+\.\s*)?(\[)?(SUMMARY|SKILLS|SECTION|ITEM|OVERVIEW|COVER LETTER|LETTER|BODY)(\])?[:\- \t]*', '', text.strip())
    text = re.sub(r'[\*\^#]', '', text)
    return text.strip()

# --- UI CONFIGURATION ---
st.set_page_config(page_title="Career Suite Architect", layout="wide")

if 'cv_blob' not in st.session_state: st.session_state.cv_blob = None
if 'cl_blob' not in st.session_state: st.session_state.cl_blob = None
if 'file_base' not in st.session_state: st.session_state.file_base = ""
if 'match_details' not in st.session_state: st.session_state.match_details = None
if 'human_score' not in st.session_state: st.session_state.human_score = 0

# --- TEMPLATE FOLDER LOGIC ---
TEMPLATE_DIR = "templates"
if not os.path.exists(TEMPLATE_DIR): os.makedirs(TEMPLATE_DIR)
available_templates = [f for f in os.listdir(TEMPLATE_DIR) if f.endswith('.docx')]

with st.sidebar:
    st.header("1. API & Templates")
    api_key = st.secrets["GEMINI_API_KEY"] if "GEMINI_API_KEY" in st.secrets else st.text_input("Gemini API Key", type="password")

    st.subheader("Template Selection")
    cv_mode = st.radio("CV Template Source", ["Folder", "Manual Upload"])
    cv_template_source = os.path.join(TEMPLATE_DIR, st.selectbox("Select CV Template", available_templates)) if cv_mode == "Folder" and available_templates else st.file_uploader("Upload CV Template", type="docx", key="cv_manual")

    cl_mode = st.radio("Cover Letter Source", ["Folder", "Manual Upload"])
    cl_template_source = os.path.join(TEMPLATE_DIR, st.selectbox("Select CL Template", available_templates)) if cl_mode == "Folder" and available_templates else st.file_uploader("Upload CL Template", type="docx", key="cl_manual")
    
    if st.button("🗑️ Reset Application"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

st.title("💼 Humanised CV Tailoring Program")

with st.expander("Application Identity", expanded=True):
    c1, c2, c3 = st.columns(3)
    with c1:
        name = st.text_input("Full Name", "Rimantas Buivydas")
        email = st.text_input("Email", "rimvntas59@gmail.com")
    with c2:
        phone = st.text_input("Phone", "+44 7783 949991")
        company_name = st.text_input("Target Company", "London Law Firm")
    with c3:
        target_role = st.text_input("Target Role", "IT Service Desk Analyst")
        linkedin = st.text_input("LinkedIn URL", "linkedin.com/in/rimantas-buivydas/")

st.markdown("---")
col_a, col_b = st.columns(2)
with col_a:
    uploaded_cv = st.file_uploader("Upload Main CV (PDF)", type="pdf")
with col_b:
    job_desc = st.text_area("2. Paste Job Description", height=200)

if st.button("🚀 Generate Humanised CV"):
    if not all([api_key, cv_template_source, uploaded_cv, job_desc]):
        st.error("Missing required inputs.")
    else:
        client = genai.Client(api_key=api_key)
        pdf_reader = PyPDF2.PdfReader(uploaded_cv)
        cv_raw_text = " ".join([p.extract_text() for p in pdf_reader.pages])

        with st.spinner("Paraphrasing for human-like flow..."):
            prompt = f"""
            Act as a Senior Resume Writer and ATS Expert. 
            Create content for {name} applying for the {target_role} role at {company_name}. 
            Use a 'Human-Written' style.

            STRICT LANGUAGE RULE: 
            Use BRITISH ENGLISH throughout (e.g., 'honours', 'specialised', 'programme', 'organise', 'centre'). 
            Localise all terminology for the UK job market.

	        STRICT Linguistic Requirements to Bypass AI Detection:
            - HIGH BURSTINESS: Mix short, punchy sentences with longer, descriptive ones. 
            - HIGH PERPLEXITY: Use industry-specific jargon naturally. 
            - PERSONAL VOICE: Use 'I' and 'My'. Avoid generic AI opening phrases like 'With a solid grounding...'.
            - NO CLICHES: Do not use 'tapestry', 'passion', 'highly motivated', or 'proven track record'.
            
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
            parts = [p.strip() for p in response.text.split("===")]
            
            summary = clean_ai_text(parts[0]) if len(parts) > 0 else ""
            skills = clean_ai_text(parts[1]) if len(parts) > 1 else ""
            cl_body = clean_ai_text(parts[2]) if len(parts) > 2 else ""
            st.session_state.match_details = parts[3] if len(parts) > 3 else ""

            # Calculate Human Score for the letter and summary
            full_text = summary + " " + cl_body
            st.session_state.human_score = calculate_human_score(full_text)

            st.session_state.file_base = f"{name.replace(' ', '_')}_{company_name.replace(' ', '_')}"
            
            cv_data = {'name': name.upper(), 'phone': phone, 'email': email, 'linkedin': linkedin, 'github': "github.com/rbuivydas", 'summary': summary, 'skills': skills}
            st.session_state.cv_blob = render_template(cv_template_source, cv_data)

            if cl_template_source:
                cl_data = {'name': name, 'company': company_name, 'role': target_role, 'date': datetime.now().strftime("%d %B %Y"), 'letter_body': cl_body}
                st.session_state.cl_blob = render_template(cl_template_source, cl_data)

# --- PERSISTENT DISPLAY ---
if st.session_state.cv_blob:
    st.success(f"Tailored documents for {company_name} are ready!")
    
    # AI DETECTION PREVIEW
    score = st.session_state.human_score
    color = "green" if score > 70 else "orange" if score > 40 else "red"
    
    st.subheader("🛡️ Content Authenticity Check")
    st.markdown(f"""
    <div style="border: 1px solid #ddd; padding: 15px; border-radius: 10px;">
        <p style="margin-bottom: 5px;">Estimated <b>Human-Written</b> Score:</p>
        <h2 style="color: {color}; margin-top: 0;">{score}%</h2>
        <div style="background-color: #eee; width: 100%; height: 10px; border-radius: 5px;">
            <div style="background-color: {color}; width: {score}%; height: 10px; border-radius: 5px;"></div>
        </div>
        <p style="font-size: 0.8em; color: #666; margin-top: 10px;">
            *Analysis based on sentence variance (burstiness) and absence of common AI linguistic patterns.
        </p>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("📊 ATS Keyword Match Analysis"):
        st.write(st.session_state.match_details)

    res_col, cl_col = st.columns(2)
    with res_col:
        st.download_button("📥 Download Tailored CV", data=st.session_state.cv_blob, file_name=f"{st.session_state.file_base}_CV.docx")
    if st.session_state.cl_blob:
        with cl_col:
            st.download_button("📥 Download Cover Letter", data=st.session_state.cl_blob, file_name=f"{st.session_state.file_base}_CoverLetter.docx")
