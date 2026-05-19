import numpy as np
import plotly.graph_objects as go
from noise import pnoise2

def generate_noise_map(width, height, scale, octaves, persistence, lacunarity, seed):
    world = np.zeros((width, height))
    for i in range(width):
        for j in range(height):
            world[i][j] = pnoise2(i/scale, 
                                  j/scale, 
                                  octaves=octaves, 
                                  persistence=persistence, 
                                  lacunarity=lacunarity, 
                                  repeatx=width, 
                                  repeaty=height, 
                                  base=seed)
    return world

# --- 설정값 ---
width, height = 150, 150
scale = 180.0
octaves = 6
persistence = 0.5
lacunarity = 2.0
seed = np.random.randint(0, 100)
sea_level = -0.01  # 해수면 높이

# 1. 지형 노이즈 생성
noise_map = generate_noise_map(width, height, scale, octaves, persistence, lacunarity, seed)

# 2. 물 레이어 마스킹 처리 (핵심!)
# 지형(noise_map)이 해수면(sea_level)보다 낮은 곳에만 sea_level 값을 넣고,
# 지형이 더 높은 곳은 np.nan(결측값)을 넣어 렌더링되지 않게 합니다.
water_map = np.where(noise_map < sea_level, sea_level, np.nan)

# 3. 시각화
fig = go.Figure()

# 지형 레이어 (불투명하게 설정하여 산맥의 무게감 표현)
fig.add_trace(go.Surface(
    z=noise_map,
    colorscale=[
        [0, 'rgb(34, 100, 34)'],    # 깊은 숲
        [0.3, 'rgb(60, 160, 60)'],   # 풀밭
        [0.6, 'rgb(140, 110, 70)'],  # 바위/흙
        [1.0, 'rgb(255, 255, 255)']  # 눈
    ],
    name='Terrain',
    showscale=True,
    colorbar=dict(title="Height", x=-0.1)
))

# 물 레이어 (산 밑에는 존재하지 않음)
fig.add_trace(go.Surface(
    z=water_map,
    showscale=False,
    opacity=0.8, # 약간의 투명도만 유지
    colorscale=[[0, 'royalblue'], [1, 'royalblue']],
    name='Sea/Lakes'
))

# 4. 레이아웃 및 카메라 설정
fig.update_layout(
    title=f"Terrain with Realistic Water (No water under mountains)",
    scene=dict(
        xaxis_title='X',
        yaxis_title='Y',
        zaxis_title='Height',
        zaxis=dict(range=[-0.15, 0.15]),
        aspectratio=dict(x=1, y=1, z=0.5)
    ),
    margin=dict(l=0, r=0, b=0, t=50)
)

fig.show()