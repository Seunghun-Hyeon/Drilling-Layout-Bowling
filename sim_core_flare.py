import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.spatial.transform import Rotation as R

# ==========================================
# 1. 볼링공 제원 & 지공 레이아웃 설정
# ==========================================
BALL_NAME = "Radical Power Hitter (Example)"
RG = 2.48
DIFF = 0.050
INT_DIFF = 0.015

# 듀얼 앵글 레이아웃: Drilling Angle(A) x Pin-to-PAP(B) x VAL Angle(C)
DRILL_ANGLE = 35.0   # A: Pin에서 PAP선과 PSA선이 이루는 각도
PIN_TO_PAP = 5.25     # B: PAP에서 Pin까지의 표면 거리 (인치)
VAL_ANGLE = 40.0     # C: PAP에서 수직선(VAL)과 Pin선이 이루는 각도

# 공 자체의 고유 Pin-to-PSA 거리 (보통 3.5" ~ 4.5", 제조사 출고 제원)
PIN_TO_PSA_DIST = 4.0

BALL_RADIUS_INCH = 4.295  # 15lbs 표준 반지름

# ==========================================
# 2. 투구 스타일 선택 + Tilt / Rotation 입력
# ==========================================
THROW_STYLES = {
    "1": {
        "name": "투핸드 / 덤리스 (Two-Handed / Dumpless)",
        "has_thumb": False,
        "rpm": 480,
        "speed_mph": 16.5,
        "axis_rot": 55.0,
        "axis_tilt": -5.0,
        "pap_x": 4.5,
        "pap_y": -0.5
    },
    "2": {
        "name": "클래식 스트로커 (Classic Stroker)",
        "has_thumb": True,
        "rpm": 270,
        "speed_mph": 15.5,
        "axis_rot": 35.0,
        "axis_tilt": 16.0,
        "pap_x": 5.0,
        "pap_y": 0.0
    },
    "3": {
        "name": "파워 크랭커 (Power Cranker)",
        "has_thumb": True,
        "rpm": 420,
        "speed_mph": 17.5,
        "axis_rot": 65.0,
        "axis_tilt": 14.0,
        "pap_x": 4.75,
        "pap_y": 0.25
    },
    "4": {
        "name": "스피너 / UFO (Spinner)",
        "has_thumb": True,
        "rpm": 350,
        "speed_mph": 16.0,
        "axis_rot": 80.0,
        "axis_tilt": 45.0,
        "pap_x": 3.5,
        "pap_y": 1.0
    }
}

print("=== [1단계] 투구 스타일을 선택하세요 ===")
for key, val in THROW_STYLES.items():
    thumb_str = "3홀" if val["has_thumb"] else "2홀(덤리스)"
    print(f"[{key}] {val['name']} [{thumb_str}] (기본 Rot: {val['axis_rot']}°, Tilt: {val['axis_tilt']}°)")

choice = input("\n번호 입력 (기본값 1): ").strip()
if choice not in THROW_STYLES:
    choice = "1"
style = THROW_STYLES[choice].copy()

print(f"\n=== [2단계] Axis Rotation & Axis Tilt 입력 (엔터 시 기본값 사용) ===")
rot_input = input(f"Axis Rotation 입력 (0°~90°, 현재 기본값 {style['axis_rot']}°): ").strip()
if rot_input:
    style["axis_rot"] = float(np.clip(float(rot_input), 0.0, 90.0))

tilt_input = input(f"Axis Tilt 입력 (-45°~90°, 현재 기본값 {style['axis_tilt']}°): ").strip()
if tilt_input:
    style["axis_tilt"] = float(np.clip(float(tilt_input), -45.0, 90.0))

# ==========================================
# 3. 구면 기하학 기반 정확한 지공(PAP / Pin / PSA) 작도 함수
# ==========================================
def move_on_sphere(start_vec, tangent_dir, dist_inch, ball_r=BALL_RADIUS_INCH):
    """구면 위의 start_vec에서 접선 방향 tangent_dir을 따라 dist_inch만큼 이동한 단위 벡터 반환"""
    s = start_vec / np.linalg.norm(start_vec)
    # start_vec에 수직인 순수 접선 벡터로 직교화
    t = tangent_dir - np.dot(tangent_dir, s) * s
    t /= np.linalg.norm(t)
    theta = dist_inch / ball_r  # 호의 각도(라디안)
    return s * np.cos(theta) + t * np.sin(theta)

def rotate_tangent(normal_vec, tangent_vec, angle_deg):
    """구면 위의 법선 normal_vec을 축으로 접선 벡터 tangent_vec을 angle_deg만큼 회전"""
    rot = R.from_rotvec(np.radians(angle_deg) * (normal_vec / np.linalg.norm(normal_vec)))
    return rot.apply(tangent_vec)

def get_great_circle_arc(p1, p2, ball_r=BALL_RADIUS_INCH, num_pts=30):
    """두 구면 단위 벡터 p1, p2를 잇는 최단 대원 호(Arc) 좌표 생성"""
    p1 = p1 / np.linalg.norm(p1)
    p2 = p2 / np.linalg.norm(p2)
    omega = np.arccos(np.clip(np.dot(p1, p2), -1.0, 1.0))
    if omega < 1e-6:
        return np.outer(p1, np.ones(num_pts)) * ball_r
    t = np.linspace(0, 1, num_pts)
    arc = (np.sin((1 - t) * omega)[:, None] * p1 + np.sin(t * omega)[:, None] * p2) / np.sin(omega)
    return (arc * ball_r).T

def get_surface_circle(center_vec, hole_radius_inch, ball_r=BALL_RADIUS_INCH, num_pts=40):
    n = center_vec / np.linalg.norm(center_vec)
    ref = np.array([0.0, 0.0, 1.0]) if abs(n[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    u_vec = np.cross(n, ref)
    u_vec /= np.linalg.norm(u_vec)
    v_vec = np.cross(n, u_vec)
    angular_r = hole_radius_inch / ball_r
    theta = np.linspace(0, 2 * np.pi, num_pts)
    return (ball_r * np.cos(angular_r) * n[:, None] +
            ball_r * np.sin(angular_r) * (u_vec[:, None] * np.cos(theta) + v_vec[:, None] * np.sin(theta)))

# 좌표계 정의:
# 공 정면(그립 중심) = -Y 방향 [0, -1, 0]
# 오른손 투구자 기준 오른쪽 = +X [1, 0, 0], 왼쪽 = -X [-1, 0, 0]
# 위쪽(중지/약지 쪽) = +Z [0, 0, 1], 아래쪽(엄지 쪽) = -Z [0, 0, -1]
grip_center_dir = np.array([0.0, -1.0, 0.0])

# (A) 지공 홀 위치
middle_finger_dir = move_on_sphere(grip_center_dir, np.array([-1.0, 0.0, 0.0]), 0.65)
middle_finger_dir = move_on_sphere(middle_finger_dir, np.array([0.0, 0.0, 1.0]), 0.3)

ring_finger_dir = move_on_sphere(grip_center_dir, np.array([1.0, 0.0, 0.0]), 0.65)
ring_finger_dir = move_on_sphere(ring_finger_dir, np.array([0.0, 0.0, 1.0]), 0.3)

thumb_dir = move_on_sphere(grip_center_dir, np.array([0.0, 0.0, -1.0]), 3.8)

# (B) PAP 위치 작도: 그립 중심에서 오른쪽(+X)으로 pap_x, 위/아래(±Z)로 pap_y 이동
pap_temp = move_on_sphere(grip_center_dir, np.array([1.0, 0.0, 0.0]), style["pap_x"])
up_dir = np.array([0.0, 0.0, 1.0]) if style["pap_y"] >= 0 else np.array([0.0, 0.0, -1.0])
pap_vec = move_on_sphere(pap_temp, up_dir, abs(style["pap_y"]))

# (C) PAP에서의 VAL(수직선) 접선 방향 계산
# 공의 위쪽(+Z)을 향하는 구면 접선 벡터 = VAL 위쪽 방향
val_up_tangent = np.array([0.0, 0.0, 1.0]) - np.dot(np.array([0.0, 0.0, 1.0]), pap_vec) * pap_vec
val_up_tangent /= np.linalg.norm(val_up_tangent)

# (D) Pin 위치 작도 (VAL 각도 & Pin-to-PAP 거리):
# 오른손 투구자 기준: PAP에서 VAL(위쪽)을 바라볼 때, 왼쪽(그립 홀 방향, 반시계 방향)으로 VAL_ANGLE만큼 회전
# pap_vec(바깥쪽 법선) 기준으로 반시계 방향(+) 회전이 왼쪽(그립 쪽)을 향함
pin_dir_from_pap = rotate_tangent(pap_vec, val_up_tangent, +VAL_ANGLE)
pin_vec = move_on_sphere(pap_vec, pin_dir_from_pap, PIN_TO_PAP)

# (E) PSA(Mass Bias) 위치 작도 (Drilling Angle & Pin-to-PSA 거리):
# Pin 위치에서 PAP를 바라보는 대원 접선 방향(pin_to_pap_tangent)을 먼저 구함
# 두 점(pin_vec, pap_vec)을 잇는 대원 위에서 pin_vec에서의 접선 = pap_vec - (pap_vec·pin_vec)*pin_vec
pin_to_pap_tangent = pap_vec - np.dot(pap_vec, pin_vec) * pin_vec
pin_to_pap_tangent /= np.linalg.norm(pin_to_pap_tangent)

# Pin에서 PAP선을 기준으로 시계 방향(-DRILL_ANGLE)으로 회전하면 아래쪽(엄지/오른쪽 하단 방향)으로 PSA가 배치됨
psa_dir_from_pin = rotate_tangent(pin_vec, pin_to_pap_tangent, -DRILL_ANGLE)
psa_vec = move_on_sphere(pin_vec, psa_dir_from_pin, PIN_TO_PSA_DIST)

pin_pos = pin_vec * BALL_RADIUS_INCH
psa_pos = psa_vec * BALL_RADIUS_INCH

# ==========================================
# 4. 내부 코어 3D 메쉬를 Pin과 PSA 벡터에 정확히 정렬
# ==========================================
# 코어 로컬 좌표계:
# 로컬 +Z축 = Pin 방향 (pin_vec)
# 로컬 +X축 = PSA 방향 (pin_vec에 직교화한 psa_vec 방향)
# 로컬 +Y축 = Z x X
z_core = pin_vec
x_core = psa_vec - np.dot(psa_vec, z_core) * z_core
x_core /= np.linalg.norm(x_core)
y_core = np.cross(z_core, x_core)

core_rot_matrix = np.column_stack([x_core, y_core, z_core])

cz = 3.2
cx = 2.0 * (1.0 - DIFF * 5.0)
cy = cx * (1.0 - INT_DIFF * 8.0)

u = np.linspace(0, 2 * np.pi, 36)
v = np.linspace(0, np.pi, 36)
core_x = cx * np.outer(np.cos(u), np.sin(v))
core_y = cy * np.outer(np.sin(u), np.sin(v))
core_z = cz * np.outer(np.ones(np.size(u)), np.cos(v))

core_pts = np.stack([core_x.flatten(), core_y.flatten(), core_z.flatten()], axis=1)
rotated_core = core_pts @ core_rot_matrix.T
rc_x = rotated_core[:, 0].reshape(core_x.shape)
rc_y = rotated_core[:, 1].reshape(core_y.shape)
rc_z = rotated_core[:, 2].reshape(core_z.shape)

# ==========================================
# 5. 60피트 레인 위 3D 궤적 물리 시뮬레이션
# ==========================================
OIL_LENGTH_FT = 42.0
LANE_LENGTH_FT = 60.0
START_BOARD = 25.0
TARGET_ARROW_BOARD = 12.0

dt = 0.01
y_ft = 0.0
x_board = START_BOARD

speed_fps = style["speed_mph"] * 1.46667
initial_angle_rad = np.arctan2((TARGET_ARROW_BOARD - START_BOARD) * 1.06 / 12.0, 15.0)
vx = speed_fps * np.sin(initial_angle_rad)
vy = speed_fps * np.cos(initial_angle_rad)

omega = style["rpm"] * 2 * np.pi / 60.0
curr_axis_rot = np.radians(style["axis_rot"])
curr_axis_tilt = np.radians(style["axis_tilt"])
core_torque_factor = (2.80 - RG) * 2.5 + DIFF * 25.0

traj_x_board, traj_y_ft = [], []

while y_ft <= LANE_LENGTH_FT:
    traj_x_board.append(x_board)
    traj_y_ft.append(y_ft)
    
    if y_ft < OIL_LENGTH_FT * 0.75:
        mu = 0.04
    elif y_ft < OIL_LENGTH_FT:
        mu = 0.09
    else:
        mu = 0.22
        
    if curr_axis_tilt < 0:
        tilt_efficiency = 1.05
        curr_axis_tilt = min(0.0, curr_axis_tilt + mu * 1.5 * dt)
    else:
        tilt_efficiency = np.cos(curr_axis_tilt)
        if mu > 0.05:
            curr_axis_tilt = max(0.0, curr_axis_tilt - mu * 1.2 * dt)
            
    hook_accel = mu * (omega * 0.085) * np.sin(curr_axis_rot) * tilt_efficiency * core_torque_factor
    if y_ft > OIL_LENGTH_FT:
        curr_axis_rot = max(0.05, curr_axis_rot - mu * 3.8 * dt)
        
    vx += hook_accel * dt
    vy -= mu * 2.5 * dt
    x_board += (vx * dt) * 12.0 / 1.06
    y_ft += vy * dt

# ==========================================
# 6. 듀얼 뷰 3D 시각화 (작도 가이드라인 포함)
# ==========================================
fig = make_subplots(
    rows=1, cols=2,
    specs=[[{'type': 'scene'}, {'type': 'scene'}]],
    subplot_titles=(
        f"지공 작도 검증 ({DRILL_ANGLE:.0f}° x {PIN_TO_PAP}\" x {VAL_ANGLE:.0f}°)",
        f"60ft 레인 3D 궤적 (입사 보드: {traj_x_board[-1]:.1f}번)"
    )
)

# 볼 외피 & 내부 코어
bx = BALL_RADIUS_INCH * np.outer(np.cos(u), np.sin(v))
by = BALL_RADIUS_INCH * np.outer(np.sin(u), np.sin(v))
bz = BALL_RADIUS_INCH * np.outer(np.ones(np.size(u)), np.cos(v))

fig.add_trace(go.Surface(x=bx, y=by, z=bz, opacity=0.22, colorscale='Blues', showscale=False), row=1, col=1)
fig.add_trace(go.Surface(x=rc_x, y=rc_y, z=rc_z, opacity=0.85, colorscale='Oranges', showscale=False), row=1, col=1)

# 지공 홀 렌더링
holes_to_draw = [
    ("Middle", middle_finger_dir, 0.45),
    ("Ring", ring_finger_dir, 0.45)
]
if style["has_thumb"]:
    holes_to_draw.append(("Thumb", thumb_dir, 0.52))

for idx, (label, h_dir, h_rad) in enumerate(holes_to_draw):
    h_pts = get_surface_circle(h_dir, h_rad)
    fig.add_trace(go.Scatter3d(
        x=h_pts[0], y=h_pts[1], z=h_pts[2],
        mode='lines', line=dict(color='black', width=6),
        name='Drilled Holes' if idx == 0 else None,
        showlegend=(idx == 0)
    ), row=1, col=1)
    label_pos = h_dir * (BALL_RADIUS_INCH + 0.18)
    fig.add_trace(go.Scatter3d(
        x=[label_pos[0]], y=[label_pos[1]], z=[label_pos[2]],
        mode='text', text=[label], textfont=dict(color='black', size=11), showlegend=False
    ), row=1, col=1)

# Pin, PSA, PAP 마커
fig.add_trace(go.Scatter3d(
    x=[pin_pos[0]], y=[pin_pos[1]], z=[pin_pos[2]],
    mode='markers+text', text=['PIN'], textposition='top center',
    marker=dict(size=7, color='red'), name='Pin'
), row=1, col=1)

if INT_DIFF > 0:
    fig.add_trace(go.Scatter3d(
        x=[psa_pos[0]], y=[psa_pos[1]], z=[psa_pos[2]],
        mode='markers+text', text=['PSA (MB)'], textposition='bottom center',
        marker=dict(size=7, color='purple'), name='PSA (Mass Bias)'
    ), row=1, col=1)

pap_surface = pap_vec * BALL_RADIUS_INCH
fig.add_trace(go.Scatter3d(
    x=[pap_surface[0]], y=[pap_surface[1]], z=[pap_surface[2]],
    mode='markers+text', text=['PAP'], textposition='middle right',
    marker=dict(size=7, color='lime'), name='PAP'
), row=1, col=1)

# --- 듀얼 앵글 작도 보조선 (가이드라인) ---
# 1) VAL 기준선 (PAP에서 위쪽으로 4.5인치)
val_top_vec = move_on_sphere(pap_vec, val_up_tangent, 4.5)
val_arc = get_great_circle_arc(pap_vec, val_top_vec, BALL_RADIUS_INCH * 1.005)
fig.add_trace(go.Scatter3d(
    x=val_arc[0], y=val_arc[1], z=val_arc[2],
    mode='lines', line=dict(color='lime', width=3, dash='dash'), name='VAL Line (기준선)'
), row=1, col=1)

# 2) Pin-to-PAP 연결선
pin_pap_arc = get_great_circle_arc(pap_vec, pin_vec, BALL_RADIUS_INCH * 1.005)
fig.add_trace(go.Scatter3d(
    x=pin_pap_arc[0], y=pin_pap_arc[1], z=pin_pap_arc[2],
    mode='lines', line=dict(color='red', width=3, dash='dot'), name='Pin-to-PAP Line'
), row=1, col=1)

# 3) Pin-to-PSA 연결선 (Drilling Angle 확인용)
if INT_DIFF > 0:
    pin_psa_arc = get_great_circle_arc(pin_vec, psa_vec, BALL_RADIUS_INCH * 1.005)
    fig.add_trace(go.Scatter3d(
        x=pin_psa_arc[0], y=pin_psa_arc[1], z=pin_psa_arc[2],
        mode='lines', line=dict(color='purple', width=3, dash='dot'), name='Pin-to-PSA Line'
    ), row=1, col=1)

# 트랙 플레어 링
stable_axis = pin_vec if np.dot(pap_vec, pin_vec) >= 0 else -pin_vec
flare_multiplier = (style["rpm"] / 350.0) * (DIFF * 550.0)
max_flare_rad = np.radians(min(45.0, flare_multiplier))
first_track_rad = np.radians(90.0 - style["axis_tilt"])

theta = np.linspace(0, 2 * np.pi, 80)
for i in range(6):
    t = i / 5.0
    curr_axis = (1 - t * 0.6) * pap_vec + (t * 0.6) * stable_axis
    curr_axis /= np.linalg.norm(curr_axis)
    
    ref = np.array([0.0, 0.0, 1.0]) if abs(curr_axis[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    u_vec = np.cross(curr_axis, ref)
    u_vec /= np.linalg.norm(u_vec)
    v_vec = np.cross(curr_axis, u_vec)
    
    curr_track_angle = first_track_rad + t * max_flare_rad * 0.35
    d_offset = BALL_RADIUS_INCH * np.cos(curr_track_angle)
    ring_r = np.sqrt(max(0.0, BALL_RADIUS_INCH**2 - d_offset**2))
    ring_pts = (d_offset * curr_axis[:, None] +
                ring_r * (u_vec[:, None] * np.cos(theta) + v_vec[:, None] * np.sin(theta)))
    
    fig.add_trace(go.Scatter3d(
        x=ring_pts[0], y=ring_pts[1], z=ring_pts[2],
        mode='lines', line=dict(color='yellow', width=3),
        name='Track Flare' if i == 0 else None, showlegend=(i == 0)
    ), row=1, col=1)

# --- [오른쪽 차트] 60ft 레인 3D 궤적 ---
lane_x = np.linspace(1, 39, 20)
lane_y_oil = np.linspace(0, OIL_LENGTH_FT, 20)
LX_oil, LY_oil = np.meshgrid(lane_x, lane_y_oil)
fig.add_trace(go.Surface(
    x=LX_oil, y=LY_oil, z=np.zeros_like(LX_oil),
    opacity=0.4, colorscale=[[0, '#a8dadc'], [1, '#a8dadc']], showscale=False, name='Oil Zone (42ft)'
), row=1, col=2)

lane_y_dry = np.linspace(OIL_LENGTH_FT, LANE_LENGTH_FT, 10)
LX_dry, LY_dry = np.meshgrid(lane_x, lane_y_dry)
fig.add_trace(go.Surface(
    x=LX_dry, y=LY_dry, z=np.zeros_like(LX_dry),
    opacity=0.5, colorscale=[[0, '#e9c46a'], [1, '#e9c46a']], showscale=False, name='Dry Backend'
), row=1, col=2)

fig.add_trace(go.Scatter3d(
    x=traj_x_board, y=traj_y_ft, z=[0.5]*len(traj_y_ft),
    mode='lines', line=dict(color='crimson', width=6), name='Ball Trajectory'
), row=1, col=2)

fig.add_trace(go.Scatter3d(
    x=[20], y=[60], z=[2.0],
    mode='markers+text', text=['Head Pin (1번 핀)'],
    marker=dict(size=8, color='black'), name='1번 핀'
), row=1, col=2)

fig.update_layout(
    title=f"Bowling 3D Simulator | {BALL_NAME} | Layout: {DRILL_ANGLE}° x {PIN_TO_PAP}\" x {VAL_ANGLE}°",
    height=720,
    scene=dict(
        aspectmode='cube',
        xaxis=dict(title='X (좌/우)', range=[-5.5, 5.5]),
        yaxis=dict(title='Y (정면/후면)', range=[-5.5, 5.5]),
        zaxis=dict(title='Z (상/하)', range=[-5.5, 5.5]),
        camera=dict(eye=dict(x=0.6, y=-2.1, z=0.4))
    ),
    scene2=dict(
        xaxis=dict(title='보드 (1=우, 39=좌)', range=[39, 1]),
        yaxis=dict(title='레인 길이 (ft)', range=[0, 62]),
        zaxis=dict(title='높이', range=[0, 10]),
        aspectratio=dict(x=1, y=3.5, z=0.4)
    )
)

fig.show()