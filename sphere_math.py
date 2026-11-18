import numpy as np
from scipy.spatial.transform import Rotation as R
from config_presets import BALL_RADIUS

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