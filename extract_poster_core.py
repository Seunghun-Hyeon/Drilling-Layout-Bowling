import cv2
import numpy as np
import plotly.graph_objects as go

def extract_clean_core_3d(img_path, core_height_inch=6.5, max_radius_inch=2.7, int_diff=0.017):
    img = cv2.imread(img_path)
    if img is None:
        raise FileNotFoundError(f"'{img_path}' 파일을 찾을 수 없습니다.")

    # 1. 흰색 배경 제거 (배경이 245 이상인 순백색이므로 반전 이진화로 코어만 100% 추출)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray, 245, 255, cv2.THRESH_BINARY_INV)

    # 노이즈 제거 및 외곽선 정리
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    main_contour = max(contours, key=cv2.contourArea)

    clean_mask = np.zeros_like(mask)
    cv2.drawContours(clean_mask, [main_contour], -1, 255, -1)

    # 2. 노란색 Pin 위치를 자동으로 찾아 위쪽(12시 방향)으로 정렬
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    # 노란색 핀 영역 검출
    yellow_mask = cv2.inRange(hsv, np.array([15, 100, 100]), np.array([35, 255, 255]))
    y_pts = np.column_stack(np.where(yellow_mask > 0))

    # 코어 전체 무게중심 계산
    M_moments = cv2.moments(clean_mask)
    cx_img = M_moments["m10"] / M_moments["m00"]
    cy_img = M_moments["m01"] / M_moments["m00"]

    if len(y_pts) > 0:
        # 노란색 핀의 중심 좌표
        pin_y, pin_x = np.mean(y_pts, axis=0)
        # 무게중심에서 노란색 핀을 향하는 벡터의 각도 -> 12시(-90도)로 회전
        angle_to_pin = np.degrees(np.arctan2(pin_y - cy_img, pin_x - cx_img))
        rot_angle = angle_to_pin + 90.0
    else:
        rot_angle = 0.0

    h, w = clean_mask.shape
    rot_mat = cv2.getRotationMatrix2D((cx_img, cy_img), rot_angle, 1.0)
    upright_mask = cv2.warpAffine(clean_mask, rot_mat, (w, h))

    # 3. 높이(Z) 구간별 좌/우 반지름 프로필 추출
    ux, uy, uw, uh = cv2.boundingRect(upright_mask)
    center_x = ux + uw / 2.0

    num_z = 70
    z_samples = np.linspace(uy + 2, uy + uh - 2, num_z)
    left_r, right_r = [], []

    for r_idx in z_samples:
        row_pixels = np.where(upright_mask[int(round(r_idx)), :] > 0)[0]
        if len(row_pixels) > 0:
            left_r.append(max(0.0, center_x - row_pixels[0]))
            right_r.append(max(0.0, row_pixels[-1] - center_x))
        else:
            left_r.append(0.0)
            right_r.append(0.0)

    left_r = np.array(left_r)
    right_r = np.array(right_r)

    max_px = max(np.max(left_r), np.max(right_r))
    scale = max_radius_inch / (max_px + 1e-6)
    left_r_inch = left_r * scale
    right_r_inch = right_r * scale
    z_inch = np.linspace(core_height_inch / 2.0, -core_height_inch / 2.0, num_z)

    # 4. 3D 메쉬 생성
    num_theta = 70
    theta = np.linspace(0, 2 * np.pi, num_theta)
    X = np.zeros((num_z, num_theta))
    Y = np.zeros((num_z, num_theta))
    Z = np.zeros((num_z, num_theta))

    y_ratio = max(0.7, 1.0 - int_diff * 10.0)

    for i in range(num_z):
        for j, th in enumerate(theta):
            w_side = (np.cos(th) + 1.0) / 2.0
            r_curr = w_side * right_r_inch[i] + (1.0 - w_side) * left_r_inch[i]
            X[i, j] = r_curr * np.cos(th)
            Y[i, j] = r_curr * np.sin(th) * y_ratio
            Z[i, j] = z_inch[i]

    return X, Y, Z

if __name__ == "__main__":
    cx, cy, cz = extract_clean_core_3d("code.jpg", int_diff=0.017)

    fig = go.Figure(data=[
        go.Surface(x=cx, y=cy, z=cz, colorscale='RdBu', opacity=0.95)
    ])
    fig.update_layout(
        title="3D Reconstructed Core (Clean Cutout)",
        scene=dict(
            xaxis=dict(title='X (비대칭 방향)', range=[-4, 4]),
            yaxis=dict(title='Y (두께)', range=[-4, 4]),
            zaxis=dict(title='Z (Pin 방향)', range=[-4, 4]),
            aspectmode='cube'
        )
    )
    fig.show()