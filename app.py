import streamlit as st
import pandas as pd
from kiwipiepy import Kiwi
from collections import Counter
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import platform

# 1. Kiwi 형태소 분석기 초기화 및 캐싱 (반복 로딩 방지)
@st.cache_resource
def load_kiwi():
    return Kiwi()

kiwi = load_kiwi()

# 2. 데이터 로드 및 캐싱
@st.cache_data
def load_data():
    # 실제 환경에서는 'news_data.csv' 파일이 파이썬 스크립트와 동일한 경로에 있어야 합니다.
    try:
        df = pd.read_csv('news_data.csv')
        return df
    except FileNotFoundError:
        st.error("news_data.csv 파일을 찾을 수 없습니다.")
        return pd.DataFrame()

# 3. 텍스트 전처리 함수 (명사만 추출)
def extract_nouns(text):
    if not isinstance(text, str):
        return []
    
    tokens = kiwi.tokenize(text)
    # NNG(일반명사), NNP(고유명사)만 추출하고 1글자 단어는 노이즈 방지를 위해 제외
    nouns = [t.form for t in tokens if t.tag in ('NNG', 'NNP') and len(t.form) > 1]
    return nouns

# ==========================================
# Streamlit UI 구성 및 실행 영역
# ==========================================

st.title("📰 뉴스 키워드 분석 애플리케이션")

# 데이터 불러오기
df = load_data()

if not df.empty:
    # 데이터에 'query'과 'title' 컬럼이 존재한다고 가정합니다.
    if '주제' in df.columns and '콘텐츠' in df.columns:
        df = df.rename(columns={'주제': 'query', '콘텐츠': 'title'})
        st.error("CSV 파일에 'query' 및 'title' 컬럼이 필요합니다. 파일 구조를 확인해 주세요.")
    else:
        # 1) 드롭다운으로 주제 선택
        query_list = df['query'].dropna().unique().tolist()
        selected_query = st.selectbox("분석할 뉴스 주제를 선택하세요:", query_list)

        st.write(f"선택된 주제: **{selected_query}**")

        # 선택된 주제의 데이터 필터링
        filtered_df = df[df['query'] == selected_query]
        
        with st.spinner('키워드를 분석 중입니다... (데이터 크기에 따라 시간이 소요될 수 있습니다)'):
            # 전체 텍스트 병합 및 형태소 분석
            all_text = " ".join(filtered_df['title'].dropna().tolist())
            nouns_list = extract_nouns(all_text)
            
            if not nouns_list:
                st.warning("추출된 키워드가 없습니다.")
            else:
                # 단어 빈도수 계산
                word_counts = Counter(nouns_list)
                top_10_words = word_counts.most_common(10)
                top_10_df = pd.DataFrame(top_10_words, columns=['키워드', '빈도수'])

                # 2) 키워드 TOP 10 테이블 표시
                st.subheader("🏆 TOP 10 키워드")
                # 인덱스(1~10)를 깔끔하게 표시하기 위해 인덱스를 1부터 시작하도록 조정
                top_10_df.index = top_10_df.index + 1
                st.table(top_10_df)

                # 3) 키워드 워드클라우드 표시
                st.subheader("☁️ 키워드 워드클라우드")
                
                # 한글 폰트 설정 (OS 환경에 따라 폰트 경로 자동 분기)
                font_path = ''
                system_name = platform.system()
                if system_name == 'Windows':
                    font_path = 'c:/Windows/Fonts/malgun.ttf'
                elif system_name == 'Darwin': # Mac OS
                    font_path = '/Library/Fonts/AppleGothic.ttf'
                else: # Linux 환경 (예: 클라우드 서버)
                    font_path = '/usr/share/fonts/truetype/nanum/NanumGothic.ttf'

                try:
                    # 워드클라우드 객체 생성
                    wc = WordCloud(
                        font_path=font_path,
                        width=800,
                        height=400,
                        background_color='white',
                        colormap='viridis'
                    ).generate_from_frequencies(word_counts)

                    # Matplotlib을 사용하여 Streamlit 화면에 출력
                    fig, ax = plt.subplots(figsize=(10, 5))
                    ax.imshow(wc, interpolation='bilinear')
                    ax.axis('off')
                    st.pyplot(fig)
                except ValueError:
                    st.error(f"지정된 경로({font_path})에서 한글 폰트를 찾을 수 없어 워드클라우드를 생성할 수 없습니다. 시스템에 맞는 폰트 경로를 코드로 수정해 주세요.")
                    import os
from wordcloud import WordCloud

# 폰트 파일 경로 설정 (현재 실행 파일과 같은 위치에 있을 경우)
# font_path = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"

# 만약 폰트 파일이 실제 존재하는지 확인하고 싶다면 아래 코드를 추가해보세요.
if not os.path.exists(font_path):
    print(f"경고: {font_path} 파일을 찾을 수 없습니다.")

wc = WordCloud(
    font_path=font_path,  # 이 부분이 핵심입니다.
    width=800,
    height=400,
    background_color='white'
).generate_from_frequencies(word_counts)