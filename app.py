"""
더 커뮤니티: 워홀녀편 — 수업 연구용 판단 경향 테스트 (Streamlit)

실행: streamlit run app.py
흐름: 시작 → E(7) → A2 → A1 → B(7) → C(2) → D(3) → 결과 → 개입 1~4 → 사후 1~2 → 마무리
"""

import csv
import json
import urllib.request
import uuid
from datetime import datetime
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

# ─────────────────────────────────────────────
# 0. 기본 설정
# ─────────────────────────────────────────────
st.set_page_config(page_title="더 커뮤니티: 워홀녀편", page_icon="🔍", layout="centered")

APP_DIR = Path(__file__).parent
IMAGE_PATH = APP_DIR / "insta-post.png"
RESPONSES_CSV = APP_DIR / "responses.csv"

# 결과 유형 기준값 (파일럿 후 조정)
A_CUTOFF = 0.8   # A 정답률 80% 이상 = 구별 잘함
B_CUTOFF = 2.5   # B 평균 2.5 이상 = 동의 높음

# ─────────────────────────────────────────────
# 1. 문항 정의 (문구를 바꿀 땐 여기만 고치면 됨)
# ─────────────────────────────────────────────
LIKERT_E = ["매우 그렇다", "약간 그렇다", "약간 그렇지 않다", "전혀 그렇지 않다"]
LIKERT_AGREE = ["매우 동의", "약간 동의", "약간 비동의", "전혀 동의하지 않음"]
A_CHOICES = ["확인할 수 있음", "짐작한 내용"]

E_ITEMS = [
    ("E1", "온라인 커뮤니티에서 새롭게 접하는 특정 주제에 대한 부정적인 의견에 많은 사람이 동의한다면, 그것이 단순한 편견만으로 그런 여론이 형성되었다고 보기는 어렵다고 생각한다."),
    ("E2", "해외에 거주한 경험이 있는 사람은 새로운 환경에 적응을 잘 할 가능성이 높다고 생각한다."),
    ("E3", "특정 집단의 일부가 사회적으로 비판받는 행동을 했다면, 그 집단의 다른 사람도 비슷한 행동을 했을/할 가능성이 있다고 생각한다."),
    ("E4", "나는 SNS 및 온라인 커뮤니티에서 얻은 정보를 쉽게 수용하는 편이다."),
    ("E5", "어떤 사람에 대한 좋지 않은 평판을 들으면, 그 사람을 실제로 알기 전에 어느 정도의 판단을 내리는 편이다."),
    ("E6", "누군가에 대한 첫인상은 새로운 정보를 접해도 쉽게 바뀌지 않는 편이다."),
    ("E7", "주변에서 비슷한 이야기를 여러 번 들으면, 어느 정도 사실일 가능성이 있다고 생각한다."),
]

# (키, 문장, 정답) — 정답: "fact" = 확인 가능 / "infer" = 짐작
A2_ITEMS = [
    ("A2_1", "이 사람은 셰어하우스에서 다른 사람들과 함께 살았다.", "fact"),
    ("A2_2", "이 사람은 남자와 같은 집에서 살았다.", "infer"),
    ("A2_3", "이 사람은 호주에서 파티를 자주 즐겼다.", "infer"),
    ("A2_4", "이 사람은 셰어하우스 사람들과 사이가 좋았다.", "infer"),
    ("A2_5", "이 사람은 멜버른에 머문 적이 있다.", "fact"),
]

A1_STORY = (
    "서연은 호주에서 워킹홀리데이를 했다. 현지 식당에서 아르바이트를 했으며, "
    "퇴근 후에는 함께 일하는 다양한 국적의 동료들과 식사를 하기도 했다. "
    "어느 날 SNS에 외국인 남성과 포옹하고 있는 사진을 올리며 '좋은 추억 만들어줘서 고마워!'라는 글을 남겼다."
)
A1_ITEMS = [
    ("A1_1", "서연은 호주의 현지 식당에서 근무했다.", "fact"),
    ("A1_2", "해당 사진 속 남성은 서연과 친구 이상의 긴밀한 관계이다.", "infer"),
    ("A1_3", "서연은 외국인과의 연애에 개방적이다.", "infer"),
    ("A1_4", "서연은 외국인 동료들과 식사를 한 경험이 있다.", "fact"),
    ("A1_5", "서연은 외향적인 성향이다.", "infer"),
]

A3_STORY = (
    "하은은 뉴질랜드에서 워킹홀리데이를 하며 농장에서 약 4개월간 일했다. "
    "일을 마친 뒤에는 다른 지역으로 이동해 여행을 했으며, SNS에는 현지 펍에서 "
    "친구들과 함께 찍은 사진과 여행 중 방문한 자연경관 사진을 게시했다."
)
A3_ITEMS = [
    ("A3_1", "하은은 뉴질랜드 농장에서 근무한 경험이 있다.", "fact"),
    ("A3_2", "하은은 평소 술자리를 즐기고 유흥에 관심이 많다.", "infer"),
    ("A3_3", "하은은 한 지역, 한 직종에 정착하는 것보다는 다양한 경험을 더 중요시하는 성격이다.", "infer"),
    ("A3_4", "하은은 현지에서 친구들과 여가 시간을 보낸 적이 있다.", "fact"),
    ("A3_5", "하은은 자유분방하고 규칙에 얽매이는 것을 싫어한다.", "infer"),
]

COMMENT = "워홀 다녀온 여자는 거르라던데"
B1_TEXT = "이 댓글의 의견에 어느 정도 동의하나요?"
B_STATEMENTS = [  # B1 다음 순서 (수위 낮은 것 → 높은 것)
    ("B7", "온라인에서 워홀 여성에 대해 떠도는 부정적인 반응들이 완전히 근거 없는 소문만은 아닐 것이라고 생각한다."),
    ("B2", "다른 정보가 없더라도 워킹홀리데이 경험을 이유로 그 여성을 교제 상대로 꺼리는 것은 타당하다고 생각한다."),
    ("B4", "워킹홀리데이를 다녀온 일부 여성에게서 부정적인 사례가 실제로 나타났다면, 워킹홀리데이를 다녀온 여성 전체를 부정적으로 평가하는 것은 타당하다."),
    ("B5", "워홀을 다녀온 여성이라는 사실만으로 그 여성의 사생활을 평가하는 것은 어느 정도 이해가 된다."),
    ("B3", "워킹홀리데이를 다녀온 여성에 대한 사회적 시선이 안 좋은 것은, 그들 스스로가 제공한 원인도 크다."),
    ("B6", "워킹홀리데이 중 이성과 자유롭게 교류하는 행동은 남성보다 여성의 경우 더 부정적으로 평가받을 만하다고 생각한다."),
]

C1_OPTS = ["좋아요를 누르거나 공감 댓글을 단다.", "그냥 넘긴다.", "댓글로 근거를 묻는다.", "반박하는 댓글을 달거나 신고한다."]
C1R_OPTS = ["댓글 내용에 어느 정도 동의해서", "관심 없는 주제라서", "내가 대응해도 소용없을 것 같아서", "논쟁에 휘말리고 싶지 않아서", "기타"]
C2_OPTS = ["친구의 말에 동의하는 반응을 남긴다.", "읽기만 하고 넘긴다.", "다른 이야기로 자연스럽게 화제를 돌린다.", "\"이거 출처 어디야?\" 또는 \"좀 일반화 아냐?\"라고 말한다."]
C2R_OPTS = ["글 내용에 어느 정도 동의해서", "친구 사이에 분위기를 어색하게 만들고 싶지 않아서", "말해도 바뀌지 않을 것 같아서", "관심 없는 주제라서"]

D_ITEMS = [  # 순서: D1 → D3 → D2
    ("D1", "한국 사회는 워홀 여성을 교제 혹은 결혼의 대상으로서 꺼린다고 생각한다."),
    ("D3", "한국 사회에서는 워킹홀리데이를 경험한 여성의 사생활이 본인의 능력이나 경험보다 더 주목받는 경향이 있다고 생각한다."),
    ("D2", "채용 담당자들은 이력서에 적힌 여성의 해외 워홀 경험을 '글로벌 역량'이나 '자립심'보다는 '단순 도피'나 '스펙을 빙자한 유흥'으로 해석하는 경향이 있다."),
]

PRE_BIAS_OPTS = ["아예 없다", "거의 없다", "중간", "조금 있다", "많이 있다"]
CHANGE_OPTS = ["긍정적으로 변했다", "조금 변했다", "변화하지 않았다", "부정적으로 변했다"]
GENDER_OPTS = ["남성", "여성"]

RESULT_TYPES = {
    "factchecker": {
        "name": "맑은 눈의 팩트체커",
        "tagline": "\"워홀을 갔군. (끄덕)\" 불필요한 색안경도, 과도한 상상도 없는 깔끔함!",
        "tendency": "주어진 정보와 추론을 잘 구분했고, 근거가 부족한 이야기에는 쉽게 동의하지 않았어요.",
        "next": "내가 근거를 따지는 건 익숙하지만, 주변에서 \"~라더라\"를 들었을 때 그 자리에서 근거를 묻는 건 또 다른 일이에요. 이 습관을 대화에서도 꺼내 써볼까요?",
    },
    "quiet_agree": {
        "name": "은근슬쩍 동의파",
        "tagline": "사실과 추측은 칼같이 가르는데, 익숙한 이야기엔 마음이 먼저 끄덕이는 사람",
        "tendency": "정보와 추론은 잘 구분했어요. 그런데 판단 문항에서는 근거가 없다는 걸 알면서도 일부 이야기에 동의하는 쪽을 골랐어요.",
        "next": "아는 것과 익숙해진 것은 다를 수 있어요. 여러 번 들은 이야기는 근거가 없어도 사실처럼 느껴지기 쉬워요. 동의하는 마음이 들 때, \"이건 내가 확인한 걸까, 자주 들어서 익숙한 걸까?\"를 한 번 물어보세요.",
    },
    "novelist": {
        "name": "선의의 소설가",
        "tagline": "빈칸을 보면 일단 따뜻한 이야기로 채워 넣는 사람",
        "tendency": "워홀 여성에 대한 부정적인 이야기에는 잘 동의하지 않았어요. 다만 정보에 없는 내용도 '확인 가능'으로 고른 경우가 있었어요.",
        "next": "좋은 쪽으로 채운 빈칸도, 나쁜 쪽으로 채운 빈칸과 출발점은 같아요. 그 사람이 독립적인지, 성실한지는 이 정보만으로는 알 수 없어요. 그리고 누군가를 존중하는 데 그 사람이 '좋은 사람임을 증명할' 필요는 없어요.",
    },
    "rumor_bag": {
        "name": "카더라 보따리",
        "tagline": "확인 안 된 이야기도 일단 보따리에 넣고 보는 사람",
        "tendency": "정보에 없는 내용을 '확인 가능'으로 고른 경우가 있었고, 워홀 여성에 대한 일부 이야기에도 동의하는 쪽을 골랐어요. 정보가 비어 있을 때, 들어본 이야기가 그 자리를 채웠을 수 있어요.",
        "next": "이건 이상한 게 아니에요. 정보가 부족하면 사람의 머리는 들어본 이야기로 빈칸을 채우곤 해요. 지금 알아차렸다면, 다음엔 그 이야기의 출처가 어디였는지부터 다시 살펴보세요.",
    },
}

BADGES = {
    "solver": ("📣 한마디 해결사", "근거 없는 말에 한마디 건넬 줄 아는 편"),
    "quiet": ("🙊 조용한 반대파", "속으론 아니라고 생각하지만, 말하기는 망설여지는 편"),
    "society": ("🔭 사회 걱정러", "\"나는 괜찮은데 다들 그럴 거야\"라고 생각하는 편"),
    "repeat": ("🔁 반복 청취형", "여러 번 들은 이야기에 귀가 얇아지는 편"),
    "firstimp": ("📌 첫인상 압정형", "첫인상에 압정을 꽂아두는 편"),
}

CLOSING_NOTE = (
    "이 결과는 당신이 어떤 사람인지 진단한 게 아니라, 이번 응답에서 나타난 판단 경향을 보여준 거예요. "
    "알아차렸다면, 그다음은 판단의 근거를 한 번 더 살펴보는 것이에요. "
    "그러면 같은 정보에서도 다른 결론이 보일 수 있어요."
)

# ─────────────────────────────────────────────
# 2. 스타일
# ─────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Black+Han+Sans&family=IBM+Plex+Sans+KR:wght@400;500;700&display=swap');
    html, body, [class*="css"], .stMarkdown, .stRadio, .stCheckbox, .stTextInput, .stTextArea {
        font-family: 'IBM Plex Sans KR', sans-serif;
    }
    .block-container { max-width: 640px; padding-top: 2rem; }
    .hero { background:#1B1F3B; color:#FFFFFF; border-radius:18px; padding:28px 24px; margin-bottom:16px; }
    .hero h1 { font-family:'Black Han Sans', sans-serif; font-weight:400; font-size:40px; line-height:1.2; margin:0 0 10px; color:#FFFFFF; }
    .hero p { color:#E3E6F7; margin:0; line-height:1.6; }
    .mark { background:#FFE45C; color:#1B1F3B; padding:0 6px; }
    .part { display:inline-block; font-size:12px; font-weight:700; color:#3D5AFE; background:#E3E8FF; padding:4px 10px; border-radius:8px; margin-bottom:8px; }
    .card { background:#FFFFFF; border:1px solid #DDE0EC; border-radius:14px; padding:16px; margin:8px 0 14px; line-height:1.7; color:#1B1F3B; }
    .comment { background:#FFFFFF; border:1px solid #DDE0EC; border-radius:14px; padding:12px 16px; margin:8px 0 14px; color:#1B1F3B; }
    .comment b { font-size:13px; }
    .badge { display:inline-block; background:#262B52; color:#E3E6F7; border:1px solid #4A5088; border-radius:999px; padding:4px 12px; margin:4px 6px 0 0; font-size:13px; }
    .note { border:1.5px solid #DDE0EC; border-radius:14px; padding:14px 16px; font-size:14px; color:#5B6078; line-height:1.7; }
    /* 버튼·선택 표시 색을 남색/파랑으로 (기본 빨강 대신) */
    .stButton button[kind="primary"] { background:#1B1F3B; border-color:#1B1F3B; color:#FFFFFF; }
    .stButton button[kind="primary"]:hover { background:#2A3060; border-color:#2A3060; color:#FFFFFF; }
    input[type="radio"], input[type="checkbox"] { accent-color:#3D5AFE; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────
# 3. 상태 관리
# ─────────────────────────────────────────────
PAGES = ["start", "E", "A2", "A1", "B", "C", "D", "result",
         "I1", "I2", "I3", "I4", "P1", "P2", "end"]

if "page" not in st.session_state:
    st.session_state.page = 0
    st.session_state.answers = {}
    st.session_state.error = None
    st.session_state.pid = uuid.uuid4().hex[:10]
    st.session_state.started_at = datetime.now().isoformat(timespec="seconds")
    st.session_state.saved = False

ans = st.session_state.answers


def go_next(keys, required):
    """현재 화면의 응답을 확인하고 저장한 뒤 다음 화면으로 이동."""
    missing = [k for k in required if st.session_state.get(k) in (None, "")]
    if missing:
        st.session_state.error = "아직 답하지 않은 문항이 있어요."
        return
    for k in keys:
        ans[k] = st.session_state.get(k)
    st.session_state.error = None
    st.session_state.page += 1


def next_button(label, keys=(), required=()):
    if st.session_state.error:
        st.warning(st.session_state.error)
    st.button(label, type="primary", width="stretch",
              on_click=go_next, args=(list(keys), list(required)))


def part(label):
    st.markdown(f'<span class="part">{label}</span>', unsafe_allow_html=True)


def progress(value):
    st.progress(value)


# ─────────────────────────────────────────────
# 4. 채점
# ─────────────────────────────────────────────
def likert(key, options):
    """매우 동의(그렇다)=4 … 전혀 동의하지 않음(그렇지 않다)=1"""
    return 4 - options.index(ans[key])


def score_a_radio(items):
    return sum(1 for k, _, key in items if (ans[k] == "짐작한 내용") == (key == "infer"))


def score_a_checkbox(items):
    # 체크 = '짐작한 내용'으로 고름. 짐작 문장은 체크, 사실 문장은 미체크가 정답
    return sum(1 for k, _, key in items if bool(ans[k]) == (key == "infer"))


def compute_scores():
    s = {}
    s["A1"] = score_a_checkbox(A1_ITEMS)
    s["A2"] = score_a_radio(A2_ITEMS)
    s["A_pre_rate"] = (s["A1"] + s["A2"]) / 10

    b_keys = ["B1"] + [k for k, _ in B_STATEMENTS]
    b_vals = {k: likert(k, LIKERT_AGREE) for k in b_keys}
    s.update({f"{k}_score": v for k, v in b_vals.items()})
    s["B_pre_mean"] = round(sum(b_vals.values()) / len(b_vals), 3)

    d_vals = {k: likert(k, LIKERT_AGREE) for k, _ in D_ITEMS}
    s.update({f"{k}_score": v for k, v in d_vals.items()})
    s["D_mean"] = round(sum(d_vals.values()) / len(d_vals), 3)

    e_vals = {k: likert(k, LIKERT_E) for k, _ in E_ITEMS}
    s.update({f"{k}_score": v for k, v in e_vals.items()})
    s["E_mean"] = round(sum(e_vals.values()) / len(e_vals), 3)

    s["C1_code"] = C1_OPTS.index(ans["C1"]) + 1
    s["C2_code"] = C2_OPTS.index(ans["C2"]) + 1
    s["C_active"] = int(s["C1_code"] in (3, 4) or s["C2_code"] == 4)

    # 결과 유형
    a_high = s["A_pre_rate"] >= A_CUTOFF
    b_high = s["B_pre_mean"] >= B_CUTOFF
    if a_high and not b_high:
        s["type"] = "factchecker"
    elif a_high and b_high:
        s["type"] = "quiet_agree"
    elif not a_high and not b_high:
        s["type"] = "novelist"
    else:
        s["type"] = "rumor_bag"

    # 배지 (C에서 1개 + D·E 중 1개)
    badges = []
    quiet = s["B1_score"] <= 2 and (
        (s["C1_code"] == 2 and ans.get("C1R") in (C1R_OPTS[2], C1R_OPTS[3]))
        or (s["C2_code"] in (2, 3) and ans.get("C2R") in (C2R_OPTS[1], C2R_OPTS[2]))
    )
    if s["C_active"]:
        badges.append("solver")
    elif quiet:
        badges.append("quiet")

    if s["D1_score"] >= 3 and s["B2_score"] <= 2:
        badges.append("society")
    elif s["E7_score"] >= 3:
        badges.append("repeat")
    elif s["E6_score"] >= 3:
        badges.append("firstimp")
    s["badges"] = ",".join(badges)
    return s


def compute_post_scores():
    return {
        "A3": score_a_radio(A3_ITEMS),
        "A3_rate": score_a_radio(A3_ITEMS) / 5,
        "A1_rate": score_a_checkbox(A1_ITEMS) / 5,
        "P_B7_score": likert("P_B7", LIKERT_AGREE),
    }


# 저장할 열 순서 (조건부 문항도 빈칸으로 항상 포함 → 시트 열이 어긋나지 않음)
ANSWER_KEYS = (
    [k for k, _ in E_ITEMS] + [k for k, _, _ in A2_ITEMS] + [k for k, _, _ in A1_ITEMS]
    + ["B1"] + [k for k, _ in B_STATEMENTS]
    + ["C1", "C1R", "C1R_etc", "C2", "C2R"] + [k for k, _ in D_ITEMS]
    + ["I1_cheer", "I3_rebuttal", "P_B7"] + [k for k, _, _ in A3_ITEMS]
    + ["P_prebias", "P_change", "P_feel", "P_gender", "P_age"]
)


def build_row():
    row = {"pid": st.session_state.pid,
           "started_at": st.session_state.started_at,
           "finished_at": datetime.now().isoformat(timespec="seconds")}
    for k in ANSWER_KEYS:
        v = ans.get(k)
        if isinstance(v, bool):
            v = int(v)                      # 체크박스: 체크=1, 미체크=0
        elif isinstance(v, float) and v.is_integer():
            v = int(v)                      # 나이 23.0 → 23
        row[k] = "" if v is None else v
    row.update(compute_scores())
    row.update(compute_post_scores())
    return row


def get_webhook_url():
    """secrets.toml(또는 Streamlit Cloud의 Secrets)에 적은 구글 시트 웹앱 주소."""
    try:
        return st.secrets.get("sheet_webhook")
    except Exception:  # secrets 파일이 아예 없을 때
        return None


def save_to_sheet(row):
    url = get_webhook_url()
    if not url:
        return False
    data = json.dumps(row, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8").strip() == "ok"


def save_to_csv(row):
    write_header = not RESPONSES_CSV.exists()
    with RESPONSES_CSV.open("a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        if write_header:
            writer.writeheader()
        writer.writerow(row)


def save_response():
    """구글 시트에 저장. 설정이 없거나 실패하면 responses.csv에 백업."""
    if st.session_state.saved:
        return
    row = build_row()
    try:
        ok = save_to_sheet(row)
    except Exception as e:  # 네트워크·권한 오류 등
        ok = False
        print("구글 시트 저장 실패:", e)
    if not ok:
        save_to_csv(row)
    st.session_state.saved = True


# ─────────────────────────────────────────────
# 5. 화면
# ─────────────────────────────────────────────
def page_start():
    st.markdown(
        '<div class="hero"><p>짧은 정보만 보고 사람을 판단할 때</p>'
        '<h1>더 커뮤니티:<br><span class="mark">워홀녀편</span></h1>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.info("정답을 맞히는 시험이 아니에요. 오래 고민하지 말고 떠오르는 대로 골라주세요.  \n약 10분 · 익명")
    st.caption("응답은 익명으로 저장되며 수업 연구 목적으로만 사용됩니다. "
               "웨이브 예능 <사상검증구역: 더 커뮤니티>와는 관계없는 수업용 패러디 테스트예요.")
    next_button("테스트 시작하기")


def page_E():
    progress(0.33)
    part("PART 1 · 일상 가치관")
    st.write("평소 내 생각과 가장 가까운 것을 골라주세요.")
    for i, (k, text) in enumerate(E_ITEMS, start=1):
        st.radio(f"**{i}. {text}**", LIKERT_E, index=None, key=k, horizontal=True)
        st.write("")
    keys = [k for k, _ in E_ITEMS]
    next_button("다음", keys, keys)


def page_A2():
    progress(0.38)
    part("PART 2 · 장면 속 판단")
    st.markdown("#### 8. 한 여성이 인스타그램에 올린 게시물이에요.")
    if IMAGE_PATH.exists():
        st.image(str(IMAGE_PATH), width="stretch")
    else:
        st.error("insta-post.png 파일을 app.py와 같은 폴더에 넣어주세요.")
    st.write("아래 문장이 이 게시물만으로 **확인할 수 있는 것**인지, **짐작한 것**인지 골라주세요.")
    for k, text, _ in A2_ITEMS:
        st.radio(text, A_CHOICES, index=None, key=k, horizontal=True)
    keys = [k for k, _, _ in A2_ITEMS]
    next_button("다음", keys, keys)


def page_A1():
    progress(0.43)
    part("PART 2 · 장면 속 판단")
    st.markdown("#### 9. 서연 (24세)")
    st.markdown(f'<div class="card">{A1_STORY}</div>', unsafe_allow_html=True)
    st.write("아래 문장 중, 위 내용을 통해 **짐작한 내용**을 모두 골라주세요.")
    for k, text, _ in A1_ITEMS:
        st.checkbox(text, key=k)
    keys = [k for k, _, _ in A1_ITEMS]
    next_button("다음", keys)  # 체크박스는 '안 고름'도 응답이라 필수 확인 없음


def page_B():
    progress(0.76)
    part("PART 3 · 내 생각은")
    st.write("SNS에서 한 여성의 호주 워홀 후기 게시물에 이런 댓글이 달려 있어요.")
    st.markdown(f'<div class="comment"><b>user_2931</b><br>{COMMENT}</div>', unsafe_allow_html=True)
    st.radio(f"**10. {B1_TEXT}**", LIKERT_AGREE, index=None, key="B1", horizontal=True)
    st.divider()
    st.write("이번엔 아래 문장에 대한 내 생각을 골라주세요.")
    for i, (k, text) in enumerate(B_STATEMENTS, start=11):
        st.radio(f"**{i}. {text}**", LIKERT_AGREE, index=None, key=k, horizontal=True)
        st.write("")
    keys = ["B1"] + [k for k, _ in B_STATEMENTS]
    next_button("다음", keys, keys)


def page_C():
    progress(0.86)
    part("PART 4 · 이럴 때 나는")
    st.write("앞에서 본 댓글을 다시 볼게요.")
    st.markdown(f'<div class="comment"><b>user_2931</b><br>{COMMENT}</div>', unsafe_allow_html=True)
    st.radio("**17. 이 댓글을 보면 나는 어떻게 할 것 같나요?**", C1_OPTS, index=None, key="C1")
    keys, required = ["C1"], ["C1"]
    if st.session_state.get("C1") == C1_OPTS[1]:
        st.radio("그냥 넘기는 가장 큰 이유는?", C1R_OPTS, index=None, key="C1R")
        keys.append("C1R"); required.append("C1R")
        if st.session_state.get("C1R") == "기타":
            st.text_input("기타 이유를 적어주세요", key="C1R_etc")
            keys.append("C1R_etc")

    st.divider()
    st.write("친구 단톡방에 한 친구가 커뮤니티 글 캡처를 올렸어요.")
    st.markdown('<div class="comment"><b>[캡처] "워홀 다녀온 여자 거르는 법 3가지"</b><br>친구: "ㅋㅋㅋ 이거 완전 맞말 아님?"</div>',
                unsafe_allow_html=True)
    st.radio("**18. 이 상황에서 나는 어떻게 할 것 같나요?**", C2_OPTS, index=None, key="C2")
    keys.append("C2"); required.append("C2")
    if st.session_state.get("C2") in (C2_OPTS[1], C2_OPTS[2]):
        st.radio("그렇게 하는 가장 큰 이유는?", C2R_OPTS, index=None, key="C2R")
        keys.append("C2R"); required.append("C2R")
    next_button("다음", keys, required)


def page_D():
    progress(1.0)
    part("PART 5 · 사회는 어떨까")
    st.write("마지막이에요. 이번엔 내 생각이 아니라, 우리 사회가 어떻다고 생각하는지 골라주세요.")
    for i, (k, text) in enumerate(D_ITEMS, start=19):
        st.radio(f"**{i}. {text}**", LIKERT_AGREE, index=None, key=k, horizontal=True)
        st.write("")
    keys = [k for k, _ in D_ITEMS]
    next_button("내 판단 경향 확인하기", keys, keys)


def page_result():
    s = compute_scores()
    t = RESULT_TYPES[s["type"]]
    badge_html = "".join(f'<span class="badge">{BADGES[b][0]}</span>' for b in s["badges"].split(",") if b)
    st.markdown(
        f'<div class="hero"><p>이번 응답에서 나타난 판단 경향</p>'
        f'<h1>{t["name"]}</h1><p>{t["tagline"]}</p><div>{badge_html}</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown("**두 가지 기준으로 봤어요**")
    st.write("정보와 짐작 구별")
    st.progress(s["A_pre_rate"])
    st.write("떠도는 이야기에 동의한 정도")
    st.progress((s["B_pre_mean"] - 1) / 3)

    st.markdown("**이번 응답에서 나타난 경향**")
    st.write(t["tendency"])
    st.markdown("**한 걸음 더**")
    st.write(t["next"])

    for b in [b for b in s["badges"].split(",") if b]:
        st.caption(f"{BADGES[b][0]} — {BADGES[b][1]}")

    st.markdown(f'<div class="note">{CLOSING_NOTE}</div>', unsafe_allow_html=True)
    st.write("")
    next_button("다음 이야기로")


def page_I1():
    part("STEP 1 / 4")
    st.markdown("#### 테스트를 마친 당신, 카톡이 하나 울립니다.")
    st.markdown('<div class="comment"><b>사랑하는 여동생</b><br>나 드디어 일주일 뒤에 호주 워홀 떠나!!<br>진짜 오래 꿈꿔왔던 건데 실감이 안 나</div>',
                unsafe_allow_html=True)
    st.write("사랑하는 여동생이 오랫동안 꿈꿔왔던 호주 워킹홀리데이를 드디어 일주일 뒤에 떠난다고 하네요.")
    st.text_input("**이때, 당신이 가장 먼저 해주고 싶은 응원의 한 마디는?**", key="I1_cheer",
                  placeholder="동생에게 보낼 한 마디")
    st.caption("이런 말도 좋아요 (예시): \"멋지다! 하고 싶은 거 다 해보고 와\" · \"몸 조심하고 자주 연락해\" · \"네가 자랑스러워, 응원할게\"")
    next_button("보내기", ["I1_cheer"], ["I1_cheer"])


def page_I2():
    part("STEP 2 / 4")
    st.write("몇 달 뒤, 동생이 워홀 현지에서 열심히 일하고 생활하는 브이로그 영상을 유튜브에 올렸습니다.")
    st.markdown('<div class="card"><b>[호주 워홀 브이로그] 카페 출근부터 퇴근까지</b><br><span style="font-size:13px;color:#5B6078">동생의 채널</span></div>',
                unsafe_allow_html=True)
    st.write("그런데, 그 영상에 사람들이 이와 같은 **익명의 악플**을 달았습니다.")
    st.markdown('<div class="comment" style="border-color:#E4B4B4"><b>방구석악플러1</b><br>'
                '여자들 워홀 가서 하는 짓 뻔하지 않나? ㅋㅋ 나중에 결혼하기 전에 워홀 갔다 왔다고 하면 알아서 걸러야 함.</div>',
                unsafe_allow_html=True)
    next_button("답글 달러 가기")


def page_I3():
    part("STEP 3 / 4")
    st.markdown("#### 가장 소중한 사람의 용기 있는 도전이 깎아내려지고 있습니다.")
    st.markdown('<div class="comment" style="border-color:#E4B4B4"><b>방구석악플러1</b><br>'
                '여자들 워홀 가서 하는 짓 뻔하지 않나? ㅋㅋ 나중에 결혼하기 전에 워홀 갔다 왔다고 하면 알아서 걸러야 함.</div>',
                unsafe_allow_html=True)
    st.text_area("**악플러의 근거를 생각해 보고, 직접 반박 댓글을 달아 주세요!**", key="I3_rebuttal",
                 placeholder="한두 문장이면 충분해요", height=120)
    st.caption("※ 욕설이나 과격한 표현은 쓰지 말아 주세요. 근거를 짚는 것만으로도 충분해요.")
    next_button("답글 등록하기", ["I3_rebuttal"], ["I3_rebuttal"])


def page_I4():
    part("STEP 4 / 4")
    st.markdown(
        '<div class="hero"><h1 style="font-size:28px">방금 당신이 지켜낸 건<br>비단 당신의 동생뿐만이 아닙니다.</h1>'
        '<p>우리가 앞서 무의식적으로 평가했던 익명의 워홀 여성들도, 누군가에게는 이토록 응원받아야 마땅한 소중한 가족이자 친구입니다.</p><br>'
        '<p>당신이 악플러에게 남긴 그 멋진 반박처럼, 타인의 낯선 궤적을 편견 대신 <span class="mark">\'용기\'</span>라는 두 글자로 바라봐 주는 사회가 되기를 바랍니다.</p></div>',
        unsafe_allow_html=True,
    )
    st.caption("마지막으로 몇 가지만 더 물어볼게요.")
    next_button("계속하기")


def page_P1():
    part("마지막 질문 1 / 2")
    st.radio("**온라인에서 워홀 여성에 대해 떠도는 부정적인 반응들이 완전히 근거 없는 소문만은 아닐 것이라고 생각한다.**",
             LIKERT_AGREE, index=None, key="P_B7", horizontal=True)
    st.divider()
    st.markdown("#### 하은 (26세)")
    st.markdown(f'<div class="card">{A3_STORY}</div>', unsafe_allow_html=True)
    st.write("아래 문장이 위 내용만으로 **확인할 수 있는 것**인지, **짐작한 것**인지 골라주세요.")
    for k, text, _ in A3_ITEMS:
        st.radio(text, A_CHOICES, index=None, key=k, horizontal=True)
    keys = ["P_B7"] + [k for k, _, _ in A3_ITEMS]
    next_button("다음", keys, keys)


def page_P2():
    part("마지막 질문 2 / 2")
    st.radio("**이 테스트를 하기 전, 워홀 여성에 대한 내 편견은 어느 정도였다고 생각하나요?**",
             PRE_BIAS_OPTS, index=None, key="P_prebias", horizontal=True)
    st.radio("**이 테스트 후 워킹홀리데이 여성에 대한 내 편견은 어떻게 바뀌었나요?**",
             CHANGE_OPTS, index=None, key="P_change", horizontal=True)
    st.text_area("**지금까지 테스트를 하며 느낀 점을 간단하게 적어주세요.**", key="P_feel", height=100)
    st.divider()
    st.markdown("**나에 대해 알려주세요**")
    st.radio("성별", GENDER_OPTS, index=None, key="P_gender", horizontal=True)
    st.number_input("나이 (만)", min_value=14, max_value=99, value=None, step=1, key="P_age",
                    placeholder="예: 23")
    keys = ["P_prebias", "P_change", "P_feel", "P_gender", "P_age"]
    next_button("제출하기", keys, ["P_prebias", "P_change", "P_feel", "P_gender", "P_age"])


def page_end():
    save_response()
    st.markdown('<div class="hero"><h1>참여해줘서<br><span class="mark">고마워요</span></h1>'
                '<p>응답이 저장됐어요. 마지막으로 이 테스트에 대해 알려드릴게요.</p></div>',
                unsafe_allow_html=True)
    st.markdown("""
**연구 안내**
- 테스트에 나온 인물, 게시물, 댓글, 대화는 모두 연구용으로 만든 것이에요. 인스타그램 사진은 [AI로 생성한 이미지]이며, 실제 인물이 아니에요.
- 댓글 속 "거르라던데" 같은 이야기는 온라인에서 떠도는 말을 재현한 것으로, 사실 여부가 확인된 정보가 아니에요.
""")


PAGE_FUNCS = {
    "start": page_start, "E": page_E, "A2": page_A2, "A1": page_A1, "B": page_B,
    "C": page_C, "D": page_D, "result": page_result,
    "I1": page_I1, "I2": page_I2, "I3": page_I3, "I4": page_I4,
    "P1": page_P1, "P2": page_P2, "end": page_end,
}

PAGE_FUNCS[PAGES[st.session_state.page]]()

# 다음 화면으로 넘어가면 맨 위부터 보이게 스크롤 올리기
components.html(
    f"""<script>
    // page {st.session_state.page}
    const doc = window.parent.document;
    ['[data-testid="stMain"]', '[data-testid="stAppViewContainer"]', 'section.main', '.main']
      .forEach(sel => {{ const el = doc.querySelector(sel); if (el) el.scrollTo(0, 0); }});
    window.parent.scrollTo(0, 0);
    </script>""",
    height=0,
)
