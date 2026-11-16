import os
import json
import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.spatial.transform import Rotation as R

st.set_page_config(page_title="Bowling 3D Layout & Track Simulator", layout="wide")
st.title("🎳 볼링 지공 레이아웃 & 코어 활성화 3D 시뮬레이터")

BALL_RADIUS = 4.295  # 15파운드 표준 반지름 (inch)
PRESET_FILE = "bowling_presets.json"

# ==========================================
# 기본 프리셋 데이터
# ==========================================
DEFAULT_PRESETS = {
    "Awesome_data": {
        "drill_hole_type": "원핸드 (3홀 - 엄지 포함)",
        "span_inch": 4.25,
        "thumb_offset": 0.5,
        "pap_x": 6.125,
        "pap_y": 0.1875,
        "layout_system": "Dual Angle (Drilling × Pin-to-PAP × VAL)",
        "pin_to_psa": 3.0,
        "drill_angle": 40,
        "pin_to_pap": 5.625,
        "val_angle": 40,
        "ls2_key": "3번: 5\" × 4\" × 3½\" (벤치마크 레이아웃 / 올라운드)",
        "ls2_pin_pap": 5.0,
        "ls2_pin_cog": 4.0,
        "ls2_buffer": 3.5,
        "vls_pin_pap": 5.625,
        "vls_psa_pap": 4.0,
        "vls_pin_val": 3.5,
        "vls_pin_pos": "Pin Up (VAL 위쪽)",
        "rg": 2.483,
        "diff": 0.052,
        "int_diff": 0.014,
        "cover_type": "하이브리드 리액티브 (Hybrid)",
        "surface_grit": 2000,
        "speed_kmh": 31.0,
        "rpm": 525,
        "axis_rot": 43,
        "axis_tilt": -2,
        "oil_length": 42,
        "start_board": 28,
        "target_board": 14
    }
}

def load_presets():
    if not os.path.exists(PRESET_FILE):
        with open(PRESET_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_PRESETS, f, ensure_ascii=False, indent=2)
        return DEFAULT_PRESETS.copy()
    with open(PRESET_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    if "Awesome_data" not in data:
        data["Awesome_data"] = DEFAULT_PRESETS["Awesome_data"]
        save_presets(data)
    elif data["Awesome_data"].get("thumb_offset") != 0.5:
        data["Awesome_data"]["thumb_offset"] = 0.5
        save_presets(data)
    return data

def save_presets(presets_dict):
    with open(PRESET_FILE, "w", encoding="utf-8") as f:
        json.dump(presets_dict, f, ensure_ascii=False, indent=2)

def apply_preset_to_state(preset_data):
    for k, v in preset_data.items():
        st.session_state[k] = v
    if "thumb_offset" not in preset_data:
        st.session_state["thumb_offset"] = 0.5

presets = load_presets()

if "initialized" not in st.session_state:
    apply_preset_to_state(presets["Awesome_data"])
    st.session_state["active_preset_name"] = "Awesome_data"
    st.session_state["initialized"] = True

# ==========================================
# 메인 화면 상단: 저장된 프리셋 원클릭 선택 바
# ==========================================
st.markdown("#### 📂 저장된 선수/데이터 프리셋 (클릭 시 즉시 적용)")
preset_names = list(presets.keys())
btn_cols = st.columns(min(len(preset_names) + 1, 6))

for idx, p_name in enumerate(preset_names):
    with btn_cols[idx % 6]:
        is_active = (st.session_state.get("active_preset_name") == p_name)
        btn_label = f"✅ {p_name}" if is_active else f"📌 {p_name}"
        if st.button(btn_label, key=f"btn_load_{p_name}", use_container_width=True):
            apply_preset_to_state(presets[p_name])
            st.session_state["active_preset_name"] = p_name
            st.rerun()

st.divider()

TWO_LS_PRESETS = {
    "1번: 5½\" × 5\" × 2\" (매우 낮은 플레어 / 백엔드 큰 앵글)": {
        "p2pap": 5.5, "p2cog": 5.0, "buffer": 2.0,
        "desc": "매우 낮은 플레어, 헤드·미드레인 통과율이 높고 백엔드에서 큰 앵글 형성"
    },
    "2번: 2\" × 6\" × 5\" (안정적·부드러운 앵글 / 고회전용)": {
        "p2pap": 2.0, "p2cog": 6.0, "buffer": 5.0,
        "desc": "안정적이고 부드러운 앵글. 쇼트 오일 및 드라이한 백엔드에서 컨트롤이 용이"
    },
    "3번: 5\" × 4\" × 3½\" (벤치마크 레이아웃 / 올라운드)": {
        "p2pap": 5.0, "p2cog": 4.0, "buffer": 3.5,
        "desc": "벤치마크 레이아웃. 파워와 컨트롤이 이상적으로 혼합되어 다양한 패턴 파악에 효과적"
    },
    "4번: 4½\" × 3\" × 4½\" (미드레인 마찰 / 미디엄-롱 패턴)": {
        "p2pap": 4.5, "p2cog": 3.0, "buffer": 4.5,
        "desc": "3번 대비 미드레인 마찰을 높이고 백엔드 전진성을 높임"
    },
    "5번: 4\" × 4\" × 5\" (강한 헤드 마찰 / 우레탄·변화 레인)": {
        "p2pap": 4.0, "p2cog": 4.0, "buffer": 5.0,
        "desc": "레인 헤드에서 강한 마찰력 유도. 우레탄 커버 또는 레인 변화 시점에 효과적"
    },
    "6번: 3½\" × 4\" × 6½\" (가장 강한 조기 반응 / 헤비·플랫 오일)": {
        "p2pap": 3.5, "p2cog": 4.0, "buffer": 6.5,
        "desc": "전진성이 강하고 가장 공격적인 움직임. 정비 직후 헤비 오일·플랫 패턴용"
    }
}

# ==========================================
# 1. 구면 기하학 유틸리티 함수
# ==========================================
def move_on_sphere(start_vec, tangent_dir, dist_inch, ball_r=BALL_RADIUS):
    s = start_vec / np.linalg.norm(start_vec)
    t = tangent_dir - np.dot(tangent_dir, s) * s
    if np.linalg.norm(t) < 1e-8:
        return s
    t /= np.linalg.norm(t)
    theta = dist_inch / ball_r
    return s * np.cos(theta) + t * np.sin(theta)

def rotate_tangent(normal_vec, tangent_vec, angle_deg):
    rot = R.from_rotvec(np.radians(angle_deg) * (normal_vec / np.linalg.norm(normal_vec)))
    return rot.apply(tangent_vec)

def intersect_two_sphere_circles(c1, d1_inch, c2, d2_inch, prefer_dir=None, ball_r=BALL_RADIUS):
    u1 = c1 / np.linalg.norm(c1)
    u2 = c2 / np.linalg.norm(c2)
    
    cos_a = np.cos(d1_inch / ball_r)
    cos_b = np.cos(d2_inch / ball_r)
    dot12 = np.clip(np.dot(u1, u2), -0.9999, 0.9999)
    
    denom = 1.0 - dot12**2
    alpha = (cos_a - cos_b * dot12) / denom
    beta = (cos_b - cos_a * dot12) / denom
    
    base = alpha * u1 + beta * u2
    norm_base_sq = np.dot(base, base)
    
    cross_u = np.cross(u1, u2)
    cross_norm = np.linalg.norm(cross_u)
    
    if norm_base_sq >= 1.0 or cross_norm < 1e-7:
        return base / np.linalg.norm(base)
        
    gamma = np.sqrt(max(0.0, 1.0 - norm_base_sq)) / cross_norm
    p_plus = base + gamma * cross_u
    p_minus = base - gamma * cross_u
    
    if prefer_dir is not None:
        return p_plus if np.dot(p_plus, prefer_dir) >= np.dot(p_minus, prefer_dir) else p_minus
    return p_plus

def get_great_circle_arc(p1, p2, ball_r=BALL_RADIUS, num_pts=30):
    p1 = p1 / np.linalg.norm(p1)
    p2 = p2 / np.linalg.norm(p2)
    omega = np.arccos(np.clip(np.dot(p1, p2), -1.0, 1.0))
    if omega < 1e-6:
        return np.outer(p1, np.ones(num_pts)) * ball_r
    t = np.linspace(0, 1, num_pts)
    arc = (np.sin((1 - t) * omega)[:, None] * p1 + np.sin(t * omega)[:, None] * p2) / np.sin(omega)
    return (arc * ball_r).T

def get_surface_circle(center_vec, hole_radius_inch, ball_r=BALL_RADIUS, num_pts=40):
    n = center_vec / np.linalg.norm(center_vec)
    ref = np.array([0.0, 0.0, 1.0]) if abs(n[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    u_vec = np.cross(n, ref)
    u_vec /= np.linalg.norm(u_vec)
    v_vec = np.cross(n, u_vec)
    angular_r = hole_radius_inch / ball_r
    theta = np.linspace(0, 2 * np.pi, num_pts)
    return (ball_r * np.cos(angular_r) * n[:, None] +
            ball_r * np.sin(angular_r) * (u_vec[:, None] * np.cos(theta) + v_vec[:, None] * np.sin(theta)))

# ==========================================
# 2. 사이드바 UI
# ==========================================
with st.sidebar:
    st.header("1. 지공 홀 타입 & PAP 설정")
    drill_hole_type = st.radio(
        "그립 형태",
        ["원핸드 (3홀 - 엄지 포함)", "투핸드 / 덤리스 (2홀 - 엄지 없음)"],
        key="drill_hole_type"
    )
    has_thumb = "3홀" in drill_hole_type

    if has_thumb:
        span_inch = st.slider("원핸드 스팬 길이 (중약지~엄지, inch)", 3.5, 5.25, step=0.125, format="%.3f", key="span_inch")
        thumb_offset = st.slider(
            "엄지 옵셋 (Thumb Offset, +는 좌측 이동, inch)",
            min_value=-0.50, max_value=1.00, step=0.0625, format="%.4f", key="thumb_offset"
        )
    else:
        span_inch = 0.0
        thumb_offset = 0.0

    col_pap1, col_pap2 = st.columns(2)
    with col_pap1:
        pap_x = st.number_input("PAP 가로 (over, inch)", min_value=2.0, max_value=7.5, step=0.0625, format="%.4f", key="pap_x")
    with col_pap2:
        pap_y = st.number_input("PAP 상/하 (up/down, inch)", min_value=-2.5, max_value=3.0, step=0.0625, format="%.4f", key="pap_y")

    st.divider()
    st.header("2. 지공 레이아웃 시스템 선택")
    layout_system = st.selectbox(
        "레이아웃 방식",
        [
            "Dual Angle (Drilling × Pin-to-PAP × VAL)",
            "2LS - 투핸드 공식 차트 (1번~6번 & 커스텀)",
            "VLS (Pin-to-PAP × PSA-to-PAP × Pin-to-VAL)"
        ],
        key="layout_system"
    )

    pin_to_psa = st.slider("볼 고유 Pin-to-PSA 거리 (inch)", 2.0, 6.75, step=0.125, format="%.3f", key="pin_to_psa")

    if "Dual Angle" in layout_system:
        st.caption("형식: Drilling Angle(°) × Pin-to-PAP(\") × VAL Angle(°)")
        drill_angle = st.slider("Drilling Angle (드릴링 각도 °)", 10, 90, step=5, key="drill_angle")
        pin_to_pap = st.slider("Pin-to-PAP 거리 (inch)", 1.0, 6.75, step=0.125, format="%.3f", key="pin_to_pap")
        val_angle = st.slider("VAL Angle (VAL 각도 °)", 10, 90, step=5, key="val_angle")

    elif "2LS" in layout_system:
        def on_2ls_preset_change():
            p = TWO_LS_PRESETS[st.session_state["ls2_key"]]
            st.session_state["ls2_pin_pap"] = float(p["p2pap"])
            st.session_state["ls2_pin_cog"] = float(p["p2cog"])
            st.session_state["ls2_buffer"] = float(p["buffer"])

        selected_2ls_key = st.selectbox(
            "2LS 표준 지공표 선택 (1번=약함 → 6번=강함)",
            list(TWO_LS_PRESETS.keys()),
            key="ls2_key",
            on_change=on_2ls_preset_change
        )
        st.info(TWO_LS_PRESETS[selected_2ls_key]["desc"])

        ls2_pin_pap = st.slider("1번 수치: Pin-to-PAP (inch)", 1.5, 6.5, step=0.125, format="%.3f", key="ls2_pin_pap")
        ls2_pin_cog = st.slider("2번 수치: Pin-to-COG (inch)", 1.5, 6.5, step=0.125, format="%.3f", key="ls2_pin_cog")
        ls2_buffer  = st.slider("3번 수치: Pin-buffer / PSA 오프셋 (inch)", 1.0, 7.0, step=0.125, format="%.3f", key="ls2_buffer")

    elif "VLS" in layout_system:
        st.caption("형식: Pin-to-PAP(\") × PSA-to-PAP(\") × Pin-to-VAL(\")")
        vls_pin_pap = st.slider("1번 수치: Pin-to-PAP 거리 (inch)", 1.0, 6.75, step=0.125, format="%.3f", key="vls_pin_pap")
        vls_psa_pap = st.slider("2번 수치: PSA-to-PAP 거리 (inch)", 1.5, 6.5, step=0.125, format="%.3f", key="vls_psa_pap")
        vls_pin_val = st.slider("3번 수치: Pin-to-VAL 거리 (inch)", 0.5, 5.5, step=0.125, format="%.3f", key="vls_pin_val")
        vls_pin_pos = st.radio("Pin 상/하 위치", ["Pin Up (VAL 위쪽)", "Pin Down (VAL 아래쪽)"], key="vls_pin_pos")

    st.divider()
    st.header("3. 볼 코어 3대 요소 & 외피 스펙")
    col_spec1, col_spec2, col_spec3 = st.columns(3)
    with col_spec1:
        rg = st.number_input("RG (2.43~2.80)", min_value=2.430, max_value=2.800, step=0.001, format="%.3f", key="rg")
    with col_spec2:
        diff = st.number_input("RG Diff (0~0.06)", min_value=0.000, max_value=0.060, step=0.001, format="%.3f", key="diff")
    with col_spec3:
        int_diff = st.number_input("Inter Diff (PSA)", min_value=0.000, max_value=0.037, step=0.001, format="%.3f", key="int_diff")

    rg_grade = "로우 RG (조기 롤)" if rg <= 2.540 else ("미디움 RG" if rg <= 2.690 else "하이 RG (긴 스키드)")
    diff_grade = "로우 Diff (적은 플레어)" if diff <= 0.020 else ("미디움 Diff (중간 플레어)" if diff <= 0.040 else "하이 Diff (많은 플레어)")
    int_grade = "대칭 코어" if int_diff < 0.005 else ("로우 MB (느린 반응)" if int_diff <= 0.020 else "하이 MB (빠른 전환)")
    st.caption(f"📊 코어 판정: **{rg_grade}** | **{diff_grade}** | **{int_grade}**")

    cover_type = st.selectbox(
        "외피 재질 (성능 비중 60~70%)",
        [
            "솔리드 리액티브 (Solid - 강한 오일 마찰)",
            "하이브리드 리액티브 (Hybrid)",
            "펄 리액티브 (Pearl - 긴 스키드/백엔드)",
            "우레탄 (Urethane - 컨트롤)",
            "플라스틱 / 폴리에스터 (스페어용)"
        ],
        key="cover_type"
    )
    surface_grit = st.select_slider(
        "표면 샌딩 그릿 (낮을수록 거침/트레드 효과 증가)",
        options=[360, 500, 1000, 1500, 2000, 3000, 4000],
        key="surface_grit"
    )

    st.divider()
    st.header("4. 투구 스펙 & 레인 조건")
    speed_kmh = st.slider("볼 스피드 (km/h)", 18.0, 36.0, step=0.5, key="speed_kmh")
    speed_mph = speed_kmh / 1.60934
    rpm = st.slider("회전수 (RPM)", 150, 650, step=5, key="rpm")
    axis_rot = st.slider("Axis Rotation (축 회전 °)", 0, 90, step=1, key="axis_rot")
    axis_tilt = st.slider("Axis Tilt (축 기울기 °)", -30, 60, step=1, key="axis_tilt")

    oil_length = st.slider("오일 패턴 길이 (ft)", 32, 48, step=1, key="oil_length")
    start_board = st.slider("스탠스 출발 보드 (번)", 5, 38, step=1, key="start_board")
    target_board = st.slider("에이밍 타겟 보드 (15ft 지점)", 3, 30, step=1, key="target_board")

    st.divider()
    st.header("💾 새 데이터 프리셋 저장")
    new_preset_name = st.text_input("저장할 이름 입력", placeholder="예: 내_마이볼_데이터")
    if st.button("현재 세팅 저장하기", use_container_width=True):
        clean_name = new_preset_name.strip()
        if clean_name:
            presets[clean_name] = {
                "drill_hole_type": st.session_state["drill_hole_type"],
                "span_inch": st.session_state.get("span_inch", 4.25),
                "thumb_offset": st.session_state.get("thumb_offset", 0.5),
                "pap_x": st.session_state["pap_x"],
                "pap_y": st.session_state["pap_y"],
                "layout_system": st.session_state["layout_system"],
                "pin_to_psa": st.session_state["pin_to_psa"],
                "drill_angle": st.session_state.get("drill_angle", 40),
                "pin_to_pap": st.session_state.get("pin_to_pap", 5.625),
                "val_angle": st.session_state.get("val_angle", 40),
                "ls2_key": st.session_state.get("ls2_key", list(TWO_LS_PRESETS.keys())[2]),
                "ls2_pin_pap": st.session_state.get("ls2_pin_pap", 5.0),
                "ls2_pin_cog": st.session_state.get("ls2_pin_cog", 4.0),
                "ls2_buffer": st.session_state.get("ls2_buffer", 3.5),
                "vls_pin_pap": st.session_state.get("vls_pin_pap", 5.625),
                "vls_psa_pap": st.session_state.get("vls_psa_pap", 4.0),
                "vls_pin_val": st.session_state.get("vls_pin_val", 3.5),
                "vls_pin_pos": st.session_state.get("vls_pin_pos", "Pin Up (VAL 위쪽)"),
                "rg": st.session_state["rg"],
                "diff": st.session_state["diff"],
                "int_diff": st.session_state["int_diff"],
                "cover_type": st.session_state["cover_type"],
                "surface_grit": st.session_state["surface_grit"],
                "speed_kmh": st.session_state["speed_kmh"],
                "rpm": st.session_state["rpm"],
                "axis_rot": st.session_state["axis_rot"],
                "axis_tilt": st.session_state["axis_tilt"],
                "oil_length": st.session_state["oil_length"],
                "start_board": st.session_state["start_board"],
                "target_board": st.session_state["target_board"]
            }
            save_presets(presets)
            st.session_state["active_preset_name"] = clean_name
            st.success(f"'{clean_name}' 저장 완료!")
            st.rerun()

# ==========================================
# 3. 오른손 볼러 정석 기준 좌표 계산
# ==========================================
grip_center_dir = np.array([0.0, -1.0, 0.0])  # 정면(-Y) = 그립 중심(CG)

if has_thumb:
    half_span = span_inch / 2.0
    finger_bridge_center = move_on_sphere(grip_center_dir, np.array([0.0, 0.0, 1.0]), half_span)
    middle_dir = move_on_sphere(finger_bridge_center, np.array([-1.0, 0.0, 0.0]), 0.55)
    ring_dir   = move_on_sphere(finger_bridge_center, np.array([1.0, 0.0, 0.0]), 0.55)

    vertical_span_comp = np.sqrt(max(0.0, span_inch**2 - thumb_offset**2))
    thumb_base_dir = move_on_sphere(finger_bridge_center, np.array([0.0, 0.0, -1.0]), vertical_span_comp)
    thumb_dir = move_on_sphere(thumb_base_dir, np.array([-1.0, 0.0, 0.0]), thumb_offset)
else:
    finger_bridge_center = move_on_sphere(grip_center_dir, np.array([0.0, 0.0, 1.0]), 0.3)
    middle_dir = move_on_sphere(finger_bridge_center, np.array([-1.0, 0.0, 0.0]), 0.55)
    ring_dir   = move_on_sphere(finger_bridge_center, np.array([1.0, 0.0, 0.0]), 0.55)
    thumb_dir  = None

pap_temp = move_on_sphere(grip_center_dir, np.array([1.0, 0.0, 0.0]), pap_x)
up_dir = np.array([0.0, 0.0, 1.0]) if pap_y >= 0 else np.array([0.0, 0.0, -1.0])
pap_vec = move_on_sphere(pap_temp, up_dir, abs(pap_y))

val_up_tangent = np.array([0.0, 0.0, 1.0]) - np.dot(np.array([0.0, 0.0, 1.0]), pap_vec) * pap_vec
val_up_tangent /= np.linalg.norm(val_up_tangent)

if "Dual Angle" in layout_system:
    pin_dir_from_pap = rotate_tangent(pap_vec, val_up_tangent, +val_angle)
    pin_vec = move_on_sphere(pap_vec, pin_dir_from_pap, pin_to_pap)

    pin_to_pap_tangent = pap_vec - np.dot(pap_vec, pin_vec) * pin_vec
    pin_to_pap_tangent /= np.linalg.norm(pin_to_pap_tangent)

    psa_dir_from_pin = rotate_tangent(pin_vec, pin_to_pap_tangent, -drill_angle)
    psa_vec = move_on_sphere(pin_vec, psa_dir_from_pin, pin_to_psa)

    layout_summary_str = f"Dual Angle: {drill_angle}° × {pin_to_pap:.3f}\" × {val_angle}°"
    effective_val_deg = val_angle
    effective_pin_pap = pin_to_pap

elif "2LS" in layout_system:
    prefer_pin = np.array([-0.2, -0.4, 0.9])
    pin_vec = intersect_two_sphere_circles(pap_vec, ls2_pin_pap, grip_center_dir, ls2_pin_cog, prefer_dir=prefer_pin)

    pin_to_pap_tangent = pap_vec - np.dot(pap_vec, pin_vec) * pin_vec
    if np.linalg.norm(pin_to_pap_tangent) > 1e-6:
        pin_to_pap_tangent /= np.linalg.norm(pin_to_pap_tangent)
    else:
        pin_to_pap_tangent = np.array([1.0, 0.0, 0.0])

    equiv_drill_angle = np.clip((ls2_buffer / 6.75) * 90.0, 15.0, 95.0)
    psa_dir_from_pin = rotate_tangent(pin_vec, pin_to_pap_tangent, -equiv_drill_angle)
    psa_vec = move_on_sphere(pin_vec, psa_dir_from_pin, pin_to_psa)

    effective_val_deg = np.clip(90.0 - (ls2_buffer * 10.0), 15.0, 80.0)
    effective_pin_pap = ls2_pin_pap
    layout_summary_str = f"2LS: {ls2_pin_pap:.3f}\" × {ls2_pin_cog:.3f}\" × {ls2_buffer:.3f}\""

elif "VLS" in layout_system:
    sin_val = np.clip(np.sin(vls_pin_val / BALL_RADIUS) / max(1e-4, np.sin(vls_pin_pap / BALL_RADIUS)), 0.0, 1.0)
    calc_val_deg = np.degrees(np.arcsin(sin_val))
    if "Down" in vls_pin_pos:
        calc_val_deg = 180.0 - calc_val_deg
        
    pin_dir_from_pap = rotate_tangent(pap_vec, val_up_tangent, +calc_val_deg)
    pin_vec = move_on_sphere(pap_vec, pin_dir_from_pap, vls_pin_pap)
    
    prefer_psa = np.array([0.3, -0.5, -0.8])
    psa_vec = intersect_two_sphere_circles(pin_vec, pin_to_psa, pap_vec, vls_psa_pap, prefer_dir=prefer_psa)

    layout_summary_str = f"VLS: {vls_pin_pap:.3f}\" × {vls_psa_pap:.3f}\" × {vls_pin_val:.3f}\""
    effective_val_deg = calc_val_deg
    effective_pin_pap = vls_pin_pap

pin_pos = pin_vec * BALL_RADIUS
psa_pos = psa_vec * BALL_RADIUS

# ==========================================
# 코어 3축 정렬 (X=Pin 최저 RG, Y=PSA 최고 RG, Z=중간 RG)
# ==========================================
x_core_pin = pin_vec / np.linalg.norm(pin_vec)
y_core_psa = psa_vec - np.dot(psa_vec, x_core_pin) * x_core_pin
if np.linalg.norm(y_core_psa) > 1e-6:
    y_core_psa /= np.linalg.norm(y_core_psa)
else:
    y_core_psa = val_up_tangent
z_core_mid = np.cross(x_core_pin, y_core_psa)
core_rot_matrix = np.column_stack([x_core_pin, y_core_psa, z_core_mid])

cx_len = 3.0
cy_len = 2.1 * (1.0 - diff * 3.0)
cz_len = cy_len * (1.0 - int_diff * 8.0)

u = np.linspace(0, 2 * np.pi, 32)
v = np.linspace(0, np.pi, 32)
core_pts = np.stack([
    (cx_len * np.cos(v)[None, :] * np.ones_like(u)[:, None]).flatten(),
    (cy_len * np.outer(np.cos(u), np.sin(v))).flatten(),
    (cz_len * np.outer(np.sin(u), np.sin(v))).flatten()
], axis=1) @ core_rot_matrix.T
rc_x = core_pts[:, 0].reshape((32, 32))
rc_y = core_pts[:, 1].reshape((32, 32))
rc_z = core_pts[:, 2].reshape((32, 32))

# ==========================================
# 4. [스키드 → 훅 → 롤] 물리 엔진
# ==========================================
spin_axis_init = pap_vec / np.linalg.norm(pap_vec)

pin_to_pap_rad = np.arccos(np.clip(np.dot(spin_axis_init, x_core_pin), -1.0, 1.0))
sym_flare_efficiency = max(0.35, abs(np.sin(2.0 * min(pin_to_pap_rad, np.pi - pin_to_pap_rad))))

is_asymmetric = (int_diff >= 0.005)
if is_asymmetric:
    target_spin_axis = psa_vec if np.dot(spin_axis_init, psa_vec) >= 0 else -psa_vec
    target_spin_axis /= np.linalg.norm(target_spin_axis)
    total_axis_gap_rad = np.arccos(np.clip(np.dot(spin_axis_init, target_spin_axis), -1.0, 1.0))
    asym_gap_efficiency = max(0.40, np.sin(min(total_axis_gap_rad, np.pi / 2.0)))
    layout_flare_factor = 0.50 * sym_flare_efficiency + 0.50 * asym_gap_efficiency
else:
    proj_on_pin = np.dot(spin_axis_init, x_core_pin) * x_core_pin
    eq_vec = spin_axis_init - proj_on_pin
    target_spin_axis = (eq_vec / np.linalg.norm(eq_vec)) if np.linalg.norm(eq_vec) > 1e-6 else y_core_psa
    total_axis_gap_rad = np.arccos(np.clip(np.dot(spin_axis_init, target_spin_axis), -1.0, 1.0))
    layout_flare_factor = sym_flare_efficiency

pap_to_psa_inch = total_axis_gap_rad * BALL_RADIUS

diff_norm = np.clip(diff / 0.050, 0.0, 1.30)
diff_area_scale = diff_norm ** 1.35

rg_area_mult = np.clip(1.0 + ((2.52 - rg) / 0.12) * 0.25, 0.70, 1.25)
rg_activation_speed = 1.0 + ((2.55 - rg) / 0.15) * 0.55

target_flare_inch = (8.2 * diff_area_scale * rg_area_mult) * (0.45 + 0.55 * layout_flare_factor)
effective_max_gap_rad = max(total_axis_gap_rad, np.radians(115.0))
actual_max_flare_rad = min(effective_max_gap_rad, target_flare_inch / BALL_RADIUS)

rg_skid_offset = ((rg - 2.50) / 0.15) * 0.08
cover_skid_map = {
    "솔리드 리액티브 (Solid - 강한 오일 마찰)": -0.07,
    "하이브리드 리액티브 (Hybrid)": 0.00,
    "펄 리액티브 (Pearl - 긴 스키드/백엔드)": +0.08,
    "우레탄 (Urethane - 컨트롤)": -0.10,
    "플라스틱 / 폴리에스터 (스페어용)": +0.25
}
grit_skid_offset = ((surface_grit - 2000) / 2000.0) * 0.05
early_val_offset = -((90.0 - min(90.0, effective_val_deg)) / 60.0) * 0.05
skid_end_ft = oil_length * np.clip(0.50 + rg_skid_offset + cover_skid_map.get(cover_type, 0.0) + grit_skid_offset + early_val_offset, 0.30, 0.75)

cover_friction_map = {
    "솔리드 리액티브 (Solid - 강한 오일 마찰)": 1.28,
    "하이브리드 리액티브 (Hybrid)": 1.05,
    "펄 리액티브 (Pearl - 긴 스키드/백엔드)": 0.92,
    "우레탄 (Urethane - 컨트롤)": 0.72,
    "플라스틱 / 폴리에스터 (스페어용)": 0.20
}
cover_mult = cover_friction_map.get(cover_type, 1.0)
grit_mult = 1.0 + (2000 - surface_grit) / 4000.0
total_surface_grip = cover_mult * grit_mult

dt = 0.005
y_ft = 0.0
elapsed_time = 0.0
x_board = float(start_board)

speed_fps = speed_mph * 1.46667
init_angle_rad = np.arctan2((target_board - start_board) * 1.06 / 12.0, 15.0)
vx = speed_fps * np.sin(init_angle_rad)
vy = speed_fps * np.cos(init_angle_rad)

omega = rpm * 2 * np.pi / 60.0
curr_rot = np.radians(axis_rot)
curr_tilt = np.radians(axis_tilt)

migrated_rad = 0.0
axis_history_rad = []
phase_history = []
rev_history = []

mb_response_factor = 1.0 + (int_diff * 15.0)

traj_x, traj_y = [], []
breakpoint_ft = None
max_right_board = start_board
roll_start_ft = None

est_flare_time = 45.0 / max(10.0, vy)

while y_ft <= 60.0:
    traj_x.append(x_board)
    traj_y.append(y_ft)
    revs_elapsed = (rpm / 60.0) * elapsed_time
    rev_history.append(revs_elapsed)
    
    if x_board < max_right_board:
        max_right_board = x_board
        breakpoint_ft = y_ft

    is_roll_phase = (curr_rot <= np.radians(12.0)) and (y_ft > oil_length * 0.85)
    if is_roll_phase and roll_start_ft is None:
        roll_start_ft = y_ft

    if y_ft < skid_end_ft:
        current_phase = "Skid"
        zone_mu = 0.012
        phase_flare_weight = 0.65 * rg_activation_speed
    elif y_ft < oil_length + 6.0:
        current_phase = "Hook"
        trans_progress = (y_ft - skid_end_ft) / max(1.0, (oil_length + 6.0) - skid_end_ft)
        zone_mu = 0.045 + 0.085 * (trans_progress ** 1.1)
        phase_flare_weight = (1.75 + 0.95 * np.sin(trans_progress * np.pi)) * rg_activation_speed
    else:
        current_phase = "Roll"
        zone_mu = 0.235
        phase_flare_weight = 0.35

    remaining_gap = max(0.0, actual_max_flare_rad - migrated_rad)
    
    if diff > 0.001 and remaining_gap > 1e-5:
        tilt_damping = np.cos(np.radians(abs(np.degrees(curr_tilt))))
        smooth_damping = (remaining_gap / max(1e-5, actual_max_flare_rad)) ** 0.28
        
        base_rate = (actual_max_flare_rad / est_flare_time) * 1.85
        precession_rate = base_rate * phase_flare_weight * smooth_damping * tilt_damping
        
        d_rad = min(remaining_gap, precession_rate * dt)
        migrated_rad += d_rad
    else:
        d_rad = 0.0

    axis_history_rad.append(migrated_rad)
    phase_history.append(current_phase)

    flare_rate_boost = 1.0 + (d_rad / dt) * 1.15
    cumulative_flare_grip = 1.0 + (migrated_rad * BALL_RADIUS) * 0.06
    mu = zone_mu * total_surface_grip * flare_rate_boost * cumulative_flare_grip

    if curr_tilt < 0:
        tilt_eff = 1.05
        curr_tilt = min(0.0, curr_tilt + mu * 1.4 * dt)
    else:
        tilt_eff = np.cos(curr_tilt)
        if mu > 0.05:
            curr_tilt = max(0.0, curr_tilt - mu * 1.1 * dt)

    core_power = ((diff * 45.0) + (int_diff * 25.0)) * layout_flare_factor * rg_activation_speed
    active_core_factor = (1.0 + core_power * 0.85) * mb_response_factor
    hook_accel = mu * (omega * 0.082) * np.sin(curr_rot) * tilt_eff * active_core_factor

    if y_ft > skid_end_ft:
        rot_decay = 1.2 if y_ft < oil_length else 3.4
        curr_rot = max(0.04, curr_rot - mu * rot_decay * dt)

    vx += hook_accel * dt
    vy -= mu * 1.15 * dt
    x_board += (vx * dt) * 12.0 / 1.06
    y_ft += vy * dt
    elapsed_time += dt

total_revolutions = (rpm / 60.0) * elapsed_time
flare_potential_inch = migrated_rad * BALL_RADIUS
if roll_start_ft is None:
    roll_start_ft = min(58.0, (breakpoint_ft or oil_length) + 7.5)

# ==========================================
# 5. 오일 트랙 링 & 나비넥타이 면적 계산 (브레이크 포인트 이후 색상 분리)
# ==========================================
bowtie_normal = np.cross(spin_axis_init, target_spin_axis)
if np.linalg.norm(bowtie_normal) > 1e-6 and flare_potential_inch > 0.2:
    bowtie_normal /= np.linalg.norm(bowtie_normal)
    bowtie_pt_vec = bowtie_normal if np.dot(bowtie_normal, grip_center_dir) >= 0 else -bowtie_normal
else:
    bowtie_pt_vec = None

track_rings = []
track_y_positions = []  # 각 트랙 링이 형성된 레인 거리(ft) 기록
min_hole_dist_inch = 99.0
first_ring_thumb_dist = 99.0

active_holes_with_rad = [(middle_dir, 0.45), (ring_dir, 0.45)]
if has_thumb and thumb_dir is not None:
    active_holes_with_rad.append((thumb_dir, 0.52))

theta = np.linspace(0, 2 * np.pi, 120)
display_track_tilt = float(axis_tilt) - 3.0
track_polar_angle = (np.pi / 2.0) - np.radians(display_track_tilt)

precession_path_pts = []

if total_axis_gap_rad > 1e-5:
    ortho_dir = target_spin_axis - np.dot(target_spin_axis, spin_axis_init) * spin_axis_init
    ortho_dir /= np.linalg.norm(ortho_dir)
else:
    ortho_dir = y_core_psa

# 0.5바퀴당 1줄씩 촘촘하게 생성
next_target_rev = 0.25
max_oil_pickup_ft = min(56.0, roll_start_ft + 3.0)

for i in range(len(traj_y)):
    if rev_history[i] >= next_target_rev and traj_y[i] <= max_oil_pickup_ft:
        mig_r = axis_history_rad[i]
        curr_axis = np.cos(mig_r) * spin_axis_init + np.sin(mig_r) * ortho_dir
        curr_axis /= np.linalg.norm(curr_axis)
        precession_path_pts.append(curr_axis * (BALL_RADIUS * 1.01))

        ref = np.array([0.0, 0.0, 1.0]) if abs(curr_axis[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
        u_vec = np.cross(curr_axis, ref)
        u_vec /= np.linalg.norm(u_vec)
        v_vec = np.cross(curr_axis, u_vec)

        ring_pts = BALL_RADIUS * (
            np.cos(track_polar_angle) * curr_axis[:, None] +
            np.sin(track_polar_angle) * (u_vec[:, None] * np.cos(theta) + v_vec[:, None] * np.sin(theta))
        )
        track_rings.append(ring_pts)
        track_y_positions.append(traj_y[i])

        if len(track_rings) == 1 and has_thumb and thumb_dir is not None:
            t_center = thumb_dir * BALL_RADIUS
            first_ring_thumb_dist = np.min(np.linalg.norm(ring_pts.T - t_center, axis=1)) - 0.52

        for h_dir, h_rad in active_holes_with_rad:
            h_center = h_dir * BALL_RADIUS
            dists = np.linalg.norm(ring_pts.T - h_center, axis=1)
            min_d = np.min(dists) - h_rad
            if min_d < min_hole_dist_inch:
                min_hole_dist_inch = min_d

        next_target_rev += 0.5

precession_path_pts = np.array(precession_path_pts)

# 브레이크 포인트 기준 지점 (브레이크 포인트가 없으면 오일 끝 지점 사용)
bp_cutoff_ft = breakpoint_ft if breakpoint_ft is not None else float(oil_length)
pre_bp_rings = [r for r, y_pos in zip(track_rings, track_y_positions) if y_pos < bp_cutoff_ft]
post_bp_rings = [r for r, y_pos in zip(track_rings, track_y_positions) if y_pos >= bp_cutoff_ft]

ref_dist = first_ring_thumb_dist if has_thumb else min_hole_dist_inch
if ref_dist <= 0.75:
    track_category = "하이 트랙 (High Track)"
    track_desc = f"표시 틸트 {display_track_tilt:.0f}° · 엄지/중지 1마디 이내 밀착"
elif ref_dist <= 1.75:
    track_category = "미디엄 / 세미 트랙"
    track_desc = f"표시 틸트 {display_track_tilt:.0f}° · 엄지 2번째 마디 부근"
else:
    track_category = "로우 트랙 (Low Track)"
    track_desc = f"표시 틸트 {display_track_tilt:.0f}° · 홀 외곽 적도 부근"

# ==========================================
# 6. 상단 KPI 지표 출력
# ==========================================
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
activation_pct = (flare_potential_inch / max(target_flare_inch, 0.01)) * 100.0
kpi1.metric(
    "실제 전개 플레어 폭 / 코어 활성화율",
    f"{flare_potential_inch:.2f}\" ({min(100.0, activation_pct):.0f}%)",
    f"총 {total_revolutions:.1f}회전 주행"
)
kpi2.metric(
    "스키드(Skid) → 훅(Hook) → 롤(Roll)",
    f"0~{skid_end_ft:.0f}ft / {skid_end_ft:.0f}~{roll_start_ft:.0f}ft / {roll_start_ft:.0f}~60ft",
    f"브레이크 포인트: {max_right_board:.1f}번 ({breakpoint_ft:.1f}ft)" if breakpoint_ft else "-"
)
kpi3.metric("핀 데크 입사 보드", f"{traj_x[-1]:.1f}번 보드", "1번 핀(포켓: 17.5번)")
kpi4.metric(
    f"트랙 판정: {track_category}",
    f"홀 여유 {max(0.0, min_hole_dist_inch):.2f} inch",
    track_desc
)

# ==========================================
# 7. 듀얼 3D 시각화 렌더링
# ==========================================
fig = make_subplots(
    rows=1, cols=2,
    specs=[[{'type': 'scene'}, {'type': 'scene'}]],
    subplot_titles=(
        f"[{st.session_state.get('active_preset_name', 'Custom')}] {layout_summary_str}",
        f"60ft 레인 3D 궤적 (Skid {skid_end_ft:.0f}ft → Hook → Roll {roll_start_ft:.0f}ft)"
    )
)

bx = BALL_RADIUS * np.outer(np.cos(u), np.sin(v))
by = BALL_RADIUS * np.outer(np.sin(u), np.sin(v))
bz = BALL_RADIUS * np.outer(np.ones(np.size(u)), np.cos(v))

fig.add_trace(go.Surface(x=bx, y=by, z=bz, opacity=0.22, colorscale='Blues', showscale=False), row=1, col=1)
fig.add_trace(go.Surface(x=rc_x, y=rc_y, z=rc_z, opacity=0.75, colorscale='Oranges', showscale=False), row=1, col=1)

holes_info = [("Middle", middle_dir, 0.45), ("Ring", ring_dir, 0.45)]
if has_thumb and thumb_dir is not None:
    holes_info.append((f"Thumb (Offset {thumb_offset:+.2f}\")", thumb_dir, 0.52))

for idx, (label, h_dir, h_rad) in enumerate(holes_info):
    h_pts = get_surface_circle(h_dir, h_rad)
    fig.add_trace(go.Scatter3d(
        x=h_pts[0], y=h_pts[1], z=h_pts[2],
        mode='lines', line=dict(color='black', width=6),
        name='Drilled Holes' if idx == 0 else None, showlegend=(idx == 0)
    ), row=1, col=1)
    l_pos = h_dir * (BALL_RADIUS + 0.2)
    fig.add_trace(go.Scatter3d(
        x=[l_pos[0]], y=[l_pos[1]], z=[l_pos[2]],
        mode='text', text=[label], textfont=dict(color='black', size=11), showlegend=False
    ), row=1, col=1)

cog_surf = grip_center_dir * BALL_RADIUS
fig.add_trace(go.Scatter3d(
    x=[cog_surf[0]], y=[cog_surf[1]], z=[cog_surf[2]],
    mode='markers+text', text=['CG'], textposition='bottom center',
    marker=dict(size=5, color='cyan'), name='CG (무게중심)'
), row=1, col=1)

if "2LS" in layout_system:
    cog_pin_arc = get_great_circle_arc(grip_center_dir, pin_vec, BALL_RADIUS * 1.005)
    fig.add_trace(go.Scatter3d(
        x=cog_pin_arc[0], y=cog_pin_arc[1], z=cog_pin_arc[2],
        mode='lines', line=dict(color='cyan', width=3, dash='dot'), name='Pin-to-COG'
    ), row=1, col=1)

fig.add_trace(go.Scatter3d(
    x=[pin_pos[0]], y=[pin_pos[1]], z=[pin_pos[2]],
    mode='markers+text', text=['PIN (X축)'], textposition='top center',
    marker=dict(size=7, color='red'), name='Pin (최저 RG축)'
), row=1, col=1)

if int_diff > 0:
    fig.add_trace(go.Scatter3d(
        x=[psa_pos[0]], y=[psa_pos[1]], z=[psa_pos[2]],
        mode='markers+text', text=['PSA (Y축)'], textposition='bottom center',
        marker=dict(size=7, color='purple'), name='PSA (최종 회전축)'
    ), row=1, col=1)

pap_surf = pap_vec * BALL_RADIUS
fig.add_trace(go.Scatter3d(
    x=[pap_surf[0]], y=[pap_surf[1]], z=[pap_surf[2]],
    mode='markers+text', text=['PAP'], textposition='middle right',
    marker=dict(size=7, color='lime'), name='PAP (초기 회전축)'
), row=1, col=1)

if len(precession_path_pts) > 1 and flare_potential_inch > 0.1:
    fig.add_trace(go.Scatter3d(
        x=precession_path_pts[:, 0], y=precession_path_pts[:, 1], z=precession_path_pts[:, 2],
        mode='lines+markers', marker=dict(size=3, color='magenta'),
        line=dict(color='magenta', width=4), name='Spin Axis Migration (축 이동)'
    ), row=1, col=1)

if bowtie_pt_vec is not None and flare_potential_inch > 0.25:
    bt_surf = bowtie_pt_vec * BALL_RADIUS
    fig.add_trace(go.Scatter3d(
        x=[bt_surf[0]], y=[bt_surf[1]], z=[bt_surf[2]],
        mode='markers+text', text=['Bowtie Pt'], textposition='middle left',
        marker=dict(size=6, color='orange', symbol='diamond'), name='Bowtie Point (트랙 교차점)'
    ), row=1, col=1)

val_top_vec = move_on_sphere(pap_vec, val_up_tangent, 4.5)
val_arc = get_great_circle_arc(pap_vec, val_top_vec, BALL_RADIUS * 1.005)
fig.add_trace(go.Scatter3d(
    x=val_arc[0], y=val_arc[1], z=val_arc[2],
    mode='lines', line=dict(color='lime', width=3, dash='dash'), name='VAL Line'
), row=1, col=1)

pin_pap_arc = get_great_circle_arc(pap_vec, pin_vec, BALL_RADIUS * 1.005)
fig.add_trace(go.Scatter3d(
    x=pin_pap_arc[0], y=pin_pap_arc[1], z=pin_pap_arc[2],
    mode='lines', line=dict(color='red', width=3, dash='dot'), name='Pin-to-PAP'
), row=1, col=1)

# [트랙 플레어 2단계 색상 분리 시각화]
# 1) 브레이크 포인트 이전 (Head ~ Midlane 구간): 기존 금빛/노란색 유지
if len(pre_bp_rings) >= 2:
    surf_pre_x = np.array([r[0] for r in pre_bp_rings])
    surf_pre_y = np.array([r[1] for r in pre_bp_rings])
    surf_pre_z = np.array([r[2] for r in pre_bp_rings])
    fig.add_trace(go.Surface(
        x=surf_pre_x, y=surf_pre_y, z=surf_pre_z,
        opacity=0.30,
        colorscale=[[0, '#ffd166'], [1, '#f77f00']],
        showscale=False,
        name='Flare Area (Head~Mid)'
    ), row=1, col=1)

for i, ring_pts in enumerate(pre_bp_rings):
    fig.add_trace(go.Scatter3d(
        x=ring_pts[0], y=ring_pts[1], z=ring_pts[2],
        mode='lines',
        line=dict(color='gold', width=4.5 if i == 0 else 2.0),
        name=f'Track: Head~Mid (0~{bp_cutoff_ft:.1f}ft)' if i == 0 else None,
        showlegend=(i == 0)
    ), row=1, col=1)

# 2) 브레이크 포인트 이후 (공이 꺾이는 구간 ~ 백엔드): 강렬한 빨간색(Crimson/Red)으로 분리
if len(post_bp_rings) >= 1:
    # 경계면이 끊어지지 않도록 브레이크 포인트 직전 링과 연결해 리본 면적 생성
    ribbon_post = ([pre_bp_rings[-1]] + post_bp_rings) if len(pre_bp_rings) > 0 else post_bp_rings
    if len(ribbon_post) >= 2:
        surf_post_x = np.array([r[0] for r in ribbon_post])
        surf_post_y = np.array([r[1] for r in ribbon_post])
        surf_post_z = np.array([r[2] for r in ribbon_post])
        fig.add_trace(go.Surface(
            x=surf_post_x, y=surf_post_y, z=surf_post_z,
            opacity=0.36,
            colorscale=[[0, '#ff4d6d'], [1, '#c9184a']],
            showscale=False,
            name='Flare Area (Breakpoint 이후)'
        ), row=1, col=1)

    for i, ring_pts in enumerate(post_bp_rings):
        fig.add_trace(go.Scatter3d(
            x=ring_pts[0], y=ring_pts[1], z=ring_pts[2],
            mode='lines',
            line=dict(color='#ff1e42', width=5.0 if i == len(post_bp_rings) - 1 else 2.4),
            name=f'Track: Breakpoint 이후 ({bp_cutoff_ft:.1f}ft~)' if i == 0 else None,
            showlegend=(i == 0)
        ), row=1, col=1)

# 우측 3D 레인: 스키드(진한 오일), 트랜지션(옅은 오일), 드라이(백엔드) 구분 표시
lane_x = np.linspace(1, 39, 20)
LX_skid, LY_skid = np.meshgrid(lane_x, np.linspace(0, skid_end_ft, 12))
fig.add_trace(go.Surface(
    x=LX_skid, y=LY_skid, z=np.zeros_like(LX_skid),
    opacity=0.45, colorscale=[[0, '#69b3a2'], [1, '#69b3a2']], showscale=False, name='Heavy Oil (Skid Zone)'
), row=1, col=2)

LX_trans, LY_trans = np.meshgrid(lane_x, np.linspace(skid_end_ft, oil_length, 10))
fig.add_trace(go.Surface(
    x=LX_trans, y=LY_trans, z=np.zeros_like(LX_trans),
    opacity=0.35, colorscale=[[0, '#a8dadc'], [1, '#a8dadc']], showscale=False, name='Transition Oil'
), row=1, col=2)

LX_dry, LY_dry = np.meshgrid(lane_x, np.linspace(oil_length, 60, 10))
fig.add_trace(go.Surface(
    x=LX_dry, y=LY_dry, z=np.zeros_like(LX_dry),
    opacity=0.5, colorscale=[[0, '#e9c46a'], [1, '#e9c46a']], showscale=False, name='Dry Backend'
), row=1, col=2)

traj_x_arr = np.array(traj_x)
traj_y_arr = np.array(traj_y)
skid_mask = traj_y_arr <= skid_end_ft
hook_mask = (traj_y_arr >= skid_end_ft) & (traj_y_arr <= roll_start_ft)
roll_mask = traj_y_arr >= roll_start_ft

if np.any(skid_mask):
    fig.add_trace(go.Scatter3d(
        x=traj_x_arr[skid_mask], y=traj_y_arr[skid_mask], z=[0.5]*int(np.sum(skid_mask)),
        mode='lines', line=dict(color='#1d3557', width=6), name='1. Skid (직진 스키드)'
    ), row=1, col=2)

if np.any(hook_mask):
    fig.add_trace(go.Scatter3d(
        x=traj_x_arr[hook_mask], y=traj_y_arr[hook_mask], z=[0.5]*int(np.sum(hook_mask)),
        mode='lines', line=dict(color='crimson', width=7), name='2. Hook (코어 활성화·꺾임)'
    ), row=1, col=2)

if np.any(roll_mask):
    fig.add_trace(go.Scatter3d(
        x=traj_x_arr[roll_mask], y=traj_y_arr[roll_mask], z=[0.5]*int(np.sum(roll_mask)),
        mode='lines', line=dict(color='#7209b7', width=7), name='3. Roll (직진 파워 롤)'
    ), row=1, col=2)

fig.add_trace(go.Scatter3d(
    x=[20], y=[60], z=[2.0],
    mode='markers+text', text=['1번 핀'],
    marker=dict(size=8, color='black'), name='Head Pin'
), row=1, col=2)

fig.update_layout(
    height=720,
    margin=dict(l=0, r=0, t=40, b=0),
    scene=dict(
        aspectmode='cube',
        xaxis=dict(title='X (좌/우)', range=[-5.5, 5.5]),
        yaxis=dict(title='Y (정면/후면)', range=[-5.5, 5.5]),
        zaxis=dict(title='Z (상/하)', range=[-5.5, 5.5]),
        camera=dict(eye=dict(x=0.5, y=-2.1, z=0.35))
    ),
    scene2=dict(
        xaxis=dict(title='보드 (1=우, 39=좌)', range=[39, 1]),
        yaxis=dict(title='레인 길이 (ft)', range=[0, 62]),
        zaxis=dict(title='높이', range=[0, 10]),
        aspectratio=dict(x=1, y=3.5, z=0.4)
    )
)

st.plotly_chart(fig, use_container_width=True)