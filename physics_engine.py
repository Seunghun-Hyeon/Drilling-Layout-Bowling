import numpy as np
from config_presets import BALL_RADIUS
from sphere_math import move_on_sphere, rotate_tangent, intersect_two_sphere_circles

def run_simulation(p):
    # 1. 그립 홀 및 PAP 좌표 계산
    grip_center_dir = np.array([0.0, -1.0, 0.0])  # 정면(-Y) = 그립 중심(CG)

    if p["has_thumb"]:
        half_span = p["span_inch"] / 2.0
        finger_bridge_center = move_on_sphere(grip_center_dir, np.array([0.0, 0.0, 1.0]), half_span)
        middle_dir = move_on_sphere(finger_bridge_center, np.array([-1.0, 0.0, 0.0]), 0.55)
        ring_dir   = move_on_sphere(finger_bridge_center, np.array([1.0, 0.0, 0.0]), 0.55)

        vertical_span_comp = np.sqrt(max(0.0, p["span_inch"]**2 - p["thumb_offset"]**2))
        thumb_base_dir = move_on_sphere(finger_bridge_center, np.array([0.0, 0.0, -1.0]), vertical_span_comp)
        thumb_dir = move_on_sphere(thumb_base_dir, np.array([-1.0, 0.0, 0.0]), p["thumb_offset"])
    else:
        finger_bridge_center = move_on_sphere(grip_center_dir, np.array([0.0, 0.0, 1.0]), 0.3)
        middle_dir = move_on_sphere(finger_bridge_center, np.array([-1.0, 0.0, 0.0]), 0.55)
        ring_dir   = move_on_sphere(finger_bridge_center, np.array([1.0, 0.0, 0.0]), 0.55)
        thumb_dir  = None

    pap_temp = move_on_sphere(grip_center_dir, np.array([1.0, 0.0, 0.0]), p["pap_x"])
    up_dir = np.array([0.0, 0.0, 1.0]) if p["pap_y"] >= 0 else np.array([0.0, 0.0, -1.0])
    pap_vec = move_on_sphere(pap_temp, up_dir, abs(p["pap_y"]))

    val_up_tangent = np.array([0.0, 0.0, 1.0]) - np.dot(np.array([0.0, 0.0, 1.0]), pap_vec) * pap_vec
    val_up_tangent /= np.linalg.norm(val_up_tangent)

    # 2. 레이아웃 시스템별 Pin / PSA 계산
    layout_system = p["layout_system"]
    pin_to_psa = p["pin_to_psa"]

    if "Dual Angle" in layout_system:
        pin_dir_from_pap = rotate_tangent(pap_vec, val_up_tangent, +p["val_angle"])
        pin_vec = move_on_sphere(pap_vec, pin_dir_from_pap, p["pin_to_pap"])

        pin_to_pap_tangent = pap_vec - np.dot(pap_vec, pin_vec) * pin_vec
        pin_to_pap_tangent /= np.linalg.norm(pin_to_pap_tangent)

        psa_dir_from_pin = rotate_tangent(pin_vec, pin_to_pap_tangent, -p["drill_angle"])
        psa_vec = move_on_sphere(pin_vec, psa_dir_from_pin, pin_to_psa)

        layout_summary_str = f"Dual Angle: {p['drill_angle']}° × {p['pin_to_pap']:.3f}\" × {p['val_angle']}°"
        effective_val_deg = p["val_angle"]

    elif "2LS" in layout_system:
        prefer_pin = np.array([-0.2, -0.4, 0.9])
        pin_vec = intersect_two_sphere_circles(pap_vec, p["ls2_pin_pap"], grip_center_dir, p["ls2_pin_cog"], prefer_dir=prefer_pin)

        pin_to_pap_tangent = pap_vec - np.dot(pap_vec, pin_vec) * pin_vec
        if np.linalg.norm(pin_to_pap_tangent) > 1e-6:
            pin_to_pap_tangent /= np.linalg.norm(pin_to_pap_tangent)
        else:
            pin_to_pap_tangent = np.array([1.0, 0.0, 0.0])

        equiv_drill_angle = np.clip((p["ls2_buffer"] / 6.75) * 90.0, 15.0, 95.0)
        psa_dir_from_pin = rotate_tangent(pin_vec, pin_to_pap_tangent, -equiv_drill_angle)
        psa_vec = move_on_sphere(pin_vec, psa_dir_from_pin, pin_to_psa)

        effective_val_deg = np.clip(90.0 - (p["ls2_buffer"] * 10.0), 15.0, 80.0)
        layout_summary_str = f"2LS: {p['ls2_pin_pap']:.3f}\" × {p['ls2_pin_cog']:.3f}\" × {p['ls2_buffer']:.3f}\""

    elif "VLS" in layout_system:
        sin_val = np.clip(np.sin(p["vls_pin_val"] / BALL_RADIUS) / max(1e-4, np.sin(p["vls_pin_pap"] / BALL_RADIUS)), 0.0, 1.0)
        calc_val_deg = np.degrees(np.arcsin(sin_val))
        if "Down" in p["vls_pin_pos"]:
            calc_val_deg = 180.0 - calc_val_deg

        pin_dir_from_pap = rotate_tangent(pap_vec, val_up_tangent, +calc_val_deg)
        pin_vec = move_on_sphere(pap_vec, pin_dir_from_pap, p["vls_pin_pap"])

        prefer_psa = np.array([0.3, -0.5, -0.8])
        psa_vec = intersect_two_sphere_circles(pin_vec, pin_to_psa, pap_vec, p["vls_psa_pap"], prefer_dir=prefer_psa)

        layout_summary_str = f"VLS: {p['vls_pin_pap']:.3f}\" × {p['vls_psa_pap']:.3f}\" × {p['vls_pin_val']:.3f}\""
        effective_val_deg = calc_val_deg

    pin_pos = pin_vec * BALL_RADIUS
    psa_pos = psa_vec * BALL_RADIUS

    # 3. 코어 3축 정렬 (X=Pin 최저 RG, Y=PSA 최고 RG, Z=중간 RG)
    rg, diff, int_diff = p["rg"], p["diff"], p["int_diff"]
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

    # 4. [스키드 → 훅 → 롤] 물리 엔진
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
    grit_skid_offset = ((p["surface_grit"] - 2000) / 2000.0) * 0.05
    early_val_offset = -((90.0 - min(90.0, effective_val_deg)) / 60.0) * 0.05
    oil_length = p["oil_length"]
    skid_end_ft = oil_length * np.clip(
        0.50 + rg_skid_offset + cover_skid_map.get(p["cover_type"], 0.0) + grit_skid_offset + early_val_offset,
        0.30, 0.75
    )

    cover_friction_map = {
        "솔리드 리액티브 (Solid - 강한 오일 마찰)": 1.28,
        "하이브리드 리액티브 (Hybrid)": 1.05,
        "펄 리액티브 (Pearl - 긴 스키드/백엔드)": 0.92,
        "우레탄 (Urethane - 컨트롤)": 0.72,
        "플라스틱 / 폴리에스터 (스페어용)": 0.20
    }
    cover_mult = cover_friction_map.get(p["cover_type"], 1.0)
    grit_mult = 1.0 + (2000 - p["surface_grit"]) / 4000.0
    total_surface_grip = cover_mult * grit_mult

    dt = 0.005
    y_ft = 0.0
    elapsed_time = 0.0
    start_board = p["start_board"]
    target_board = p["target_board"]
    x_board = float(start_board)

    speed_fps = p["speed_mph"] * 1.46667
    init_angle_rad = np.arctan2((target_board - start_board) * 1.06 / 12.0, 15.0)
    vx = speed_fps * np.sin(init_angle_rad)
    vy = speed_fps * np.cos(init_angle_rad)

    rpm = p["rpm"]
    omega = rpm * 2 * np.pi / 60.0
    curr_rot = np.radians(p["axis_rot"])
    curr_tilt = np.radians(p["axis_tilt"])

    migrated_rad = 0.0
    axis_history_rad = []
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
        rev_history.append((rpm / 60.0) * elapsed_time)

        if x_board < max_right_board:
            max_right_board = x_board
            breakpoint_ft = y_ft

        is_roll_phase = (curr_rot <= np.radians(12.0)) and (y_ft > oil_length * 0.85)
        if is_roll_phase and roll_start_ft is None:
            roll_start_ft = y_ft

        if y_ft < skid_end_ft:
            zone_mu = 0.012
            phase_flare_weight = 0.65 * rg_activation_speed
        elif y_ft < oil_length + 6.0:
            trans_progress = (y_ft - skid_end_ft) / max(1.0, (oil_length + 6.0) - skid_end_ft)
            zone_mu = 0.045 + 0.085 * (trans_progress ** 1.1)
            phase_flare_weight = (1.75 + 0.95 * np.sin(trans_progress * np.pi)) * rg_activation_speed
        else:
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

    # 5. 오일 트랙 링 & 나비넥타이 면적 계산
    bowtie_normal = np.cross(spin_axis_init, target_spin_axis)
    if np.linalg.norm(bowtie_normal) > 1e-6 and flare_potential_inch > 0.2:
        bowtie_normal /= np.linalg.norm(bowtie_normal)
        bowtie_pt_vec = bowtie_normal if np.dot(bowtie_normal, grip_center_dir) >= 0 else -bowtie_normal
    else:
        bowtie_pt_vec = None

    track_rings = []
    track_y_positions = []
    min_hole_dist_inch = 99.0
    first_ring_thumb_dist = 99.0

    active_holes_with_rad = [(middle_dir, 0.45), (ring_dir, 0.45)]
    if p["has_thumb"] and thumb_dir is not None:
        active_holes_with_rad.append((thumb_dir, 0.52))

    theta = np.linspace(0, 2 * np.pi, 120)
    display_track_tilt = float(p["axis_tilt"]) - 3.0
    track_polar_angle = (np.pi / 2.0) - np.radians(display_track_tilt)

    precession_path_pts = []
    if total_axis_gap_rad > 1e-5:
        ortho_dir = target_spin_axis - np.dot(target_spin_axis, spin_axis_init) * spin_axis_init
        ortho_dir /= np.linalg.norm(ortho_dir)
    else:
        ortho_dir = y_core_psa

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

            if len(track_rings) == 1 and p["has_thumb"] and thumb_dir is not None:
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
    bp_cutoff_ft = breakpoint_ft if breakpoint_ft is not None else float(oil_length)
    pre_bp_rings = [r for r, y_pos in zip(track_rings, track_y_positions) if y_pos < bp_cutoff_ft]
    post_bp_rings = [r for r, y_pos in zip(track_rings, track_y_positions) if y_pos >= bp_cutoff_ft]

    ref_dist = first_ring_thumb_dist if p["has_thumb"] else min_hole_dist_inch
    if ref_dist <= 0.75:
        track_category = "하이 트랙 (High Track)"
        track_desc = f"표시 틸트 {display_track_tilt:.0f}° · 엄지/중지 1마디 이내 밀착"
    elif ref_dist <= 1.75:
        track_category = "미디엄 / 세미 트랙"
        track_desc = f"표시 틸트 {display_track_tilt:.0f}° · 엄지 2번째 마디 부근"
    else:
        track_category = "로우 트랙 (Low Track)"
        track_desc = f"표시 틸트 {display_track_tilt:.0f}° · 홀 외곽 적도 부근"

    activation_pct = (flare_potential_inch / max(target_flare_inch, 0.01)) * 100.0

    return {
        "u": u, "v": v, "rc_x": rc_x, "rc_y": rc_y, "rc_z": rc_z,
        "grip_center_dir": grip_center_dir, "middle_dir": middle_dir,
        "ring_dir": ring_dir, "thumb_dir": thumb_dir,
        "pin_vec": pin_vec, "pin_pos": pin_pos, "psa_pos": psa_pos,
        "pap_vec": pap_vec, "val_up_tangent": val_up_tangent,
        "bowtie_pt_vec": bowtie_pt_vec, "precession_path_pts": precession_path_pts,
        "pre_bp_rings": pre_bp_rings, "post_bp_rings": post_bp_rings,
        "bp_cutoff_ft": bp_cutoff_ft, "layout_summary_str": layout_summary_str,
        "skid_end_ft": skid_end_ft, "roll_start_ft": roll_start_ft,
        "traj_x": traj_x, "traj_y": traj_y,
        "flare_potential_inch": flare_potential_inch, "activation_pct": activation_pct,
        "total_revolutions": total_revolutions, "min_hole_dist_inch": min_hole_dist_inch,
        "track_category": track_category, "track_desc": track_desc
    }