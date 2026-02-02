import sys
import asyncio
import time  
import streamlit as st
import pandas as pd
import subprocess
import os
import json
from fpdf import FPDF
from fpdf.enums import XPos, YPos # Needed for new FPDF version

#-------------------------------------------------------------------------------#
# INSTALLATION & SYSTEM CONFIG
#-------------------------------------------------------------------------------#
def ensure_playwright():
    marker_file = "playwright_installed.txt"
    if not os.path.exists(marker_file):
        with st.spinner("Setting up browser engine..."):
            # We only install the chromium binary here
            subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
            with open(marker_file, "w") as f: f.write("done")

ensure_playwright()

if not os.path.exists("playwright_installed.txt"):
    os.system("playwright install chromium")
    with open("playwright_installed.txt", "w") as f: f.write("done")

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

st.set_page_config(page_title="LeadGen Pro 2026", layout="wide")

# The Master Whitelist
ALLOWED_EMAILS = ["nmirnes32@gmail.com", "mirnesnuhanovic9@gmail.com"]
SESSION_FILE = "session_token.json"

#-------------------------------------------------------------------------------#
# HELPER FUNCTIONS
#-------------------------------------------------------------------------------#
def get_demo_data(category, city, count): # Add count parameter
    """Generates simulated data for the Demo Mode limited by count"""
    full_list = [
        {"name": f"{city} {category} Solutions", "email": f"info@{city.lower()}-business.de", "status": "Ready"},
        {"name": f"Bavarian {category} Group", "email": f"contact@bavaria-pro.com", "status": "Ready"},
        {"name": f"Munich {category} Specialists", "email": f"hello@munich-tech.de", "status": "Ready"},
        {"name": f"Gentleman's Choice {category}", "email": f"marketing@gentleman-solutions.de", "status": "Ready"},
        {"name": f"Alpine {category} Partners", "email": f"office@alpine-leads.com", "status": "Ready"},
        {"name": f"Digital {city} {category}", "email": f"growth@{city.lower()}-digital.de", "status": "Ready"},
    ]
    # Return only the number of leads requested by the user
    return full_list[:count]

def create_pdf_report(df, category, city):
    """Generates a professional PDF Lead Audit with updated FPDF2 syntax"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", 'B', 20)
    pdf.cell(0, 20, "Gentleman Solutions - Lead Audit", 
             new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    
    pdf.set_font("helvetica", 'I', 12)
    pdf.cell(0, 10, f"Target Industry: {category} | Location: {city}", 
             new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.ln(10)
    
    # Table Header
    pdf.set_fill_color(200, 220, 255)
    pdf.set_font("helvetica", 'B', 12)
    pdf.cell(90, 10, "Business Name", border=1, fill=True)
    pdf.cell(100, 10, "Contact Email", border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True)
    
    # Table Body
    pdf.set_font("helvetica", '', 10)
    for _, row in df.iterrows():
        pdf.cell(90, 10, str(row['name'])[:45], border=1)
        pdf.cell(100, 10, str(row['email']), border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    return pdf.output()

def save_session_to_disk():
    session_data = {
        "email_val": st.session_state.get("email_val"),
        "pass_val": st.session_state.get("pass_val"),
        "name_val": st.session_state.get("name_val"),
        "comp_val": st.session_state.get("comp_val"),
        "user_id": st.session_state.get("user_id"),
        "logged_in": True
    }
    with open(SESSION_FILE, "w") as f:
        json.dump(session_data, f)

def load_session_from_disk():
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, "r") as f:
                data = json.load(f)
                for key, val in data.items():
                    st.session_state[key] = val
        except:
            pass

# Initialize session
if "logged_in" not in st.session_state:
    load_session_from_disk()
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

#-------------------------------------------------------------------------------#
# SIDEBAR & AUTHENTICATION
#-------------------------------------------------------------------------------#
st.sidebar.title("🛠️ Control Center")

if not st.session_state["logged_in"]:
    st.sidebar.info("Currently in **Demo Mode**. Real outreach features are locked.")
    if st.sidebar.button("🔑 Login"):
        st.session_state["show_login"] = True
else:
    st.sidebar.success(f"✅ Connected: {st.session_state.name_val}")
    if st.sidebar.button("Logout & Wipe Session"):
        if os.path.exists(SESSION_FILE): os.remove(SESSION_FILE)
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

# Login Form (Dropdown)
if st.session_state.get("show_login") and not st.session_state["logged_in"]:
    with st.sidebar.expander("Enter Credentials", expanded=True):
        with st.form("login_form"):
            email_in = st.text_input("Gmail").lower().strip()
            pass_in = st.text_input("App Password", type="password")
            name_in = st.text_input("Your Name")
            comp_in = st.text_input("Company")
            if st.form_submit_button("Authenticate"):
                if email_in in ALLOWED_EMAILS:
                    st.session_state.update({
                        "email_val": email_in, "pass_val": pass_in,
                        "name_val": name_in, "comp_val": comp_in,
                        "logged_in": True, "user_id": email_in
                    })
                    save_session_to_disk()
                    st.rerun()
                else:
                    st.error("Unauthorized email.")

#-------------------------------------------------------------------------------#
# MAIN UI
#-------------------------------------------------------------------------------#
st.title("🚀 LeadGen Pro 2026")
st.markdown("### High-Performance B2B Discovery & Outreach")

col1, col2, col3 = st.columns(3)
with col1:
    cat = st.text_input("Business Category", value="Software Agency", key="cat_val")
with col2:
    city = st.text_input("Target City", value="Munich", key="city_val")
with col3:
    # THE FIX: This 4th value (2) is why it says 2 initially. Change it to your liking.
    count = st.number_input("Lead Count", 1, 20, 2, key="count_val")

# Email Template
with st.expander("📧 Customize Outreach Template"):
    subj = st.text_input("Subject Line", value="Question for [Business Name]", key="subj_val")
    body = st.text_area("Email Body", height=150, key="body_val", 
                       value=f"Hello [Business Name],\n\nI noticed your work in {city} and wanted to reach out regarding a potential collaboration.\n\nBest, {st.session_state.get('name_val', 'Gentleman Solutions')}")

#-------------------------------------------------------------------------------#
# ENGINE EXECUTION
#-------------------------------------------------------------------------------#
if st.button("⚡ Start Lead Engine", width="stretch"):
    start_time = time.time()
    
    if not st.session_state["logged_in"]:
        # PUBLIC DEMO MODE
        with st.spinner("DEMO MODE: Simulating market extraction..."):
            time.sleep(2)
            # Pass the count_val from st.number_input here
            st.session_state["leads_df"] = pd.DataFrame(get_demo_data(cat, city, count)) 
            st.session_state["is_real_data"] = False
            st.success("✅ Demo leads generated successfully.")
    else:
        # REAL OUTREACH MODE
        output_file = "leads_with_emails.csv"
        email_data = {"subject": subj, "body": body}
        cmd = [
            sys.executable, "scraper.py", str(count), output_file, 
            cat, city, f"{cat} in {city}", st.session_state.email_val, 
            st.session_state.pass_val, st.session_state.name_val, 
            st.session_state.comp_val, json.dumps(email_data), st.session_state.user_id
        ]
        
        with st.spinner("ACTUAL OUTREACH: Launching web drivers..."):
            try:
                subprocess.run(cmd, text=True, check=True)
                if os.path.exists(output_file):
                    st.session_state["leads_df"] = pd.read_csv(output_file)
                    st.session_state["is_real_data"] = True
            except Exception as e:
                st.error(f"Engine Error: {e}")

#-------------------------------------------------------------------------------#
# RESULTS & EXPORT
#-------------------------------------------------------------------------------#
if "leads_df" in st.session_state:
    st.divider()
    df = st.session_state["leads_df"]
    
    if not st.session_state.get("is_real_data", True):
        st.info("💡 Pro Tip: These leads are simulated. Log in to run the live scraper and send real emails.")

    st.subheader("📊 Extraction Results")
    st.dataframe(df, width="stretch")
    
    col_dl1, col_dl2 = st.columns(2)
    
    # Export Options
    csv_data = df.to_csv(index=False).encode('utf-8')
    col_dl1.download_button("📥 Download Raw Data (CSV)", csv_data, "leads.csv", "text/csv", width="stretch")
    
    pdf_output = create_pdf_report(df, cat, city)
    col_dl2.download_button("📜 Download Executive Audit (PDF)", bytes(pdf_output), "Lead_Audit.pdf", "application/pdf", width="stretch")