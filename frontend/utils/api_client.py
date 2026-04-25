#  frontend/utils/api_client.py
import os
import requests

BASE_URL = os.getenv("API_BASE_URL")


def login_api(email, password):
    res = requests.post(
        f"{BASE_URL}/auth/login", json={"email": email, "password": password}
    )
    if res.status_code == 200:
        return True, res.json().get("user_info")
    return False, res.json().get("detail", "로그인 실패")


def signup_api(name, email, password):
    res = requests.post(
        f"{BASE_URL}/auth/signup",
        json={"name": name, "email": email, "password": password},
    )
    if res.status_code == 200:
        return True, "가입 성공"
    return False, res.json().get("detail", "회원가입 처리 중 오류 발생")


def update_password_api(email, new_password):
    res = requests.post(
        f"{BASE_URL}/auth/reset-pw", json={"email": email, "new_password": new_password}
    )
    return res.status_code == 200


def get_user_resume_api(email):
    res = requests.get(f"{BASE_URL}/resume/{email}")
    if res.status_code == 200:
        return res.json().get("resume_data", "{}")
    return "{}"


def update_resume_data_api(email, new_resume_data):
    res = requests.put(f"{BASE_URL}/resume/{email}", json=new_resume_data)
    return res.status_code == 200


def load_chat_history_api(email):
    res = requests.get(f"{BASE_URL}/chat/history/{email}")
    if res.status_code == 200:
        return res.json().get("messages", [])
    return []


def save_chat_message_api(email, role, content):
    # content가 None인 경우 빈 문자열로 처리하여 422 에러 방지
    payload = {"email": email, "role": role, "content": content or ""}
    requests.post(f"{BASE_URL}/chat/message", json=payload)


def delete_chat_history_api(email):
    requests.delete(f"{BASE_URL}/chat/history/{email}")


def parse_request_api(prompt, selected_model):
    res = requests.post(
        f"{BASE_URL}/chat/step-parse", json={"prompt": prompt, "model": selected_model}
    )
    return res.json() if res.status_code == 200 else {}


def generate_exaone_draft_api(parsed_data, user_info, selected_model):
    res = requests.post(
        f"{BASE_URL}/chat/step-draft",
        json={"parsed_data": parsed_data, "user_info": user_info, "model": selected_model},
    )
    return res.json().get("draft") if res.status_code == 200 else None


def revise_existing_draft_api(existing_draft, revision_request, selected_model):
    res = requests.post(
        f"{BASE_URL}/chat/step-revise",
        json={
            "existing_draft": existing_draft,
            "revision_request": revision_request,
            "model": selected_model,
        },
    )
    return res.json().get("revised") if res.status_code == 200 else existing_draft


def refine_with_api_api(draft, parsed_data, selected_model):
    res = requests.post(
        f"{BASE_URL}/chat/step-refine",
        json={"draft": draft, "parsed_data": parsed_data, "model": selected_model},
    )
    return res.json().get("refined") if res.status_code == 200 else draft


def fit_length_api(refined, parsed_data, selected_model):
    res = requests.post(
        f"{BASE_URL}/chat/step-fit",
        json={"refined": refined, "parsed_data": parsed_data, "model": selected_model},
    )
    return res.json().get("adjusted") if res.status_code == 200 else refined


def build_final_response_api(
    adjusted, parsed_data, selected_model, result_label="자소서 초안", change_summary=None
):
    payload = {
        "adjusted": adjusted,
        "parsed_data": parsed_data,
        "model": selected_model,
        "result_label": result_label,
        "change_summary": change_summary,
    }
    res = requests.post(f"{BASE_URL}/chat/step-final", json=payload)
    return res.json().get("final_response") if res.status_code == 200 else adjusted
