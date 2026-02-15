import streamlit as st
from docxtpl import DocxTemplate
import PyPDF2
from google import genai
import io
import pypandoc
import os
import re

# --- CONVERSION ENGINES ---
def convert_docx_to_pdf(docx_stream):
    """Converts Word byte stream to PDF byte stream using Pandoc."""
    with open("temp_output.docx", "wb") as f:
        f.write(docx_stream.getvalue())
    pypandoc.convert_file("temp_output.docx", "pdf", outputfile="temp_output.pdf", 
                         extra_args=['--pdf-engine=weasyprint'])
    with open("temp_output.pdf", "rb") as f:
        pdf_bytes = f.read()
    os.remove("temp_output.docx")
    os.remove("temp_output.pdf")
    return pdf_bytes

def render_from_template(template_file, data_map):
    """Fills the .docx template with AI-generated data."""
    with open("input_template.docx", "wb") as f:
        f.write(template_file.getbuffer())
    doc = DocxTemplate("input_template.docx")
    doc.render(data_map)
    output_stream = io.BytesIO()
    doc.save(output_stream)
    os.remove("input_template.docx")
    return output_stream

# --- UI CONFIGURATION ---
st.set_page_config(page_title="Pro Career Suite", layout="wide")

with st.sidebar:
    st.header("Admin Settings")
    api_key = st.text_input("Gemini API Key", type="password")
    docx_template = st.file_uploader("📂 Upload CV Template (.docx)", type="docx")
    cl_template = st.file_uploader("📂 Upload Cover Letter Template (.docx)", type="docx")

st.title("💼 AI Professional Career Suite")

# Unified Applicant & Company Info
with st.container():
    st.subheader("Application Identity")
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

if st.button("🚀 Generate Professional Suite"):
    if not all([api_key, docx_template, uploaded_cv, job_desc]):
        st.error("Please provide the API Key, CV Template, Master CV, and Job Description.")
    else:
        client = genai.Client(api_key=api_key)
        pdf_reader = PyPDF2.PdfReader(uploaded_cv)
        master_text = " ".join([p.extract_text() for p in pdf_reader.pages])

        with st.spinner("Refining document content and removing titles..."):
            # Refined prompt for cleaner section injection
            prompt = f"""
            Act as a Senior Resume Writer. Tailor a CV and Cover Letter for {full_name} applying to {target_company}.
            
            STRUCTURE RULES:
            - Split sections using '==='.
            - Part 1 (Summary): Natural, professional sentences. NO header/title.
            - Part 2 (Experience): Bulleted list.
            - Part 3 (Skills): Comma-separated list only. NO header/title.
            - Part 4 (Cover Letter): A full, professional cover letter tailored to the job.
            
            CV: {master_text}
            JOB: {job_desc}
            """
            
            response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
            sections = response.text.split("===")
            
            def clean(text):
                return re.sub(r'[\*\^#]', '', text).strip()

            # Dynamic Filename Preparation
            file_base = f"{full_name.replace(' ', '_')}_{target_company.replace(' ', '_')}"
            
            # --- CV GENERATION ---
            cv_data = {
                'name': full_name.upper(),
                'summary': clean(sections[1]) if len(sections) > 1 else "",
                'experience': clean(sections[2]) if len(sections) > 2 else "",
                'skills': clean(sections[3]) if len(sections) > 3 else ""
            }
            
            # --- COVER LETTER GENERATION ---
            cl_content = clean(sections[4]) if len(sections) > 4 else "Cover Letter failed to generate."
            cl_data = {
                'name': full_name,
                'company': target_company,
                'role': target_role,
                'letter_body': cl_content
            }

            try:
                # Process CV
                cv_docx = render_from_template(docx_template, cv_data)
                cv_pdf = convert_docx_to_pdf(cv_docx)
                
                # Process Cover Letter (if template provided)
                cl_pdf = None
                if cl_template:
                    cl_docx = render_from_template(cl_template, cl_data)
                    cl_pdf = convert_docx_to_pdf(cl_docx)

                st.success(f"Professional documents for {target_company} are ready!")
                
                res_col, cl_col = st.columns(2)
                with res_col:
                    st.download_button(
                        label="📄 Download Tailored CV (PDF)",
                        data=cv_pdf,
                        file_name=f"{file_base}_CV.pdf",
                        mime="application/pdf"
                    )
                
                if cl_pdf:
                    with cl_col:
                        st.download_button(
                            label="✉️ Download Cover Letter (PDF)",
                            data=cl_pdf,
                            file_name=f"{file_base}_CoverLetter.pdf",
                            mime="application/pdf"
                        )
                else:
                    st.info("Upload a Cover Letter template in the sidebar to generate the PDF version.")

            except Exception as e:
                st.error(f"Processing Error: {e}")
