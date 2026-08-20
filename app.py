import streamlit as st
import json
import os
from datetime import date, datetime
import calendar
import uuid

st.set_page_config(page_title="MyDay", page_icon="📋", layout="wide")

DATA_FILE = "tasks.json"
GOALS_FILE = "goals.json"
TEMPLATES_FILE = "templates.json"
WIP_LIMIT = 3  # Doing 상태 동시 진행 최대 개수

# ============================================
# [코칭 워크북 질문]
# docs/03-coaching-design.md 의 설계를 그대로 옮긴 것.
# 질문/힌트를 고치고 싶으면 이 부분만 수정하면 된다.
# ============================================
WORKBOOK_5 = [
    {
        "title": "가능성 점검",
        "question": "이 목표, 진짜로 할 수 있다고 믿나요? 믿기 어렵다면 그 이유는?",
        "hint": "비슷한 걸 해낸 사람이 한 명이라도 있다면 가능해요.",
    },
    {
        "title": "자기 인식",
        "question": "지금 나는 어떤 상태예요? 무엇을 갖고 있고, 무엇이 부족해요?",
        "hint": "강점/약점/시간/돈/관계 등으로 나눠서 생각해보세요.",
    },
    {
        "title": "기준점 찾기",
        "question": "내가 이걸 해냈다고 생각할 수 있는 기준이 무엇인가요?",
        "hint": "낮은 기준은 지속할 수 있는 성취감을 높여주고, 높은 기준은 나의 한계를 높여줍니다.",
    },
    {
        "title": "시작점 정하기",
        "question": "이 목표의 마감기한이 1시간 뒤라면, 어느 정도까진 했어야 했다고 생각하시나요?",
        "hint": '보통 "이것도 못하면 안되지" 부터 시작해야 합니다.',
    },
    {
        "title": "실행 쪼개기",
        "question": "위 답변을 바탕으로, 내일까지 할 수 있는 30분짜리 행동 3개를 뽑아보세요.",
        "hint": "무엇을 해야 할지 모를 때 긴 시간이 필요한 일을 먼저 도전하지 마세요. "
                '숙제가 문제집 20장 풀기라면, 모두 풀지 못할 것 같아도 "이것도 못하면 안되지"의 분량만 해결하십시오. '
                "아무것도 못한 사람이 되지 마십시오.",
        "slots": 3,
        "slot_label": "행동",
    },
]

WORKBOOK_3 = [
    {
        "title": "최종 모습",
        "question": "이 목표가 다 끝났을 때, 어떤 상태가 되어 있어야 하나요?",
        "hint": '"끝"을 스스로 정해두지 않으면 계속 끝나지 않아요.',
    },
    {
        "title": "현재 위치",
        "question": "지금 어디까지 와 있나요? 이미 한 것과 아직 안 한 것을 나눠보세요.",
        "hint": "알고는 있는데 정리가 안 된 상태일 수 있어요. 적어서 밖으로 꺼내보세요.",
    },
    {
        "title": "첫 걸음",
        "question": "그럼 지금 당장 시작할 수 있는 것은 무엇인가요?",
        "hint": "30분 안에 끝낼 수 있는 크기로 잘라보세요. 하나만 적어도 괜찮아요.",
        "slots": 3,
        "slot_label": "첫 걸음",
    },
]

# 할 일 하나가 막막할 때 쓰는 워크북.
# 목표보다 작은 단위라 3단계로 줄이고, 결과는 "새 할 일"로 쪼개진다.
WORKBOOK_TASK = [
    {
        "title": "막힌 지점",
        "question": "이 일, 어디서부터 막히나요?",
        "hint": "몰라서 못 하는 건지, 알지만 손이 안 가는 건지만 갈라도 절반은 풀려요.",
    },
    {
        "title": "최소 기준",
        "question": "오늘 이만큼만 하면 \"했다\"고 칠 수 있는 건 어디까지예요?",
        "hint": '"이것도 못하면 안되지" 의 분량을 찾으세요.',
    },
    {
        "title": "첫 조각",
        "question": "그럼 30분 안에 끝낼 수 있는 조각으로 나눠보세요.",
        "hint": "적은 것들은 각각 새 할 일로 등록돼요. 하나만 적어도 괜찮아요.",
        "slots": 3,
        "slot_label": "조각",
    },
]

# 진단 결과별 설정: (버튼 라벨, 선택 후 안내문, 워크북)
DIAGNOSIS = {
    "stuck":   ("😶 막막해요",        "막막할 땐 5단계로 천천히 풀어봐요.", WORKBOOK_5),
    "partial": ("🤔 어느 정도 알아요", "핵심 3단계만 짚어볼게요.",          WORKBOOK_3),
    "clear":   ("💪 잘 알아요",       "그럼 바로 체크리스트를 채워보세요.",  None),
}


# ============================================
# [데이터 저장/불러오기]
# ============================================
def load_tasks():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_tasks(tasks):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

def load_goals():
    if os.path.exists(GOALS_FILE):
        with open(GOALS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_goals(goals):
    with open(GOALS_FILE, "w", encoding="utf-8") as f:
        json.dump(goals, f, ensure_ascii=False, indent=2)

def load_templates():
    if os.path.exists(TEMPLATES_FILE):
        with open(TEMPLATES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_templates(templates):
    with open(TEMPLATES_FILE, "w", encoding="utf-8") as f:
        json.dump(templates, f, ensure_ascii=False, indent=2)

if "tasks" not in st.session_state:
    st.session_state.tasks = load_tasks()

# 기존 task 데이터 구조 보정
tasks_structure_changed = False

for i in range(len(st.session_state.tasks)):
    if "status" not in st.session_state.tasks[i]:
        if st.session_state.tasks[i].get("completed", False):
            st.session_state.tasks[i]["status"] = "done"
        else:
            st.session_state.tasks[i]["status"] = "todo"
        tasks_structure_changed = True

    # 막막할 때 쓰는 워크북 (나중에 추가된 항목)
    if "stuck" not in st.session_state.tasks[i]:
        st.session_state.tasks[i]["stuck"] = False
        tasks_structure_changed = True

    if "workbook" not in st.session_state.tasks[i]:
        st.session_state.tasks[i]["workbook"] = {}
        tasks_structure_changed = True

if tasks_structure_changed:
    save_tasks(st.session_state.tasks)

# ============================================
# [목표 데이터 저장 공간]
# goals = 장기 목표 목록
# ============================================
if "goals" not in st.session_state:
    st.session_state.goals = load_goals()

# 예전 목표 데이터 구조 보정
goals_structure_changed = False

for i in range(len(st.session_state.goals)):
    if "items" not in st.session_state.goals[i]:
        st.session_state.goals[i]["items"] = []
        goals_structure_changed = True

    # 자기 진단 / 코칭 워크북 (나중에 추가된 항목)
    if "diagnosis" not in st.session_state.goals[i]:
        st.session_state.goals[i]["diagnosis"] = None
        goals_structure_changed = True

    if "workbook" not in st.session_state.goals[i]:
        st.session_state.goals[i]["workbook"] = {}
        goals_structure_changed = True

    for j in range(len(st.session_state.goals[i]["items"])):
        if "sent_to_today" not in st.session_state.goals[i]["items"][j]:
            st.session_state.goals[i]["items"][j]["sent_to_today"] = False
            goals_structure_changed = True

        if "item_id" not in st.session_state.goals[i]["items"][j]:
            st.session_state.goals[i]["items"][j]["item_id"] = uuid.uuid4().hex
            goals_structure_changed = True

if goals_structure_changed:
    save_goals(st.session_state.goals)

# ============================================
# [템플릿 데이터 저장 공간]
# templates = 재사용 가능한 체크리스트 템플릿 목록
# ============================================
if "templates" not in st.session_state:
    st.session_state.templates = load_templates()

# 템플릿 구조 보정
templates_structure_changed = False
for i in range(len(st.session_state.templates)):
    if "items" not in st.session_state.templates[i]:
        st.session_state.templates[i]["items"] = []
        templates_structure_changed = True

if templates_structure_changed:
    save_templates(st.session_state.templates)

if "selected_date" not in st.session_state:
    st.session_state.selected_date = None

if "view_year" not in st.session_state:
    st.session_state.view_year = date.today().year
if "view_month" not in st.session_state:
    st.session_state.view_month = date.today().month


# ============================================
# [자동 기한 초과 체크]
# ============================================
today = date.today()
for task in st.session_state.tasks:
    if not task["completed"]:
        deadline = datetime.strptime(task["deadline"], "%Y-%m-%d").date()
        task["expired"] = deadline < today
    else:
        task["expired"] = False
save_tasks(st.session_state.tasks)


# ============================================
# [헤더 - 모든 탭 공통]
# ============================================
st.title("MyDay 📋")
st.caption(f"오늘은 {today.strftime('%Y년 %m월 %d일')}")


# ============================================
# [사이드바 - 할 일 추가 (오늘 탭에서만 사용)]
# ============================================
with st.sidebar:
    st.header("➕ 새 할 일")
    
    with st.form("add_task", clear_on_submit=True):
        title = st.text_input("제목")
        description = st.text_area(
            "상세 설명",
            placeholder="해야 할 일을 자세히 적어주세요",
            height=120
        )
        estimated_min = st.number_input("예상 소요시간(분)", min_value=5, max_value=480, value=30, step=5)
        deadline = st.date_input("마감일", value=today)
        
        col_u, col_i = st.columns(2)
        with col_u:
            is_urgent = st.checkbox("🔥 급함")
        with col_i:
            is_important = st.checkbox("⭐ 중요")
        
        submitted = st.form_submit_button("추가하기", use_container_width=True)
        
        if submitted and title:
            st.session_state.tasks.append({
                "id": len(st.session_state.tasks),
                "title": title,
                "description": description,
                "estimated_min": estimated_min,
                "deadline": str(deadline),
                "urgent": is_urgent,
                "important": is_important,
                "completed": False,
                "completed_at": None,
                "expired": False,
                "status": "todo"
            })
            save_tasks(st.session_state.tasks)
            st.success("추가됨!")
            st.rerun()
    
    st.divider()
    st.header("⏰ 오늘 가용시간")
    available_hours = st.slider("시간", 1, 12, 4)
    available_min = available_hours * 60


# ============================================
# [할 일 카드 함수 - 탭에서 공통 사용]
# ============================================
def render_task(task, idx):
    task_key = task.get("id", idx)
    edit_key = f"editing_task_{task_key}"
    if edit_key not in st.session_state:
        st.session_state[edit_key] = False

    with st.container(border=True):

        # -----------------------------
        # 수정 모드
        # -----------------------------
        if st.session_state[edit_key]:
            new_title = st.text_input("제목", value=task["title"], key=f"edit_title_{task_key}")
            new_desc = st.text_area(
                "상세 설명",
                value=task.get("description", ""),
                key=f"edit_desc_{task_key}",
                height=100
            )
            new_estimated_min = st.number_input(
                "예상 소요시간(분)",
                min_value=5, max_value=480,
                value=task.get("estimated_min", 30), step=5,
                key=f"edit_min_{task_key}"
            )
            new_deadline = st.date_input(
                "마감일",
                value=datetime.strptime(task["deadline"], "%Y-%m-%d").date(),
                key=f"edit_deadline_{task_key}"
            )
            col_eu, col_ei = st.columns(2)
            with col_eu:
                new_urgent = st.checkbox("🔥 급함", value=task.get("urgent", False), key=f"edit_urgent_{task_key}")
            with col_ei:
                new_important = st.checkbox("⭐ 중요", value=task.get("important", False), key=f"edit_important_{task_key}")

            col_save, col_cancel = st.columns(2)
            with col_save:
                if st.button("💾 저장", key=f"save_task_{task_key}", use_container_width=True):
                    st.session_state.tasks[idx]["title"] = new_title
                    st.session_state.tasks[idx]["description"] = new_desc
                    st.session_state.tasks[idx]["estimated_min"] = new_estimated_min
                    st.session_state.tasks[idx]["deadline"] = str(new_deadline)
                    st.session_state.tasks[idx]["urgent"] = new_urgent
                    st.session_state.tasks[idx]["important"] = new_important
                    save_tasks(st.session_state.tasks)
                    st.session_state[edit_key] = False
                    st.rerun()
            with col_cancel:
                if st.button("취소", key=f"cancel_task_{task_key}", use_container_width=True):
                    st.session_state[edit_key] = False
                    st.rerun()

            return  # 수정 모드일 땐 상태 이동 버튼 등은 숨김

        # -----------------------------
        # 일반 보기 모드
        # -----------------------------
        col_title, col_edit = st.columns([5, 1])
        with col_title:
            st.write(f"**{task['title']}**")
        with col_edit:
            if st.button("✏", key=f"edit_btn_{task_key}", use_container_width=True):
                st.session_state[edit_key] = True
                st.rerun()

        if task.get("source_goal"):
            st.caption(f"🎯 목표에서 옴: {task['source_goal']}")

        st.caption(f"⏱ {task['estimated_min']}분 | 📅 {task['deadline']}")

        badges = []
        if task.get("important"):
            badges.append("⭐ 중요")
        if task.get("urgent"):
            badges.append("🔥 급함")
        if badges:
            st.caption(" | ".join(badges))

        if task.get("description"):
            with st.expander("📄 상세 보기"):
                st.write(task["description"])

        status = task.get("status", "todo")

        # -----------------------------
        # 막막할 때 — 할 일 쪼개기 워크북
        # 아직 시작도 못한 To Do 에서만 필요하다.
        # -----------------------------
        if status == "todo":
            if not task.get("stuck"):
                if st.button("😶 막막해요", key=f"task_stuck_{task_key}", use_container_width=True):
                    st.session_state.tasks[idx]["stuck"] = True
                    save_tasks(st.session_state.tasks)
                    st.rerun()
            else:
                written = sum(
                    1 for v in (task.get("workbook") or {}).values() if has_answer(v)
                )
                with st.expander(f"✍️ 쪼개보기 ({written}/{len(WORKBOOK_TASK)} 작성)", expanded=True):
                    render_workbook(task, idx, WORKBOOK_TASK, kind="task")
                    if st.button("접기", key=f"task_unstuck_{task_key}", use_container_width=True):
                        st.session_state.tasks[idx]["stuck"] = False
                        save_tasks(st.session_state.tasks)
                        st.rerun()

        if status == "todo":
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("➡ Doing", key=f"to_doing_{task_key}", use_container_width=True):
                    doing_count = sum(1 for t in st.session_state.tasks if t.get("status") == "doing")
                    if doing_count >= WIP_LIMIT:
                        st.warning(f"⚠️ Doing은 최대 {WIP_LIMIT}개까지만 가능해요. 먼저 하나를 끝내거나 To Do로 되돌리세요.")
                    else:
                        st.session_state.tasks[idx]["status"] = "doing"
                        save_tasks(st.session_state.tasks)
                        st.rerun()

            with col2:
                if st.button("✅ Done", key=f"todo_done_{task_key}", use_container_width=True):
                    st.session_state.tasks[idx]["status"] = "done"
                    st.session_state.tasks[idx]["completed"] = True
                    st.session_state.tasks[idx]["completed_at"] = str(today)
                    save_tasks(st.session_state.tasks)
                    st.rerun()

            with col3:
                if st.button("🗑 삭제", key=f"todo_delete_{task_key}", use_container_width=True):
                    st.session_state.tasks.pop(idx)
                    save_tasks(st.session_state.tasks)
                    st.rerun()

        elif status == "doing":
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("⬅ To Do", key=f"doing_todo_{task_key}", use_container_width=True):
                    st.session_state.tasks[idx]["status"] = "todo"
                    save_tasks(st.session_state.tasks)
                    st.rerun()

            with col2:
                if st.button("✅ Done", key=f"doing_done_{task_key}", use_container_width=True):
                    st.session_state.tasks[idx]["status"] = "done"
                    st.session_state.tasks[idx]["completed"] = True
                    st.session_state.tasks[idx]["completed_at"] = str(today)
                    save_tasks(st.session_state.tasks)
                    st.rerun()

            with col3:
                if st.button("🗑 삭제", key=f"doing_delete_{task_key}", use_container_width=True):
                    st.session_state.tasks.pop(idx)
                    save_tasks(st.session_state.tasks)
                    st.rerun()

        elif status == "done":
            col1, col2 = st.columns(2)

            with col1:
                if st.button("↩ Doing", key=f"done_doing_{task_key}", use_container_width=True):
                    doing_count = sum(1 for t in st.session_state.tasks if t.get("status") == "doing")
                    if doing_count >= WIP_LIMIT:
                        st.warning(f"⚠️ Doing은 최대 {WIP_LIMIT}개까지만 가능해요. 먼저 하나를 끝내거나 To Do로 되돌리세요.")
                    else:
                        st.session_state.tasks[idx]["status"] = "doing"
                        st.session_state.tasks[idx]["completed"] = False
                        st.session_state.tasks[idx]["completed_at"] = None
                        save_tasks(st.session_state.tasks)
                        st.rerun()

            with col2:
                if st.button("🗑 삭제", key=f"done_delete_{task_key}", use_container_width=True):
                    st.session_state.tasks.pop(idx)
                    save_tasks(st.session_state.tasks)
                    st.rerun()


# ============================================
# [코칭 워크북 함수]
# 질문을 한 화면에 전부 펼쳐서 보여준다.
# (단계별로 넘기지 않는 이유는 docs/00-decisions.md 결정 #4 참고)
# ============================================
def answer_list(value):
    """워크북 답변을 항상 리스트로 돌려준다. (예전 자유 입력 방식도 함께 처리)"""
    if isinstance(value, list):
        return [v.strip() for v in value if v and v.strip()]
    if isinstance(value, str):
        return [line.strip() for line in value.split("\n") if line.strip()]
    return []


def has_answer(value):
    return bool(answer_list(value))


def render_workbook(record, idx, steps, kind="goal"):
    """kind="goal" 이면 답을 목표의 체크리스트로, "task" 면 새 할 일로 등록한다."""
    saved = record.get("workbook") or {}

    with st.form(f"workbook_form_{kind}_{idx}"):
        answers = {}

        for s_i, step in enumerate(steps):
            st.markdown(f"**{s_i + 1}. {step['title']}**")
            st.caption(step["question"])

            slots = step.get("slots")

            if slots:
                # 칸을 나눠서 받는 질문. 한 칸 = 항목 하나가 된다.
                # (한 칸에 여러 줄을 적게 하면 폼 안에서 Enter가 줄바꿈으로 먹히지 않아
                #  전부 한 덩어리로 저장되는 문제가 있었다)
                previous = answer_list(saved.get(str(s_i)))
                filled = []
                for n in range(slots):
                    filled.append(st.text_input(
                        f"{step['slot_label']} {n + 1}",
                        value=previous[n] if n < len(previous) else "",
                        key=f"wb_{kind}_{idx}_{s_i}_{n}",
                    ))
                answers[str(s_i)] = filled
            else:
                previous_text = saved.get(str(s_i), "")
                if not isinstance(previous_text, str):
                    previous_text = "\n".join(answer_list(previous_text))
                answers[str(s_i)] = st.text_area(
                    step["question"],
                    value=previous_text,
                    key=f"wb_{kind}_{idx}_{s_i}",
                    label_visibility="collapsed",
                    height=90,
                )

            st.caption(f"💡 {step['hint']}")

        if st.form_submit_button("💾 답변 저장", use_container_width=True):
            if kind == "goal":
                st.session_state.goals[idx]["workbook"] = answers
                save_goals(st.session_state.goals)
            else:
                st.session_state.tasks[idx]["workbook"] = answers
                save_tasks(st.session_state.tasks)
            st.rerun()

    # 마지막 단계 = 실제로 할 행동. 밖으로 꺼내야 실행으로 이어진다.
    actions = answer_list(saved.get(str(len(steps) - 1)))
    target = "체크리스트" if kind == "goal" else "할 일"

    if not actions:
        st.caption(f"마지막 단계를 채우고 저장하면, {target}로 옮기는 버튼이 생겨요.")
        return

    if not st.button(f"📋 마지막 답변 {len(actions)}개를 {target}로 등록",
                     key=f"wb_to_items_{kind}_{idx}", use_container_width=True):
        return

    added = 0

    if kind == "goal":
        existing = {item["text"] for item in st.session_state.goals[idx]["items"]}

        for text in actions:
            if text in existing:
                continue
            st.session_state.goals[idx]["items"].append({
                "item_id": uuid.uuid4().hex,
                "text": text,
                "done": False,
                "sent_to_today": False,
            })
            existing.add(text)
            added += 1

        save_goals(st.session_state.goals)
    else:
        # 막막했던 할 일을 조각 단위 할 일로 쪼갠다
        existing = {t["title"] for t in st.session_state.tasks}

        for text in actions:
            if text in existing:
                continue
            st.session_state.tasks.append({
                "id": len(st.session_state.tasks),
                "title": text,
                "description": f"'{record['title']}' 에서 쪼갠 조각",
                "estimated_min": 30,
                "deadline": record["deadline"],
                "urgent": record.get("urgent", False),
                "important": record.get("important", False),
                "completed": False,
                "completed_at": None,
                "expired": False,
                "status": "todo",
                "stuck": False,
                "workbook": {},
            })
            existing.add(text)
            added += 1

        save_tasks(st.session_state.tasks)

    if added:
        st.success(f"{target} {added}개를 만들었어요!")
    else:
        st.info("이미 다 등록되어 있어요.")
    st.rerun()


# ============================================
# 🆕 [탭 3개 생성]
# st.tabs() = 화면 상단에 클릭 가능한 탭들 만들기
# ============================================
tab_today, tab_goals, tab_calendar, tab_templates = st.tabs(["📋 오늘", "🎯 목표", "📅 달력", "🗂 템플릿"])


# ============================================
# 📋 [오늘 탭]
# ============================================
with tab_today:
    total = len(st.session_state.tasks)
    completed = sum(1 for t in st.session_state.tasks if t.get("status") == "done")
    expired = sum(1 for t in st.session_state.tasks if t.get("expired") and t.get("status") != "done")
    pending = total - completed - expired

    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("전체", total)
    col_b.metric("완료", completed)
    col_c.metric("진행 중", pending)
    col_d.metric("기한 초과", expired)

    st.divider()

    total_needed = sum(
        t["estimated_min"]
        for t in st.session_state.tasks
        if t.get("status") != "done" and not t.get("expired")
    )

    if total_needed > 0:
        if total_needed <= available_min:
            st.success(f"✅ 오늘 다 할 수 있어요! ({total_needed}분 / {available_min}분)")
        else:
            st.warning(f"⚠️ 시간 부족! {total_needed}분 필요한데 {available_min}분만 있음.")

    st.divider()

    st.subheader("📋 오늘의 칸반 보드")

    active_tasks = [
        (idx, task)
        for idx, task in enumerate(st.session_state.tasks)
        if not task.get("expired", False)
    ]

    todo_tasks = sorted(
        [(idx, task) for idx, task in active_tasks if task.get("status", "todo") == "todo"],
        key=lambda x: (
            -int(x[1].get("important", False)),
            x[1].get("deadline", "9999-12-31"),
            -int(x[1].get("urgent", False))
        )
    )

    doing_tasks = [
        (idx, task)
        for idx, task in active_tasks
        if task.get("status", "todo") == "doing"
    ]

    done_tasks = [
        (idx, task)
        for idx, task in active_tasks
        if task.get("status", "todo") == "done"
    ]

    col_todo, col_doing, col_done = st.columns(3)

    with col_todo:
        st.markdown("### To Do")
        for idx, task in todo_tasks:
            render_task(task, idx)

    with col_doing:
        st.markdown(f"### Doing ({len(doing_tasks)}/{WIP_LIMIT})")
        for idx, task in doing_tasks:
            render_task(task, idx)

    with col_done:
        st.markdown("### Done")
        for idx, task in done_tasks:
            render_task(task, idx)

    st.divider()
    st.subheader(f"⏰ 기한 초과 ({expired}개)")

    expired_tasks = [
        (i, t) for i, t in enumerate(st.session_state.tasks)
        if t.get("expired") and t.get("status") != "done"
    ]

    if not expired_tasks:
        st.caption("기한 초과된 일이 없어요. 잘하고 있어요! 👍")
    else:
        st.caption("마감일이 지났어요. 다시 일정을 잡거나 정리하세요.")
        for idx, task in expired_tasks:
            with st.container(border=True):
                st.write(f"**{task['title']}**")
                st.caption(f"⏱ {task['estimated_min']}분 | 📅 마감일이었던 날: {task['deadline']}")

                if task.get("description"):
                    with st.expander("📄 상세 보기"):
                        st.write(task["description"])

                col_done, col_reset, col_del = st.columns(3)

                with col_done:
                    if st.button("✅ 늦었지만 완료", key=f"exp_done_{task.get('id', idx)}", use_container_width=True):
                        st.session_state.tasks[idx]["status"] = "done"
                        st.session_state.tasks[idx]["completed"] = True
                        st.session_state.tasks[idx]["completed_at"] = str(today)
                        save_tasks(st.session_state.tasks)
                        st.rerun()

                with col_reset:
                    if st.button("🔄 오늘로 미루기", key=f"exp_reset_{task.get('id', idx)}", use_container_width=True):
                        st.session_state.tasks[idx]["deadline"] = str(today)
                        st.session_state.tasks[idx]["expired"] = False
                        st.session_state.tasks[idx]["status"] = "todo"
                        save_tasks(st.session_state.tasks)
                        st.rerun()

                with col_del:
                    if st.button("🗑 삭제", key=f"exp_del_{task.get('id', idx)}", use_container_width=True):
                        st.session_state.tasks.pop(idx)
                        save_tasks(st.session_state.tasks)
                        st.rerun()


# ============================================
# 🎯 [목표 탭 - 다음 단계에서 채울 자리]
# ============================================
# ============================================
# 🎯 [목표 탭 - 기본 CRUD]
# ============================================
with tab_goals:
    st.subheader("🎯 내 목표")

    # -----------------------------
    # 목표 추가 폼
    # -----------------------------
    with st.form("add_goal", clear_on_submit=True):
        goal_title = st.text_input("목표 제목")
        goal_description = st.text_area(
            "목표 설명",
            placeholder="예: 왜 이 목표를 세웠는지, 어떤 상태가 되면 완료인지 적어두기",
            height=100
        )
        goal_deadline = st.date_input("목표 마감일", value=today)

        template_options = ["(사용 안 함)"] + [t["name"] for t in st.session_state.templates]
        selected_template_name = st.selectbox("체크리스트 템플릿 불러오기", template_options)

        goal_submitted = st.form_submit_button("목표 추가", use_container_width=True)

        if goal_submitted and goal_title:
            new_items = []
            if selected_template_name != "(사용 안 함)":
                matched_template = next(
                    (t for t in st.session_state.templates if t["name"] == selected_template_name), None
                )
                if matched_template:
                    for item_text in matched_template["items"]:
                        new_items.append({
                            "item_id": uuid.uuid4().hex,
                            "text": item_text,
                            "done": False,
                            "sent_to_today": False
                        })

            st.session_state.goals.append({
                "id": len(st.session_state.goals),
                "title": goal_title,
                "description": goal_description,
                "deadline": str(goal_deadline),
                "progress": 0,
                "items": new_items
            })
            save_goals(st.session_state.goals)
            st.success("목표가 추가되었어요!" if not new_items else f"목표가 추가되었어요! 템플릿 항목 {len(new_items)}개도 함께 들어갔어요.")
            st.rerun()

    st.divider()

    # -----------------------------
    # 목표 목록
    # -----------------------------
    if not st.session_state.goals:
        st.caption("아직 등록한 목표가 없어요.")
    else:
        for idx, goal in enumerate(st.session_state.goals):
            # 진행률 계산
            total_items = len(goal.get("items", []))
            done_items = sum(1 for item in goal.get("items", []) if item["done"])
            progress = int((done_items / total_items) * 100) if total_items > 0 else 0

            # 계산된 진행률 저장
            st.session_state.goals[idx]["progress"] = progress

            goal_edit_key = f"editing_goal_{goal['id']}"
            if goal_edit_key not in st.session_state:
                st.session_state[goal_edit_key] = False

            with st.container(border=True):

                # -----------------------------
                # 목표 수정 모드
                # -----------------------------
                if st.session_state[goal_edit_key]:
                    new_goal_title = st.text_input(
                        "목표 제목", value=goal["title"], key=f"edit_goal_title_{goal['id']}"
                    )
                    new_goal_desc = st.text_area(
                        "목표 설명",
                        value=goal.get("description", ""),
                        key=f"edit_goal_desc_{goal['id']}",
                        height=100
                    )

                    col_gsave, col_gcancel = st.columns(2)
                    with col_gsave:
                        if st.button("💾 저장", key=f"save_goal_{goal['id']}", use_container_width=True):
                            st.session_state.goals[idx]["title"] = new_goal_title
                            st.session_state.goals[idx]["description"] = new_goal_desc
                            save_goals(st.session_state.goals)
                            st.session_state[goal_edit_key] = False
                            st.rerun()
                    with col_gcancel:
                        if st.button("취소", key=f"cancel_goal_{goal['id']}", use_container_width=True):
                            st.session_state[goal_edit_key] = False
                            st.rerun()

                    continue  # 수정 모드일 땐 체크리스트 등 나머지는 숨김

                # -----------------------------
                # 목표 일반 보기 모드
                # -----------------------------
                col_gtitle, col_gedit = st.columns([5, 1])
                with col_gtitle:
                    st.write(f"**{goal['title']}**")
                with col_gedit:
                    if st.button("✏", key=f"edit_goal_btn_{goal['id']}", use_container_width=True):
                        st.session_state[goal_edit_key] = True
                        st.rerun()

                st.caption(f"📅 마감일: {goal['deadline']}")
                st.progress(progress / 100)
                st.caption(f"진행률: {progress}% ({done_items}/{total_items})")

                if goal.get("description"):
                    with st.expander("📄 목표 설명 보기"):
                        st.write(goal["description"])

                # -----------------------------
                # 자기 진단 → 코칭 워크북
                # -----------------------------
                st.markdown("**🧭 자기 진단**")
                diagnosis = goal.get("diagnosis")

                if not diagnosis:
                    st.caption("이 목표, 지금 어느 정도 그려지나요?")
                    diag_cols = st.columns(3)
                    for col, (diag_key, (diag_label, _, _)) in zip(diag_cols, DIAGNOSIS.items()):
                        with col:
                            if st.button(diag_label, key=f"diag_{diag_key}_{idx}", use_container_width=True):
                                st.session_state.goals[idx]["diagnosis"] = diag_key
                                save_goals(st.session_state.goals)
                                st.rerun()
                else:
                    diag_label, diag_guide, diag_steps = DIAGNOSIS[diagnosis]

                    col_diag, col_diag_reset = st.columns([4, 1])
                    with col_diag:
                        st.caption(f"{diag_label} — {diag_guide}")
                    with col_diag_reset:
                        if st.button("↩ 다시", key=f"diag_reset_{idx}", use_container_width=True):
                            st.session_state.goals[idx]["diagnosis"] = None
                            save_goals(st.session_state.goals)
                            st.rerun()

                    if diag_steps:
                        written = sum(
                            1 for v in (goal.get("workbook") or {}).values() if has_answer(v)
                        )
                        with st.expander(f"✍️ {len(diag_steps)}단계 워크북 ({written}/{len(diag_steps)} 작성)"):
                            render_workbook(goal, idx, diag_steps)

                # -----------------------------
                # 체크리스트 추가 폼
                # -----------------------------
                with st.form(f"add_goal_item_{idx}", clear_on_submit=True):
                    new_item = st.text_input(
                        "체크리스트 추가",
                        key=f"goal_item_input_{idx}",
                        placeholder="예: 목표 탭 만들기"
                    )
                    item_submitted = st.form_submit_button("항목 추가", use_container_width=True)

                    if item_submitted and new_item:
                        st.session_state.goals[idx]["items"].append({
                            "item_id": uuid.uuid4().hex,
                            "text": new_item,
                            "done": False,
                            "sent_to_today": False
                        })
                        save_goals(st.session_state.goals)
                        st.success("체크리스트가 추가되었어요!")
                        st.rerun()

                # -----------------------------
                # 체크리스트 목록
                # -----------------------------
                if not goal.get("items", []):
                    st.caption("아직 체크리스트가 없어요.")
                else:
                    st.markdown("**체크리스트**")
                    for item_idx, item in enumerate(goal.get("items", [])):
                        item_edit_key = f"editing_item_{item['item_id']}"
                        if item_edit_key not in st.session_state:
                            st.session_state[item_edit_key] = False

                        # -----------------------------
                        # 체크리스트 항목 수정 모드
                        # -----------------------------
                        if st.session_state[item_edit_key]:
                            col_edit_text, col_isave, col_icancel = st.columns([6, 2, 2])
                            with col_edit_text:
                                new_item_text = st.text_input(
                                    "체크리스트 항목 수정",
                                    value=item["text"],
                                    key=f"edit_item_text_{idx}_{item_idx}",
                                    label_visibility="collapsed"
                                )
                            with col_isave:
                                if st.button("💾 저장", key=f"save_item_{idx}_{item_idx}", use_container_width=True):
                                    st.session_state.goals[idx]["items"][item_idx]["text"] = new_item_text
                                    save_goals(st.session_state.goals)
                                    st.session_state[item_edit_key] = False
                                    st.rerun()
                            with col_icancel:
                                if st.button("취소", key=f"cancel_item_{idx}_{item_idx}", use_container_width=True):
                                    st.session_state[item_edit_key] = False
                                    st.rerun()
                            continue  # 수정 모드일 땐 나머지 버튼들 숨김

                        already_in_today = any(
                            task.get("source_goal_id") == goal["id"] and
                            task.get("source_item_id") == item["item_id"] and
                            not task["completed"]
                            for task in st.session_state.tasks
                        )
                        col_text, col_minutes, col_today, col_action, col_edit, col_delete = st.columns([3.5, 1.5, 2, 1.5, 1, 1.5])

                        with col_text:
                            if item["done"]:
                                st.write(f"✅ ~~{item['text']}~~")
                            else:
                                st.write(f"⬜ {item['text']}")
                        
                        with col_minutes:
                            estimated_minutes = st.number_input(
                                "분",
                                min_value=5,
                                max_value=480,
                                value=30,
                                step=5,
                                key=f"item_minutes_{idx}_{item_idx}",
                                label_visibility="collapsed"
                            )

                        with col_today:
                            if already_in_today:
                                st.button(
                                    "📋 보냄",
                                    key=f"sent_item_{idx}_{item_idx}",
                                    use_container_width=True,
                                    disabled=True
                                )
                            else:
                                if st.button("📋 오늘 하기", key=f"send_today_{idx}_{item_idx}", use_container_width=True):
                                    st.session_state.tasks.append({
                                        "id": len(st.session_state.tasks),
                                        "title": item["text"],
                                        "description": f"목표: {goal['title']}\n\n{goal.get('description', '')}",
                                        "estimated_min": estimated_minutes,
                                        "deadline": goal["deadline"],
                                        "urgent": False,
                                        "important": True,
                                        "completed": False,
                                        "completed_at": None,
                                        "expired": False,
                                        "status": "todo",
                                        "source_goal": goal["title"],
                                        "source_goal_id": goal["id"],
                                        "source_item_id": item["item_id"]
                                    })
                                    save_tasks(st.session_state.tasks)
                                    st.success("오늘 할 일로 보냈어요!")
                                    st.rerun()

                        with col_action:
                            if item["done"]:
                                if st.button("↩ 되돌리기", key=f"undo_item_{idx}_{item_idx}", use_container_width=True):
                                    st.session_state.goals[idx]["items"][item_idx]["done"] = False
                                    save_goals(st.session_state.goals)
                                    st.rerun()
                            else:
                                if st.button("✅ 완료", key=f"done_item_{idx}_{item_idx}", use_container_width=True):
                                    st.session_state.goals[idx]["items"][item_idx]["done"] = True
                                    save_goals(st.session_state.goals)
                                    st.rerun()

                        with col_edit:
                            if st.button("✏", key=f"edit_item_btn_{idx}_{item_idx}", use_container_width=True):
                                st.session_state[item_edit_key] = True
                                st.rerun()

                        with col_delete:
                            if st.button("🗑 삭제", key=f"delete_item_{idx}_{item_idx}", use_container_width=True):
                                st.session_state.goals[idx]["items"].pop(item_idx)
                                save_goals(st.session_state.goals)
                                st.rerun()

                st.divider()

                # 목표 자체 삭제
                if st.button("🗑 목표 삭제", key=f"delete_goal_{idx}", use_container_width=True):
                    st.session_state.goals.pop(idx)
                    save_goals(st.session_state.goals)
                    st.success("목표를 삭제했어요.")
                    st.rerun()



# ============================================
# 📅 [달력 탭]
# ============================================
with tab_calendar:
    completed_count = sum(1 for t in st.session_state.tasks if t["completed"])
    st.subheader(f"✅ 완료한 일 ({completed_count}개)")
    
    # 완료 일자별로 묶기
    completed_by_date = {}
    for task in st.session_state.tasks:
        if task["completed"] and task.get("completed_at"):
            d = task["completed_at"]
            if d not in completed_by_date:
                completed_by_date[d] = []
            completed_by_date[d].append(task)
    
    # 달력 헤더
    col_prev, col_title, col_next = st.columns([1, 3, 1])
    
    with col_prev:
        if st.button("◀ 이전 달", use_container_width=True):
            if st.session_state.view_month == 1:
                st.session_state.view_month = 12
                st.session_state.view_year -= 1
            else:
                st.session_state.view_month -= 1
            st.rerun()
    
    with col_title:
        st.markdown(
            f"<h3 style='text-align: center;'>📅 {st.session_state.view_year}년 {st.session_state.view_month}월</h3>",
            unsafe_allow_html=True
        )
    
    with col_next:
        if st.button("다음 달 ▶", use_container_width=True):
            if st.session_state.view_month == 12:
                st.session_state.view_month = 1
                st.session_state.view_year += 1
            else:
                st.session_state.view_month += 1
            st.rerun()
    
    # 요일 헤더
    weekdays = ["월", "화", "수", "목", "금", "토", "일"]
    cols = st.columns(7)
    for i, day_name in enumerate(weekdays):
        with cols[i]:
            color = "blue" if i == 5 else "red" if i == 6 else "gray"
            st.markdown(f"<p style='text-align:center; color:{color}; font-weight:bold;'>{day_name}</p>",
                        unsafe_allow_html=True)
    
    # 달력 그리기
    cal = calendar.monthcalendar(st.session_state.view_year, st.session_state.view_month)
    
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            with cols[i]:
                if day == 0:
                    st.write("")
                else:
                    day_str = f"{st.session_state.view_year}-{st.session_state.view_month:02d}-{day:02d}"
                    count = len(completed_by_date.get(day_str, []))
                    is_today = (day_str == str(today))
                    
                    if count > 0:
                        label = f"{day}\n🟢 {count}"
                    elif is_today:
                        label = f"📍{day}"
                    else:
                        label = f"{day}"
                    
                    if st.button(label, key=f"cal_{day_str}", use_container_width=True):
                        if st.session_state.selected_date == day_str:
                            st.session_state.selected_date = None
                        else:
                            st.session_state.selected_date = day_str
                        st.rerun()
    
    # 선택한 날짜의 완료 목록
    if st.session_state.selected_date:
        st.divider()
        selected = st.session_state.selected_date
        tasks_on_day = completed_by_date.get(selected, [])
        
        st.markdown(f"### 📌 {selected} 완료한 일 ({len(tasks_on_day)}개)")
        
        if not tasks_on_day:
            st.caption("이 날짜에 완료한 일이 없어요.")
        else:
            for task in tasks_on_day:
                with st.expander(f"✓ {task['title']}"):
                    st.write(f"**📅 마감일이었던 날:** {task['deadline']}")
                    st.write(f"**⏱ 예상 소요시간:** {task['estimated_min']}분")
                    
                    if task.get("description"):
                        st.write("**📄 했던 일 상세:**")
                        st.write(task["description"])
                    else:
                        st.caption("상세 설명 없음")


# ============================================
# [템플릿 탭]
# 기획할 때 매번 챙겨야 하는 체크리스트를 미리 만들어두고,
# 목표를 새로 만들 때 그대로 불러와서 항목만 수정하는 용도
# ============================================
with tab_templates:
    st.subheader("🗂 내 템플릿")
    st.caption("기획할 때마다 반복되는 체크리스트를 템플릿으로 만들어두면, 목표를 만들 때 그대로 불러와서 쓸 수 있어요.")

    # -----------------------------
    # 템플릿 추가 폼
    # -----------------------------
    with st.form("add_template", clear_on_submit=True):
        template_name = st.text_input("템플릿 이름", placeholder="예: 기획 착수 전 체크리스트")
        template_submitted = st.form_submit_button("템플릿 추가", use_container_width=True)

        if template_submitted and template_name:
            st.session_state.templates.append({
                "id": uuid.uuid4().hex,
                "name": template_name,
                "items": []
            })
            save_templates(st.session_state.templates)
            st.success("템플릿이 추가되었어요! 이제 항목을 채워보세요.")
            st.rerun()

    st.divider()

    # -----------------------------
    # 템플릿 목록
    # -----------------------------
    if not st.session_state.templates:
        st.caption("아직 만든 템플릿이 없어요.")
    else:
        for t_idx, template in enumerate(st.session_state.templates):
            template_edit_key = f"editing_template_{template['id']}"
            if template_edit_key not in st.session_state:
                st.session_state[template_edit_key] = False

            with st.container(border=True):

                # 템플릿 이름 수정 모드
                if st.session_state[template_edit_key]:
                    new_template_name = st.text_input(
                        "템플릿 이름", value=template["name"], key=f"edit_template_name_{template['id']}"
                    )
                    col_tsave, col_tcancel = st.columns(2)
                    with col_tsave:
                        if st.button("💾 저장", key=f"save_template_{template['id']}", use_container_width=True):
                            st.session_state.templates[t_idx]["name"] = new_template_name
                            save_templates(st.session_state.templates)
                            st.session_state[template_edit_key] = False
                            st.rerun()
                    with col_tcancel:
                        if st.button("취소", key=f"cancel_template_{template['id']}", use_container_width=True):
                            st.session_state[template_edit_key] = False
                            st.rerun()
                    continue

                col_tname, col_tedit, col_tdelete = st.columns([5, 1, 1])
                with col_tname:
                    st.write(f"**{template['name']}**")
                with col_tedit:
                    if st.button("✏", key=f"edit_template_btn_{template['id']}", use_container_width=True):
                        st.session_state[template_edit_key] = True
                        st.rerun()
                with col_tdelete:
                    if st.button("🗑", key=f"delete_template_{template['id']}", use_container_width=True):
                        st.session_state.templates.pop(t_idx)
                        save_templates(st.session_state.templates)
                        st.rerun()

                st.caption(f"항목 {len(template['items'])}개")

                with st.expander("상세 보기 / 항목 관리"):
                    # 템플릿 항목 목록
                    for i_idx, item_text in enumerate(template["items"]):
                        item_edit_key = f"editing_template_item_{template['id']}_{i_idx}"
                        if item_edit_key not in st.session_state:
                            st.session_state[item_edit_key] = False

                        if st.session_state[item_edit_key]:
                            col_ie, col_isave, col_icancel = st.columns([5, 1.5, 1.5])
                            with col_ie:
                                new_item_text = st.text_input(
                                    "항목 수정", value=item_text,
                                    key=f"edit_template_item_{template['id']}_{i_idx}",
                                    label_visibility="collapsed"
                                )
                            with col_isave:
                                if st.button("💾", key=f"save_template_item_{template['id']}_{i_idx}", use_container_width=True):
                                    st.session_state.templates[t_idx]["items"][i_idx] = new_item_text
                                    save_templates(st.session_state.templates)
                                    st.session_state[item_edit_key] = False
                                    st.rerun()
                            with col_icancel:
                                if st.button("취소", key=f"cancel_template_item_{template['id']}_{i_idx}", use_container_width=True):
                                    st.session_state[item_edit_key] = False
                                    st.rerun()
                        else:
                            col_text, col_edit_i, col_delete_i = st.columns([5, 1.5, 1.5])
                            with col_text:
                                st.write(f"• {item_text}")
                            with col_edit_i:
                                if st.button("✏", key=f"edit_template_item_btn_{template['id']}_{i_idx}", use_container_width=True):
                                    st.session_state[item_edit_key] = True
                                    st.rerun()
                            with col_delete_i:
                                if st.button("🗑", key=f"delete_template_item_{template['id']}_{i_idx}", use_container_width=True):
                                    st.session_state.templates[t_idx]["items"].pop(i_idx)
                                    save_templates(st.session_state.templates)
                                    st.rerun()

                    # 템플릿 항목 추가
                    with st.form(f"add_template_item_{template['id']}", clear_on_submit=True):
                        new_item = st.text_input("새 항목", key=f"new_template_item_{template['id']}", label_visibility="collapsed", placeholder="예: 타겟 사용자 정의하기")
                        if st.form_submit_button("항목 추가", use_container_width=True):
                            if new_item:
                                st.session_state.templates[t_idx]["items"].append(new_item)
                                save_templates(st.session_state.templates)
                                st.rerun()