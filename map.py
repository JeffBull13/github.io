import pandas as pd
import geopandas as gpd
import folium
from folium.plugins import MiniMap
from branca.colormap import LinearColormap

# 设置常量
SHAPE_CITIES_PATH = 'china_cities.shp'  # 推荐转换为TopoJSON
EXCEL_DATA_PATH = '客户投资数据.xlsx'
OUTPUT_HTML = 'invest_map_optimized.html'

# 读取并预处理数据
def load_and_preprocess():
    df = pd.read_excel(EXCEL_DATA_PATH, sheet_name='原始数据')
    df['城市'] = df['城市'].replace({'重庆市': '重庆'})
    return df.groupby('城市', as_index=False)['投资额'].sum()

df_merged = load_and_preprocess()

# 加载并优化地理数据
def optimize_geodata():
    # 读取时筛选必要列并简化几何
    cities = gpd.read_file(SHAPE_CITIES_PATH, columns=['市', 'geometry'])
    cities['geometry'] = cities.simplify(0.005)  # 简化几何精度
    
    # 合并数据时筛选有效数据
    merged = cities.merge(
        df_merged,
        left_on='市',
        right_on='城市',
        how='inner'
    )
    return merged[['市', '投资额', 'geometry']]  # 仅保留必要字段

geo_data = optimize_geodata()

# 创建基础地图
m = folium.Map(
    location=[35, 105],
    zoom_start=5,
    tiles='https://webrd02.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}',
    attr='高德地图',
    control_scale=True,
    prefer_canvas=True
)

# 绿色渐变颜色映射
colormap = LinearColormap(
    colors=['#c0d8b6', '#48a23f', '#1a5d1a'],
    vmin=df_merged['投资额'].min(),
    vmax=df_merged['投资额'].max(),
    caption='投资额（万元）'
)

# 使用优化后的GeoJSON添加图层
folium.GeoJson(
    geo_data,
    name='投资分布',
    style_function=lambda x: {
        'fillColor': colormap(x['properties']['投资额']),
        'color': '#096dd9',
        'weight': 0.8,
        'fillOpacity': 0.7
    },
    tooltip=folium.GeoJsonTooltip(
        fields=['市', '投资额'],
        aliases=['城市: ', '投资额: '],
        style='font-size:12px;padding:3px'
    ),
    control=False,
    smooth_factor=1,  # 减少路径平滑处理
    zoom_on_click=False,
    highlight_function=lambda x: {'weight': 2, 'color': '#ff4d4f'}
).add_to(m)

# 简化标题样式
title_html = '''
<div style="position:fixed;top:10px;left:50px;z-index:999;
background:rgba(255,255,255,0.8);padding:5px;border-radius:3px;
font:bold 14px Arial">客户投资分布（万元）</div>
'''
m.get_root().html.add_child(folium.Element(title_html))

m.save(OUTPUT_HTML)
print(f"优化版地图已生成：{OUTPUT_HTML}")