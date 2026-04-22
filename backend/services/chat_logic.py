import json
import re
import os
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama # runpod 적용 시 제거 예정
from langchain_openai import ChatOpenAI

from langchain_huggingface import HuggingFaceEmbeddings

from .chat_ollama import call_runpod_ollama 

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
SAMPLE_PATH = BASE_DIR / "essay_samples.json"

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from retriever import HybridRetriever

# -----------------------------
# DB 연결 설정
# -----------------------------

DB_CONFIG = {
    'host': os.getenv('VECTOR_DB_URL'),
    'port': 3306,
    'user': os.getenv('MYSQL_VECTOR_USER'),
    'password': os.getenv('MYSQL_VECTOR_PASSWORD'),
    'db': 'job_pocket_vector',
    'charset': 'utf8mb4'    
}

# -----------------------------
# 모델 설정
# -----------------------------

# Ollama = runpod 적용 시 제거 예정
local_llm = ChatOllama(
    model="exaone3.5:7.8b",
    base_url="http://localhost:11434",
    temperature=0.9,
)

llm_gpt = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.55,
)

llm_groq = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0.65,
    top_p=1,
    stop=None,
)

hf_embeddings = HuggingFaceEmbeddings(
    model_name="Qwen/Qwen3-Embedding-0.6B",
    model_kwargs={'device': 'cpu'}, # GPU 없으면 'cpu'
    encode_kwargs={'normalize_embeddings': True}
)

selfintro_retriever = HybridRetriever(
    db_config=DB_CONFIG,
    embeddings=hf_embeddings,
    top_n=3,       
    initial_k=5,
    index_folder= str(ROOT_DIR / "faiss_index_high") # 4/22 추후 드라이브 경로로 수정 예정
)  

OVERSTATEMENT_PATTERNS = [
    "차별화된 경쟁력을 확보",
    "사회적 영향력을 확대",
    "혁신을 선도",
    "업계를 선도",
    "압도적인 성과",
    "무궁한 발전",
    "최고의 인재",
    "실현하겠습니다",
    "주도하겠습니다",
]


# -----------------------------
# 공통 유틸
# -----------------------------
def choose_refine_llm(selected_model: str):
    if "GPT-OSS-120B" in selected_model:
        return llm_groq
    return llm_gpt


def parse_user_profile(user_profile: tuple) -> dict[str, str]:
    resume_str = user_profile[4]

    try:
        resume_data = json.loads(resume_str) if resume_str else {}
    except json.JSONDecodeError:
        resume_data = {}

    personal = resume_data.get("personal", {})
    edu = resume_data.get("education", {})
    add = resume_data.get("additional", {})

    return {
        "gender": personal.get("gender", "선택안함"),
        "school": edu.get("school", "정보 없음"),
        "major": edu.get("major", "정보 없음"),
        "exp": add.get("internship", "정보 없음"),
        "awards": add.get("awards", "정보 없음"),
        "tech": add.get("tech_stack", "정보 없음"),
    }


def clean_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def remove_forbidden_headers(text: str) -> str:
    cleaned = text.strip()

    block_patterns = [
        r"\[평가 및 코멘트\][\s\S]*$",
    ]
    for pattern in block_patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.MULTILINE)

    line_patterns = [
        r"^\[자소서 초안\]\s*",
        r"^\[\d+차 수정안\]\s*",
        r"^초안\s*[:：]\s*",
        r"^본문\s*[:：]\s*",
        r"^반영 사항:\s*.*$",
    ]
    for pattern in line_patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.MULTILINE)

    return cleaned.strip()


def split_sentences_korean(text: str) -> list[str]:
    chunks = re.split(r"(?<=[.!?다요])\s+", text.strip())
    return [c.strip() for c in chunks if c.strip()]


def repetition_ratio(text: str) -> float:
    sentences = split_sentences_korean(text)
    if not sentences:
        return 1.0
    unique_count = len(set(sentences))
    return 1 - (unique_count / len(sentences))


def detect_question_type(user_message: str) -> str:
    text = user_message.lower()

    if any(k in text for k in ["지원 이유", "지원이유", "지원 동기", "지원동기", "왜 지원", "입사 이유"]):
        return "motivation"
    if any(k in text for k in ["입사 후 포부", "포부", "입사후"]):
        return "future_goal"
    if any(k in text for k in ["협업", "팀워크", "같이", "소통"]):
        return "collaboration"
    if any(k in text for k in ["문제 해결", "문제해결", "해결 경험", "어려움", "개선"]):
        return "problem_solving"
    if any(k in text for k in ["성장", "노력", "배운 점", "배움"]):
        return "growth"
    return "general"


def parse_user_request_regex(user_message: str) -> dict[str, Any]:
    text = user_message.strip()

    char_limit = None
    patterns = [
        r"(\d{3,4})\s*자\s*이내",
        r"(\d{3,4})\s*자\s*내외",
        r"(\d{3,4})\s*자\s*정도",
        r"(\d{3,4})\s*자",
        r"(\d{3,4})\s*byte",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                char_limit = int(match.group(1))
                break
            except ValueError:
                pass

    company = ""
    job = ""
    question = ""

    company_match = re.search(r"(회사|기업|지원회사)\s*[:：]\s*(.+)", text)
    if company_match:
        company = company_match.group(2).splitlines()[0].strip()

    job_match = re.search(r"(직무|포지션|지원직무)\s*[:：]\s*(.+)", text)
    if job_match:
        job = job_match.group(2).splitlines()[0].strip()

    natural_patterns = [
        r"(.+?)에\s+(.+?)\s*직무로\s+지원",
        r"(.+?)\s+(.+?)\s*직무에\s+지원",
        r"(.+?)에\s+지원",
    ]

    for idx, pattern in enumerate(natural_patterns):
        match = re.search(pattern, text)
        if match:
            if idx == 0:
                if not company:
                    company = match.group(1).strip()
                if not job:
                    job = match.group(2).strip()
            elif idx == 1:
                if not company:
                    company = match.group(1).strip()
                if not job:
                    job = match.group(2).strip()
            elif idx == 2:
                if not company:
                    company = match.group(1).strip()

    q_patterns = [
        r"(.+?)(?:를|을)\s*물어봤",
        r"문항\s*[:：]\s*(.+)",
        r"질문\s*[:：]\s*(.+)",
    ]
    for pattern in q_patterns:
        match = re.search(pattern, text)
        if match:
            question = match.group(1).strip()
            break

    return {
        "raw": text,
        "company": company,
        "job": job,
        "question": question,
        "char_limit": char_limit,
        "question_type": detect_question_type(text),
    }


def llm_parse_user_request(user_message: str, selected_model: str) -> dict[str, Any]:
    active_llm = choose_refine_llm(selected_model)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """
너는 자기소개서 요청 문장을 구조화하는 파서다.
반드시 JSON만 출력하라.
키는 아래만 사용하라:
company, job, question, char_limit, question_type

규칙:
- 없는 값은 빈 문자열 또는 null
- question_type은 아래 중 하나만:
  motivation, future_goal, collaboration, problem_solving, growth, general
- 사용자의 표현을 과도하게 바꾸지 말고 핵심만 추출
        """),
        ("human", """
사용자 요청:
{user_message}
        """)
    ])

    chain = prompt | active_llm | StrOutputParser()
    raw = chain.invoke({"user_message": user_message}).strip()

    try:
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1:
            raw = raw[start:end + 1]

        data = json.loads(raw)
        return {
            "company": str(data.get("company", "") or "").strip(),
            "job": str(data.get("job", "") or "").strip(),
            "question": str(data.get("question", "") or "").strip(),
            "char_limit": data.get("char_limit", None),
            "question_type": str(data.get("question_type", "") or "").strip() or "general",
        }
    except Exception:
        return {
            "company": "",
            "job": "",
            "question": "",
            "char_limit": None,
            "question_type": "general",
        }


def parse_user_request(user_message: str, selected_model: str = "GPT-4o-mini") -> dict[str, Any]:
    base = parse_user_request_regex(user_message)

    needs_llm = (
        not base["company"]
        or not base["job"]
        or base["question_type"] == "general"
    )

    if needs_llm:
        llm_data = llm_parse_user_request(user_message, selected_model)

        if not base["company"] and llm_data["company"]:
            base["company"] = llm_data["company"]
        if not base["job"] and llm_data["job"]:
            base["job"] = llm_data["job"]
        if not base["question"] and llm_data["question"]:
            base["question"] = llm_data["question"]
        if not base["char_limit"] and llm_data["char_limit"]:
            try:
                base["char_limit"] = int(llm_data["char_limit"])
            except Exception:
                pass
        if base["question_type"] == "general" and llm_data["question_type"]:
            base["question_type"] = llm_data["question_type"]

    if not base["question"]:
        qtype_map = {
            "motivation": "지원한 이유",
            "future_goal": "입사 후 포부",
            "collaboration": "협업 경험",
            "problem_solving": "문제 해결 경험",
            "growth": "성장 과정 또는 노력 경험",
            "general": "자기소개서 문항",
        }
        base["question"] = qtype_map.get(base["question_type"], "자기소개서 문항")

    return base


# -----------------------------
# 샘플 문자열 로딩/패턴 추출
# -----------------------------
def load_raw_samples() -> list[str]:
    if not SAMPLE_PATH.exists():
        return []

    try:
        with open(SAMPLE_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except Exception:
        return []

    if isinstance(raw, list):
        return [str(x).strip() for x in raw if str(x).strip()]
    return []

def retrieve_raw_samples(query: str) -> list[str]:
    search_results = selfintro_retriever.invoke(query)
    return [doc.page_content.strip() for doc in search_results]

def build_sample_excerpt(samples: list[str], max_chars_per_sample: int = 700) -> str:
    trimmed = []
    for idx, sample in enumerate(samples, start=1):
        cleaned = sample.strip()
        if len(cleaned) > max_chars_per_sample:
            cleaned = cleaned[:max_chars_per_sample].rstrip() + "..."
        trimmed.append(f"[샘플 {idx}]\n{cleaned}")
    return "\n\n".join(trimmed)


def summarize_samples(samples: list[str], selected_model: str) -> str:
    if not samples:
        return (
            "공통 강점:\n"
            "- 유사 샘플이 없어 기본 패턴만 참고\n\n"
            "서술 구조:\n"
            "- 사용자의 경험을 중심으로 문항에 직접 답변\n\n"
            "표현 톤:\n"
            "- 담백하고 과장 없는 문장"
        )

    active_llm = choose_refine_llm(selected_model)
    joined = build_sample_excerpt(samples)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """
너는 문자열 형태의 유사 자소서 샘플들에서 패턴을 추출하는 도우미다.
반드시 한국어로만 작성하라.

중요:
- 샘플은 회사 정보가 아니라 표현 패턴 참고용이다.
- 특정 회사나 직무를 추측하지 말라.
- 샘플 문장을 그대로 베끼지 말고 패턴만 요약하라.
- 출력은 아래 형식만 따르라.

출력 형식:
공통 강점:
- ...
- ...
- ...

서술 구조:
- ...
- ...
- ...

표현 톤:
- ...
- ...
- ...

피해야 할 점:
- ...
- ...
        """),
        ("human", """
다음은 유사 지원자 자소서 문자열 샘플이다.

{joined}
        """)
    ])

    chain = prompt | active_llm | StrOutputParser()

    try:
        result = chain.invoke({"joined": joined})
        return clean_text(result)
    except Exception:
        return (
            "공통 강점:\n"
            "- 데이터를 활용 가능한 형태로 정리하는 관심\n"
            "- 기준을 세우고 반복적으로 점검하는 성향\n"
            "- 기술 역량을 실무 경험과 연결하려는 태도\n\n"
            "서술 구조:\n"
            "- 경험을 단순 나열하지 않고 강점과 연결\n"
            "- 프로젝트 경험을 데이터 정리와 전처리 관점으로 풀어냄\n"
            "- 마지막 문단에서 실무 기여 방향으로 마무리\n\n"
            "표현 톤:\n"
            "- 담백하고 실무형 표현\n"
            "- 과장보다 기준과 과정 중심 서술\n"
            "- 기술 사용 경험을 무리 없이 연결하는 문체\n\n"
            "피해야 할 점:\n"
            "- 과장된 포부 표현\n"
            "- 샘플 문장 그대로 재사용"
        )


def extract_sample_style_rules(sample_summary: str, selected_model: str) -> str:
    active_llm = choose_refine_llm(selected_model)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """
너는 샘플 요약을 생성 프롬프트에서 바로 쓸 수 있는 규칙으로 바꾸는 도우미다.
반드시 한국어로만 작성하라.

출력 형식:
작성 규칙:
- ...
- ...
- ...
- ...
        """),
        ("human", """
다음 샘플 요약을 바탕으로 실제 자소서 생성 시 지켜야 할 작성 규칙 4개를 정리해줘.

{sample_summary}
        """)
    ])

    chain = prompt | active_llm | StrOutputParser()

    try:
        return clean_text(chain.invoke({"sample_summary": sample_summary}))
    except Exception:
        return (
            "작성 규칙:\n"
            "- 경험을 단순 나열하지 말고 강점과 연결해 쓸 것\n"
            "- 데이터를 구조화하고 기준을 정리하는 관점이 드러나게 쓸 것\n"
            "- 기술 역량은 실무 활용 경험과 함께 자연스럽게 설명할 것\n"
            "- 문장은 담백하게 유지하고 과장된 표현은 피할 것"
        )


def get_sample_context(selected_model: str, profile: dict[str, Any]) -> dict[str, Any]:
    query = f"""[최종학력] {profile["school"]} {profile['major']}
    [경력 및 경험]
    {profile["exp"]}
    {profile["awards"]}
    [기술 및 역량]
    {profile["tech"]}
    """
    samples = retrieve_raw_samples(query)
    sample_summary = summarize_samples(samples, selected_model)
    style_rules = extract_sample_style_rules(sample_summary, selected_model)

    return {
        "samples": samples,
        "sample_excerpt": build_sample_excerpt(samples),
        "sample_summary": sample_summary,
        "style_rules": style_rules,
    }


# -----------------------------
# 품질 점검
# -----------------------------
def score_local_draft(text: str, parsed_request: dict[str, Any]) -> tuple[bool, str]:
    if not text or len(text.strip()) < 220:
        return False, "초안 길이가 너무 짧습니다."

    ratio = repetition_ratio(text)
    if ratio > 0.48:
        return False, "문장 반복이 많습니다."

    if parsed_request.get("char_limit"):
        target = parsed_request["char_limit"]
        current = len(text)
        if current < max(220, int(target * 0.55)):
            return False, "글자 수가 목표 대비 지나치게 짧습니다."

    if parsed_request.get("question_type") == "motivation":
        company = parsed_request.get("company", "")
        if company and company not in text:
            return False, "지원동기 문항인데 실제 지원 회사명이 반영되지 않았습니다."

        first_para = text.split("\n\n")[0].strip()
        if len(first_para) < 40:
            return False, "첫 문단에서 지원 이유가 충분히 드러나지 않습니다."

    for pattern in OVERSTATEMENT_PATTERNS:
        if pattern in text:
            return False, f"과장 표현이 포함되어 있습니다: {pattern}"

    return True, "통과"


# -----------------------------
# 프롬프트
# -----------------------------
def get_local_system_prompt(question_type: str) -> str:
    common = """
당신은 한국어 자기소개서 초안 작성 도우미다.
반드시 한국어로만 작성하라.

공통 규칙:
- 사용자 정보 안에서만 소재를 고른다.
- 없는 경험, 없는 수치, 없는 성과를 절대 추가하지 않는다.
- 샘플은 회사 정보가 아니라 표현 패턴 참고용이다.
- 샘플 문장을 복사하거나 부분적으로 이어 붙이지 말라.
- 실제 회사 정보는 사용자 입력 범위만 반영하라.
- 회사에 대한 구체 사업 내용이나 내부 프로젝트는 추측하지 말라.
- 문체는 담백하면서도 설득력 있게 유지하라.
- 자기소개서 본문만 작성하라.
- 사용자의 경험을 단순 나열하지 말고, 문항과 연결되는 이유를 분명히 드러내라.
- 너무 짧거나 메마르게 쓰지 말고, 2~3문단 정도로 자연스럽게 구성하라.
- 과장된 기업 홍보 문구처럼 쓰지 말라.
- '차별화된 경쟁력 확보', '사회적 영향력 확대', '혁신을 선도' 같은 표현은 피하라.
"""

    if question_type == "motivation":
        return common + """
이 문항은 지원동기 문항이다.

반드시 아래 흐름을 우선하라:
1. 실제 지원 회사와 직무에 관심을 갖게 된 이유를 먼저 밝힌다.
2. 그 관심이 사용자의 경험이나 관점과 어떻게 이어지는지 구체적으로 보여준다.
3. 마지막은 입사 후 어떤 방식으로 기여하고 싶은지로 마무리한다.

중요:
- 첫 문장이 곧바로 지원 이유가 되게 써라.
- 사용자의 강점이 단순 분석이 아니라 데이터 구조화, 기준 정리, 활용 가능한 형태로 연결하는 관점으로 보이게 하라.
- 마지막 문단은 과장된 포부 대신 현실적인 기여 방식으로 끝내라.
"""
    if question_type == "future_goal":
        return common + """
이 문항은 입사 후 포부 문항이다.
현재 경험을 바탕으로 입사 후 배우고 기여할 방향을 구체적으로 써라.
"""
    if question_type == "collaboration":
        return common + """
이 문항은 협업 문항이다.
역할 분담보다 기준 정렬, 전달 조율, 연결을 중심으로 써라.
"""
    if question_type == "problem_solving":
        return common + """
이 문항은 문제 해결 문항이다.
문제 인식 → 원인 파악 → 기준 정리 → 해결 방식 → 결과 흐름으로 써라.
"""
    if question_type == "growth":
        return common + """
이 문항은 성장/노력 문항이다.
무엇을 배우려 했고, 어떤 기준을 새로 세웠는지가 드러나게 써라.
"""
    return common + """
문항 의도에 맞는 흐름을 먼저 세우고 가장 관련 있는 경험 중심으로 써라.
"""


def get_refine_system_prompt(question_type: str) -> str:
    common = """
당신은 한국어 자기소개서 첨삭 전문가다.
역할은 새로 쓰는 것이 아니라, 이미 작성된 초안을 더 설득력 있게 다듬는 것이다.

공통 규칙:
- 반드시 한국어로만 작성
- 없는 경험, 없는 수치, 없는 성과 추가 금지
- 문체는 담백하면서도 설득력 있게 유지
- 반복 표현과 어색한 연결을 정리
- 제목, 평가, 설명문 없이 본문만 출력
- 지나치게 축약해 글의 힘이 빠지지 않게 할 것
- 과장된 표현이나 기업 홍보 문구처럼 보이는 문장은 줄일 것
- 실제 회사 정보는 사용자 입력 범위를 넘어서 추측하지 말 것
"""

    if question_type == "motivation":
        return common + """
지원동기 문항에서는 아래를 우선 점검하라:
- 첫 문장이 회사 지원 이유로 바로 시작하는가
- 실제 지원 회사/직무와 사용자 경험이 자연스럽게 이어지는가
- 사용자의 강점이 '분석 결과 제시'보다 '구조와 기준 정리' 쪽으로 드러나는가
- 마지막이 추상적 다짐이 아니라 실제 기여 방향으로 끝나는가
"""
    return common


# -----------------------------
# 생성 단계
# -----------------------------
def build_local_draft(user_message: str, user_profile: tuple, selected_model: str = "GPT-4o-mini") -> str:
    profile = parse_user_profile(user_profile)
    parsed = parse_user_request(user_message, selected_model)
    sample_context = get_sample_context(selected_model, profile) #profile 정보 기반 sample 검색

    prompt = ChatPromptTemplate.from_messages([
        ("system", get_local_system_prompt(parsed["question_type"])),
        ("human", """
[지원자 정보]
- 성별: {gender}
- 학교: {school}
- 전공: {major}
- 직무 관련 경험: {exp}
- 수상 및 대외활동: {awards}
- 기술 스택 / 자격증: {tech}

[사용자 요청 원문]
{user_message}

[실제 지원 정보]
- 실제 지원 회사명: {company}
- 실제 지원 직무명: {job}
- 문항: {question}
- 문항 유형: {question_type}
- 글자 수 제한: {char_limit}

[유사 샘플 패턴 요약]
{sample_summary}

[샘플 기반 작성 규칙]
{style_rules}

[유사 샘플 원문 발췌]
{sample_excerpt}

요구사항:
- 샘플은 표현 패턴과 강점 서술 방식을 참고하는 용도로만 활용하라.
- 실제 회사명과 직무명은 사용자 입력 기준으로만 반영하라.
- 샘플 문장을 베끼지 말고, 사용자 이력으로 새롭게 써라.
- 사용자를 단순히 분석 툴을 쓴 사람처럼 쓰지 말고, 데이터를 구조화하고 기준을 정리해 활용 가능한 형태로 연결한 사람처럼 보이게 하라.
- 자기소개서 본문 초안만 써라.
        """)
    ])

    chain = prompt | local_llm | StrOutputParser()
    result = chain.invoke({
        "gender": profile["gender"],
        "school": profile["school"],
        "major": profile["major"],
        "exp": profile["exp"],
        "awards": profile["awards"],
        "tech": profile["tech"],
        "user_message": parsed["raw"],
        "company": parsed["company"] or "미기재",
        "job": parsed["job"] or "미기재",
        "question": parsed["question"] or "미기재",
        "question_type": parsed["question_type"],
        "char_limit": parsed["char_limit"] or "미기재",
        "sample_summary": sample_context["sample_summary"],
        "style_rules": sample_context["style_rules"],
        "sample_excerpt": sample_context["sample_excerpt"] or "없음",
    })

    return clean_text(remove_forbidden_headers(result))

# 4/21 runpod serverless 대응 수정
def build_draft_with_ollama(user_message: str, user_profile: tuple, selected_model: str = "GPT-4o-mini") -> str:
    profile = parse_user_profile(user_profile)
    parsed = parse_user_request(user_message, selected_model)
    sample_context = get_sample_context(selected_model, profile) #profile 정보 기반 sample 검색

    prompt = ChatPromptTemplate.from_messages([
        ("system", get_local_system_prompt(parsed["question_type"])),
        ("human", """
[지원자 정보]
- 성별: {gender}
- 학교: {school}
- 전공: {major}
- 직무 관련 경험: {exp}
- 수상 및 대외활동: {awards}
- 기술 스택 / 자격증: {tech}

[사용자 요청 원문]
{user_message}

[실제 지원 정보]
- 실제 지원 회사명: {company}
- 실제 지원 직무명: {job}
- 문항: {question}
- 문항 유형: {question_type}
- 글자 수 제한: {char_limit}

[유사 샘플 패턴 요약]
{sample_summary}

[샘플 기반 작성 규칙]
{style_rules}

[유사 샘플 원문 발췌]
{sample_excerpt}

요구사항:
- 샘플은 표현 패턴과 강점 서술 방식을 참고하는 용도로만 활용하라.
- 실제 회사명과 직무명은 사용자 입력 기준으로만 반영하라.
- 샘플 문장을 베끼지 말고, 사용자 이력으로 새롭게 써라.
- 사용자를 단순히 분석 툴을 쓴 사람처럼 쓰지 말고, 데이터를 구조화하고 기준을 정리해 활용 가능한 형태로 연결한 사람처럼 보이게 하라.
- 자기소개서 본문 초안만 써라.
        """)
    ])

    final_prompt = prompt.invoke({
        "gender": profile["gender"],
        "school": profile["school"],
        "major": profile["major"],
        "exp": profile["exp"],
        "awards": profile["awards"],
        "tech": profile["tech"],
        "user_message": parsed["raw"],
        "company": parsed["company"] or "미기재",
        "job": parsed["job"] or "미기재",
        "question": parsed["question"] or "미기재",
        "question_type": parsed["question_type"],
        "char_limit": parsed["char_limit"] or "미기재",
        "sample_summary": sample_context["sample_summary"],
        "style_rules": sample_context["style_rules"],
        "sample_excerpt": sample_context["sample_excerpt"] or "없음",
    })
    
    
    result = call_runpod_ollama(final_prompt.to_messages()) #runpod 호출로 생성된 답변 받아옴
    return clean_text(remove_forbidden_headers(result))

def regenerate_local_draft_if_needed(
    user_message: str,
    user_profile: tuple,
    selected_model: str = "GPT-4o-mini",
    max_attempts: int = 3,
) -> str:
    parsed = parse_user_request(user_message, selected_model)
    last_text = ""
    working_message = user_message

    for attempt in range(max_attempts):
        draft = build_local_draft(working_message, user_profile, selected_model) #build_draft_with_ollama(working_message, user_profile, selected_model)
        is_ok, reason = score_local_draft(draft, parsed)
        last_text = draft

        if is_ok:
            return draft

        if attempt < max_attempts - 1:
            working_message = (
                user_message
                + f"\n\n추가 지시: 이전 초안은 '{reason}' 문제가 있었어. "
                  "실제 지원 회사명과 직무가 더 선명하게 드러나게 하고, "
                  "사용자의 강점이 단순 분석이 아니라 데이터 구조화와 기준 정리 쪽으로 보이게 다시 써줘. "
                  "샘플은 참고만 하고 문장은 새롭게 써줘."
            )

    return last_text


def refine_with_api(local_draft_body: str, user_message: str, selected_model: str) -> str:
    parsed = parse_user_request(user_message, selected_model)
    active_llm = choose_refine_llm(selected_model)

    prompt = ChatPromptTemplate.from_messages([
        ("system", get_refine_system_prompt(parsed["question_type"])),
        ("human", """
[사용자 요청]
{user_message}

[실제 지원 정보]
- 실제 지원 회사명: {company}
- 실제 지원 직무명: {job}
- 문항: {question}
- 문항 유형: {question_type}
- 글자 수 제한: {char_limit}

[초안 본문]
{local_draft_body}

요구사항:
- 초안의 방향은 유지하되 문장을 더 자연스럽고 설득력 있게 다듬어라.
- 사용자의 경험이 실제 지원 회사/직무와 왜 맞닿는지 연결감을 살려라.
- 사용자의 강점이 구조와 기준 정리, 실무 연결 관점으로 보이게 하라.
- 문장을 지나치게 축약해 힘이 빠지지 않게 하라.
- 과장 표현은 줄이고, 현실적인 기여 방식으로 정리하라.
        """)
    ])

    chain = prompt | active_llm | StrOutputParser()
    result = chain.invoke({
        "user_message": parsed["raw"],
        "company": parsed["company"] or "미기재",
        "job": parsed["job"] or "미기재",
        "question": parsed["question"] or "미기재",
        "question_type": parsed["question_type"],
        "char_limit": parsed["char_limit"] or "미기재",
        "local_draft_body": local_draft_body,
    })

    return clean_text(remove_forbidden_headers(result))


def revise_existing_draft(existing_draft: str, revision_request: str, selected_model: str = "GPT-4o-mini") -> str:
    active_llm = choose_refine_llm(selected_model)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """
당신은 한국어 자기소개서 수정 전문가다.
반드시 한국어로만 작성하라.

역할:
- 기존 초안을 버리지 말고 수정 요청에 맞춰 다듬는다.
- 요청이 특정 문단, 특정 문장, 특정 톤을 가리키면 그 부분을 우선 반영한다.
- 없는 경험, 없는 수치, 없는 성과를 추가하지 않는다.
- 제목, 평가, 설명문 없이 본문만 출력한다.
- 수정된 결과는 자연스럽게 이어지는 완성된 자기소개서 본문이어야 한다.
- 수정 후에도 지나치게 짧아지지 않게 하고, 전체 흐름을 유지하라.
- 과장 표현은 줄이고, 사용자의 강점이 구조와 기준 정리 쪽으로 드러나게 하라.
        """),
        ("human", """
[기존 결과]
{existing_draft}

[수정 요청]
{revision_request}

요구사항:
- 수정 요청을 반영한 전체 본문을 다시 써라.
- 단, 불필요하게 전체를 새로 갈아엎지 말고 요청한 방향 중심으로 수정하라.
        """)
    ])

    chain = prompt | active_llm | StrOutputParser()
    result = chain.invoke({
        "existing_draft": existing_draft,
        "revision_request": revision_request,
    })

    return clean_text(remove_forbidden_headers(result))


def fit_length_if_needed(text: str, user_message: str, selected_model: str) -> str:
    parsed = parse_user_request(user_message, selected_model)
    target = parsed.get("char_limit")

    if not target:
        return text

    current = len(text)
    lower = int(target * 0.9)
    upper = int(target * 1.05)

    if lower <= current <= upper:
        return text

    active_llm = choose_refine_llm(selected_model)

    direction = (
        "조금 더 압축해 주세요."
        if current > upper
        else "조금 더 내용을 보강해 주세요. 단, 없는 경험은 추가하지 마세요."
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", """
당신은 한국어 자기소개서 문장 길이 조정 전문가다.

규칙:
- 반드시 한국어로만 작성
- 사실관계 유지
- 없는 경험, 수치, 성과 추가 금지
- 문체는 담백하면서도 설득력 있게 유지
- 제목, 설명문 없이 본문만 출력
- 목표 글자 수에 최대한 맞출 것
- 문장을 줄이더라도 글의 핵심 설득력은 남길 것
- 과장 표현은 줄일 것
        """),
        ("human", """
[사용자 요청]
{user_message}

[현재 본문]
{text}

[목표]
- 목표 글자 수: {target}자
- 현재 글자 수: {current}자
- 요청: {direction}
        """)
    ])

    chain = prompt | active_llm | StrOutputParser()
    adjusted = chain.invoke({
        "user_message": parsed["raw"],
        "text": text,
        "target": target,
        "current": current,
        "direction": direction,
    })

    return clean_text(remove_forbidden_headers(adjusted))


# -----------------------------
# 평가 전용 API
# -----------------------------
def evaluate_draft_with_api(
    body: str,
    user_message: str,
    selected_model: str = "GPT-4o-mini",
    is_revision: bool = False,
) -> str:
    parsed = parse_user_request(user_message, selected_model)
    active_llm = choose_refine_llm(selected_model)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """
당신은 한국어 자기소개서 평가 전문가다.
반드시 한국어로만 작성하라.

역할:
- 주어진 자소서 본문을 평가하고, 사용자에게 도움이 되는 짧은 피드백을 만든다.
- 절대 과장하거나 허위 칭찬하지 말고, 실제 문장을 기준으로 평가하라.
- 출력은 아래 형식만 따르라.

출력 형식:
평가 결과: <좋다 / 보통 / 아쉬움>
이유: <한 문장>
보완 포인트:
- <포인트 1>
- <포인트 2>

규칙:
- 2개의 보완 포인트만 작성
- 보완 포인트는 실제 수정에 바로 쓸 수 있게 구체적이고 짧게 작성
- 'AI 표절률', '유사도', '탐지율' 같은 표현은 절대 쓰지 말 것
- 실제 회사 정보는 사용자 입력 범위를 넘어서 추측하지 말 것
        """),
        ("human", """
[사용자 요청]
{user_message}

[실제 지원 정보]
- 실제 지원 회사명: {company}
- 실제 지원 직무명: {job}
- 문항: {question}
- 문항 유형: {question_type}

[평가 대상 본문]
{body}

[평가 관점]
- 문항 적합성
- 직무 적합성
- 사용자 이력 반영도
- 첫 문장 완성도
- 마지막 문단 완성도
- 과장 표현 여부
- 수정본이면 요청 방향 반영 여부
        """)
    ])

    chain = prompt | active_llm | StrOutputParser()
    result = chain.invoke({
        "user_message": parsed["raw"],
        "company": parsed["company"] or "미기재",
        "job": parsed["job"] or "미기재",
        "question": parsed["question"] or "미기재",
        "question_type": parsed["question_type"],
        "body": body,
    })

    return clean_text(result)


def fallback_evaluation_comment(body: str, is_revision: bool = False) -> str:
    current_len = len(body)
    result_label = "좋다" if current_len >= 300 else "보통"

    reason = (
        "요청한 수정 방향이 문장 흐름에 반영되도록 정리했습니다."
        if is_revision
        else "문항 의도와 사용자 경험이 자연스럽게 이어지도록 정리했습니다."
    )

    return (
        f"평가 결과: {result_label}\n"
        f"이유: {reason}\n"
        "보완 포인트:\n"
        "- 첫 문장을 조금 더 구체적으로 다듬어 보세요.\n"
        "- 마지막 문단의 기여 방향을 조금 더 현실적인 표현으로 정리하면 좋습니다."
    )


# -----------------------------
# 최종 포맷 조립
# -----------------------------
def build_final_response(
    body: str,
    user_message: str,
    selected_model: str = "GPT-4o-mini",
    result_label: str = "자소서 초안",
    change_summary: str | None = None,
) -> str:
    is_revision = result_label.endswith("수정안")

    try:
        evaluation_text = evaluate_draft_with_api(
            body=body,
            user_message=user_message,
            selected_model=selected_model,
            is_revision=is_revision,
        )
    except Exception:
        evaluation_text = fallback_evaluation_comment(body=body, is_revision=is_revision)

    lines = [f"[{result_label}]", ""]

    if change_summary:
        lines.append(f"반영 사항: {change_summary}")
        lines.append("")

    lines.append(body)
    lines.append("")
    lines.append("[평가 및 코멘트]")
    lines.append(evaluation_text)

    return "\n".join(lines).strip()