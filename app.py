import sys
import asyncio
import time  
import streamlit as st
import pandas as pd
import subprocess
import os
import json

#-------------------------------------------------------------------------------#
# INSTALLATION & SYSTEM CONFIG
#-------------------------------------------------------------------------------#
try:
    import playwright
except ImportError:
    subprocess.run(['pip', 'install', 'playwright'])

# Force install the chromium binaries for deployment stability
if not os.path.exists("playwright_installed.txt"):
    os.system("playwright install chromium")
    with open("playwright_installed.txt", "w") as f: f.write("done")

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

st.set_page_config(page_title="LeadGen Pro 2026", layout="wide")

# The Master Whitelist
ALLOWED_EMAILS = ["nmirnes32@gmail.com"]
SESSION_FILE = "session_token.json"

#-------------------------------------------------------------------------------#
# PERSISTENT LOGIN LOGIC
#-------------------------------------------------------------------------------#
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

# Run session loader on every script refresh
if "logged_in" not in st.session_state:
    load_session_from_disk()
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

#-------------------------------------------------------------------------------#
# LOGIN SCREEN
#-------------------------------------------------------------------------------#
if not st.session_state["logged_in"]:
    st.title("🔒 Outreach Login")
    with st.form("login_form"):
        email = st.text_input("Gmail Address").lower().strip()
        app_password = st.text_input("Gmail App Password", type="password")
        sender_name = st.text_input("Your Name")
        company = st.text_input("Company Name")
        submit = st.form_submit_button("Enter Dashboard")

        if submit:
            if not (email and app_password and sender_name):
                st.error("Please fill in all required fields.")
            elif email not in ALLOWED_EMAILS:
                st.error(f"🚫 Access Denied. {email} is not authorized.")
            else:
                st.session_state["email_val"] = email
                st.session_state["pass_val"] = app_password
                st.session_state["name_val"] = sender_name
                st.session_state["comp_val"] = company
                st.session_state["logged_in"] = True
                st.session_state["user_id"] = email
                save_session_to_disk() # Persist the login
                st.success("Access Granted!")
                st.rerun()
    st.stop() 

#-------------------------------------------------------------------------------#
# SIDEBAR & LOGOUT
#-------------------------------------------------------------------------------#
st.sidebar.success(f"Logged in as: {st.session_state.name_val}")

if st.sidebar.button("Logout & Wipe Data"):
    # Clear CSV content but keep file
    if os.path.exists("leads_with_emails.csv"):
        pd.DataFrame().to_csv("leads_with_emails.csv", index=False)
    
    # Remove session file
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)
        
    # Wipe memory
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

#-------------------------------------------------------------------------------#
# MAIN UI: SEARCH PARAMETERS
#-------------------------------------------------------------------------------#
st.title("🚀 Lead Generator & Outreach")

col1, col2, col3 = st.columns(3)
with col1:
    st.text_input("Business Type", value="Software Development", key="cat_val")
with col2:
    st.text_input("Location", value="Munich", key="city_val")
with col3:
    # UPDATED: Max value capped at 20
    st.number_input("Count (Max 20)", min_value=1, max_value=20, value=5, key="count_val")

#-------------------------------------------------------------------------------#
# EMAIL TEMPLATE
#-------------------------------------------------------------------------------#
st.header("📧 Email Template")
st.text_input("Subject", value="Question regarding [Business Name]", key="subj_val")
st.text_area("Email Content", height=200, key="body_val", 
             value=f"Hello [Business Name],\n\nMy name is {st.session_state.name_val} from {st.session_state.comp_val}. I saw your business in {st.session_state.city_val} and would like to help you.\n\nBest regards,\n{st.session_state.name_val}")

#-------------------------------------------------------------------------------#
# SCRAPER EXECUTION
#-------------------------------------------------------------------------------#
if st.button("🚀 Start Scraper & Outreach"):
    start_time = time.time()
    output_file = "leads_with_emails.csv"
    query = f"{st.session_state.cat_val} in {st.session_state.city_val}"
    email_data = {"subject": st.session_state.subj_val, "body": st.session_state.body_val}

    cmd = [
        sys.executable, "scraper.py", 
        str(st.session_state.count_val),
        output_file, 
        st.session_state.cat_val,
        st.session_state.city_val,
        query, 
        st.session_state.email_val,
        st.session_state.pass_val, 
        st.session_state.name_val,
        st.session_state.comp_val, 
        json.dumps(email_data),
        str(st.session_state.user_id)
    ]

    with st.spinner("Scraping and processing leads..."):
        try:
            subprocess.run(cmd, text=True, check=True)
            if os.path.exists(output_file):
                df = pd.read_csv(output_file)
                st.session_state["leads_df"] = df
                st.session_state["scrape_duration"] = time.time() - start_time
        except subprocess.CalledProcessError as e:
            st.error("Backend Error")

#-------------------------------------------------------------------------------#
# DISPLAY BLOCK
#-------------------------------------------------------------------------------#
if "leads_df" in st.session_state:
    st.divider()
    df = st.session_state["leads_df"]
    if not df.empty:
        sent_df = df[df['email'].notna() & (df['email'] != "N/A")]
        st.success(f"Processed {len(sent_df)} leads.")
        
        for idx, row in sent_df.iterrows():
            st.write(f"✔️ **{row['name']}** — {row['email']}")
        
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Report", data=csv, file_name="leads.csv", mime="text/csv")