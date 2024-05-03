from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

import subprocess, os, json, pandas as pd, requests
from pymongo import MongoClient
from statistics import mean
import numpy as np

import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

from database import db_conn
from models import year_barGraph,region_versus,social_graph
from database import engine

# 전역 변수 정의
app = FastAPI()
db = db_conn()
session = db.sessionmaker()

# secret.json파일 설정 및 경로
secret_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) , 'secret.json')
with open(secret_file) as f:
    secrets = json.loads(f.read())
def get_secret(setting, secrets=secrets):
    try:
        return secrets[setting]
    except KeyError:
        errorMsg = "Set the {} environment variable.".format(setting)
        return errorMsg

# secret.json => MySQL 설정
HOSTNAME = get_secret("Mysql_Hostname")
PORT = get_secret("Mysql_Port")
USERNAME = get_secret("Mysql_Username")
PASSWORD = get_secret("Mysql_Password")
DBNAME = get_secret("Mysql_DBname")    

# Font 경로 및 설정
font_path = '/usr/share/fonts/truetype/nanum/NanumGothic.ttf'
font_prop = FontProperties(fname=font_path)
plt.rcParams['font.family'] = font_prop.get_name()

# MongoDB 설정
client = MongoClient('mongodb://192.168.1.105:27017')  
db = client['project']  
stress_collection = db['stress'] 
stress_mean_collection = db['stress_mean']
stress_region_collection = db['stress_region']
social_mobility_collection = db['Social_mobility']

initial_port = 5000  

# cors 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 도메인 허용
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메소드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)

# 경로 설정
data_path = os.path.join(os.getcwd(), 'api_data/data')
json_path = os.path.join(os.getcwd(), 'api_data/json')
os.makedirs(json_path, exist_ok=True)  # json 경로가 없다면 생성

# FastAPI
@app.get('/start_jsonserver')  # GET 메서드 사용
async def start_jsonserver():
    global data_path, json_path
    port = initial_port
    files = os.listdir(data_path)

    for input_file in files:
        file_name, _ = os.path.splitext(input_file)
        if input_file.endswith('.csv'):
            data = pd.read_csv(os.path.join(data_path, input_file), encoding='cp949')
        elif input_file.endswith('.xlsx'):
            data = pd.read_excel(os.path.join(data_path, input_file))
        
        # 각 파일의 모든 데이터를 하나의 객체로 만들어 배열에 담기
        all_data = [data.to_dict(orient='records')]
        output_json = os.path.join(json_path, f"{file_name}.json")
        
        # 하나의 객체를 담은 배열을 JSON 파일로 저장
        with open(output_json, 'w') as f:
            json.dump(all_data, f, indent=4)
        # JSON Server 실행
        cmd = f'json-server --watch {output_json} --host 0.0.0.0 --port {port}'
        subprocess.Popen(cmd, shell=True)
        port += 1        
    return {"message": f"JSON Servers started, starting from port {initial_port}."} 

@app.get("/make_df")
async def get_df():
    response = requests.get('http://192.168.1.105:5000/0')
    data = response.json()
    # stress_collection.insert_many(data)
    
    stress = pd.DataFrame(data)
    regions = stress['region_name'].values
    stress.drop(columns=['id'], inplace=True)
    stress.set_index('region_name', inplace=True)
    
    stress_year_columns = {year: [] for year in range(2013, 2023)}
    for col in stress.columns:
        year = col.split('.')[0]
        if year.isdigit() and int(year) in stress_year_columns:
            stress_year_columns[int(year)].append(col)

    def make_df_year(df, regions):
        df = df.copy()
        df.set_index(regions, inplace=True)
        columns = [
            '전혀 느끼지 않았다 (%)',
            '느끼지 않은 편이다 (%)',
            '보통이다 (%)',
            '느낀 편이다 (%)',
            '매우 많이 느꼈다 (%)'
        ]
        
        df.columns = columns
        return df

    def stress_year_mean(df):
        return {col: df[col].mean() for col in df.columns}

    stress_dfs = {}
    for year, columns in stress_year_columns.items():
        if columns:
            year_df = stress[columns]
            prepared_df = make_df_year(year_df, regions)
            stress_dfs[year] = stress_year_mean(prepared_df)
    stress_mean_collection.insert_many([{"year": year, "data": data} for year, data in stress_dfs.items()])
    
@app.get('/get_data')
def get_data():
    items = list(stress_collection.find({} , {"_id":0}))
    return jsonable_encoder(items)

@app.get('/get_data_mean')
def get_data():
    items = list(stress_mean_collection.find({} , {"_id":0}))
    return jsonable_encoder(items)

@app.get('/visual/region_graph/{region}/{start_year}_{end_year}/{select_year}')
async def draw_plot(region: str, start_year: int, end_year: int, select_year: int):
    name = f'{region}_{start_year}_to_{end_year}'

    data_mysql = session.query(year_barGraph).filter(year_barGraph.name == name).first()
    if data_mysql:
        return FileResponse(data_mysql.image_url)
    else :
        items = list(stress_mean_collection.find({} , {"_id":0}))
        df_mean = pd.DataFrame(items)
        expanded_data = {str(item['year']): item['data'] for item in items}
        df_expanded = pd.DataFrame(expanded_data)
        df_expanded.columns = df_expanded.columns.astype(int)

        df_selected_range = df_expanded.loc[:, start_year:end_year]
        df_selected_range_mean = df_selected_range.mean(axis=1)
        
        
        items = list(stress_collection.find({"region_name": region}, {'_id':0}))
        df = pd.DataFrame(items)
        selected_year_columns = [col for col in df.columns if col.startswith(f'{select_year}.')]
        df_selected_year = df[selected_year_columns]
        
        rename_mapping = {
            f'{select_year}.1': '전혀 느끼지 않았다 (%)',
            f'{select_year}.2': '느끼지 않은 편이다 (%)',
            f'{select_year}.3': '보통이다 (%)',
            f'{select_year}.4': '느낀 편이다 (%)',
            f'{select_year}.5': '매우 많이 느꼈다 (%)'
        }
        
        df_selected_year = df_selected_year.rename(columns=rename_mapping)

        colors = sns.color_palette('hls', 5)
        bar_width = 0.35
        selected_year_row_np = df_selected_year.loc[0].values 

        plt.figure(figsize=(8, 6))
        plt.title(f'{region}_스트레스 분포', fontproperties=font_prop)

        plt.bar(np.arange(len(df_selected_range_mean)) - bar_width/2, df_selected_range_mean.values, bar_width, color=colors[2], label=f'평균 ({start_year}-{end_year})')
        plt.bar(np.arange(len(df_selected_year.loc[0])) + bar_width/2, df_selected_year.loc[0].values, bar_width, color=colors[3], label=f'{select_year}년 데이터')

        plt.xticks(np.arange(len(df_selected_year.loc[0])), df_selected_year.columns, rotation=30)
        file_path = f'./img/{region}_bar_chart.png'
        plt.legend()
        plt.tight_layout()
        plt.savefig(file_path,dpi=400, bbox_inches='tight')
        plt.close() # 여기까지 그림그리기
        
        graph = year_barGraph(image_url=file_path, name=name) # 여기가 mysql에 없으면 이니까 저장해주기
        session.add(graph)
        session.commit()    
        return FileResponse(file_path)   

@app.get('/visual/{region1}vs{region2}/{start_year}to{end_year}')
async def draw_graph(region1: str, region2: str,start_year: int, end_year: int):
    name = f'{region1}vs{region2}_bar chart_{start_year}_{end_year}.png'

    data_mysql = session.query(region_versus).filter(region_versus.name == name).first()
    if data_mysql:
        return FileResponse(data_mysql.image_url)
    else:
        # MongoDB에서 전체 데이터를 검색하여 DataFrame 생성
        stress_items = list(stress_collection.find({}, {"_id": 0}))
        stress = pd.DataFrame(stress_items)
        
        # Mean DataFrame
        stress_items = list(stress_mean_collection.find({}, {"_id":0}))
        stress_mean = pd.DataFrame(stress_items)
        
        # 연도별 컬럼을 저장할 딕셔너리
        stress_columns = {str(year): [] for year in range(2013, 2023)}

        # 각 연도별로 해당하는 컬럼을 딕셔너리에 추가
        for column in stress.columns:
            if "." in column and column.split('.')[0].isdigit():
                year = column.split('.')[0]
                stress_columns[year].append(column)

        # DataFrame을 만드는 함수
        def make_df_year(df, columns, year):
            df_year = df[['region_name'] + columns].copy()
            df_year.columns = ['region_name'] + columns
            df_year.set_index('region_name', inplace=True)
            df_year.columns = [
                '전혀 느끼지 않았다 (%)',
                '느끼지 않은 편이다 (%)',
                '보통이다 (%)',
                '느낀 편이다 (%)',
                '매우 많이 느꼈다 (%)'
            ]
            df_year['year'] = int(year)  # 연도 추가
            return df_year.reset_index()

        # 각 연도별로 DataFrame을 만들고 병합합니다.
        stress_dfs = []
        for year, columns in stress_columns.items():
            if columns:
                df_year = make_df_year(stress, columns, year)
                stress_dfs.append(df_year)

        # 모든 연도의 데이터프레임을 하나로 병합합니다.
        final_stress_df = pd.concat(stress_dfs).set_index(['region_name', 'year'])
        
        # MongoDB 저장 stress_region
        # data_dicts = final_stress_df.reset_index().to_dict('records')
        # stress_region_collection.insert_many(data_dicts)
        
        file_path = f'./img/{region1}vs{region2}_bar chart.png'

        region1_df = final_stress_df.loc[f'{region1}'].loc[start_year:end_year]
        region2_df = final_stress_df.loc[f'{region2}'].loc[start_year:end_year]
        
        df = stress_mean
        data_df = pd.json_normalize(df['data'])
        df = df.drop('data', axis=1).join(data_df)
        filtered_df = df[df['year'].between(start_year, end_year)]
        filtered_df.set_index('year', inplace=True)
        # merged_df = pd.concat([region1_df, region2_df])
        
        def create_index_tuples(region1, region2, start_year, end_year):
            index_tuples = []
            # region1에 대한 튜플 추가
            for year in range(start_year, end_year + 1):
                index_tuples.append((region1, year))
            
            # mean에 대한 튜플 추가
            for year in range(start_year, end_year + 1):
                index_tuples.append(('mean', year))
            
            # region2에 대한 튜플 추가
            for year in range(start_year, end_year + 1):
                index_tuples.append((region2, year))
            
            return index_tuples

        def draw_region_compare_stress(region1_df, region2_df, filtered_df, index_tuples):
            merged_df = pd.concat([region1_df, filtered_df, region2_df], axis=0)
            multi_index = pd.MultiIndex.from_tuples(index_tuples, names=['location', 'year'])
            merged_df.set_index(multi_index, inplace=True)
            print(merged_df)
            merged_df.plot(kind='barh', stacked=True, figsize=(12, 8), title=f'{region1} vs {region2}')
            
            last_indices = [] 
            locations = merged_df.index.get_level_values('location').unique()
            
            for location in locations:
                last_index = merged_df.loc[location].index[-1] 
                overall_index = merged_df.index.tolist().index((location, last_index)) 
                last_indices.append(overall_index)
            for idx in last_indices:
                plt.axhline(y=idx + 0.5, color='k', linestyle='--', linewidth=2)
                
            plt.legend(loc='best')
            plt.xticks(rotation=30)
            file_path = f'./img/{name}'
            plt.tight_layout()
            plt.legend(bbox_to_anchor=(1,1))
            plt.savefig(file_path,dpi=400, bbox_inches='tight')    
            graph = region_versus(image_url=file_path, name=name) # 여기가 mysql에 없으면 이니까 저장해주기
            session.add(graph)
            session.commit() 
            return FileResponse(data_mysql.image_url)

        index_tuples = create_index_tuples(region1, region2, start_year, end_year)
        draw_region_compare_stress(region1_df, region2_df, filtered_df, index_tuples)


@app.get('/save_mongo_social_mobility')
def save_mongo():
    response = requests.get('http://192.168.1.105:5001/0')
    social_mobility_data = response.json()
    social_mobility_collection.insert_many(social_mobility_data)
    
    return {'message': 'Social Mobility data saved to MongoDB successfully.'}
        
@app.get('/save_mongo_stress')
def save_mongo():
    response = requests.get('http://192.168.1.105:5000/0')
    data = response.json()
    stress_collection.insert_many(data)
    return {'message': 'Stress data saved to MongoDB successfully.'}

@app.get('/visual/social_graph/{start_year}_{end_year}/{region1}vs{region2}')
async def draw_plot(start_year:int, end_year:int, region1:str, region2:str):
    name = f'social_mobility_{region1}vs{region2}_graph_{start_year}_{end_year}'
    data_mysql = session.query(social_graph).filter(social_graph.name == name).first()
    if data_mysql:
        return FileResponse(data_mysql.image_url)
    else:
        # 평균값 구하기
        all_data = list(social_mobility_collection.find({},{"_id": 0, 'id':0,'10점 평균 (점)' : 0}))
        all_data = pd.DataFrame(all_data)
        all_data.rename(columns={'시점':'year','구분별(2)':'region_name'}, inplace=True)
        all_data['year'] = all_data['year'].astype(int)
        all_data = all_data.set_index('year')

        # Assuming 'region_name' or any other non-numeric columns are not required for the mean calculation
        # Adjust the column names as per your DataFrame structure
        all_data = all_data.drop(columns='region_name')

        filtered_df = all_data.loc[start_year:end_year]
        year_avg = filtered_df.groupby('year').mean()
        year_avg['region_name'] = 'Mean'
        year_avg = year_avg.reset_index()
        year_avg.set_index(['year', 'region_name'], inplace=True)

        print(year_avg)
        
        # 계층 이동 가능성 df
        social_items = list(social_mobility_collection.find({'구분별(2)':{'$in' : [region1, region2]}}, {"_id": 0, 'id':0, '10점 평균 (점)' : 0}))
        df = pd.DataFrame(social_items)
        df.rename(columns={'시점':'year','구분별(2)':'region_name'}, inplace=True)
        df['year'] = df['year'].astype(int)
        df = df.set_index(['year', 'region_name'])
        df = df.loc[start_year:end_year]
        print(df)
        
        index_tuples = []
        # region1에 대한 튜플 추가
        def create_index_tuples(region1, region2, start_year, end_year):
            index_tuples = []
            # region1에 대한 튜플 추가
            for year in range(start_year, end_year + 1):
                index_tuples.append((region1, year))
            
            # mean에 대한 튜플 추가
            for year in range(start_year, end_year + 1):
                index_tuples.append(('Mean', year))
            
            # region2에 대한 튜플 추가
            for year in range(start_year, end_year + 1):
                index_tuples.append((region2, year))
            
            return index_tuples
        
        index_tuples = create_index_tuples(region1, region2, start_year, end_year)    
        print(index_tuples)
        df_ = pd.concat([year_avg, df])
        print(df_)
        df_index = pd.MultiIndex.from_tuples(index_tuples, names=['location', 'year'])
        df_ = df_.set_index(df_index)
        locations = df_.index.get_level_values('location').unique()
        df_.plot(kind='barh', stacked=True)
        plt.legend(bbox_to_anchor=(1,1))
        last_indices = []
        # 밑에는 다 선긋기 위한 로직
        for location in locations:
            last_index = df_.loc[location].index[-1] 
            overall_index = df_.index.tolist().index((location, last_index)) 
            last_indices.append(overall_index)
        for idx in last_indices:
            plt.axhline(y=idx + 0.5, color='k', linestyle='--', linewidth=2)
        plt.title(f'{region1}vs{region2}')
        plt.legend(bbox_to_anchor=(1,1))
        plt.xticks(rotation=45)
        plt.legend(bbox_to_anchor=(1, 1))
        
        file_path = f'./img/{name}.png'
        plt.tight_layout()
        plt.savefig(file_path, dpi=400, bbox_inches='tight')
        graph = social_graph(image_url=file_path, name=name)
        session.add(graph)
        session.commit()
        return FileResponse(file_path)

