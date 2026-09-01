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
    @import url('https://fonts.googleapis.com/css2?family=Tiro+Bangla&family=Hind+Siliguri:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

    :root {
        --paper: #F6F1E4;
        --ledger-line: #D9CFB4;
        --ink: #211D17;
        --green-deep: #0B5C3C;
        --red-stamp: #B3392C;
    }

    .stApp {
        background-color: var(--paper);
    }

    html, body, [class*="css"] {
        font-family: 'Hind Siliguri', sans-serif;
        color: var(--ink);
    }

    /* --- হেডার: লেজার বুকের লেটারহেড --- */
    .main-header {
        position: relative;
        background:
            repeating-linear-gradient(
                var(--paper) 0px, var(--paper) 37px,
                var(--ledger-line) 38px
            );
        border-left: 10px solid var(--green-deep);
        border-radius: 2px;
        padding: 28px 32px 28px 28px;
        margin-bottom: 30px;
        box-shadow: 0 1px 3px rgba(33,29,23,0.15);
    }
    .main-header h1 {
        font-family: 'Tiro Bangla', serif;
        font-size: 2.1rem;
        color: var(--green-deep);
        margin: 0 0 6px 0;
    }
    .main-header p {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85rem;
        letter-spacing: 0.5px;
        color: var(--ink);
        opacity: 0.75;
        margin: 0;
    }
    .stamp-badge {
        position: absolute;
        top: 18px;
        right: 28px;
        width: 78px;
        height: 78px;
        border: 3px solid var(--red-stamp);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        transform: rotate(-12deg);
        color: var(--red-stamp);
        font-family: 'JetBrains Mono', monospace;
        font-weight: 600;
        font-size: 0.7rem;
        text-align: center;
        line-height: 1.2;
        opacity: 0.85;
    }

    /* --- বাটন --- */
    .stButton > button {
        background-color: var(--green-deep);
        color: var(--paper);
        border: none;
        border-radius: 2px;
        font-family: 'Hind Siliguri', sans-serif;
        font-weight: 600;
        padding: 0.55rem 1.4rem;
        transition: background-color 0.15s ease;
    }
    .stButton > button:hover {
        background-color: var(--red-stamp);
        color: var(--paper);
    }

    /* --- ফাইল আপলোডার: ফর্ম-ফিলিং এরিয়ার মতো --- */
    [data-testid="stFileUploaderDropzone"] {
        background-color: var(--paper);
        border: 2px dashed var(--green-deep);
        border-radius: 2px;
    }

    /* --- ডেটা টেবিল --- */
    [data-testid="stDataFrame"] {
        border: 1px solid var(--ledger-line);
        font-family: 'JetBrains Mono', monospace;
    }

    /* --- সতর্কতা/সাকসেস/এরর: স্ট্যাম্পের মতো ফ্ল্যাট বর্ডার --- */
    div[data-testid="stAlert"] {
        border-radius: 2px;
        font-family: 'Hind Siliguri', sans-serif;
    }
    div[data-testid="stAlertContentSuccess"] {
        border-left: 6px solid var(--green-deep);
    }
    div[data-testid="stAlertContentError"] {
        border-left: 6px solid var(--red-stamp);
    }

    /* --- সাইডবার --- */
    [data-testid="stSidebar"] {
        background-color: #EFE8D4;
        border-right: 1px solid var(--ledger-line);
    }
    </style>

    <div class="main-header">
        <div class="stamp-badge">BRTC<br>দিনাজপুর</div>
        <h1>BRTC Form Extractor</h1>
        <p>বিআরটিসি বাস ডিপো ও প্রশিক্ষণ কেন্দ্র · দিনাজপুর · রেজিস্টার এন্ট্রি সিস্টেম</p>
    </div>
""", unsafe_allow_html=True)

# ২. সাইডবারে এপিআই কি ইনপুট
api_key = st.sidebar.text_input("🔑 আপনার Gemini API Key দিন", type="password")

# ৩. সেশন স্টেটে এক্সেল ডাটা ফ্রেম ইনিশিয়েলাইজ করা
if 'excel_df' not in st.session_state:
    st.session_state.excel_df = pd.DataFrame(columns=["ক্রঃনং", "প্রশিক্ষণার্থীর নাম ও পিতার নাম", "জাতীয় পরিচয়পত্র নং", "মোবাইল নম্বর", "জেলা"])

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

            st.warning(f"⏳ {label}: সার্ভারে বেশি চাপ আছে, {wait_seconds} সেকেন্ড পর আবার চেষ্টা করা হচ্ছে... (Attempt {attempt + 1}/{max_retries})")
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


# ৫. একটা PDF-কে আলাদা আলাদা পেজে ভেঙে দেওয়ার ফাংশন
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


# ৬. ফাইল আপলোডার (Image এবং PDF একসাথে সাপোর্ট করবে)
uploaded_files = st.file_uploader("আপনার PDF বা Image ফর্মগুলো আপলোড করুন (একাধিক ফাইল একসাথে সিলেক্ট করতে পারবেন)", type=["jpg", "jpeg", "png", "pdf"], accept_multiple_files=True)

if uploaded_files:
    if st.button("🚀 ডেটা এক্সট্রাক্ট এবং এক্সেল তালিকায় যোগ করুন"):
        if not api_key:
            st.error("অনুগ্রহ করে সাইডবারে আপনার Gemini API Key-টি প্রদান করুন।")
        else:
            for uploaded_file in uploaded_files:
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
                    progress_bar = st.progress(0, text=f"{uploaded_file.name}: শুরু হচ্ছে...")

                    all_new_rows = []
                    for page_index, page_bytes in enumerate(page_bytes_list):
                        page_label = f"{uploaded_file.name} (পেজ {page_index + 1}/{total_pages})"
                        progress_bar.progress((page_index) / total_pages, text=f"⏳ {page_label} প্রসেস করা হচ্ছে...")

                        # ফ্রি টিয়ারের rate limit (মিনিটে সীমিত রিকোয়েস্ট) এড়াতে পরপর কলের মাঝে ছোট বিরতি
                        if page_index > 0:
                            time.sleep(4)

                        base64_data = base64.b64encode(page_bytes).decode("utf-8")

                        try:
                            entries_list = extract_entries_from_gemini(base64_data, page_mime, api_key, page_label)
                        except Exception as page_error:
                            st.error(f"{page_label} প্রসেস করতে ত্রুটি হয়েছে: {str(page_error)}")
                            continue

                        for data_json in entries_list:
                            current_sl = len(st.session_state.excel_df) + len(all_new_rows) + 1
                            formatted_name_father = f"নাম- {data_json.get('name')}   পিতা- {data_json.get('father')}"
                            all_new_rows.append({
                                "ক্রঃনং": current_sl,
                                "প্রশিক্ষণার্থীর নাম ও পিতার নাম": formatted_name_father,
                                "জাতীয় পরিচয়পত্র নং": str(data_json.get('nid')),
                                "মোবাইল নম্বর": str(data_json.get('mobile')),
                                "জেলা": data_json.get('district')
                            })

                        progress_bar.progress((page_index + 1) / total_pages, text=f"✅ {page_label} সম্পন্ন")

                    if all_new_rows:
                        st.session_state.excel_df = pd.concat([st.session_state.excel_df, pd.DataFrame(all_new_rows)], ignore_index=True)

                    progress_bar.empty()
                    st.info(f"📄 {uploaded_file.name}: {total_pages} পেজ থেকে {len(all_new_rows)} টি এন্ট্রি পাওয়া গেছে।")

                except Exception as e:
                    st.error(f"{uploaded_file.name} প্রসেস করতে ত্রুটি হয়েছে: {str(e)}")

            st.success("✅ সব ফাইলের ডেটা সফলভাবে এক্সট্রাক্ট করা হয়েছে!")

# ৭. এক্সেল ডেটা টেবিল প্রিভিউ এবং ডাউনলোড সেকশন
if not st.session_state.excel_df.empty:
    st.write("### 📊 এক্সেল তালিকা প্রিভিউ (আপনি চাইলে বক্সে ডাবল ক্লিক করে এডিট করতে পারবেন):")

    edited_df = st.data_editor(st.session_state.excel_df, num_rows="dynamic", use_container_width=True)

    if st.button("🗑️ তালিকা পরিষ্কার করুন"):
        st.session_state.excel_df = pd.DataFrame(columns=["ক্রঃনং", "প্রশিক্ষণার্থীর নাম ও পিতার নাম", "জাতীয় পরিচয়পত্র নং", "মোবাইল নম্বর", "জেলা"])
        st.rerun()

    towrite = io.BytesIO()
    edited_df.to_excel(towrite, index=False, header=True, engine='openpyxl')
    towrite.seek(0)

    st.download_button(
        label="📥 জেনারেট হওয়া Excel ফাইলটি ডাউনলোড করুন",
        data=towrite,
        file_name="BRTC_Driver_Training_List.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
