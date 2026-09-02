import streamlit as st
import pandas as pd
import io
import json
import requests
import base64
import time
from pypdf import PdfReader, PdfWriter

# ১. পেজ কনফিগারেশন ও কাস্টম ডিজাইন (লেজার/রেজিস্টার বুক থিম)
st.set_page_config(page_title="BRTC Form Extractor Pro", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Hind+Siliguri:wght@400;500;600;700&family=Inter:wght@400;500;600;700&display=swap');

    :root {
        --bg: #F4F6F5;
        --card: #FFFFFF;
        --border: #E1E5E3;
        --ink: #1A1F1D;
        --ink-muted: #5B6560;
        --green-deep: #0E6B45;
        --green-dark: #0A4E33;
        --red-stamp: #C0392B;
    }

    .stApp {
        background-color: var(--bg);
    }

    html, body, [class*="css"] {
        font-family: 'Hind Siliguri', 'Inter', sans-serif;
        color: var(--ink);
    }

    /* --- হেডার: পরিষ্কার, উচ্চ-কনট্রাস্ট প্রফেশনাল কার্ড --- */
    .main-header {
        background: var(--green-deep);
        border-radius: 10px;
        padding: 26px 32px;
        margin-bottom: 28px;
        box-shadow: 0 2px 8px rgba(10,78,51,0.18);
    }
    .main-header h1 {
        font-family: 'Hind Siliguri', sans-serif;
        font-weight: 700;
        font-size: 1.9rem;
        color: #FFFFFF;
        margin: 0 0 6px 0;
    }
    .main-header p {
        font-family: 'Hind Siliguri', sans-serif;
        font-size: 0.95rem;
        font-weight: 500;
        color: #E7F3EC;
        margin: 0;
    }
    .header-tag {
        display: inline-block;
        background: rgba(255,255,255,0.15);
        color: #FFFFFF;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 4px 12px;
        border-radius: 20px;
        margin-top: 10px;
    }

    /* --- সেকশন টাইটেল --- */
    h3 {
        font-weight: 700 !important;
        color: var(--ink) !important;
    }

    /* --- বাটন --- */
    .stButton > button {
        background-color: var(--green-deep);
        color: #FFFFFF;
        border: none;
        border-radius: 8px;
        font-family: 'Hind Siliguri', sans-serif;
        font-weight: 600;
        font-size: 0.95rem;
        padding: 0.6rem 1.5rem;
        transition: background-color 0.15s ease;
    }
    .stButton > button:hover {
        background-color: var(--green-dark);
        color: #FFFFFF;
    }

    /* --- ফাইল আপলোডার --- */
    [data-testid="stFileUploader"] {
        background-color: transparent;
    }
    [data-testid="stFileUploaderDropzone"] {
        background-color: var(--card);
        border: 2px dashed #B7C4BE;
        border-radius: 10px;
    }
    [data-testid="stFileUploaderDropzone"] * {
        color: var(--ink) !important;
        fill: var(--ink) !important;
        background-color: var(--card) !important;
    }
    [data-testid="stFileUploaderDropzone"] button {
        background-color: var(--card) !important;
        color: var(--green-deep) !important;
        border: 1.5px solid var(--green-deep) !important;
        border-radius: 6px !important;
    }
    [data-testid="stFileUploaderDropzone"] small {
        color: var(--ink-muted) !important;
    }
    [data-testid="stFileUploaderFile"], [data-testid="stFileUploaderFile"] * {
        background-color: var(--card) !important;
        color: var(--ink) !important;
    }
    [data-testid="stFileUploaderDropzone"] svg circle,
    [data-testid="stFileUploaderDropzone"] svg path {
        fill: none !important;
        stroke: var(--green-deep) !important;
    }
    [data-testid="stFileUploaderFileName"] {
        color: var(--ink) !important;
    }

    /* --- সাধারণ ফর্ম/উইজেট লেবেল (যেমন file uploader-এর উপরের নির্দেশনা) --- */
    [data-testid="stWidgetLabel"] p {
        color: var(--ink) !important;
        font-weight: 500;
    }

    /* --- ডেটা টেবিল --- */
    [data-testid="stDataFrame"] {
        border: 1px solid var(--border);
        border-radius: 8px;
        overflow: hidden;
    }

    /* --- সতর্কতা/সাকসেস/এরর --- */
    div[data-testid="stAlert"] {
        border-radius: 8px;
        font-family: 'Hind Siliguri', sans-serif;
        font-size: 0.95rem;
    }
    div[data-testid="stAlertContentSuccess"] {
        border-left: 5px solid var(--green-deep);
    }
    div[data-testid="stAlertContentError"] {
        border-left: 5px solid var(--red-stamp);
    }
    div[data-testid="stAlert"] *,
    div[data-testid="stAlert"] p,
    div[data-testid="stAlert"] span,
    div[data-testid="stAlert"] div {
        color: var(--ink) !important;
        opacity: 1 !important;
    }

    /* --- প্রোগ্রেস বারের উপরের লেখা --- */
    [data-testid="stProgress"] *,
    [data-testid="stProgress"] p,
    [data-testid="stProgress"] span,
    [data-testid="stProgress"] div {
        color: var(--ink) !important;
        opacity: 1 !important;
    }

    /* --- সাইডবার --- */
    [data-testid="stSidebar"] {
        background-color: var(--card);
        border-right: 1px solid var(--border);
    }
    [data-testid="stSidebar"] * {
        color: var(--ink) !important;
    }
    [data-testid="stSidebar"] input {
        background-color: #FFFFFF !important;
        color: var(--ink) !important;
        border: 1.5px solid var(--border) !important;
        border-radius: 6px !important;
    }
    [data-testid="stSidebar"] input:focus {
        border-color: var(--green-deep) !important;
    }
    [data-testid="stSidebar"] [data-baseweb="input"] {
        background-color: #FFFFFF !important;
    }
    /* --- Streamlit স্ক্রিপ্ট রান করার সময় পুরনো লেখা ফিকে (dim) হয়ে যায়, সেটা বন্ধ করা --- */
    [data-stale="true"] {
        opacity: 1 !important;
    }
    .main .block-container {
        opacity: 1 !important;
    }
    /* Streamlit inline style দিয়ে opacity কমিয়ে দেয়, সেটাও জোর করে ওভাররাইড করা হচ্ছে */
    [style*="opacity"] {
        opacity: 1 !important;
    }
    .element-container, .stMarkdown, .stAlert, .stProgress {
        opacity: 1 !important;
        transition: none !important;
    }
    </style>

    <div class="main-header">
        <h1>📄 BRTC Form Extractor</h1>
        <p>বিআরটিসি বাস ডিপো ও প্রশিক্ষণ কেন্দ্র, দিনাজপুর</p>
        <span class="header-tag">রেজিস্টার এন্ট্রি সিস্টেম</span>
    </div>
""", unsafe_allow_html=True)

# ২. সাইডবারে এপিআই কি ইনপুট
# ২. সাইডবারে এপিআই কি ইনপুট (Secrets-এ সেভ থাকলে অটো-ফিল হয়ে যাবে, বারবার টাইপ করতে হবে না)
def get_secret(key):
    try:
        return st.secrets.get(key, "")
    except Exception:
        return ""

api_key = st.sidebar.text_input("🔑 আপনার Gemini API Key দিন", value=get_secret("GEMINI_API_KEY"), type="password")
groq_api_key = st.sidebar.text_input("🔑 Groq API Key (ঐচ্ছিক - ১ম ব্যাকআপ)", value=get_secret("GROQ_API_KEY"), type="password")
mistral_api_key = st.sidebar.text_input("🔑 Mistral API Key (ঐচ্ছিক - ২য় ব্যাকআপ)", value=get_secret("MISTRAL_API_KEY"), type="password")
st.sidebar.caption("ফ্রি key বানাতে: console.groq.com এবং console.mistral.ai")
st.sidebar.caption("💡 key বারবার না দিতে চাইলে Secrets-এ সেভ করুন (নিচে instruction দেখুন)")

# ৩. সেশন স্টেটে এক্সেল ডাটা ফ্রেম ও API ব্যবহারের কাউন্টার ইনিশিয়েলাইজ করা
if 'excel_df' not in st.session_state:
    st.session_state.excel_df = pd.DataFrame(columns=["ক্রঃনং", "প্রশিক্ষণার্থীর নাম ও পিতার নাম", "জাতীয় পরিচয়পত্র নং", "মোবাইল নম্বর", "জেলা", "থাম্বনেইল"])

if 'api_usage' not in st.session_state:
    st.session_state.api_usage = {"gemini": 0, "groq": 0, "mistral": 0}

# সাইডবারে আজকের API ব্যবহারের কাউন্টার দেখানো
st.sidebar.markdown("---")
st.sidebar.markdown("**📊 এই সেশনে ব্যবহার হয়েছে**")
u_col1, u_col2, u_col3 = st.sidebar.columns(3)
u_col1.metric("Gemini", st.session_state.api_usage["gemini"])
u_col2.metric("Groq", st.session_state.api_usage["groq"])
u_col3.metric("Mistral", st.session_state.api_usage["mistral"])

# ৪. একটা সিঙ্গেল পেজ/ইমেজ Gemini-তে পাঠিয়ে ডেটা এক্সট্রাক্ট করার ফাংশন (রিট্রাই লজিক সহ)
def extract_entries_from_gemini(base64_data, mime_type, api_key, label):
    model_name = "gemini-3.6-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}

    prompt = """
    You are an expert OCR and data extraction AI. This file may contain ONE or MULTIPLE separate BRTC Driver Training forms.

    Carefully extract, for EACH form you find:
    - Applicant's name in Bangla (প্রশিক্ষণার্থীর নাম)
    - Father's name in Bangla (পিতার নাম)
    - National ID number (জাতীয় পরিচয়পত্র নং)
    - Mobile number (মোবাইল নম্বর)
    - District/location name from the center name at the top (e.g., দিনাজপুর)

    Strictly format the Mobile number by keeping the last 9 or 11 digits and stripping hyphens based on user example.

    You MUST output ONLY a valid JSON ARRAY (a list), with ONE object per form found, even if there is only 1 form. Do not include markdown code blocks like ```json or any trailing words.

    Example format:
    [
        {
            "name": "Exact Name in Bangla",
            "father": "Exact Father Name in Bangla",
            "nid": "NID Number String",
            "mobile": "Mobile Number String",
            "district": "দিনাজপুর"
        }
    ]
    """

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": mime_type, "data": base64_data}}
                ]
            }
        ]
    }

    max_retries = 4
    response_json = None
    for attempt in range(max_retries):
        response = requests.post(url, headers=headers, json=payload)
        response_json = response.json()

        error_info = response_json.get("error") if isinstance(response_json, dict) else None
        if not error_info:
            break

        error_message = str(error_info.get("message", error_info))
        is_quota_error = "quota" in error_message.lower() or "rate_limit" in error_message.lower()
        is_temporary = is_quota_error or any(keyword in error_message.lower() for keyword in
                            ["high demand", "overload", "unavailable", "try again", "503", "429"])

        if is_temporary and attempt < max_retries - 1:
            # API নিজে যদি "retry in Xs" বলে দেয়, সেটাই ব্যবহার করা হবে (quota error-এর জন্য সবচেয়ে নির্ভরযোগ্য)
            suggested_wait = None
            error_details = error_info.get("details", []) if isinstance(error_info, dict) else []
            for detail in error_details:
                if isinstance(detail, dict) and "retryDelay" in detail:
                    try:
                        suggested_wait = int(str(detail["retryDelay"]).replace("s", "")) + 2
                    except ValueError:
                        pass

            if suggested_wait:
                wait_seconds = suggested_wait
            elif is_quota_error:
                wait_seconds = 20  # quota error হলে একটু বেশি সময় অপেক্ষা করা ভালো
            else:
                wait_seconds = (attempt + 1) * 5

            time.sleep(wait_seconds)
            continue
        else:
            raise Exception(error_message)

    response_text = response_json['candidates'][0]['content']['parts'][0]['text']
    clean_json = response_text.replace("```json", "").replace("```", "").strip()
    parsed_data = json.loads(clean_json)

    if isinstance(parsed_data, dict):
        return [parsed_data]
    return parsed_data


# ৫. একটা সিঙ্গেল পেজ/ইমেজ Groq (ব্যাকআপ)-তে পাঠিয়ে ডেটা এক্সট্রাক্ট করার ফাংশন
def extract_entries_from_groq(base64_data, mime_type, api_key, label):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    model_name = "meta-llama/llama-4-scout-17b-16e-instruct"

    prompt = """
    You are an expert OCR and data extraction AI. This image may contain ONE or MULTIPLE separate BRTC Driver Training forms.

    Carefully extract, for EACH form you find:
    - Applicant's name in Bangla (প্রশিক্ষণার্থীর নাম)
    - Father's name in Bangla (পিতার নাম)
    - National ID number (জাতীয় পরিচয়পত্র নং)
    - Mobile number (মোবাইল নম্বর)
    - District/location name from the center name at the top (e.g., দিনাজপুর)

    Strictly format the Mobile number by keeping the last 9 or 11 digits and stripping hyphens based on user example.

    You MUST output ONLY a valid JSON ARRAY (a list), with ONE object per form found, even if there is only 1 form. Do not include markdown code blocks like ```json or any trailing words.

    Example format:
    [
        {
            "name": "Exact Name in Bangla",
            "father": "Exact Father Name in Bangla",
            "nid": "NID Number String",
            "mobile": "Mobile Number String",
            "district": "দিনাজপুর"
        }
    ]
    """

    payload = {
        "model": model_name,
        "temperature": 0,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{base64_data}"}}
                ]
            }
        ]
    }

    response = requests.post(url, headers=headers, json=payload)
    response_json = response.json()

    if isinstance(response_json, dict) and "error" in response_json:
        raise Exception(str(response_json["error"].get("message", response_json["error"])))

    response_text = response_json['choices'][0]['message']['content']
    clean_json = response_text.replace("```json", "").replace("```", "").strip()
    parsed_data = json.loads(clean_json)

    if isinstance(parsed_data, dict):
        return [parsed_data]
    return parsed_data


# ৬. PDF পেজকে ছবিতে রূপান্তর (Groq ও Mistral vision মডেল শুধু ছবি নেয়, PDF সরাসরি নেয় না)
def pdf_page_to_png(pdf_page_bytes):
    import fitz  # PyMuPDF
    doc = fitz.open(stream=pdf_page_bytes, filetype="pdf")
    pix = doc[0].get_pixmap(dpi=200)
    return pix.tobytes("png")


# ৬.১ প্রিভিউ/QA-এর জন্য ছোট থাম্বনেইল বানানো (এক্সট্র্যাক্ট করা ডেটার পাশে দেখানোর জন্য)
def make_thumbnail_data_uri(page_bytes, page_mime, max_width=200):
    try:
        if page_mime == "application/pdf":
            import fitz
            doc = fitz.open(stream=page_bytes, filetype="pdf")
            page = doc[0]
            zoom = max_width / page.rect.width
            pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
            img_bytes = pix.tobytes("jpeg")
        else:
            from PIL import Image
            img = Image.open(io.BytesIO(page_bytes)).convert("RGB")
            ratio = max_width / img.width
            img = img.resize((max_width, max(1, int(img.height * ratio))))
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=70)
            img_bytes = buf.getvalue()

        b64 = base64.b64encode(img_bytes).decode("utf-8")
        return f"data:image/jpeg;base64,{b64}"
    except Exception:
        return None  # থাম্বনেইল বানাতে ব্যর্থ হলেও মূল ডেটা এক্সট্রাকশন যেন থেমে না যায়


# ৬.১ একটা সিঙ্গেল পেজ/ইমেজ Mistral (২য় ব্যাকআপ)-এ পাঠিয়ে ডেটা এক্সট্রাক্ট করার ফাংশন
def extract_entries_from_mistral(base64_data, mime_type, api_key, label):
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    model_name = "pixtral-12b-2409"  # Mistral-এর vision-capable মডেল, হাতে-লেখা ফর্মে তুলনামূলক ভালো

    prompt = """
    You are an expert OCR and data extraction AI. This image may contain ONE or MULTIPLE separate BRTC Driver Training forms.

    Carefully extract, for EACH form you find:
    - Applicant's name in Bangla (প্রশিক্ষণার্থীর নাম)
    - Father's name in Bangla (পিতার নাম)
    - National ID number (জাতীয় পরিচয়পত্র নং)
    - Mobile number (মোবাইল নম্বর)
    - District/location name from the center name at the top (e.g., দিনাজপুর)

    Strictly format the Mobile number by keeping the last 9 or 11 digits and stripping hyphens based on user example.

    You MUST output ONLY a valid JSON ARRAY (a list), with ONE object per form found, even if there is only 1 form. Do not include markdown code blocks like ```json or any trailing words.

    Example format:
    [
        {
            "name": "Exact Name in Bangla",
            "father": "Exact Father Name in Bangla",
            "nid": "NID Number String",
            "mobile": "Mobile Number String",
            "district": "দিনাজপুর"
        }
    ]
    """

    payload = {
        "model": model_name,
        "temperature": 0,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{base64_data}"}}
                ]
            }
        ]
    }

    response = requests.post(url, headers=headers, json=payload)
    response_json = response.json()

    if isinstance(response_json, dict) and "error" in response_json:
        raise Exception(str(response_json["error"].get("message", response_json["error"])))
    if isinstance(response_json, dict) and "message" in response_json and "choices" not in response_json:
        raise Exception(str(response_json.get("message")))

    response_text = response_json['choices'][0]['message']['content']
    clean_json = response_text.replace("```json", "").replace("```", "").strip()
    parsed_data = json.loads(clean_json)

    if isinstance(parsed_data, dict):
        return [parsed_data]
    return parsed_data


# ৭. একটা PDF-কে আলাদা আলাদা পেজে ভেঙে দেওয়ার ফাংশন
def split_pdf_into_pages(file_bytes):
    reader = PdfReader(io.BytesIO(file_bytes))
    page_bytes_list = []
    for page in reader.pages:
        writer = PdfWriter()
        writer.add_page(page)
        buf = io.BytesIO()
        writer.write(buf)
        page_bytes_list.append(buf.getvalue())
    return page_bytes_list


# ৮. ফাইল আপলোডার (Image এবং PDF একসাথে সাপোর্ট করবে)
uploaded_files = st.file_uploader("আপনার PDF বা Image ফর্মগুলো আপলোড করুন (একাধিক ফাইল একসাথে সিলেক্ট করতে পারবেন)", type=["jpg", "jpeg", "png", "pdf"], accept_multiple_files=True)

if uploaded_files:
    if st.button("🚀 ডেটা এক্সট্রাক্ট এবং এক্সেল তালিকায় যোগ করুন"):
        if not api_key:
            st.error("অনুগ্রহ করে সাইডবারে আপনার Gemini API Key-টি প্রদান করুন।")
        else:
            for uploaded_file in uploaded_files:
                with st.spinner(f"{uploaded_file.name} প্রসেস করা হচ্ছে... (একটু সময় লাগতে পারে)"):
                    try:
                        file_bytes = uploaded_file.read()
                        file_name_lower = uploaded_file.name.lower()
                        is_pdf = file_name_lower.endswith('.pdf')

                        # PDF হলে পেজ-বাই-পেজ ভেঙে ফেলা হচ্ছে, ইমেজ হলে একটাই "পেজ" হিসেবে ধরা হচ্ছে
                        if is_pdf:
                            page_bytes_list = split_pdf_into_pages(file_bytes)
                            page_mime = "application/pdf"
                        else:
                            page_bytes_list = [file_bytes]
                            if file_name_lower.endswith('.png'):
                                page_mime = "image/png"
                            elif file_name_lower.endswith('.webp'):
                                page_mime = "image/webp"
                            else:
                                page_mime = "image/jpeg"

                        total_pages = len(page_bytes_list)
                        all_new_rows = []
                        failed_pages = 0
                        last_error = None

                        for page_index, page_bytes in enumerate(page_bytes_list):
                            page_label = f"{uploaded_file.name} (পেজ {page_index + 1}/{total_pages})"

                            # ফ্রি টিয়ারের rate limit (মিনিটে সীমিত রিকোয়েস্ট) এড়াতে পরপর কলের মাঝে ছোট বিরতি
                            if page_index > 0:
                                time.sleep(4)

                            base64_data = base64.b64encode(page_bytes).decode("utf-8")
                            source_used = None

                            try:
                                entries_list = extract_entries_from_gemini(base64_data, page_mime, api_key, page_label)
                                source_used = "gemini"
                            except Exception as gemini_error:
                                entries_list = None
                                last_error = gemini_error

                                # ১ম ব্যাকআপ: Groq
                                if groq_api_key:
                                    try:
                                        if page_mime == "application/pdf":
                                            png_bytes = pdf_page_to_png(page_bytes)
                                            backup_base64 = base64.b64encode(png_bytes).decode("utf-8")
                                            backup_mime = "image/png"
                                        else:
                                            backup_base64 = base64_data
                                            backup_mime = page_mime
                                        entries_list = extract_entries_from_groq(backup_base64, backup_mime, groq_api_key, page_label)
                                        source_used = "groq"
                                    except Exception as groq_error:
                                        last_error = groq_error

                                # ২য় ব্যাকআপ: Mistral (Groq-ও fail করলে বা key না থাকলে)
                                if entries_list is None and mistral_api_key:
                                    try:
                                        if page_mime == "application/pdf":
                                            png_bytes = pdf_page_to_png(page_bytes)
                                            backup_base64 = base64.b64encode(png_bytes).decode("utf-8")
                                            backup_mime = "image/png"
                                        else:
                                            backup_base64 = base64_data
                                            backup_mime = page_mime
                                        entries_list = extract_entries_from_mistral(backup_base64, backup_mime, mistral_api_key, page_label)
                                        source_used = "mistral"
                                    except Exception as mistral_error:
                                        last_error = mistral_error

                                if entries_list is None:
                                    failed_pages += 1
                                    continue

                            # API ব্যবহারের কাউন্টার আপডেট
                            if source_used:
                                st.session_state.api_usage[source_used] += 1

                            # এই পেজের জন্য একটা থাম্বনেইল বানানো (QA-এর জন্য, একবারই বানিয়ে সব এন্ট্রিতে ব্যবহার হবে)
                            thumbnail_uri = make_thumbnail_data_uri(page_bytes, page_mime)

                            for data_json in entries_list:
                                current_sl = len(st.session_state.excel_df) + len(all_new_rows) + 1
                                formatted_name_father = f"নাম- {data_json.get('name')}   পিতা- {data_json.get('father')}"
                                all_new_rows.append({
                                    "ক্রঃনং": current_sl,
                                    "প্রশিক্ষণার্থীর নাম ও পিতার নাম": formatted_name_father,
                                    "জাতীয় পরিচয়পত্র নং": str(data_json.get('nid')),
                                    "মোবাইল নম্বর": str(data_json.get('mobile')),
                                    "জেলা": data_json.get('district'),
                                    "থাম্বনেইল": thumbnail_uri
                                })

                        if all_new_rows:
                            st.session_state.excel_df = pd.concat([st.session_state.excel_df, pd.DataFrame(all_new_rows)], ignore_index=True)

                        if failed_pages > 0:
                            st.info(f"📄 {uploaded_file.name}: {total_pages} পেজ থেকে {len(all_new_rows)} টি এন্ট্রি পাওয়া গেছে। ({failed_pages} টি পেজ প্রসেস করা যায়নি: {str(last_error)[:120]})")
                        else:
                            st.info(f"📄 {uploaded_file.name}: {total_pages} পেজ থেকে {len(all_new_rows)} টি এন্ট্রি পাওয়া গেছে।")

                    except Exception as e:
                        st.error(f"{uploaded_file.name} প্রসেস করতে ত্রুটি হয়েছে: {str(e)}")


            st.success("✅ সব ফাইলের ডেটা সফলভাবে এক্সট্রাক্ট করা হয়েছে!")

# ৭. এক্সেল ডেটা টেবিল প্রিভিউ এবং ডাউনলোড সেকশন
if not st.session_state.excel_df.empty:
    st.write("### 📊 এক্সেল তালিকা প্রিভিউ (ডেটা সঠিক কিনা থাম্বনেইল দেখে মিলিয়ে নিন, চাইলে বক্সে ডাবল ক্লিক করে এডিট করতে পারবেন):")

    edited_df = st.data_editor(
        st.session_state.excel_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "থাম্বনেইল": st.column_config.ImageColumn("ফর্ম প্রিভিউ", help="মূল ফর্মের ছবি — এন্ট্রির সাথে মিলিয়ে দেখুন")
        }
    )

    if st.button("🗑️ তালিকা পরিষ্কার করুন"):
        st.session_state.excel_df = pd.DataFrame(columns=["ক্রঃনং", "প্রশিক্ষণার্থীর নাম ও পিতার নাম", "জাতীয় পরিচয়পত্র নং", "মোবাইল নম্বর", "জেলা", "থাম্বনেইল"])
        st.rerun()

    # Excel-এ থাম্বনেইলের base64 ডেটা রাখার দরকার নেই (unusable + ফাইল সাইজ বাড়িয়ে দেয়), তাই বাদ দেওয়া হচ্ছে
    export_df = edited_df.drop(columns=["থাম্বনেইল"], errors="ignore")

    towrite = io.BytesIO()
    export_df.to_excel(towrite, index=False, header=True, engine='openpyxl')
    towrite.seek(0)

    st.download_button(
        label="📥 জেনারেট হওয়া Excel ফাইলটি ডাউনলোড করুন",
        data=towrite,
        file_name="BRTC_Driver_Training_List.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
