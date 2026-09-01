import streamlit as st
import pandas as pd
import io
import json
import requests
import base64
import time

# ১. পেজ কনফিগারেশন ও সিএসএস দিয়ে গ্রিন থিম বজায় রাখা
st.set_page_config(page_title="BRTC Form Extractor Pro", layout="wide")

st.markdown("""
    <style>
    .main-header {
        background-color: #007A33;
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 25px;
    }
    </style>
    <div class="main-header">
        <h2>📄 BRTC Form Extractor Pro</h2>
        <p>বিআরটিসি বাস ডিপো ও প্রশিক্ষণ কেন্দ্র, দিনাজপুর</p>
    </div>
""", unsafe_allow_html=True)

# ২. সাইডবারে এপিআই কি ইনপুট
api_key = st.sidebar.text_input("🔑 আপনার Gemini API Key দিন", type="password")

# ৩. সেশন স্টেটে এক্সেল ডাটা ফ্রেম ইনিশিয়েলাইজ করা
if 'excel_df' not in st.session_state:
    st.session_state.excel_df = pd.DataFrame(columns=["ক্রঃনং", "প্রশিক্ষণার্থীর নাম ও পিতার নাম", "জাতীয় পরিচয়পত্র নং", "মোবাইল নম্বর", "জেলা"])

# ৪. ফাইল আপলোডার (Image এবং PDF একসাথে সাপোর্ট করবে)
uploaded_files = st.file_uploader("আপনার PDF বা Image ফর্মগুলো আপলোড করুন (একাধিক ফাইল একসাথে সিলেক্ট করতে পারবেন)", type=["jpg", "jpeg", "png", "pdf"], accept_multiple_files=True)

if uploaded_files:
    if st.button("🚀 ডেটা এক্সট্রাক্ট এবং এক্সেল তালিকায় যোগ করুন"):
        if not api_key:
            st.error("অনুগ্রহ করে সাইডবারে আপনার Gemini API Key-টি প্রদান করুন।")
        else:
            for uploaded_file in uploaded_files:
                with st.spinner(f"{uploaded_file.name} প্রসেস করা হচ্ছে..."):
                    try:
                        file_bytes = uploaded_file.read()

                        # ফাইলের সঠিক এক্সটেনশন অনুযায়ী MIME Type নির্ধারণ
                        file_name_lower = uploaded_file.name.lower()
                        if file_name_lower.endswith('.pdf'):
                            mime_type = "application/pdf"
                        elif file_name_lower.endswith('.png'):
                            mime_type = "image/png"
                        elif file_name_lower.endswith('.webp'):
                            mime_type = "image/webp"
                        else:
                            mime_type = "image/jpeg"

                        # ফাইল ডেটাকে বেইজ৬৪ ফরম্যাটে রূপান্তর
                        base64_data = base64.b64encode(file_bytes).decode("utf-8")

                        # সঠিক Gemini API URL (FIX: আগের ভার্সনে এখানে বাগ ছিল -
                        # api_key সরাসরি "googleapis.com" এর সাথে জোড়া লেগে যাচ্ছিল,
                        # যার ফলে DNS resolve করতে পারছিল না)
                        model_name = "gemini-3.6-flash"  # নতুন API key-এর জন্য Google এই মডেল সরাসরি রিকমেন্ড করেছে
                        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

                        headers = {"Content-Type": "application/json"}

                        prompt = """
                        You are an expert OCR and data extraction AI. Extract data from this BRTC Driver Training form.
                        Find the applicant's name in Bangla (প্রশিক্ষণার্থীর নাম), father's name in Bangla (পিতার নাম), National ID number (জাতীয় পরিচয়পত্র নং), and Mobile number (মোবাইল নম্বর).
                        Also, identify the district/location name from the center name at the top (e.g., দিনাজপুর).

                        Strictly format the Mobile number by keeping the last 9 or 11 digits and stripping hyphens based on user example.

                        You MUST output ONLY a valid JSON object matching the keys below. Do not include markdown code blocks like ```json or any trailing words.
                        {
                            "name": "Exact Name in Bangla",
                            "father": "Exact Father Name in Bangla",
                            "nid": "NID Number String",
                            "mobile": "Mobile Number String",
                            "district": "দিনাজপুর"
                        }
                        """

                        payload = {
                            "contents": [
                                {
                                    "parts": [
                                        {"text": prompt},
                                        {
                                            "inline_data": {
                                                "mime_type": mime_type,
                                                "data": base64_data
                                            }
                                        }
                                    ]
                                }
                            ]
                        }

                        # সরাসরি HTTP পোস্ট রিকোয়েস্ট পাঠানো (High demand/temporary error হলে অটো-রিট্রাই করবে)
                        max_retries = 4
                        response_json = None
                        for attempt in range(max_retries):
                            response = requests.post(url, headers=headers, json=payload)
                            response_json = response.json()

                            # এরর আছে কিনা চেক করা
                            error_info = response_json.get("error") if isinstance(response_json, dict) else None

                            if not error_info:
                                break  # সফল হয়েছে, লুপ থেকে বের হয়ে যাও

                            error_message = str(error_info.get("message", error_info))
                            # শুধু temporary/high-demand/overload/rate-limit টাইপ এরর হলে রিট্রাই করবে
                            is_temporary = any(keyword in error_message.lower() for keyword in
                                                ["high demand", "overload", "unavailable", "try again",
                                                 "rate limit", "quota", "503", "429"])

                            if is_temporary and attempt < max_retries - 1:
                                wait_seconds = (attempt + 1) * 5  # ৫, ১০, ১৫... সেকেন্ড করে wait বাড়বে
                                st.warning(f"⏳ {uploaded_file.name}: সার্ভারে বেশি চাপ আছে, {wait_seconds} সেকেন্ড পর আবার চেষ্টা করা হচ্ছে... (Attempt {attempt + 1}/{max_retries})")
                                time.sleep(wait_seconds)
                                continue
                            else:
                                # temporary না হলে বা শেষ চেষ্টাও ব্যর্থ হলে, এরর তুলে দাও
                                raise Exception(error_message)

                        # এআই-এর রেসপন্স থেকে টেক্সট এক্সট্রাক্ট করা
                        # FIX: candidates এবং parts আসলে list, তাই [0] ইনডেক্স লাগবে
                        response_text = response_json['candidates'][0]['content']['parts'][0]['text']

                        # রেসপন্স টেক্সট ক্লিন এবং JSON পার্স করা
                        clean_json = response_text.replace("```json", "").replace("```", "").strip()
                        data_json = json.loads(clean_json)

                        # নতুন ক্রঃনং এবং ফরম্যাটিং হিসাব করা
                        current_sl = len(st.session_state.excel_df) + 1
                        formatted_name_father = f"নাম- {data_json.get('name')}   পিতা- {data_json.get('father')}"

                        # নতুন রো বা সারি তৈরি করা
                        new_row = {
                            "ক্রঃনং": current_sl,
                            "প্রশিক্ষণার্থীর নাম ও পিতার নাম": formatted_name_father,
                            "জাতীয় পরিচয়পত্র নং": str(data_json.get('nid')),
                            "মোবাইল নম্বর": str(data_json.get('mobile')),
                            "জেলা": data_json.get('district')
                        }

                        # মূল তালিকার সাথে যুক্ত করা
                        st.session_state.excel_df = pd.concat([st.session_state.excel_df, pd.DataFrame([new_row])], ignore_index=True)

                    except Exception as e:
                        st.error(f"{uploaded_file.name} প্রসেস করতে ত্রুটি হয়েছে: {str(e)}")

            st.success("✅ সব ফাইলের ডেটা সফলভাবে এক্সট্রাক্ট করা হয়েছে!")

# ৫. এক্সেল ডেটা টেবিল প্রিভিউ এবং ডাউনলোড সেকশন
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
