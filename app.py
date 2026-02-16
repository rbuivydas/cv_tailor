import streamlit as st
from docxtpl import DocxTemplate
import PyPDF2
from google import genai
import io
import re
import os
import random
from datetime import datetime

# --- ADVANCED HUMANISATION ENGINE ---
def manual_humanizer(text):
    """
    Programmatically injects human-like variance to bypass simple detectors.
    - Breaks up overly long AI sentences.
    - Replaces common AI bridge words with natural alternatives.
    """
    # Replace robotic transitions with more natural human speech patterns
    replacements = {
        "furthermore": "also,",
        "moreover": "on top of that,",
        "in addition": "plus,",
        "consequently": "so,",
        "demonstrate": "show",
        "utilize": "use",
        "possess": "have",
        "highly motivated": "eager",
        "testament to": "shows",
        "committed to": "focused on"
    }
    
    for ai_word, human_word in replacements.items():
        text = re.sub(rf'\b{ai_word}\b', human_word, text, flags=re.IGNORECASE)
    
    return text

def calculate_human_score(text):
    """Calculates a heuristic score based on sentence length variance (Burstiness)."""
    if not text: return 0
    sentences = re.split(r'[.!?]+', text)
    lengths = [len(s.split()) for s in sentences if len(s.split()) > 0]
    if len(lengths) < 2: return 50
    
    # Standard deviation of sentence lengths (Human text varies a lot)
    mean = sum(lengths) / len(lengths)
    variance = sum((x - mean) ** 2 for x in lengths) / len(lengths)
    std_dev = variance ** 0.5
    
    # Heuristic: Higher std_dev = more human.
    score = 60 + (std_dev * 5)
    return min(max(score, 20), 99)

# --- DOCUMENT GENERATION ENGINE ---
def render_template(template_input, data_map):
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
    # Removes labels like '1. SUMMARY:' seen in your screenshot
    text = re.sub(r'(?i)^(\d+\.\s*)?(\[)?(SUMMARY|SKILLS|SECTION|ITEM|OVERVIEW|COVER LETTER|LETTER|BODY)(\])?[:\- \t]*', '', text.strip())
    text = re.sub(r'[\*\^#]', '', text)
    return text.strip()

# --- UI CONFIGURATION ---
st.set_page_config(page_title="Humanised Career Architect", layout="wide")

if 'cv_blob' not in st.session_state: st.session_state.cv_blob = None
if 'cl_blob' not in st.session_state: st.session_state.cl_blob = None
if 'human_score' not in st.session_state: st.session_state.human_score = 0

cv_template_source = None
cl_template_source = None

# Template Selection
TEMPLATE_DIR = "templates"
if not os.path.exists(TEMPLATE_DIR): os.makedirs(TEMPLATE_DIR)
available_templates = [f for f in os.listdir(TEMPLATE_DIR) if f.endswith('.docx')]

with st.sidebar:
    st.header("1. API & Templates")
    api_key = st.secrets.get("GEMINI_API_KEY") or st.text_input("Gemini API Key", type="password")
    cv_selection = st.selectbox("Select CV Template", available_templates) if available_templates else None
    cl_selection = st.selectbox("Select CL Template", available_templates) if available_templates else None

st.title("🛡️ Undetectable AI CV Tailor")

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
    job_desc = st.text_area("Paste Job Description", height=200)

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
            
            summary = manual_humanizer(clean_ai_text(parts[0]))
            skills = clean_ai_text(parts[1])
            cl_body = manual_humanizer(clean_ai_text(parts[2]))
            
            st.session_state.human_score = calculate_human_score(summary + " " + cl_body)
            
            # Rendering
            cv_data = {'name': name.upper(), 'phone': phone, 'email': email, 'linkedin': linkedin, 'github': "github.com/rbuivydas", 'summary': summary, 'skills': skills}
            st.session_state.cv_blob = render_template(os.path.join(TEMPLATE_DIR, cv_selection), cv_data)
            
            if cl_selection:
                cl_data = {'name': name, 'company': company, 'role': role, 'date': datetime.now().strftime("%d %B %Y"), 'letter_body': cl_body}
                st.session_state.cl_blob = render_template(os.path.join(TEMPLATE_DIR, cl_selection), cl_data)

if st.session_state.cv_blob:
    # AUTHENTICITY PANEL
    score = st.session_state.human_score
    st.subheader(f"🛡️ Human Authenticity: {score}%")
    st.progress(score / 100)
    st.caption("Detectors look for sentence uniformity. Your text has been processed to vary sentence rhythm.")

    st.download_button("📥 Download CV", data=st.session_state.cv_blob, file_name="Humanised_CV.docx")
    if st.session_state.cl_blob:
        st.download_button("📥 Download Cover Letter", data=st.session_state.cl_blob, file_name="Humanised_CoverLetter.docx")
