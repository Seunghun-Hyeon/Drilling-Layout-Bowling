import streamlit as st
from config_presets import load_presets, apply_preset_to_state
from sidebar_ui import render_sidebar
from physics_engine import run_simulation
from visualizer_3d import render_3d_charts

st.set_page_config(page_title="Bowling 3D Layout & Track Simulator", layout="wide")
st.title("🎳 볼링 지공 레이아웃 & 코어 활성화 3D 시뮬레이터")

presets = load_presets()

if "initialized" not in st.session_state:
    apply_preset_to_state(presets["Awesome_data"])
    st.session_state["active_preset_name"] = "Awesome_data"
    st.session_state["initialized"] = True

# 상단 저장 프리셋 원클릭 선택 바
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

# 1. 사이드바 입력 수집
params = render_sidebar(presets)

# 2. 물리 & 트랙 플레어 연산 수행
sim_results = run_simulation(params)

# 3. 상단 KPI 지표 출력 (빈 컬럼 없이 3열 균등 배치)
kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric(
    "실제 전개 플레어 폭 / 코어 활성화율",
    f"{sim_results['flare_potential_inch']:.2f}\" ({min(100.0, sim_results['activation_pct']):.0f}%)",
    f"총 {sim_results['total_revolutions']:.1f}회전 주행"
)
kpi2.metric(
    "핀 데크 입사 보드",
    f"{sim_results['traj_x'][-1]:.1f}번 보드",
    "1번 핀(포켓: 17.5번)"
)
kpi3.metric(
    f"트랙 판정: {sim_results['track_category']}",
    f"홀 여유 {max(0.0, sim_results['min_hole_dist_inch']):.2f} inch",
    sim_results['track_desc']
)

# 4. 듀얼 3D 시각화 렌더링
render_3d_charts(params, sim_results)