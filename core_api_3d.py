import os
import time
import requests
import trimesh
import numpy as np
import plotly.graph_objects as go

# 1. 발급받은 Tripo3D API 키 입력 (반드시 'tsk_...' 형태의 실제 키를 입력하세요)
API_KEY = "tsk_Qm6wrBoH9PlWX_eY_c21s1-P_zdVV6oLffe2APVOp1d"
IMAGE_PATH = "code.jpg"        # 변환할 코어 이미지 파일명
OUTPUT_GLB = "bowling_core.glb" # 저장될 3D 모델 파일명

HEADERS = {
    "Authorization": f"Bearer {API_KEY}"
}

def upload_image(image_path):
    """로컬 코어 이미지를 API 서버에 업로드하고 image_token 획득"""
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"'{image_path}' 파일을 찾을 수 없습니다. 같은 폴더에 있는지 확인해주세요.")

    ext = os.path.splitext(image_path)[1].lower().replace(".", "")
    if ext == "jpg":
        ext = "jpeg"
    mime_type = f"image/{ext}"

    print(f"1. 코어 이미지({image_path}) 업로드 중...")
    url = "https://api.tripo3d.ai/v2/openapi/upload"
    with open(image_path, "rb") as f:
        files = {"file": (os.path.basename(image_path), f, mime_type)}
        res = requests.post(url, headers=HEADERS, files=files)
    
    if res.status_code != 200:
        print("업로드 에러 상세:", res.text)
        res.raise_for_status()
        
    token = res.json()["data"]["image_token"]
    print("   -> 업로드 완료!")
    return token, ext

def generate_3d_model(image_token, file_ext):
    """업로드된 이미지 토큰으로 Image-to-3D 변환 작업 요청"""
    print("2. 3D 메쉬 생성 요청 중...")
    url = "https://api.tripo3d.ai/v2/openapi/task"
    payload = {
        "type": "image_to_model",
        "model_version": "v2.5-20250123",
        "file": {
            "type": file_ext,
            "file_token": image_token
        }
    }
    res = requests.post(url, headers=HEADERS, json=payload)
    
    if res.status_code != 200:
        print("생성 요청 에러 상세:", res.text)
        res.raise_for_status()
        
    task_id = res.json()["data"]["task_id"]
    print(f"   -> 작업 시작됨 (Task ID: {task_id})")
    return task_id

def wait_and_download(task_id, output_path):
    """3D 생성이 완료될 때까지 대기 후 .glb 파일 다운로드"""
    print("3. 3D 모델 렌더링 대기 중 (약 5~15초 소요)...")
    url = f"https://api.tripo3d.ai/v2/openapi/task/{task_id}"
    
    while True:
        res = requests.get(url, headers=HEADERS)
        if res.status_code != 200:
            print("상태 조회 에러 상세:", res.text)
            res.raise_for_status()
            
        data = res.json()["data"]
        status = data["status"]
        
        if status == "success":
            model_url = data["output"].get("pbr_model") or data["output"].get("model")
            print("   -> 3D 생성 완료! 파일 다운로드 중...")
            glb_data = requests.get(model_url).content
            with open(output_path, "wb") as f:
                f.write(glb_data)
            print(f"   -> '{output_path}' 저장 완료!")
            break
        elif status in ["failed", "cancelled", "unknown"]:
            raise RuntimeError(f"3D 생성 실패: {data}")
        
        time.sleep(2)

def preview_glb_in_plotly(glb_path):
    """생성된 .glb 3D 메쉬 파일을 로드해 Plotly로 3D 확인"""
    scene_or_mesh = trimesh.load(glb_path)
    if isinstance(scene_or_mesh, trimesh.Scene):
        mesh = trimesh.util.concatenate(
            [g for g in scene_or_mesh.geometry.values()]
        )
    else:
        mesh = scene_or_mesh

    mesh.vertices -= mesh.centroid
    max_extent = np.max(mesh.extents)
    mesh.vertices *= (6.2 / max_extent)

    vertices = mesh.vertices
    faces = mesh.faces

    if hasattr(mesh.visual, 'vertex_colors') and len(mesh.visual.vertex_colors) == len(vertices):
        colors = mesh.visual.vertex_colors[:, :3]
        vertex_color = [f'rgb({r},{g},{b})' for r, g, b in colors]
    else:
        vertex_color = None

    fig = go.Figure(data=[
        go.Mesh3d(
            x=vertices[:, 0], y=vertices[:, 1], z=vertices[:, 2],
            i=faces[:, 0], j=faces[:, 1], k=faces[:, 2],
            vertexcolor=vertex_color,
            color='silver' if vertex_color is None else None,
            opacity=1.0,
            flatshading=False,
            lighting=dict(ambient=0.5, diffuse=0.8, specular=0.6, roughness=0.3)
        )
    ])
    fig.update_layout(
        title="AI Reconstructed 3D Bowling Core (.glb)",
        scene=dict(aspectmode='data')
    )
    fig.show()

if __name__ == "__main__":
    if not API_KEY.startswith("tsk_"):
        raise ValueError("API_KEY 변수에 'tsk_'로 시작하는 실제 Tripo3D API 키를 입력해주세요!")
        
    token, ext = upload_image(IMAGE_PATH)
    tid = generate_3d_model(token, ext)
    wait_and_download(tid, OUTPUT_GLB)
    preview_glb_in_plotly(OUTPUT_GLB)