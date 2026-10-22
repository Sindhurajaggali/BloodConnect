import os
import sqlite3
from datetime import date, datetime

import pandas as pd
import plotly.express as px
import streamlit as st

# =========================================================
# BLOODCONNECT - PROFESSIONAL EDITION
# =========================================================

st.set_page_config(
    page_title="BloodConnect | Blood Support",
    page_icon="🩸",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_NAME = "bloodconnect.db"

BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
STATUSES = ["Open", "Donor Contacted", "Fulfilled", "Cancelled"]

st.markdown("""
<style>
    .stApp {
        background-color: #f7f8fc;
    }

    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e8eaf0;
    }

    .hero {
        padding: 28px;
        border-radius: 18px;
        background: linear-gradient(120deg, #9f1239, #e11d48);
        color: white;
        margin-bottom: 22px;
    }

    .hero h1 {
        color: white;
        font-size: 36px;
        margin-bottom: 8px;
    }

    .hero p {
        color: #fff1f2;
        font-size: 16px;
    }

    .metric-card {
        background: white;
        padding: 20px;
        border: 1px solid #eceef4;
        border-radius: 14px;
        min-height: 125px;
    }

    .metric-label {
        color: #64748b;
        font-size: 14px;
    }

    .metric-value {
        color: #9f1239;
        font-size: 30px;
        font-weight: 700;
        margin-top: 8px;
    }

    .section-note {
        color: #64748b;
        font-size: 14px;
    }

    div.stButton > button {
        border-radius: 9px;
        font-weight: 600;
    }

    div[data-testid="stForm"] {
        background: white;
        padding: 20px;
        border-radius: 14px;
        border: 1px solid #eceef4;
    }
</style>
""", unsafe_allow_html=True)


# ---------------- DATABASE ----------------

def connect_db():
    conn = sqlite3.connect(DB_NAME, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_db():
    with connect_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS donors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                blood_group TEXT NOT NULL,
                city TEXT NOT NULL,
                phone TEXT NOT NULL,
                email TEXT,
                available INTEGER NOT NULL DEFAULT 1,
                consent INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                blood_group TEXT NOT NULL,
                units INTEGER NOT NULL,
                hospital TEXT NOT NULL,
                city TEXT NOT NULL,
                needed_by TEXT NOT NULL,
                urgency TEXT NOT NULL,
                contact_name TEXT NOT NULL,
                contact_phone TEXT NOT NULL,
                notes TEXT,
                status TEXT NOT NULL DEFAULT 'Open',
                created_at TEXT NOT NULL
            )
        """)


initialize_db()


def request_code(request_id):
    return f"BC-{int(request_id):05d}"


def valid_phone(phone):
    digits = "".join(c for c in phone if c.isdigit())
    return 7 <= len(digits) <= 15


def fetch_all(query, params=()):
    with connect_db() as conn:
        return conn.execute(query, params).fetchall()


def count_query(query):
    rows = fetch_all(query)
    return rows[0][0]


# ---------------- SIDEBAR ----------------

with st.sidebar:
    st.markdown("# 🩸 BloodConnect")
    st.caption("Blood Donation & Emergency Support")
    st.divider()

    page = st.radio(
        "MAIN MENU",
        [
            "🏠 Dashboard",
            "🙋 Register as Donor",
            "🚨 Emergency Blood Request",
            "🔎 Find Potential Donors",
            "📋 Track Request",
            "📚 Awareness Center",
            "🤖 Awareness Assistant",
            "🔐 Admin Dashboard",
        ],
    )

    st.divider()
    st.caption("Built with Python • Streamlit • SQLite")
    st.caption("College Project Prototype")


# ---------------- HEADER ----------------

st.markdown("""
<div class="hero">
    <h1>🩸 BloodConnect</h1>
    <p>Connecting willing donors with people seeking blood support.</p>
</div>
""", unsafe_allow_html=True)

st.warning(
    "Emergency? Contact the treating hospital or a licensed blood bank "
    "immediately. This application does not guarantee blood availability "
    "or determine medical compatibility."
)


# ---------------- DASHBOARD ----------------

if page == "🏠 Dashboard":
    st.subheader("Dashboard Overview")
    st.markdown(
        '<p class="section-note">A quick overview of donor registrations '
        'and blood requests recorded in this application.</p>',
        unsafe_allow_html=True,
    )

    total_donors = count_query("SELECT COUNT(*) FROM donors")
    available_donors = count_query(
        "SELECT COUNT(*) FROM donors WHERE available = 1 AND consent = 1"
    )
    open_requests = count_query(
        "SELECT COUNT(*) FROM requests WHERE status = 'Open'"
    )
    fulfilled_requests = count_query(
        "SELECT COUNT(*) FROM requests WHERE status = 'Fulfilled'"
    )

    cards = [
        ("Registered Donors", total_donors, "🙋"),
        ("Available Donors", available_donors, "🩸"),
        ("Open Requests", open_requests, "🚨"),
        ("Fulfilled Requests", fulfilled_requests, "✅"),
    ]

    cols = st.columns(4)
    for col, (label, value, emoji) in zip(cols, cards):
        with col:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">{emoji} {label}</div>
                    <div class="metric-value">{value}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.write("")
    left, right = st.columns(2)

    donor_rows = fetch_all("""
        SELECT blood_group, COUNT(*) AS total
        FROM donors
        WHERE available = 1 AND consent = 1
        GROUP BY blood_group
    """)

    request_rows = fetch_all("""
        SELECT status, COUNT(*) AS total
        FROM requests
        GROUP BY status
    """)

    with left:
        st.subheader("Donor Blood-Group Distribution")
        if donor_rows:
            df = pd.DataFrame(
                [dict(row) for row in donor_rows]
            )
            fig = px.bar(
                df,
                x="blood_group",
                y="total",
                text="total",
                labels={
                    "blood_group": "Blood Group",
                    "total": "Number of Donors",
                },
                color="blood_group",
                color_discrete_sequence=px.colors.sequential.Reds,
            )
            fig.update_layout(
                showlegend=False,
                plot_bgcolor="white",
                paper_bgcolor="white",
                margin=dict(l=10, r=10, t=25, b=10),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Register consenting, available test donors to populate this chart.")

    with right:
        st.subheader("Request Status Distribution")
        if request_rows:
            df = pd.DataFrame(
                [dict(row) for row in request_rows]
            )
            fig = px.pie(
                df,
                names="status",
                values="total",
                hole=0.55,
                color_discrete_sequence=px.colors.sequential.Reds,
            )
            fig.update_layout(
                paper_bgcolor="white",
                margin=dict(l=10, r=10, t=25, b=10),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Submit a test blood request to populate this chart.")

    st.subheader("Recent Blood Requests")

    recent = fetch_all("""
        SELECT id, blood_group, units, hospital, city,
               needed_by, urgency, status
        FROM requests
        ORDER BY id DESC
        LIMIT 10
    """)

    if recent:
        df = pd.DataFrame([
            {
                "Request ID": request_code(r["id"]),
                "Blood Group": r["blood_group"],
                "Units": r["units"],
                "Hospital": r["hospital"],
                "City": r["city"],
                "Needed By": r["needed_by"],
                "Urgency": r["urgency"],
                "Status": r["status"],
            }
            for r in recent
        ])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No blood requests have been submitted yet.")

    st.divider()
    a, b = st.columns(2)
    with a:
        st.markdown("### 🙋 Become a Donor")
        st.write("Register and choose your contact-sharing preferences.")
    with b:
        st.markdown("### 🚨 Request Blood")
        st.write("Submit a request and keep its reference ID.")


# ---------------- DONOR REGISTRATION ----------------

elif page == "🙋 Register as Donor":
    st.subheader("Donor Registration")
    st.write("Fields marked * are required.")

    with st.form("donor_form"):
        name = st.text_input("Full Name *")
        group = st.selectbox("Blood Group *", BLOOD_GROUPS)
        city = st.text_input("City *")
        phone = st.text_input("Phone Number *")
        email = st.text_input("Email (Optional)")

        available = st.checkbox("I am currently willing to be contacted", True)
        consent = st.checkbox(
            "I consent to sharing my name and contact details with people "
            "searching for potential donors. *",
            value=False,
        )

        submitted = st.form_submit_button("Register Donor")

    if submitted:
        name, city, phone = name.strip(), city.strip(), phone.strip()
        email = email.strip()

        if not name or not city or not phone:
            st.error("Please complete all required fields.")
        elif not valid_phone(phone):
            st.error("Please enter a valid phone number.")
        elif not consent:
            st.error("Contact-sharing consent is required for matching.")
        else:
            with connect_db() as conn:
                conn.execute("""
                    INSERT INTO donors
                    (name, blood_group, city, phone, email,
                     available, consent, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    name, group, city, phone, email or None,
                    int(available), int(consent),
                    datetime.now().isoformat(timespec="seconds"),
                ))
            st.success("Donor registered successfully!")
            st.info("Donor statistics on the Dashboard will reflect this record.")


# ---------------- EMERGENCY REQUEST ----------------

elif page == "🚨 Emergency Blood Request":
    st.subheader("Emergency Blood Request")
    st.write("For a real emergency, contact a hospital or blood bank directly.")

    with st.form("request_form"):
        group = st.selectbox("Required Blood Group *", BLOOD_GROUPS)
        units = st.number_input("Number of Units *", 1, 20, 1)
        hospital = st.text_input("Hospital Name *")
        city = st.text_input("City *")
        needed_by = st.date_input(
            "Date Needed",
            value=date.today(),
            min_value=date.today(),
        )
        urgency = st.selectbox("Urgency", ["Routine", "Urgent", "Critical"])
        contact = st.text_input("Contact Person *")
        phone = st.text_input("Contact Phone *")
        notes = st.text_area("Additional Information (Optional)")

        submitted = st.form_submit_button("Submit Request")

    if submitted:
        hospital, city = hospital.strip(), city.strip()
        contact, phone = contact.strip(), phone.strip()

        if not all([hospital, city, contact, phone]):
            st.error("Please complete all required fields.")
        elif not valid_phone(phone):
            st.error("Please enter a valid contact phone number.")
        else:
            with connect_db() as conn:
                cursor = conn.execute("""
                    INSERT INTO requests
                    (blood_group, units, hospital, city, needed_by,
                     urgency, contact_name, contact_phone, notes,
                     status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Open', ?)
                """, (
                    group, int(units), hospital, city,
                    needed_by.isoformat(), urgency, contact, phone,
                    notes.strip(),
                    datetime.now().isoformat(timespec="seconds"),
                ))
                new_id = cursor.lastrowid

            st.success("Blood request submitted successfully.")
            st.markdown(f"## Your Request ID: `{request_code(new_id)}`")
            st.write("Save this ID to look up the request in this application.")


# ---------------- DONOR MATCHING ----------------

elif page == "🔎 Find Potential Donors":
    st.subheader("Find Potential Donors")
    st.write(
        "Search for available, registered donors who consented to share "
        "their contact details."
    )

    with st.form("search_form"):
        group = st.selectbox("Required Blood Group", BLOOD_GROUPS)
        city = st.text_input("City")
        search = st.form_submit_button("Search Donors")

    if search:
        if not city.strip():
            st.error("Enter a city.")
        else:
            donors = fetch_all("""
                SELECT name, blood_group, city, phone, email
                FROM donors
                WHERE blood_group = ?
                  AND LOWER(TRIM(city)) = LOWER(TRIM(?))
                  AND available = 1
                  AND consent = 1
                ORDER BY name
            """, (group, city.strip()))

            if donors:
                st.success(f"Found {len(donors)} potential donor(s).")
                for d in donors:
                    with st.container(border=True):
                        st.markdown(f"### 🙋 {d['name']}")
                        st.write(f"**Blood Group:** {d['blood_group']}")
                        st.write(f"**City:** {d['city']}")
                        st.write(f"**Phone:** {d['phone']}")
                        if d["email"]:
                            st.write(f"**Email:** {d['email']}")
            else:
                st.info("No matching registered donors found.")

            st.warning(
                "This is only a preliminary search. Hospital professionals "
                "must verify eligibility, testing and transfusion compatibility."
            )


# ---------------- TRACK REQUEST ----------------

elif page == "📋 Track Request":
    st.subheader("Track a Blood Request")
    code = st.text_input("Request ID", placeholder="BC-00001")

    if st.button("Track Request"):
        try:
            if not code.strip().upper().startswith("BC-"):
                raise ValueError

            rid = int(code.strip().upper()[3:])
            rows = fetch_all("SELECT * FROM requests WHERE id = ?", (rid,))

            if not rows:
                st.error("Request not found.")
            else:
                r = rows[0]
                st.markdown(f"### {request_code(r['id'])}")
                st.metric("Current Recorded Status", r["status"])

                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"**Blood Group:** {r['blood_group']}")
                    st.write(f"**Units:** {r['units']}")
                    st.write(f"**Hospital:** {r['hospital']}")
                    st.write(f"**City:** {r['city']}")
                with c2:
                    st.write(f"**Needed By:** {r['needed_by']}")
                    st.write(f"**Urgency:** {r['urgency']}")
                    st.write(f"**Created:** {r['created_at']}")

                st.info(
                    "This status reflects information stored in the app. "
                    "It does not confirm actual blood availability."
                )
        except ValueError:
            st.error("Enter a valid ID, for example BC-00001.")


# ---------------- AWARENESS CENTER ----------------

elif page == "📚 Awareness Center":
    st.subheader("Blood Donation Awareness Center")

    with st.expander("Who can donate blood?"):
        st.write(
            "Eligibility depends on age, weight, health, medicines and other "
            "factors. A qualified blood-bank professional must assess eligibility."
        )

    with st.expander("Blood groups"):
        st.write(
            "Common blood groups include A, B, AB and O, with positive or "
            "negative Rh status. A blood-group label alone does not establish "
            "transfusion compatibility."
        )

    with st.expander("Blood donation myths and facts"):
        st.write(
            "Many eligible donors tolerate donation well, but temporary "
            "dizziness or other effects may occur. Follow blood-centre instructions."
        )

    with st.expander("What to do during an emergency"):
        st.write(
            "Contact the treating hospital or licensed blood bank immediately. "
            "Follow the medical team's instructions and do not delay treatment "
            "while waiting for an online response."
        )

    with st.expander("What BloodConnect cannot do"):
        st.write(
            "The app cannot reserve blood, confirm donor eligibility, determine "
            "transfusion compatibility or guarantee that a donor will respond."
        )


# ---------------- AWARENESS ASSISTANT ----------------


# ---------------- AWARENESS ASSISTANT ----------------

elif page == "🤖 Awareness Assistant":
    st.subheader("🩸 BloodConnect Awareness Assistant")
    st.write(
        "Ask questions about blood donation, donor registration, "
        "blood requests, and general safety."
    )

    st.info(
        "This is a rule-based awareness chatbot, not a medical professional "
        "or a generative AI model. For emergencies, contact a hospital "
        "or licensed blood bank immediately."
    )

    # Knowledge base: reliable general information
    FAQS = [
        {
            "question": "Who can donate blood?",
            "keywords": ["eligibility", "eligible", "who can donate", "age", "weight"],
            "answer": (
                "Blood donation eligibility depends on your age, weight, "
                "health, medicines, and local blood-bank rules. A qualified "
                "blood-bank professional must assess you before donation. "
                "Do not donate if the blood-bank team advises against it."
            ),
        },
        {
            "question": "How do I register as a donor?",
            "keywords": ["register", "registration", "become a donor", "donor form"],
            "answer": (
                "Open 'Register as Donor' from the sidebar. Enter your name, "
                "blood group, city, and phone number. Provide contact-sharing "
                "consent only if you agree to share your details with people "
                "searching for potential donors."
            ),
        },
        {
            "question": "How can I find a donor?",
            "keywords": ["find donor", "search donor", "need blood", "find blood"],
            "answer": (
                "Open 'Find Potential Donors', choose the required blood "
                "group, enter the city, and select Search Donors. Results "
                "include only registered donors who are marked available "
                "and consented to contact sharing. No match does not mean "
                "blood is unavailable elsewhere. Contact a licensed blood "
                "bank or hospital as well."
            ),
        },
        {
            "question": "How do I submit an emergency request?",
            "keywords": ["emergency", "urgent", "critical", "request blood"],
            "answer": (
                "For a real emergency, contact the treating hospital or "
                "licensed blood bank immediately. Do not wait for an online "
                "response. In this app, open 'Emergency Blood Request', "
                "complete the required fields, and submit the form. Save "
                "the request ID displayed after submission."
            ),
        },
        {
            "question": "How do I track my request?",
            "keywords": ["track", "request id", "request status", "status"],
            "answer": (
                "Open 'Track Request' and enter your reference ID, for "
                "example BC-00001. The app displays the status recorded "
                "in its database. This status does not confirm that blood "
                "has been reserved or is available."
            ),
        },
        {
            "question": "Are all blood groups compatible?",
            "keywords": ["compatibility", "compatible", "blood groups", "transfusion"],
            "answer": (
                "No. Transfusion compatibility depends on blood group, "
                "Rh type, testing, and the clinical situation. A qualified "
                "healthcare team or blood bank must perform the necessary "
                "testing and determine compatibility. Never rely on this "
                "chatbot to decide which blood can be transfused."
            ),
        },
        {
            "question": "What should I do after donating blood?",
            "keywords": ["after donation", "after donating", "recovery", "dizzy"],
            "answer": (
                "Follow the blood centre's aftercare instructions, rest as "
                "advised, and take fluids and refreshments as recommended. "
                "If you feel unwell, inform the blood-centre staff. Seek "
                "medical help for severe or persistent symptoms."
            ),
        },
        {
            "question": "Does BloodConnect guarantee blood availability?",
            "keywords": ["guarantee", "available blood", "availability", "reserve blood"],
            "answer": (
                "No. BloodConnect is an educational prototype that helps "
                "search registered potential donors and record requests. "
                "It cannot confirm donor eligibility, reserve blood, "
                "guarantee a response, or replace a licensed blood bank."
            ),
        },
        {
            "question": "Is my contact information shared?",
            "keywords": ["privacy", "personal information", "contact details", "consent"],
            "answer": (
                "Donor matching in this prototype displays contact details "
                "for donors who have consented to sharing and are marked "
                "available. Only provide genuine details with appropriate "
                "consent. The current prototype does not provide complete "
                "privacy controls for a public production service."
            ),
        },
    ]

    # Initialise conversation for the current Streamlit session
    if "bc_chat_history" not in st.session_state:
        st.session_state["bc_chat_history"] = [
            {
                "role": "assistant",
                "content": (
                    "Hello! 👋 I am the BloodConnect Awareness Assistant. "
                    "Choose a suggested question below or type your own "
                    "question. I can answer common questions about using "
                    "this app and general blood donation awareness."
                ),
            }
        ]

    def get_awareness_answer(user_question):
        q = user_question.lower().strip()

        if not q:
            return "Please type a question or choose one of the suggestions."

        # Emergency-related queries take priority
        emergency_terms = [
            "emergency", "urgent", "critical", "right now",
            "immediately", "bleeding heavily"
        ]

        if any(term in q for term in emergency_terms):
            return (
                "🚨 If this is a real medical emergency, contact emergency "
                "services, the treating hospital, or a licensed blood bank "
                "immediately. Do not wait for a chatbot or an online donor "
                "response. Follow the medical team's instructions."
            )

        # Find the closest matching FAQ using keyword overlap
        best_match = None
        best_score = 0

        for item in FAQS:
            score = sum(
                1 for keyword in item["keywords"]
                if keyword in q
            )

            # Also recognise the displayed FAQ question
            if item["question"].lower() in q:
                score += 3

            if score > best_score:
                best_score = score
                best_match = item

        if best_match and best_score > 0:
            return best_match["answer"]

        return (
            "I don't have a verified answer for that question yet. "
            "You can ask about donor eligibility, donor registration, "
            "finding donors, submitting or tracking a request, blood-group "
            "compatibility, or donation aftercare. For medical advice, "
            "please consult a qualified healthcare professional."
        )

    # Suggested questions
    st.markdown("### 💡 Suggested questions")

    suggestions = [
        "Who can donate blood?",
        "How do I register as a donor?",
        "How can I find a donor?",
        "How do I track my request?",
        "Are all blood groups compatible?",
        "Does BloodConnect guarantee blood availability?",
    ]

    suggestion_cols = st.columns(2)

    for index, suggestion in enumerate(suggestions):
        with suggestion_cols[index % 2]:
            if st.button(
                suggestion,
                key=f"bc_suggestion_{index}",
                use_container_width=True,
            ):
                st.session_state["bc_pending_question"] = suggestion

    st.divider()
    st.markdown("### 💬 Chat with the assistant")

    # Display the previous conversation
    for message in st.session_state["bc_chat_history"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Use a suggested question or typed question
    pending_question = st.session_state.pop(
        "bc_pending_question", None
    )

    typed_question = st.chat_input(
        "Type your blood donation awareness question..."
    )

    current_question = pending_question or typed_question

    if current_question:
        st.session_state["bc_chat_history"].append(
            {
                "role": "user",
                "content": current_question,
            }
        )

        answer = get_awareness_answer(current_question)

        st.session_state["bc_chat_history"].append(
            {
                "role": "assistant",
                "content": answer,
            }
        )

        st.rerun()

    if st.button("Clear conversation", key="bc_clear_chat"):
        st.session_state["bc_chat_history"] = [
            {
                "role": "assistant",
                "content": (
                    "Conversation cleared! Ask me a question about "
                    "BloodConnect or blood donation awareness."
                ),
            }
        ]
        st.rerun()



# ---------------- ADMIN DASHBOARD ----------------

elif page == "🔐 Admin Dashboard":
    st.subheader("Admin Dashboard")

    password = os.environ.get("BLOODCONNECT_ADMIN_PASSWORD")

    if not password:
        st.error("Admin access is disabled until a password is configured.")
        st.code(
            '$env:BLOODCONNECT_ADMIN_PASSWORD = "Choose-A-Strong-Password"'
        )
        st.caption(
            "Set this variable in PowerShell before starting Streamlit. "
            "Never publish the password."
        )
    else:
        entered = st.text_input("Admin Password", type="password")

        if st.button("Login"):
            st.session_state["bc_admin"] = (entered == password)

            if st.session_state["bc_admin"]:
                st.success("Admin login successful.")
            else:
                st.error("Incorrect password.")

        if st.session_state.get("bc_admin", False):
            st.divider()
            st.markdown("### Manage Requests")

            requests = fetch_all("SELECT * FROM requests ORDER BY id DESC")

            if not requests:
                st.info("No requests available.")
            else:
                for r in requests:
                    with st.expander(
                        f"{request_code(r['id'])} | "
                        f"{r['blood_group']} | {r['status']}"
                    ):
                        st.write(f"Hospital: {r['hospital']}")
                        st.write(f"City: {r['city']}")
                        st.write(f"Contact: {r['contact_name']}")
                        st.write(f"Phone: {r['contact_phone']}")

                        new_status = st.selectbox(
                            "Status",
                            STATUSES,
                            index=STATUSES.index(r["status"])
                            if r["status"] in STATUSES else 0,
                            key=f"status_{r['id']}",
                        )

                        if st.button(
                            "Save Status",
                            key=f"save_{r['id']}",
                        ):
                            with connect_db() as conn:
                                conn.execute(
                                    "UPDATE requests SET status = ? WHERE id = ?",
                                    (new_status, r["id"]),
                                )
                            st.success("Status updated.")
                            st.rerun()

            st.divider()
            st.markdown("### Manage Donors")

            donors = fetch_all("SELECT * FROM donors ORDER BY id DESC")

            for d in donors:
                with st.expander(
                    f"{d['name']} | {d['blood_group']} | {d['city']}"
                ):
                    st.write(f"Phone: {d['phone']}")
                    st.write(f"Contact consent: {'Yes' if d['consent'] else 'No'}")

                    if st.button("Delete Donor", key=f"del_{d['id']}"):
                        with connect_db() as conn:
                            conn.execute(
                                "DELETE FROM donors WHERE id = ?",
                                (d["id"],),
                            )
                        st.success("Donor record deleted.")
                        st.rerun()

            if st.button("Logout"):
                st.session_state["bc_admin"] = False
                st.rerun()


# ---------------- FOOTER ----------------

st.divider()
st.caption(
    "BloodConnect | Educational prototype | "
    "Use verified hospitals and licensed blood banks for real emergencies."
)