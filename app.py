import streamlit as st
from docxtpl import DocxTemplate
import PyPDF2
from google import genai
import io
import os
import re

# --- TEMPLATE FILLING ENGINE ---
def render_from_template(template_file, data_map):
    """Fills the .docx template with AI-generated data and returns a byte stream."""
    # Temporarily save the uploaded template to disk
    with open("input_template.docx", "wb") as f:
        f.write(template_file.getbuffer())
    
    doc = DocxTemplate("input_template.docx")
    doc.render(data_map)
    
    output_stream = io.BytesIO()
    doc.save(output_stream)
    output_stream.seek(0)
    
    # Cleanup temporary file
    if os.path.exists("input_template.docx"):
        os.remove("input_template.docx")
        
    return output_stream

# --- UI CONFIGURATION ---
st.set_page_config(page_title="Pro CV Architect", layout="wide")

with st.sidebar:
    st.header("Admin Settings")
    api_key = st.secrets.get("GEMINI_API_KEY") if "GEMINI_API_KEY" in st.secrets else st.text_input("Gemini API Key", type="password")
    docx_template = st.file_uploader("📂 Upload CV Template (.docx)", type="docx")
    cl_template = st.file_uploader("📂 Upload Cover Letter Template (.docx)", type="docx")
    
    if "keywords" in st.session_state:
        st.markdown("---")
        st.subheader("🔍 AI Keyword Review")
        st.caption("Key terms prioritized for this application:")
        for kw in st.session_state.keywords:
            st.write(f"✔️ {kw}")

st.title("💼 Professional CV & Cover Letter Tailor")

# Application Identity
with st.container():
    st.subheader("Applicant & Company Details")
    c1, c2, c3 = st.columns(3)
    with c1:
        full_name = st.text_input("Applicant Name", "Rimantas Buivydas")
    with c2:
        target_company = st.text_input("Target Company", "e.g., London Law Firm")
    with c3:
        target_role = st.text_input("Target Role", "e.g., IT Service Desk Analyst")

st.markdown("---")

col_a, col_b = st.columns(2)
with col_a:
    uploaded_cv = st.file_uploader("1. Master CV (PDF)", type="pdf")
with col_b:
    job_desc = st.text_area("2. Job Description", height=200)

if st.button("🚀 Generate Professional Suite (.docx)"):
    if not all([api_key, docx_template, uploaded_cv, job_desc]):
        st.error("Please provide the API Key, CV Template, Master CV, and Job Description.")
    else:
        client = genai.Client(api_key=api_key)
        pdf_reader = PyPDF2.PdfReader(uploaded_cv)
        master_text = " ".join([p.extract_text() for p in pdf_reader.pages])

        with st.spinner("Analyzing Law Firm requirements..."):
            # Refined prompt for clean injection into docxtpl tags
            prompt = f"""
            Act as a Senior Resume Writer. Tailor a CV and Cover Letter for {full_name} applying to {target_company} for the {target_role} role.
            
            STRUCTURE RULES:
            - Split sections using '==='.
            - Part 1 (Summary): Natural, professional sentences. NO header/title.
            - Part 2 (Experience): Bulleted list.
            - Part 3 (Skills): Comma-separated list only. NO header/title.
            - Part 4 (Cover Letter): A full, professional cover letter.
            - Part 5 (Keywords): List the top 5 technical keywords you optimized for.
            
            CV: {master_text}
            JOB: {job_desc}
            """
            
            response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
            sections = response.text.split("===")
            
            def clean(text):
                return re.sub(r'[\*\^#]', '', text).strip()

            # Prepare dynamic filename base
            file_base = f"{full_name.replace(' ', '_')}_{target_company.replace(' ', '_')}"
            
            # Store keywords for the sidebar
            if len(sections) > 5:
                st.session_state.keywords = [kw.strip() for kw in sections[5].split('\n') if kw.strip()]

            # --- CV DATA MAPPING ---
            cv_data = {
                'name': full_name.upper(),
                'summary': clean(sections[1]) if len(sections) > 1 else "",
                'experience': clean(sections[2]) if len(sections) > 2 else "",
                'skills': clean(sections[3]) if len(sections) > 3 else ""
            }
            
            # --- COVER LETTER DATA MAPPING ---
            cl_content = clean(sections[4]) if len(sections) > 4 else "Cover Letter failed."
            cl_data = {
                'name': full_name,
                'company': target_company,
                'role': target_role,
                'letter_body': cl_content
            }

            try:
                # Process CV
                cv_docx = render_from_template(docx_template, cv_data)
                
                st.success(f"Tailored documents for {target_company} are ready!")
                
                res_col, cl_col = st.columns(2)
                with res_col:
                    st.download_button(
                        label="📄 Download Tailored CV (.docx)",
                        data=cv_docx,
                        file_name=f"{file_base}_CV.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
                
                # Process Cover Letter (if template provided)
                if cl_template:
                    cl_docx = render_from_template(cl_template, cl_data)
                    with cl_col:
                        st.download_button(
                            label="✉️ Download Cover Letter (.docx)",
                            data=cl_docx,
                            file_name=f"{file_base}_CoverLetter.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )
                else:
                    st.info("Upload a Cover Letter template in the sidebar to generate the document.")

            except Exception as e:
                st.error(f"Processing Error: {e}")
