import sqlite3
import re
import PyPDF2
import streamlit as st
import google.generativeai as genai
from fpdf import FPDF

# API Key Config
MY_API_KEY = "(GEMINI_API_KEY)"
genai.configure(api_key=MY_API_KEY)
ai_model = genai.GenerativeModel("gemini-2.5-flash")


# Function to clean text because FPDF crashes on unicode symbols and markdown
def clean_pdf_text(text):
    if text is None:
        return ""
    # Strip markdown asterisks
    no_stars = re.sub(r'\*+', '', text)
    # Convert fancy bullets to regular hyphens
    no_bullets = no_stars.replace('•', '-').replace('▪', '-')
    # Encode to latin-1 and drop unmappable emoji characters safely
    return no_bullets.encode('latin-1', 'replace').decode('latin-1')


# Function to build the PDF file data
def get_pdf_bytes(pdf_title, pdf_body):
    my_pdf = FPDF()
    my_pdf.set_auto_page_break(auto=True, margin=15)
    my_pdf.add_page()
    
    # Render PDF Title
    my_pdf.set_font("Arial", 'B', size=16)
    my_pdf.cell(0, 10, clean_pdf_text(pdf_title), ln=True, align='C')
    my_pdf.ln(5)
    
    # Render PDF Content
    my_pdf.set_font("Arial", size=11)
    clean_body = clean_pdf_text(pdf_body)
    
    # Print line by line to prevent overflow bugs
    for line in clean_body.split('\n'):
        my_pdf.multi_cell(0, 7, line)
        
    # Standard string output converted to clean binary stream for download button
    pdf_string = my_pdf.output(dest='S')
    return pdf_string.encode('latin-1')


# Dictionary containing standard career tracking data
CAREERS = {
    "Software Developer": {
        "reqs": "- Python\n- DSA\n- Web Development\n- SQL",
        "channels": "- freeCodeCamp\n- Programming with Mosh\n- Coreyms",
        "sites": "- LeetCode\n- GeeksforGeeks",
        "certs": "- Meta Front-End Developer\n- Google IT Automation",
    },
    "Data Scientist": {
        "reqs": "- Python\n- Machine Learning\n- Pandas\n- Statistics",
        "channels": "- StatQuest with Josh Starmer\n- Ken Jee\n- Data Professor",
        "sites": "- Kaggle\n- Towards Data Science",
        "certs": "- IBM Data Science Professional Certificate\n- Google Data Analytics",
    },
    "Cyber Security": {
        "reqs": "- Networking\n- Linux\n- Ethical Hacking\n- Security Tools",
        "channels": "- NetworkChuck\n- John Hammond\n- David Bombal",
        "sites": "- TryHackMe\n- Hack The Box",
        "certs": "- CompTIA Security+\n- CEH (Certified Ethical Hacker)",
    },
    "AI Engineer": {
        "reqs": "- Python\n- Machine Learning\n- Deep Learning\n- AI Models",
        "channels": "- Sentdex\n- Yannic Kilcher\n- DeepLearningAI",
        "sites": "- Hugging Face Docs\n- OpenAI API Docs",
        "certs": "- Google AI Essentials\n- DeepLearning.AI Generative AI",
    },
    "Cloud Engineer": {
        "reqs": "- AWS\n- Azure\n- Linux\n- Networking",
        "channels": "- Tech With Nana\n- freeCodeCamp",
        "sites": "- AWS Docs\n- Microsoft Learn",
        "certs": "- AWS Cloud Practitioner\n- Microsoft Azure Fundamentals (AZ-900)",
    },
    "DevOps Engineer": {
        "reqs": "- Linux\n- Docker\n- Kubernetes\n- Jenkins",
        "channels": "- TechWorld with Nana\n- KodeKloud",
        "sites": "- Docker Docs\n- Kubernetes Docs",
        "certs": "- Docker Certified Associate\n- AWS Cloud Practitioner",
    },
    "Machine Learning Engineer": {
        "reqs": "- Python\n- TensorFlow\n- Deep Learning\n- Machine Learning",
        "channels": "- Krish Naik\n- Andrew Ng",
        "sites": "- Kaggle\n- TensorFlow Docs",
        "certs": "- TensorFlow Developer Certificate\n- DeepLearning.AI ML Specialization",
    },
    "Data Analyst": {
        "reqs": "- Excel\n- SQL\n- Power BI\n- Python",
        "channels": "- Alex The Analyst\n- Simplilearn",
        "sites": "- Kaggle\n- Power BI Docs",
        "certs": "- Google Data Analytics\n- Microsoft Power BI Data Analyst",
    },
    "Business Analyst": {
        "reqs": "- Excel\n- SQL\n- Communication\n- Requirement Analysis",
        "channels": "- BA Blocks\n- Analyst Answers",
        "sites": "- IIBA\n- Modern Analyst",
        "certs": "- ECBA\n- Google Project Management",
    },
    "Full Stack Developer": {
        "reqs": "- HTML\n- CSS\n- JavaScript\n- React",
        "channels": "- CodeWithHarry\n- Traversy Media",
        "sites": "- MDN Web Docs\n- freeCodeCamp",
        "certs": "- Meta Full Stack Developer\n- IBM Full Stack Developer",
    },
    "Frontend Developer": {
        "reqs": "- HTML\n- CSS\n- JavaScript\n- React",
        "channels": "- Kevin Powell\n- CodeWithHarry",
        "sites": "- MDN\n- W3Schools",
        "certs": "- Meta Front-End Developer\n- Responsive Web Design (freeCodeCamp)",
    },
    "Backend Developer": {
        "reqs": "- Python\n- Django\n- APIs\n- SQL",
        "channels": "- Programming with Mosh\n- freeCodeCamp",
        "sites": "- Django Docs\n- FastAPI Docs",
        "certs": "- Django Developer Certificate\n- REST API Certification",
    },
    "Mobile App Developer": {
        "reqs": "- Flutter\n- Dart\n- Firebase\n- Android",
        "channels": "- Flutter\n- Codepur",
        "sites": "- Flutter Docs\n- Firebase Docs",
        "certs": "- Flutter & Dart Certificate\n- Android Developer Fundamentals",
    },
    "UI/UX Designer": {
        "reqs": "- Figma\n- Wireframing\n- Prototyping\n- UX Research",
        "channels": "- DesignCourse\n- Flux Academy",
        "sites": "- Figma\n- Dribbble",
        "certs": "- Google UX Design Certificate\n- Figma UI/UX Design",
    },
    "Blockchain Developer": {
        "reqs": "- Solidity\n- Ethereum\n- Smart Contracts\n- Web3",
        "channels": "- Dapp University\n- Patrick Collins",
        "sites": "- Solidity Docs\n- Ethereum Docs",
        "certs": "- Certified Blockchain Developer\n- Ethereum Developer Bootcamp",
    },
}

# Initializing Session State Variables
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "skill_analysis_result" not in st.session_state:
    st.session_state.skill_analysis_result = None

if "resume_analysis_result" not in st.session_state:
    st.session_state.resume_analysis_result = None

if "roadmap_result" not in st.session_state:
    st.session_state.roadmap_result = None

if "interview_result" not in st.session_state:
    st.session_state.interview_result = None


def clear_old_data():
    st.session_state.skill_analysis_result = None
    st.session_state.resume_analysis_result = None
    st.session_state.roadmap_result = None
    st.session_state.interview_result = None
    st.session_state.chat_history = []


# Local database connection setup
db_conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = db_conn.cursor()
cursor.execute(
    "CREATE TABLE IF NOT EXISTS users (username TEXT UNIQUE, password TEXT)"
)
db_conn.commit()

st.title("AI Career Copilot")

# Auth Layout Management
if not st.session_state.logged_in:
    menu_choice = st.sidebar.selectbox("Menu", ["Login", "Signup"])

    if menu_choice == "Signup":
        st.subheader("Create New Account")
        reg_user = st.text_input("Username")
        reg_pass = st.text_input("Password", type="password")

        if st.button("Signup"):
            if reg_user and reg_pass:
                try:
                    cursor.execute(
                        "INSERT INTO users VALUES(?, ?)", (reg_user, reg_pass)
                    )
                    db_conn.commit()
                    st.success("Account created successfully! You can login now.")
                except sqlite3.IntegrityError:
                    st.error("This username is already taken!")
            else:
                st.warning("Please fill all fields.")

    elif menu_choice == "Login":
        st.subheader("Login Here")
        login_user = st.text_input("Username")
        login_pass = st.text_input("Password", type="password")

        if st.button("Login"):
            cursor.execute(
                "SELECT * FROM users WHERE username=? AND password=?",
                (login_user, login_pass),
            )
            user_found = cursor.fetchone()
            if user_found:
                st.session_state.logged_in = True
                st.session_state.username = login_user
                st.success("Logged in successfully!")
                st.rerun()
            else:
                st.error("Invalid username or password.")
else:
    st.sidebar.write(f"Logged in as: **{st.session_state.username}**")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        clear_old_data()
        st.rerun()

    st.subheader(f"Welcome, {st.session_state.username}!")

    selected_role = st.selectbox(
        "Select Your Career Path",
        list(CAREERS.keys()),
        key="selected_career_path",
        on_change=clear_old_data,
    )

    st.write(f"Target Role: *{selected_role}*")

    t1, t2, t3, t4, t5 = st.tabs(
        [
            "📊 Skill Analysis",
            "📚 Resources & Quick Tips",
            "📄 Resume Analyzer",
            "🗺️ Career Roadmap",
            "💬 Interview & Chat",
        ]
    )

    # Tab 1: Skills Gap
    with t1:
        st.subheader("Skill Gap Analysis")
        user_input_skills = st.text_input(
            "Enter your current skills (comma separated)", key="skills_input"
        )

        if st.button("Analyze Skills"):
            if user_input_skills:
                with st.spinner("Analyzing..."):
                    try:
                        prompt_text = f"Career: {selected_role}. Current Skills: {user_input_skills}. Analyze the skill gap. Give: 1. Existing Skills 2. Missing Skills 3. Short-term Learning Path 4. Project Suggestions."
                        ai_response = ai_model.generate_content(prompt_text)
                        st.session_state.skill_analysis_result = {
                            "career": selected_role,
                            "text": ai_response.text,
                        }
                    except Exception as err:
                        st.error(f"Something went wrong: {err}")
            else:
                st.warning("Please enter some skills first.")

        if st.session_state.skill_analysis_result:
            if st.session_state.skill_analysis_result["career"] == selected_role:
                st.info("Analysis Report:")
                st.write(st.session_state.skill_analysis_result["text"])
            else:
                st.session_state.skill_analysis_result = None

    # Tab 2: Core Matrix Info Display
    with t2:
        role_info = CAREERS[selected_role]
        st.subheader("Core Competencies")
        st.write(role_info["reqs"])
        st.write("---")
        st.subheader("Recommended Channels & Prep Platforms")
        st.write("### Recommended Channels")
        st.write(role_info["channels"])
        st.write("### Practice Environments")
        st.write(role_info["sites"])
        st.write("### Certifications")
        st.write(role_info["certs"])

    # Tab 3: Resume PDF Parser
    with t3:
        st.subheader("Resume Analyzer")
        uploaded_file = st.file_uploader(
            "Upload Resume (PDF)", type=["pdf"], key="cv_pdf"
        )

        if st.button("Analyze Resume"):
            if uploaded_file:
                with st.spinner("Reading pdf..."):
                    try:
                        pdf_reader = PyPDF2.PdfReader(uploaded_file)
                        extracted_text = ""
                        for current_page in pdf_reader.pages:
                            page_content = current_page.extract_text()
                            if page_content:
                                extracted_text += page_content

                        prompt_text = f"Analyze this resume for a {selected_role} position. Resume Content: {extracted_text} Give: 1. Resume Summary 2. Core Strengths 3. Missing Skills 4. Improvement Suggestions 5. ATS Score out of 100"
                        ai_response = ai_model.generate_content(prompt_text)
                        st.session_state.resume_analysis_result = ai_response.text
                    except Exception as err:
                        st.error(f"Error reading file: {err}")
            else:
                st.warning("Please upload a file first.")

        if st.session_state.resume_analysis_result:
            st.info("Resume Analysis Report:")
            st.write(st.session_state.resume_analysis_result)

            res_pdf = get_pdf_bytes(f"Resume Analysis Report - {selected_role}", st.session_state.resume_analysis_result)
            st.download_button(
                label="📄 Download Resume Report PDF",
                data=res_pdf,
                file_name="resume_report.pdf",
                mime="application/pdf"
            )

    # Tab 4: Roadmaps Engine
    with t4:
        st.subheader("Strategic Career Roadmap")
        if st.button("Generate Roadmap"):
            with st.spinner("Generating..."):
                try:
                    prompt_text = f"Generate a detailed roadmap for becoming a {selected_role}. Include: 1. Skills to Learn 2. Beginner Projects 3. Intermediate Projects 4. Advanced Projects 5. Certifications 6. Learning Resources 7. Timeline (3, 6, 12 months)"
                    ai_response = ai_model.generate_content(prompt_text)
                    st.session_state.roadmap_result = ai_response.text
                except Exception as err:
                    st.error(f"Error: {err}")

        if st.session_state.roadmap_result:
            st.info("Roadmap Output:")
            st.write(st.session_state.roadmap_result)

            map_pdf = get_pdf_bytes(f"Strategic Career Roadmap - {selected_role}", st.session_state.roadmap_result)
            st.download_button(
                label="🗺️ Download Roadmap PDF",
                data=map_pdf,
                file_name="career_roadmap.pdf",
                mime="application/pdf"
            )

    # Tab 5: Mock Prep Workspace
    with t5:
        st.subheader("Mock Interview Workspace")
        if st.button("Generate Interview Questions"):
            with st.spinner("Working on it..."):
                try:
                    prompt_text = f"Generate 10 interview questions for {selected_role}. Include: 1. Beginner Questions 2. Intermediate Questions 3. Advanced Questions 4. Scenario-Based Questions"
                    ai_response = ai_model.generate_content(prompt_text)
                    st.session_state.interview_result = ai_response.text
                except Exception as err:
                    st.error(f"Error: {err}")

        if st.session_state.interview_result:
            st.info("Mock Question Set:")
            st.write(st.session_state.interview_result)

        st.write("---")
        st.subheader("Interactive Advisory Chat")
        user_query = st.text_input("Ask a specific career question:", key="chat_query")

        if st.button("Submit Query"):
            if user_query:
                with st.spinner("Thinking..."):
                    try:
                        prompt_text = f"Career: {selected_role}. User Question: {user_query}. Give a clear and student-friendly answer. If salary is asked, focus on India."
                        ai_response = ai_model.generate_content(prompt_text)
                        st.session_state.chat_history.append(
                            {"q": user_query, "a": ai_response.text}
                        )
                    except Exception as err:
                        st.error(f"Error: {err}")
            else:
                st.warning("Please type something first.")

        if st.session_state.chat_history:
            st.write("---")
            st.subheader("Chat Log")
            for thread in reversed(st.session_state.chat_history):
                st.markdown(f"**User:** {thread['q']}")
                st.markdown(f"**Assistant:** {thread['a']}")
                st.write("---")



                
