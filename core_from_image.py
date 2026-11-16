import cv2
import numpy as np
import plotly.graph_objects as go
from scipy.interpolate import interp1d

def extract_3d_core_from_image(img_path, core_height_inch=6.4, max_radius_inch=2.6, int_diff=0.015):
    """
    코어 단면 이미지에서 외곽선을 추출해 3D 표면 좌표(X, Y, Z)를 생성합니다.
    - 대칭 코어(int_diff == 0): 360도 회전체 생성
    - 비대칭 코어(int_diff > 0): PSA(+X) 방향으로 비대칭 돌기(Mass Bias) 형상 반영
    """
    img = cv2.imread(img_path)
    if img is None:
        raise FileNotFoundError(f"코어 이미지 '{img_path}'를 찾을 수 없습니다.")

    # 1. 그레이스케일 변환 및 이진화 (배경과 코어 분리)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # 배경이 흰색/밝은색이라고 가정하고 어두운 코어 영역 추출 (필요 시 THRESH_BINARY로 반전)
    _, thresh = cv2.threshold(blurred, 220, 255, cv2.THRESH_BINARY_INV)
    
    # 가장 큰 외곽선(코어 본체) 찾기
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        raise ValueError("이미지에서 코어 외곽선을 찾지 못했습니다. 배경 대비를 확인해주세요.")
    
    main_contour = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(main_contour)
    
    # 2. 높이(Z) 구간별로 코어의 좌측/우측 반지름 프로필 추출
    num_z_slices = 60
    z_samples = np.linspace(y + 2, y + h - 2, num_z_slices)
    
    # 마스크 이미지 생성
    mask = np.zeros_like(gray)
    cv2.drawContours(mask, [main_contour], -1, 255, -1)
    
    center_x = x + w / 2.0
    left_radii = []
    right_radii = []
    
    for row_idx in z_samples:
        r_idx = int(round(row_idx))
        white_pixels = np.where(mask[r_idx, :] > 0)[0]
        if len(white_pixels) > 0:
            l_dist = max(0.0, center_x - white_pixels[0])
            r_dist = max(0.0, white_pixels[-1] - center_x)
        else:
            l_dist, r_dist = 0.0, 0.0
        left_radii.append(l_dist)
        right_radii.append(r_dist)
        
    left_radii = np.array(left_radii)
    right_radii = np.array(right_radii)
    
    # 픽셀 단위를 실제 인치(inch) 단위로 스케일링
    max_px_radius = max(np.max(left_radii), np.max(right_radii))
    scale_factor = max_radius_inch / (max_px_radius + 1e-6)
    
    left_r_inch = left_radii * scale_factor
    right_r_inch = right_radii * scale_factor
    
    # Z 좌표: 위쪽(+Z)이 Pin 방향, 아래쪽(-Z)이 바닥
    z_inch = np.linspace(core_height_inch / 2.0, -core_height_inch / 2.0, num_z_slices)
    
    # 3. 360도 각도(theta)별로 반지름 보간하여 3D 메쉬 생성
    # theta = 0 (+X 방향)이 PSA(Mass Bias) 방향이므로 right_r_inch 적용
    # theta = pi (-X 방향)는 반대편이므로 left_r_inch 적용
    num_theta = 60
    theta = np.linspace(0, 2 * np.pi, num_theta)
    
    X = np.zeros((num_z_slices, num_theta))
    Y = np.zeros((num_z_slices, num_theta))
    Z = np.zeros((num_z_slices, num_theta))
    
    # 비대칭성(INT-Diff)에 따른 깊이(Y축) 납작함 비율
    y_asymmetry_ratio = max(0.65, 1.0 - int_diff * 12.0)
    
    for i in range(num_z_slices):
        for j, th in enumerate(theta):
            # cos(th)가 +1일 때 right_r(PSA 쪽), -1일 때 left_r(반대쪽) 사용
            weight = (np.cos(th) + 1.0) / 2.0
            r_curr = weight * right_r_inch[i] + (1.0 - weight) * left_r_inch[i]
            
            X[i, j] = r_curr * np.cos(th)
            Y[i, j] = r_curr * np.sin(th) * y_asymmetry_ratio
            Z[i, j] = z_inch[i]
            
    return X, Y, Z

# ==========================================
# 테스트 실행 (가지고 계신 코어 이미지 경로 입력)
# ==========================================
if __name__ == "__main__":
    # 예시: Power Hitter 코어 사진 파일명을 'power_hitter_core.jpg'로 저장 후 실행
    try:
        cx, cy, cz = extract_3d_core_from_image(
            "power_hitter_core.jpg",
            core_height_inch=6.5,
            max_radius_inch=2.7,
            int_diff=0.015
        )
        
        fig = go.Figure(data=[
            go.Surface(x=cx, y=cy, z=cz, colorscale='Oranges', opacity=0.9)
        ])
        fig.update_layout(
            title="Extracted 3D Bowling Core from Image",
            scene=dict(
                xaxis=dict(title='X (PSA Direction)', range=[-4, 4]),
                yaxis=dict(title='Y (Depth)', range=[-4, 4]),
                zaxis=dict(title='Z (Pin Direction)', range=[-4, 4]),
                aspectmode='cube'
            )
        )
        fig.show()
    except Exception as e:
        print(e)