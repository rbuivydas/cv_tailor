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
    """Removes headers like '1. SUMMARY', '[SKILLS]', and markdown artifacts."""
    text = re.sub(r'(?i)^(\d+\.\s*)?(\[)?(SUMMARY|SKILLS|SECTION|ITEM|OVERVIEW|COVER LETTER|LETTER|BODY)(\])?[:\- \t]*', '', text.strip())
    text = re.sub(r'[\*\^#]', '', text)
    return text.strip()

# --- STREAMLIT UI ---
st.set_page_config(page_title="Career Suite Architect", layout="wide")

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
    job_desc = st.text_area("Paste Job Description", height=200)

if st.button("🚀 Generate Professional Suite"):
    if not all([api_key, cv_template_file, uploaded_cv, job_desc]):
        st.error("Please provide API Key, CV Template, Master CV, and Job Description.")
    else:
        client = genai.Client(api_key=api_key)
        pdf_reader = PyPDF2.PdfReader(uploaded_cv)
        cv_raw_text = " ".join([p.extract_text() for p in pdf_reader.pages])

        with st.spinner("Crafting tailored documents..."):
            prompt = f"""
            Act as a Senior Career Consultant. Create content for {name} applying to {company_name} for the {target_role} role.
            Split into 3 parts using '===':
            1. Professional Summary (3-4 sentences).
            2. Technical Skills (comma-separated list).
            3. A full, persuasive Cover Letter.
            
            NO titles like '1. Summary' or 'Cover Letter:'. Just the prose.
            CV Data: {cv_raw_text}
            Job Desc: {job_desc}
            """
            
            response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
            parts = response.text.split("===")
            
            # Sanitizing AI output
            summary_val = clean_ai_text(parts[0]) if len(parts) > 0 else ""
            skills_val = clean_ai_text(parts[1]) if len(parts) > 1 else ""
            cl_body_val = clean_ai_text(parts[2]) if len(parts) > 2 else ""

            # PREVIEW
            st.markdown("### 🔍 Content Preview")
            p1, p2 = st.columns(2)
            with p1:
                st.info("**Tailored Summary**")
                st.write(summary_val)
            with p2:
                st.info("**Skills List**")
                st.write(skills_val)
            st.info("**Cover Letter Preview**")
            st.write(cl_body_val)

            # Data Mapping
            safe_name = name.replace(' ', '_')
            safe_company = re.sub(r'[^\w\s-]', '', company_name).strip().replace(' ', '_')
            today_date = datetime.now().strftime("%B %d, %Y")

            try:
                # 1. Generate CV
                cv_data = {
                    'name': name.upper(), 'phone': phone, 'email': email,
                    'linkedin': linkedin, 'github': "github.com/rbuivydas",
                    'summary': summary_val, 'skills': skills_val
                }
                final_cv = render_template(cv_template_file, cv_data)
                
                st.download_button(
                    label=f"📥 Download {safe_name}_{safe_company}_CV.docx",
                    data=final_cv,
                    file_name=f"{safe_name}_{safe_company}_CV.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )

                # 2. Generate Cover Letter
                if cl_template_file:
                    cl_data = {
                        'name': name, 'company': company_name, 'role': target_role,
                        'date': today_date, 'letter_body': cl_body_val
                    }
                    final_cl = render_template(cl_template_file, cl_data)
                    
                    st.download_button(
                        label=f"📥 Download {safe_name}_{safe_company}_CoverLetter.docx",
                        data=final_cl,
                        file_name=f"{safe_name}_{safe_company}_CoverLetter.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
                
            except Exception as e:
                st.error(f"Generation Error: {e}")
