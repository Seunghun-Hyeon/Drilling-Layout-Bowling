import os
import json
import streamlit as st

BALL_RADIUS = 4.295  # 15파운드 표준 반지름 (inch)
PRESET_FILE = "bowling_presets.json"

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