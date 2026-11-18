import streamlit as st
from config_presets import TWO_LS_PRESETS, save_presets

def render_sidebar(presets):
    params = {}
    with st.sidebar:
        st.header("1. 지공 홀 타입 & PAP 설정")
        drill_hole_type = st.radio(
            "그립 형태",
            ["원핸드 (3홀 - 엄지 포함)", "투핸드 / 덤리스 (2홀 - 엄지 없음)"],
            key="drill_hole_type"
        )
        has_thumb = "3홀" in drill_hole_type
        params["has_thumb"] = has_thumb

        if has_thumb:
            params["span_inch"] = st.slider("원핸드 스팬 길이 (중약지~엄지, inch)", 3.5, 5.25, step=0.125, format="%.3f", key="span_inch")
            params["thumb_offset"] = st.slider(
                "엄지 옵셋 (Thumb Offset, +는 좌측 이동, inch)",
                min_value=-0.50, max_value=1.00, step=0.0625, format="%.4f", key="thumb_offset"
            )
        else:
            params["span_inch"] = 0.0
            params["thumb_offset"] = 0.0

        col_pap1, col_pap2 = st.columns(2)
        with col_pap1:
            params["pap_x"] = st.number_input("PAP 가로 (over, inch)", min_value=2.0, max_value=7.5, step=0.0625, format="%.4f", key="pap_x")
        with col_pap2:
            params["pap_y"] = st.number_input("PAP 상/하 (up/down, inch)", min_value=-2.5, max_value=3.0, step=0.0625, format="%.4f", key="pap_y")

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
        params["layout_system"] = layout_system
        params["pin_to_psa"] = st.slider("볼 고유 Pin-to-PSA 거리 (inch)", 2.0, 6.75, step=0.125, format="%.3f", key="pin_to_psa")

        if "Dual Angle" in layout_system:
            st.caption("형식: Drilling Angle(°) × Pin-to-PAP(\") × VAL Angle(°)")
            params["drill_angle"] = st.slider("Drilling Angle (드릴링 각도 °)", 10, 90, step=5, key="drill_angle")
            params["pin_to_pap"] = st.slider("Pin-to-PAP 거리 (inch)", 1.0, 6.75, step=0.125, format="%.3f", key="pin_to_pap")
            params["val_angle"] = st.slider("VAL Angle (VAL 각도 °)", 10, 90, step=5, key="val_angle")

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

            params["ls2_pin_pap"] = st.slider("1번 수치: Pin-to-PAP (inch)", 1.5, 6.5, step=0.125, format="%.3f", key="ls2_pin_pap")
            params["ls2_pin_cog"] = st.slider("2번 수치: Pin-to-COG (inch)", 1.5, 6.5, step=0.125, format="%.3f", key="ls2_pin_cog")
            params["ls2_buffer"]  = st.slider("3번 수치: Pin-buffer / PSA 오프셋 (inch)", 1.0, 7.0, step=0.125, format="%.3f", key="ls2_buffer")

        elif "VLS" in layout_system:
            st.caption("형식: Pin-to-PAP(\") × PSA-to-PAP(\") × Pin-to-VAL(\")")
            params["vls_pin_pap"] = st.slider("1번 수치: Pin-to-PAP 거리 (inch)", 1.0, 6.75, step=0.125, format="%.3f", key="vls_pin_pap")
            params["vls_psa_pap"] = st.slider("2번 수치: PSA-to-PAP 거리 (inch)", 1.5, 6.5, step=0.125, format="%.3f", key="vls_psa_pap")
            params["vls_pin_val"] = st.slider("3번 수치: Pin-to-VAL 거리 (inch)", 0.5, 5.5, step=0.125, format="%.3f", key="vls_pin_val")
            params["vls_pin_pos"] = st.radio("Pin 상/하 위치", ["Pin Up (VAL 위쪽)", "Pin Down (VAL 아래쪽)"], key="vls_pin_pos")

        st.divider()
        st.header("3. 볼 코어 3대 요소 & 외피 스펙")
        col_spec1, col_spec2, col_spec3 = st.columns(3)
        with col_spec1:
            rg = st.number_input("RG (2.43~2.80)", min_value=2.430, max_value=2.800, step=0.001, format="%.3f", key="rg")
        with col_spec2:
            diff = st.number_input("RG Diff (0~0.06)", min_value=0.000, max_value=0.060, step=0.001, format="%.3f", key="diff")
        with col_spec3:
            int_diff = st.number_input("Inter Diff (PSA)", min_value=0.000, max_value=0.037, step=0.001, format="%.3f", key="int_diff")

        params["rg"] = rg
        params["diff"] = diff
        params["int_diff"] = int_diff

        rg_grade = "로우 RG (조기 롤)" if rg <= 2.540 else ("미디움 RG" if rg <= 2.690 else "하이 RG (긴 스키드)")
        diff_grade = "로우 Diff (적은 플레어)" if diff <= 0.020 else ("미디움 Diff (중간 플레어)" if diff <= 0.040 else "하이 Diff (많은 플레어)")
        int_grade = "대칭 코어" if int_diff < 0.005 else ("로우 MB (느린 반응)" if int_diff <= 0.020 else "하이 MB (빠른 전환)")
        st.caption(f"📊 코어 판정: **{rg_grade}** | **{diff_grade}** | **{int_grade}**")

        params["cover_type"] = st.selectbox(
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
        params["surface_grit"] = st.select_slider(
            "표면 샌딩 그릿 (낮을수록 거침/트레드 효과 증가)",
            options=[360, 500, 1000, 1500, 2000, 3000, 4000],
            key="surface_grit"
        )

        st.divider()
        st.header("4. 투구 스펙 & 레인 조건")
        speed_kmh = st.slider("볼 스피드 (km/h)", 18.0, 36.0, step=0.5, key="speed_kmh")
        params["speed_kmh"] = speed_kmh
        params["speed_mph"] = speed_kmh / 1.60934
        params["rpm"] = st.slider("회전수 (RPM)", 150, 650, step=5, key="rpm")
        params["axis_rot"] = st.slider("Axis Rotation (축 회전 °)", 0, 90, step=1, key="axis_rot")
        params["axis_tilt"] = st.slider("Axis Tilt (축 기울기 °)", -30, 60, step=1, key="axis_tilt")

        params["oil_length"] = st.slider("오일 패턴 길이 (ft)", 32, 48, step=1, key="oil_length")
        params["start_board"] = st.slider("스탠스 출발 보드 (번)", 5, 38, step=1, key="start_board")
        params["target_board"] = st.slider("에이밍 타겟 보드 (15ft 지점)", 3, 30, step=1, key="target_board")

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

    return params