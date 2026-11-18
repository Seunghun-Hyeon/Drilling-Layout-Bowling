import numpy as np
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from config_presets import BALL_RADIUS
from sphere_math import move_on_sphere, get_great_circle_arc, get_surface_circle

def render_3d_charts(p, sim):
    u, v = sim["u"], sim["v"]
    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{'type': 'scene'}, {'type': 'scene'}]],
        subplot_titles=(
            f"[{st.session_state.get('active_preset_name', 'Custom')}] {sim['layout_summary_str']}",
            f"60ft 레인 3D 궤적 (Skid {sim['skid_end_ft']:.0f}ft → Hook → Roll {sim['roll_start_ft']:.0f}ft)"
        )
    )

    bx = BALL_RADIUS * np.outer(np.cos(u), np.sin(v))
    by = BALL_RADIUS * np.outer(np.sin(u), np.sin(v))
    bz = BALL_RADIUS * np.outer(np.ones(np.size(u)), np.cos(v))

    fig.add_trace(go.Surface(x=bx, y=by, z=bz, opacity=0.22, colorscale='Blues', showscale=False), row=1, col=1)
    fig.add_trace(go.Surface(x=sim["rc_x"], y=sim["rc_y"], z=sim["rc_z"], opacity=0.75, colorscale='Oranges', showscale=False), row=1, col=1)

    holes_info = [("Middle", sim["middle_dir"], 0.45), ("Ring", sim["ring_dir"], 0.45)]
    if p["has_thumb"] and sim["thumb_dir"] is not None:
        holes_info.append((f"Thumb (Offset {p['thumb_offset']:+.2f}\")", sim["thumb_dir"], 0.52))

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

    cog_surf = sim["grip_center_dir"] * BALL_RADIUS
    fig.add_trace(go.Scatter3d(
        x=[cog_surf[0]], y=[cog_surf[1]], z=[cog_surf[2]],
        mode='markers+text', text=['CG'], textposition='bottom center',
        marker=dict(size=5, color='cyan'), name='CG (무게중심)'
    ), row=1, col=1)

    if "2LS" in p["layout_system"]:
        cog_pin_arc = get_great_circle_arc(sim["grip_center_dir"], sim["pin_vec"], BALL_RADIUS * 1.005)
        fig.add_trace(go.Scatter3d(
            x=cog_pin_arc[0], y=cog_pin_arc[1], z=cog_pin_arc[2],
            mode='lines', line=dict(color='cyan', width=3, dash='dot'), name='Pin-to-COG'
        ), row=1, col=1)

    pin_pos = sim["pin_pos"]
    fig.add_trace(go.Scatter3d(
        x=[pin_pos[0]], y=[pin_pos[1]], z=[pin_pos[2]],
        mode='markers+text', text=['PIN (X축)'], textposition='top center',
        marker=dict(size=7, color='red'), name='Pin (최저 RG축)'
    ), row=1, col=1)

    if p["int_diff"] > 0:
        psa_pos = sim["psa_pos"]
        fig.add_trace(go.Scatter3d(
            x=[psa_pos[0]], y=[psa_pos[1]], z=[psa_pos[2]],
            mode='markers+text', text=['PSA (Y축)'], textposition='bottom center',
            marker=dict(size=7, color='purple'), name='PSA (최종 회전축)'
        ), row=1, col=1)

    pap_vec = sim["pap_vec"]
    pap_surf = pap_vec * BALL_RADIUS
    fig.add_trace(go.Scatter3d(
        x=[pap_surf[0]], y=[pap_surf[1]], z=[pap_surf[2]],
        mode='markers+text', text=['PAP'], textposition='middle right',
        marker=dict(size=7, color='lime'), name='PAP (초기 회전축)'
    ), row=1, col=1)

    precession_path_pts = sim["precession_path_pts"]
    if len(precession_path_pts) > 1 and sim["flare_potential_inch"] > 0.1:
        fig.add_trace(go.Scatter3d(
            x=precession_path_pts[:, 0], y=precession_path_pts[:, 1], z=precession_path_pts[:, 2],
            mode='lines+markers', marker=dict(size=3, color='magenta'),
            line=dict(color='magenta', width=4), name='Spin Axis Migration (축 이동)'
        ), row=1, col=1)

    if sim["bowtie_pt_vec"] is not None and sim["flare_potential_inch"] > 0.25:
        bt_surf = sim["bowtie_pt_vec"] * BALL_RADIUS
        fig.add_trace(go.Scatter3d(
            x=[bt_surf[0]], y=[bt_surf[1]], z=[bt_surf[2]],
            mode='markers+text', text=['Bowtie Pt'], textposition='middle left',
            marker=dict(size=6, color='orange', symbol='diamond'), name='Bowtie Point (트랙 교차점)'
        ), row=1, col=1)

    val_top_vec = move_on_sphere(pap_vec, sim["val_up_tangent"], 4.5)
    val_arc = get_great_circle_arc(pap_vec, val_top_vec, BALL_RADIUS * 1.005)
    fig.add_trace(go.Scatter3d(
        x=val_arc[0], y=val_arc[1], z=val_arc[2],
        mode='lines', line=dict(color='lime', width=3, dash='dash'), name='VAL Line'
    ), row=1, col=1)

    pin_pap_arc = get_great_circle_arc(pap_vec, sim["pin_vec"], BALL_RADIUS * 1.005)
    fig.add_trace(go.Scatter3d(
        x=pin_pap_arc[0], y=pin_pap_arc[1], z=pin_pap_arc[2],
        mode='lines', line=dict(color='red', width=3, dash='dot'), name='Pin-to-PAP'
    ), row=1, col=1)

    pre_bp_rings = sim["pre_bp_rings"]
    post_bp_rings = sim["post_bp_rings"]
    bp_cutoff_ft = sim["bp_cutoff_ft"]

    if len(pre_bp_rings) >= 2:
        fig.add_trace(go.Surface(
            x=np.array([r[0] for r in pre_bp_rings]),
            y=np.array([r[1] for r in pre_bp_rings]),
            z=np.array([r[2] for r in pre_bp_rings]),
            opacity=0.30, colorscale=[[0, '#ffd166'], [1, '#f77f00']],
            showscale=False, name='Flare Area (Head~Mid)'
        ), row=1, col=1)

    for i, ring_pts in enumerate(pre_bp_rings):
        fig.add_trace(go.Scatter3d(
            x=ring_pts[0], y=ring_pts[1], z=ring_pts[2],
            mode='lines', line=dict(color='gold', width=4.5 if i == 0 else 2.0),
            name=f'Track: Head~Mid (0~{bp_cutoff_ft:.1f}ft)' if i == 0 else None,
            showlegend=(i == 0)
        ), row=1, col=1)

    if len(post_bp_rings) >= 1:
        ribbon_post = ([pre_bp_rings[-1]] + post_bp_rings) if len(pre_bp_rings) > 0 else post_bp_rings
        if len(ribbon_post) >= 2:
            fig.add_trace(go.Surface(
                x=np.array([r[0] for r in ribbon_post]),
                y=np.array([r[1] for r in ribbon_post]),
                z=np.array([r[2] for r in ribbon_post]),
                opacity=0.36, colorscale=[[0, '#ff4d6d'], [1, '#c9184a']],
                showscale=False, name='Flare Area (Breakpoint 이후)'
            ), row=1, col=1)

        for i, ring_pts in enumerate(post_bp_rings):
            fig.add_trace(go.Scatter3d(
                x=ring_pts[0], y=ring_pts[1], z=ring_pts[2],
                mode='lines', line=dict(color='#ff1e42', width=5.0 if i == len(post_bp_rings) - 1 else 2.4),
                name=f'Track: Breakpoint 이후 ({bp_cutoff_ft:.1f}ft~)' if i == 0 else None,
                showlegend=(i == 0)
            ), row=1, col=1)

    # 우측 3D 레인 시각화
    skid_end_ft = sim["skid_end_ft"]
    roll_start_ft = sim["roll_start_ft"]
    oil_length = p["oil_length"]
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

    traj_x_arr = np.array(sim["traj_x"])
    traj_y_arr = np.array(sim["traj_y"])
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