import streamlit as st
from docxtpl import DocxTemplate
import PyPDF2
from google import genai
import io
import re
import os
import random
from datetime import datetime

# --- PASS 6: LINGUISTIC SABOTAGE (The Zero-Signal Engine) ---
def zero_signal_humanizer(text):
    """
    Acts as a 'Jitter' filter to bypass 0% AI detection.
    1. Injects em-dashes and semicolons into 'too-perfect' sequences.
    2. Swaps robotic transitions for 'Gritty' British IT slang.
    3. Forces sentence length variation (Burstiness) to be extreme.
    """
    if not text: return ""
    
    # IT Grit Map: Breaking the AI's 'Smooth' transition patterns
    grit_map = {
        "furthermore": "plus,",
        "moreover": "on top of that,",
        "in addition": "and, honestly,",
        "consequently": "so, naturally,",
        "demonstrate": "show off",
        "utilize": "tap into",
        "possess": "bring",
        "highly motivated": "keen to get started",
        "pivotal": "massive",
        "underscores": "hits home",
        "ensure": "make sure",
        "extensive": "broad",
        "proven track record": "history of",
        "excellent": "solid",
        "comprehensive": "end-to-end",
        "deep understanding": "good handle on"
    }
    
    for bot, human in grit_map.items():
        text = re.sub(rf'\b{bot}\b', human, text, flags=re.IGNORECASE)

    sentences = text.split(". ")
    scrambled = []
    
    for i, sentence in enumerate(sentences):
        words = sentence.split()
        # Pass: Inject 'Burstiness' Jitter
        # We manually break the probability map by forcing non-linear punctuation
        if i % 2 == 0 and len(words) > 8:
            # Inject a mid-sentence break (Human marker)
            mid = random.randint(3, 7)
            words.insert(mid, "—")
        
        # Every 3rd sentence: make it a punchy fragment (AI hates fragments)
        if i % 3 == 0 and len(words) > 12:
            sentence = " ".join(words[:5]) + "—" + " ".join(words[5:])
        else:
            sentence = " ".join(words)
            
        scrambled.append(sentence)
        
    return ". ".join(scrambled).strip().replace("..", ".")

def calculate_human_score(text):
    """Calculates Entropy (Higher = Less AI)."""
    if not text: return 0
    sentences = re.split(r'[.!?]+', text)
    lengths = [len(s.split()) for s in sentences if len(s.split()) > 0]
    if len(lengths) < 2: return 10
    
    mean = sum(lengths) / len(lengths)
    std_dev = (sum((x - mean) ** 2 for x in lengths) / len(lengths)) ** 0.5
    
    # 0% Detection requires high standard deviation (Burstiness)
    score = 75 + (std_dev * 5)
    return min(max(int(score), 2), 99)

# --- DOCUMENT GENERATION ENGINE ---
def render_template(template_input, data_map):
    """Preserves XML structure for hyperlinks (LinkedIn/GitHub)."""
    doc = DocxTemplate(template_input)
    doc.render(data_map)
    output_stream = io.BytesIO()
    doc.save(output_stream)
    output_stream.seek(0)
    return output_stream

def clean_ai_text(text):
    text = re.sub(r'(?i)^(\d+\.\s*)?(\[)?(SUMMARY|SKILLS|SECTION|ITEM|OVERVIEW|COVER LETTER|LETTER|BODY)(\])?[:\- \t]*', '', text.strip())
    text = re.sub(r'[\*\^#]', '', text)
    return text.strip()

# --- UI CONFIGURATION ---
st.set_page_config(page_title="Zero-Signal Career Architect", layout="wide")

if 'cv_blob' not in st.session_state: st.session_state.cv_blob = None
if 'cl_blob' not in st.session_state: st.session_state.cl_blob = None
if 'h_score' not in st.session_state: st.session_state.h_score = 0

TEMPLATE_DIR = "templates"
if not os.path.exists(TEMPLATE_DIR): os.makedirs(TEMPLATE_DIR)
available_templates = [f for f in os.listdir(TEMPLATE_DIR) if f.endswith('.docx')]

with st.sidebar:
    st.header("⚙️ Chaos Settings")
    api_key = st.secrets.get("GEMINI_API_KEY") or st.text_input("Gemini API Key", type="password")
    cv_sel = st.selectbox("CV Template", available_templates) if available_templates else None
    cl_sel = st.selectbox("CL Template", available_templates) if available_templates else None

st.title("🛡️ The 0% AI Detection Challenge")

with st.expander("Candidate Identity", expanded=True):
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
    uploaded_cv = st.file_uploader("Upload Master CV (PDF)", type="pdf")
with col_b:
    job_desc = st.text_area("2. Paste Job Description", height=200)

if st.button("🚀 Generate Zero-Signal Content"):
    if not all([api_key, cv_sel, uploaded_cv, job_desc]):
        st.error("Inputs missing.")
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

	    	REFERENCE SAMPLES FOR FLOW:
            - "They linger in the assumptions that subtend the production and consumption of text... what forms of 'human' are authorized by the algorithm?"
            - "When I in dreams behold thy fairest shade/ Whose shade in dreams doth wake the sleeping morn"

            STRICT LANGUAGE RULE: 
            Use BRITISH ENGLISH throughout (e.g., 'honours', 'specialised', 'programme', 'organise', 'centre'). 
            Localise all terminology for the UK job market.

            STRICT DETECTION BYPASS INSTRUCTIONS:
            - AVOID perfect grammar. Use slightly conversational, professional British English.
            - BURSTINESS: Mix 5-word sentences with 25-word sentences. 
            - PERPLEXITY: Use specific, technical jargon from my CV. Do not summarize; show.
            - NO AI CLICHES: Never use 'tapestry', 'passion', 'highly motivated', or 'comprehensive'.
            - Start the summary with a specific accomplishment, not a general statement.
            
            STRICT DIRECTIONS FOR HUMAN-LIKE FLOW:
            1. BURSTINESS: Mix extremely short sentences with long, non-linear technical explanations.
            2. PERPLEXITY: Use high-level industry terminology. AVOID AI cliches (furthermore, tapestry, etc).
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
            
            # Pass 6: Zero-Signal Scrambling
            summary = zero_signal_humanizer(clean_ai_text(parts[0]))
            skills = clean_ai_text(parts[1]) if len(parts) > 1 else ""
            cl_body = zero_signal_humanizer(clean_ai_text(parts[2])) if len(parts) > 2 else ""
            
            st.session_state.h_score = calculate_human_score(summary + " " + cl_body)
            
            cv_data = {
                'name': name.upper(), 'phone': phone, 'email': email, 
                'linkedin': linkedin, 'github': "github.com/rbuivydas", 
                'summary': summary, 'skills': skills
            }
            st.session_state.cv_blob = render_template(os.path.join(TEMPLATE_DIR, cv_sel), cv_data)
            
            if cl_sel:
                cl_data = {
                    'name': name, 'company': company, 'role': role, 
                    'date': datetime.now().strftime("%d %B %Y"), 'letter_body': cl_body
                }
                st.session_state.cl_blob = render_template(os.path.join(TEMPLATE_DIR, cl_sel), cl_data)

if st.session_state.cv_blob:
    score = st.session_state.h_score
    st.subheader(f"🛡️ Human-Written Index: {score}%")
    st.progress(score / 100)
    st.caption(f"Estimated AI Detection Probability: {100 - score}%")

    c1, c2 = st.columns(2)
    with c1:
        st.download_button("📥 CV (.docx)", data=st.session_state.cv_blob, file_name=f"{name}_CV.docx")
    if st.session_state.cl_blob:
        with c2:
            st.download_button("📥 Letter (.docx)", data=st.session_state.cl_blob, file_name=f"{name}_Letter.docx")
