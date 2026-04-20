import os
import streamlit as st
import requests

API_BASE_URL = os.getenv("API_BASE_URL")

st.title("Job Pocket - Health Check")

try:
    res = requests.get(f"{API_BASE_URL}/health/z")
    data = res.json()
    st.json(data)
except Exception as e:
    st.error(f"API 연결 실패: {e}")