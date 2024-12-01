import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np
import folium
from streamlit_folium import folium_static

# 페이지 설정
st.set_page_config(
    page_title="스포츠강좌 분석 대시보드", page_icon="🏃‍♂️", layout="wide"
)


def create_price_boxplot(filtered_df):
    # 각 종목별로 다른 색상 지정
    colors = px.colors.qualitative.Set3

    fig = px.box(
        filtered_df,
        x="ITEM_NM",
        y="COURSE_PRC",
        color="ITEM_NM",  # 종목별 색상 구분
        color_discrete_sequence=colors,
        labels={"ITEM_NM": "강좌 종목", "COURSE_PRC": "가격 (원)"},
    )

    fig.update_yaxes(title_text="가격 (원)")
    fig.update_layout(xaxis_title="강좌 종목", showlegend=True, legend_title="종목")

    return fig


def create_additional_charts(filtered_df):
    # 가격대별 색상 매핑
    price_colors = {
        "0-5만원": "#1f77b4",
        "5-10만원": "#ff7f0e",
        "10-15만원": "#2ca02c",
        "15-20만원": "#d62728",
        "20만원 이상": "#9467bd",
    }

    # 1. 가격대별 강좌 분포
    price_ranges = pd.cut(
        filtered_df["COURSE_PRC"],
        bins=[0, 50000, 100000, 150000, 200000, float("inf")],
        labels=["0-5만원", "5-10만원", "10-15만원", "15-20만원", "20만원 이상"],
    )

    price_dist = filtered_df.groupby(price_ranges).size().reset_index(name="count")

    fig_price_dist = px.bar(
        price_dist,
        x="COURSE_PRC",
        y="count",
        color="COURSE_PRC",  # 가격대별 색상 구분
        color_discrete_map=price_colors,
        title="가격대별 강좌 분포",
        labels={"COURSE_PRC": "가격대", "count": "강좌 수"},
    )

    # 2. 종목별 평균 수강 인원
    colors = px.colors.qualitative.Set3

    avg_students = (
        filtered_df.groupby("ITEM_NM")["COURSE_REQST_NMPR_CO"].mean().reset_index()
    )
    fig_avg_students = px.bar(
        avg_students,
        x="ITEM_NM",
        y="COURSE_REQST_NMPR_CO",
        color="ITEM_NM",  # 종목별 색상 구분
        color_discrete_sequence=colors,
        title="종목별 평균 수강 인원",
        labels={"ITEM_NM": "종목", "COURSE_REQST_NMPR_CO": "평균 수강 인원"},
    )

    # 레이아웃 업데이트
    fig_price_dist.update_layout(showlegend=True, legend_title="가격대")

    fig_avg_students.update_layout(showlegend=True, legend_title="종목")

    return fig_price_dist, fig_avg_students


def create_location_map(filtered_df):
    # 지역별 중심 좌표 (예시)
    region_coordinates = {
        "서울": {"lat": 37.5665, "lon": 126.9780},
        "경기": {"lat": 37.2636, "lon": 127.0286},
        "인천": {"lat": 37.4563, "lon": 126.7052},
        "강원": {"lat": 37.8813, "lon": 127.7300},
        "충북": {"lat": 36.6357, "lon": 127.4912},
        "충남": {"lat": 36.6588, "lon": 126.6728},
        "대전": {"lat": 36.3504, "lon": 127.3845},
        "세종": {"lat": 36.4808, "lon": 127.2892},
        "전북": {"lat": 35.8468, "lon": 127.1297},
        "전남": {"lat": 34.8161, "lon": 126.4629},
        "광주": {"lat": 35.1595, "lon": 126.8526},
        "경북": {"lat": 36.5764, "lon": 128.5058},
        "경남": {"lat": 35.2382, "lon": 128.6923},
        "대구": {"lat": 35.8714, "lon": 128.6014},
        "울산": {"lat": 35.5384, "lon": 129.3114},
        "부산": {"lat": 35.1796, "lon": 129.0756},
        "제주": {"lat": 33.4996, "lon": 126.5312},
    }

    # 색상 매핑
    color_map = px.colors.qualitative.Set3
    region_colors = {
        region: color_map[i % len(color_map)]
        for i, region in enumerate(region_coordinates.keys())
    }

    # 지도 데이터 준비
    map_data = []
    for idx, row in filtered_df.drop_duplicates(
        ["FCLTY_NM", "CTPRVN_NM", "ITEM_NM"]
    ).iterrows():
        if row["CTPRVN_NM"] in region_coordinates:
            coords = region_coordinates[row["CTPRVN_NM"]]
            map_data.append(
                {
                    "FCLTY_NM": row["FCLTY_NM"],
                    "CTPRVN_NM": row["CTPRVN_NM"],
                    "ITEM_NM": row["ITEM_NM"],
                    "lat": coords["lat"]
                    + np.random.normal(0, 0.02),  # 약간의 랜덤 오프셋 추가
                    "lon": coords["lon"] + np.random.normal(0, 0.02),
                }
            )

    map_df = pd.DataFrame(map_data)

    # Plotly 맵 생성
    fig = go.Figure()

    # 지역별로 마커 추가
    for region in region_coordinates.keys():
        region_data = map_df[map_df["CTPRVN_NM"] == region]
        if not region_data.empty:
            fig.add_trace(
                go.Scattermapbox(
                    lat=region_data["lat"],
                    lon=region_data["lon"],
                    mode="markers",
                    marker=dict(size=10, color=region_colors[region], opacity=0.7),
                    text=[
                        f"시설명: {name}<br>지역: {region}<br>종목: {sport}"
                        for name, sport in zip(
                            region_data["FCLTY_NM"], region_data["ITEM_NM"]
                        )
                    ],
                    hoverinfo="text",
                    name=region,
                )
            )

    # 지도 레이아웃 설정
    fig.update_layout(
        mapbox=dict(style="carto-positron", zoom=6, center=dict(lat=36.5, lon=127.5)),
        showlegend=True,
        legend=dict(title="지역", yanchor="top", y=0.99, xanchor="left", x=0.01),
        margin=dict(l=0, r=0, t=0, b=0),
        height=600,
    )

    return fig


# 데이터 로드 함수
@st.cache_data
def load_data():
    df = pd.read_csv("KS_DSPSN_SVCH_UTILIIZA_CRSTAT_INFO_202410.csv")

    # 날짜 컬럼 변환
    df["COURSE_BEGIN_DE"] = pd.to_datetime(df["COURSE_BEGIN_DE"], format="%Y%m%d")
    df["COURSE_END_DE"] = pd.to_datetime(df["COURSE_END_DE"], format="%Y%m%d")

    return df


def create_region_count_chart(filtered_df):
    colors = px.colors.qualitative.Set3
    region_count = filtered_df.groupby("CTPRVN_NM").size().reset_index(name="강좌 수")
    fig = px.bar(
        region_count,
        x="CTPRVN_NM",
        y="강좌 수",
        labels={"CTPRVN_NM": "지역", "강좌 수": "강좌 수"},
        color="CTPRVN_NM",
        color_discrete_sequence=colors,  # 색상 추가
    )
    fig.update_traces(hovertemplate="강좌 수: %{y}<extra></extra>")
    fig.update_layout(showlegend=True, legend_title="지역")
    return fig


def create_sports_pie_chart(filtered_df):
    colors = px.colors.qualitative.Set3
    sport_count = filtered_df.groupby("ITEM_NM").size().reset_index(name="count")
    fig = px.pie(
        sport_count,
        values="count",
        names="ITEM_NM",
        title="종목별 분포",
        labels={"ITEM_NM": "종목", "count": "강좌 수"},
        color_discrete_sequence=colors,  # 색상 추가
    )
    fig.update_traces(textinfo="label+percent")
    return fig


def create_monthly_trend_chart(filtered_df):
    monthly_trend = (
        filtered_df.groupby(
            [filtered_df["COURSE_BEGIN_DE"].dt.strftime("%Y-%m"), "CTPRVN_NM"]
        )
        .size()
        .reset_index(name="count")
    )

    fig = px.line(
        monthly_trend,
        x="COURSE_BEGIN_DE",
        y="count",
        color="CTPRVN_NM",
        labels={"COURSE_BEGIN_DE": "개설 월", "count": "강좌 수", "CTPRVN_NM": "지역"},
    )

    # x축 한글 날짜 포맷
    fig.update_xaxes(title_text="개설 월")
    return fig


def create_price_boxplot(filtered_df):
    colors = px.colors.qualitative.Set3
    fig = px.box(
        filtered_df,
        x="ITEM_NM",
        y="COURSE_PRC",
        color="ITEM_NM",  # 색상 구분 추가
        color_discrete_sequence=colors,  # 색상 추가
        labels={"ITEM_NM": "강좌", "COURSE_PRC": "가격 (천원)"},
    )

    fig.update_yaxes(title_text="가격 (천원)")
    fig.update_layout(
        xaxis_title="강좌 종목",
        showlegend=True,
        legend_title="종목",
        yaxis=dict(tickformat=",d"),
    )
    return fig


def create_map(filtered_df):
    # 중심 좌표 계산 (예시 좌표)
    center_lat, center_lon = 37.5665, 126.9780

    m = folium.Map(location=[center_lat, center_lon], zoom_start=7)

    # 시설별로 마커 추가
    for idx, row in filtered_df.drop_duplicates("FCLTY_NM").iterrows():
        folium.Marker(
            [37.5665, 126.9780],  # 실제 데이터에서는 각 시설의 좌표를 사용해야 합니다
            popup=f"{row['FCLTY_NM']}<br>종목: {row['ITEM_NM']}<br>가격: {row['COURSE_PRC']:,}원",
        ).add_to(m)

    return m


def create_additional_charts(filtered_df):
    # 가격대별 색상 매핑
    price_colors = {
        "0-5만원": "#1f77b4",
        "5-10만원": "#ff7f0e",
        "10-15만원": "#2ca02c",
        "15-20만원": "#d62728",
        "20만원 이상": "#9467bd",
    }

    # 1. 가격대별 강좌 분포
    price_ranges = pd.cut(
        filtered_df["COURSE_PRC"],
        bins=[0, 50000, 100000, 150000, 200000, float("inf")],
        labels=["0-5만원", "5-10만원", "10-15만원", "15-20만원", "20만원 이상"],
    )

    price_dist = filtered_df.groupby(price_ranges).size().reset_index(name="count")
    fig_price_dist = px.bar(
        price_dist,
        x="COURSE_PRC",
        y="count",
        color="COURSE_PRC",  # 색상 구분 추가
        color_discrete_map=price_colors,  # 색상 매핑 추가
        title="가격대별 강좌 분포",
        labels={"COURSE_PRC": "가격대", "count": "강좌 수"},
    )
    fig_price_dist.update_layout(showlegend=True, legend_title="가격대")

    # 2. 종목별 평균 수강 인원
    colors = px.colors.qualitative.Set3
    avg_students = (
        filtered_df.groupby("ITEM_NM")["COURSE_REQST_NMPR_CO"].mean().reset_index()
    )
    fig_avg_students = px.bar(
        avg_students,
        x="ITEM_NM",
        y="COURSE_REQST_NMPR_CO",
        color="ITEM_NM",  # 색상 구분 추가
        color_discrete_sequence=colors,  # 색상 추가
        title="종목별 평균 수강 인원",
        labels={"ITEM_NM": "종목", "COURSE_REQST_NMPR_CO": "평균 수강 인원"},
    )
    fig_avg_students.update_layout(showlegend=True, legend_title="종목")

    return fig_price_dist, fig_avg_students


def main():
    st.title("🏃‍♂️ 스포츠강좌 분석 대시보드")

    try:
        df = load_data()

        # 사이드바 필터
        st.sidebar.header("필터 옵션")
        selected_region = st.sidebar.multiselect(
            "지역 선택",
            options=sorted(df["CTPRVN_NM"].unique()),
            default=sorted(df["CTPRVN_NM"].unique())[0],
        )

        selected_sports = st.sidebar.multiselect(
            "종목 선택",
            options=sorted(df["ITEM_NM"].unique()),
            default=sorted(df["ITEM_NM"].unique())[0],
        )

        filtered_df = df[
            (df["CTPRVN_NM"].isin(selected_region))
            & (df["ITEM_NM"].isin(selected_sports))
        ]

        # 레이아웃
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("지역별 강좌 수")
            st.plotly_chart(
                create_region_count_chart(filtered_df), use_container_width=True
            )

        with col2:
            st.subheader("종목별 분포")
            st.plotly_chart(
                create_sports_pie_chart(filtered_df), use_container_width=True
            )

        # 월별 트렌드
        st.subheader("월별 강좌 개설 추이")
        st.plotly_chart(
            create_monthly_trend_chart(filtered_df), use_container_width=True
        )

        # 가격 분석
        st.subheader("강좌 가격 분포")
        fig_price = create_price_boxplot(filtered_df)
        st.plotly_chart(fig_price, use_container_width=True)

        # 추가 차트들
        col3, col4 = st.columns(2)
        fig_price_dist, fig_avg_students = create_additional_charts(filtered_df)

        with col3:
            st.plotly_chart(fig_price_dist, use_container_width=True)

        with col4:
            st.plotly_chart(fig_avg_students, use_container_width=True)

        # 지도 생성
        st.subheader("강좌 개설 위치")
        fig = create_location_map(filtered_df)
        st.plotly_chart(fig, use_container_width=True)

        # 통계 정보 표시
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("총 시설 수", len(filtered_df["FCLTY_NM"].unique()))
        with col2:
            st.metric("총 강좌 수", len(filtered_df))
        with col3:
            st.metric("평균 강좌 가격", f"{filtered_df['COURSE_PRC'].mean():,.0f}원")

        # 상세 데이터 테이블
        st.subheader("상세 데이터")
        st.dataframe(
            filtered_df[
                [
                    "FCLTY_NM",
                    "ITEM_NM",
                    "COURSE_NM",
                    "COURSE_BEGIN_DE",
                    "COURSE_END_DE",
                    "COURSE_PRC",
                ]
            ]
        )

    except Exception as e:
        st.error(f"데이터 로드 중 오류가 발생했습니다: {str(e)}")


if __name__ == "__main__":
    main()
