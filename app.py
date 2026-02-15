import streamlit as st
from docxtpl import DocxTemplate
import PyPDF2
from google import genai
import io
import os
import re

# --- CORE RENDERING ENGINE ---
def render_from_template(template_file, data_map):
    """Injects data into the 7 specific tags in the .docx template."""
    temp_path = "user_template.docx"
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

# --- UI LAYOUT ---
st.set_page_config(page_title="CV Tag Architect", layout="wide")

with st.sidebar:
    st.header("1. Setup")
    # Using Gemini API Key
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
        st.success("API Key active.")
    else:
        api_key = st.text_input("Gemini API Key", type="password")
    
    docx_template = st.file_uploader("2. Upload .docx Template", type="docx")
    st.caption("Template must use: {{ name }}, {{ email }}, {{ linkedin }}, {{ github }}, {{ summary }}, {{ skills }}, {{ phone }}")

st.title("💼 Precise CV Tailorer")

# Applicant Info for Tags
with st.expander("Candidate Details", expanded=True):
    c1, c2, c3 = st.columns(3)
    with c1:
        full_name = st.text_input("Name", "Rimantas Buivydas")
        email_addr = st.text_input("Email", "rimvntas59@gmail.com")
    with c2:
        phone_num = st.text_input("Phone", "+44 7783 949991")
        target_company = st.text_input("Target Company", "e.g., London Law Firm")
    with c3:
        li_url = st.text_input("LinkedIn", "linkedin.com/in/rimantas-buivydas/")
        gh_url = st.text_input("GitHub", "github.com/rbuivydas")

st.markdown("---")
col_a, col_b = st.columns(2)
with col_a:
    uploaded_cv = st.file_uploader("Upload Master CV (PDF)", type="pdf")
with col_b:
    job_desc = st.text_area("Paste Job Description", height=150)

if st.button("🚀 Populate Template Tags"):
    if not all([api_key, docx_template, uploaded_cv, job_desc]):
        st.error("Please ensure all fields are filled and a template is uploaded.")
    else:
        client = genai.Client(api_key=api_key)
        
        # Extract CV text for AI analysis
        pdf_reader = PyPDF2.PdfReader(uploaded_cv)
        master_text = " ".join([p.extract_text() for p in pdf_reader.pages])

        with st.spinner("Analyzing and drafting natural content..."):
            # Prompt specifically designed to fill summary and skills naturally
            prompt = f"""
            Act as a Professional Resume Writer. Tailor a profile for {target_company}.
            
            OUTPUT REQUIREMENTS:
            - Split response using '==='.
            - Part 1 (Summary Content): 3-4 natural, flowing sentences. No title or numbering.
            - Part 2 (Skills Content): A clean comma-separated list of technical skills. No title.
            - DO NOT use markdown (**, ##).
            
            CV: {master_text}
            JOB: {job_desc}
            """
            
            response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
            sections = response.text.split("===")
            
            def clean(text):
                return re.sub(r'[\*\^#]', '', text).strip()

            # Mapping specifically to your 7 requested tags
            data_map = {
                'name': full_name.upper(),
                'email': email_addr,
                'phone': phone_num,
                'linkedin': li_url,
                'github': gh_url,
                'summary': clean(sections[1]) if len(sections) > 1 else "",
                'skills': clean(sections[2]) if len(sections) > 2 else ""
            }

            try:
                final_docx = render_from_template(docx_template, data_map)
                
                # Naming the file professionally
                safe_name = full_name.replace(" ", "_")
                safe_company = target_company.replace(" ", "_")
                
                st.success("CV Tags Populated!")
                st.download_button(
                    label="📥 Download Tailored CV (.docx)",
                    data=final_docx,
                    file_name=f"{safe_name}_{safe_company}_Tailored.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
            except Exception as e:
                st.error(f"Rendering Error: {e}")
