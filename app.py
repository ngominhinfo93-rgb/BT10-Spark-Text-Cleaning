from pathlib import Path
import json

import pandas as pd
import plotly.express as px
import streamlit as st
import matplotlib.pyplot as plt
from wordcloud import WordCloud


# ============================================================
# CẤU HÌNH ỨNG DỤNG
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

st.set_page_config(
    page_title="BT10 - Làm sạch dữ liệu văn bản lớn",
    page_icon="📊",
    layout="wide"
)

st.markdown(
    '''
    <style>
    .block-container {
        padding-top: 1.5rem;
    }
    h1, h2, h3 {
        letter-spacing: -0.02em;
    }
    </style>
    ''',
    unsafe_allow_html=True
)


# ============================================================
# HÀM ĐỌC DỮ LIỆU
# ============================================================

@st.cache_data(show_spinner=False)
def read_csv(filename):
    path = DATA_DIR / filename

    if not path.exists():
        return None

    return pd.read_csv(
        path,
        encoding="utf-8-sig",
        low_memory=False
    )


@st.cache_data(show_spinner=False)
def read_json(filename):
    path = DATA_DIR / filename

    if not path.exists():
        return None

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def fmt_int(value):
    return f"{int(value):,}".replace(",", ".")


def as_bool(series):
    return (
        series.fillna(False)
        .astype(str)
        .str.lower()
        .isin(["true", "1", "yes"])
    )


# ============================================================
# ĐỌC DỮ LIỆU
# ============================================================

reviews = read_csv("reviews_clean.csv")
keywords = read_csv("keyword_frequency.csv")
category_keywords = read_csv("keyword_by_category.csv")
metrics = read_json("data_quality_metrics.json")
benchmark = read_json("udf_benchmark_50000.json")

st.title("Phân tích và làm sạch dữ liệu đánh giá Tiki")

st.caption(
    "BT10 | Apache Spark - Python UDF - Pandas UDF - Streamlit"
)

if reviews is None:
    st.error("Không tìm thấy data/reviews_clean.csv")
    st.stop()

if reviews.empty:
    st.warning("Tệp dữ liệu đánh giá đang rỗng.")
    st.stop()


# ============================================================
# BỘ LỌC SIDEBAR
# ============================================================

st.sidebar.header("Bộ lọc dữ liệu")

filtered = reviews.copy()

product_col = None

if "product_name_clean" in filtered.columns:
    product_col = "product_name_clean"
elif "product_name" in filtered.columns:
    product_col = "product_name"

if product_col:
    product_values = sorted(
        filtered[product_col]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    selected_products = st.sidebar.multiselect(
        "Chọn sản phẩm",
        options=product_values,
        default=[],
        help="Để trống để xem tất cả sản phẩm"
    )

    if selected_products:
        filtered = filtered[
            filtered[product_col]
            .astype(str)
            .isin(selected_products)
        ]

if "rating" in filtered.columns:
    filtered["rating"] = pd.to_numeric(
        filtered["rating"],
        errors="coerce"
    )

    rating_options = sorted(
        filtered["rating"]
        .dropna()
        .unique()
        .tolist()
    )

    selected_ratings = st.sidebar.multiselect(
        "Số sao",
        options=rating_options,
        default=[]
    )

    if selected_ratings:
        filtered = filtered[
            filtered["rating"].isin(selected_ratings)
        ]

if "spam_candidate" in filtered.columns:
    spam_mode = st.sidebar.selectbox(
        "Trạng thái nghi vấn spam",
        [
            "Tất cả",
            "Có dấu hiệu nghi vấn",
            "Không bị gắn cờ"
        ]
    )

    spam_flag = as_bool(
        filtered["spam_candidate"]
    )

    if spam_mode == "Có dấu hiệu nghi vấn":
        filtered = filtered[spam_flag]
    elif spam_mode == "Không bị gắn cờ":
        filtered = filtered[~spam_flag]

if "review_date" in filtered.columns:
    filtered["review_date_parsed"] = pd.to_datetime(
        filtered["review_date"],
        errors="coerce"
    )

    valid_dates = (
        filtered["review_date_parsed"]
        .dropna()
    )

    if not valid_dates.empty:
        min_date = valid_dates.min().date()
        max_date = valid_dates.max().date()

        selected_dates = st.sidebar.date_input(
            "Khoảng thời gian",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )

        if len(selected_dates) == 2:
            start_date, end_date = selected_dates

            filtered = filtered[
                filtered["review_date_parsed"]
                .dt.date
                .between(start_date, end_date)
            ]

st.sidebar.caption(
    "Bộ lọc áp dụng cho bảng đánh giá "
    "và các thống kê tính trực tiếp từ bảng."
)


# ============================================================
# TẠO 6 TAB
# ============================================================

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Tổng quan",
    "Trước / sau chuẩn hóa",
    "Từ khóa và Word Cloud",
    "Nghi vấn spam",
    "Hiệu năng UDF",
    "Dữ liệu đánh giá"
])


# ============================================================
# TAB 1 - TỔNG QUAN
# ============================================================

with tab1:
    st.subheader("Tổng quan dữ liệu")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Tổng đánh giá",
        fmt_int(len(reviews))
    )

    c2.metric(
        "Đánh giá sau lọc",
        fmt_int(len(filtered))
    )

    if "spam_candidate" in filtered.columns:
        spam_count = int(
            as_bool(
                filtered["spam_candidate"]
            ).sum()
        )

        c3.metric(
            "Nghi vấn spam",
            fmt_int(spam_count)
        )
    else:
        c3.metric("Nghi vấn spam", "N/A")

    if "product_id" in filtered.columns:
        c4.metric(
            "Số sản phẩm",
            fmt_int(
                filtered["product_id"].nunique()
            )
        )
    else:
        c4.metric("Số sản phẩm", "N/A")

    st.info(
        "Dữ liệu dashboard đã qua lọc và loại trùng. "
        "Đây không phải toàn bộ dữ liệu gốc."
    )

    if metrics:
        st.subheader("Chỉ số chất lượng dữ liệu")

        st.caption(
            "Các chỉ số dưới đây được tính tại Bước 37 "
            "trên toàn bộ dữ liệu, không thay đổi theo bộ lọc."
        )

        metric_names = {
            "raw_deduplicated_rows":
                "Dòng sau loại trùng",
            "clean_stage1_rows":
                "Dòng sau chuẩn hóa",
            "raw_missing_text":
                "Văn bản thiếu trước chuẩn hóa",
            "clean_missing_text":
                "Văn bản thiếu sau chuẩn hóa",
            "spam_short_count":
                "Đánh giá ngắn",
            "spam_url_count":
                "Đánh giá chứa URL",
            "spam_candidate_count":
                "Nghi vấn spam"
        }

        metric_rows = [
            {
                "Chỉ số": label,
                "Giá trị": metrics.get(key)
            }
            for key, label in metric_names.items()
        ]

        st.dataframe(
            pd.DataFrame(metric_rows),
            use_container_width=True,
            hide_index=True
        )

    if "rating" in filtered.columns and not filtered.empty:
        rating_counts = (
            filtered["rating"]
            .value_counts()
            .sort_index()
            .reset_index()
        )

        rating_counts.columns = [
            "Số sao",
            "Số đánh giá"
        ]

        fig = px.bar(
            rating_counts,
            x="Số sao",
            y="Số đánh giá",
            title="Phân bố số sao"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


# ============================================================
# TAB 2 - TRƯỚC VÀ SAU CHUẨN HÓA
# ============================================================

with tab2:
    st.subheader("So sánh trước và sau chuẩn hóa")

    columns = [
        c for c in [
            "product_name",
            "product_name_clean",
            "review_text",
            "review_text_clean"
        ]
        if c in filtered.columns
    ]

    if columns:
        st.dataframe(
            filtered[columns].head(200),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.warning(
            "Chưa có cột văn bản để so sánh."
        )

    st.caption(
        "Bảng hiển thị tối đa 200 dòng "
        "theo bộ lọc hiện tại."
    )


# ============================================================
# TAB 3 - TỪ KHÓA VÀ WORD CLOUD
# ============================================================

with tab3:
    st.subheader("Phân tích từ khóa")

    if (
        keywords is not None
        and {"token", "count"}.issubset(keywords.columns)
    ):
        st.caption(
            "Thống kê từ khóa được tính trước bằng Spark "
            "trên toàn bộ dữ liệu ở Bước 32; "
            "không thay đổi theo bộ lọc hiện tại."
        )

        top_n = st.slider(
            "Số từ khóa hiển thị",
            min_value=10,
            max_value=50,
            value=20
        )

        top_words = (
            keywords
            .sort_values(
                "count",
                ascending=False
            )
            .head(top_n)
        )

        fig = px.bar(
            top_words.sort_values("count"),
            x="count",
            y="token",
            orientation="h",
            title=f"Top {top_n} từ khóa"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        frequencies = {
            str(row["token"]): float(row["count"])
            for _, row in keywords.iterrows()
            if pd.notna(row["token"])
            and pd.notna(row["count"])
            and float(row["count"]) > 0
        }

        if frequencies:
            try:
                cloud = WordCloud(
                    width=1200,
                    height=500,
                    background_color="white",
                    collocations=False
                ).generate_from_frequencies(
                    frequencies
                )

                fig_wc, ax = plt.subplots(
                    figsize=(12, 5)
                )

                ax.imshow(
                    cloud,
                    interpolation="bilinear"
                )

                ax.axis("off")

                st.pyplot(fig_wc)
                plt.close(fig_wc)

            except Exception as exc:
                st.warning(
                    f"Không thể hiển thị Word Cloud: {exc}"
                )

    else:
        st.warning(
            "Chưa có dữ liệu thống kê từ khóa."
        )

    if (
        category_keywords is not None
        and {
            "category",
            "token",
            "count"
        }.issubset(category_keywords.columns)
    ):
        st.subheader("Từ khóa theo danh mục")

        categories = sorted(
            category_keywords["category"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        if categories:
            selected_category = st.selectbox(
                "Chọn danh mục",
                categories
            )

            subset = category_keywords[
                category_keywords["category"]
                .astype(str)
                == selected_category
            ]

            subset = (
                subset
                .sort_values(
                    "count",
                    ascending=False
                )
                .head(20)
            )

            fig = px.bar(
                subset.sort_values("count"),
                x="count",
                y="token",
                orientation="h",
                title=(
                    "Từ khóa theo danh mục: "
                    + selected_category
                )
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )
    else:
        st.info(
            "Chưa có dữ liệu danh mục được xác minh."
        )


# ============================================================
# TAB 4 - NGHI VẤN SPAM
# ============================================================

with tab4:
    st.subheader("Phân tích dấu hiệu spam")

    spam_columns = [
        c for c in [
            "spam_short",
            "spam_url",
            "spam_candidate"
        ]
        if c in filtered.columns
    ]

    if spam_columns:
        spam_counts = pd.DataFrame([
            {
                "Dấu hiệu": c,
                "Số đánh giá": int(
                    as_bool(filtered[c]).sum()
                )
            }
            for c in spam_columns
        ])

        fig = px.bar(
            spam_counts,
            x="Dấu hiệu",
            y="Số đánh giá",
            title="Thống kê dấu hiệu spam"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        if "spam_candidate" in filtered.columns:
            suspects = filtered[
                as_bool(
                    filtered["spam_candidate"]
                )
            ]

            display_cols = [
                c for c in [
                    "product_name_clean",
                    "review_text_clean",
                    "spam_short",
                    "spam_url",
                    "spam_candidate"
                ]
                if c in suspects.columns
            ]

            st.dataframe(
                suspects[display_cols].head(200),
                use_container_width=True,
                hide_index=True
            )

        st.caption(
            "Các cờ spam là kết quả phát hiện sơ bộ. "
            "Phân tích tương đồng chưa bao phủ "
            "toàn bộ các cặp đánh giá."
        )
    else:
        st.warning(
            "Chưa có dữ liệu đánh dấu spam."
        )


# ============================================================
# TAB 5 - HIỆU NĂNG UDF
# ============================================================

with tab5:
    st.subheader(
        "So sánh Python UDF và Pandas UDF"
    )

    if benchmark:
        python_data = benchmark.get(
            "python_udf",
            {}
        )

        pandas_data = benchmark.get(
            "pandas_udf",
            {}
        )

        if (
            isinstance(python_data, dict)
            and isinstance(pandas_data, dict)
        ):
            python_seconds = python_data.get(
                "seconds"
            )

            pandas_seconds = pandas_data.get(
                "seconds"
            )

            if (
                python_seconds is not None
                and pandas_seconds is not None
            ):
                bench_df = pd.DataFrame([
                    {
                        "Phương pháp": "Python UDF",
                        "Thời gian (giây)":
                            python_seconds
                    },
                    {
                        "Phương pháp": "Pandas UDF",
                        "Thời gian (giây)":
                            pandas_seconds
                    }
                ])

                fig = px.bar(
                    bench_df,
                    x="Phương pháp",
                    y="Thời gian (giây)",
                    text="Thời gian (giây)",
                    title="So sánh thời gian thực nghiệm"
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

                ratio = benchmark.get(
                    "speedup_python_over_pandas"
                )

                if ratio is not None:
                    st.metric(
                        "Tỷ số Python / Pandas",
                        f"{ratio:.3f} lần"
                    )

        st.caption(
            "Quy mô: "
            f"{benchmark.get('benchmark_rows', 'N/A')} "
            "dòng. "
            "Số lượt mỗi phương pháp: "
            f"{benchmark.get('runs_per_method', 'N/A')}."
        )

        st.warning(
            "Đây là thực nghiệm sơ bộ 50.000 dòng, "
            "không phải kết quả 1 triệu dòng."
        )

        with st.expander(
            "Xem cấu hình và kết quả thực nghiệm"
        ):
            st.json(benchmark)

    else:
        st.warning(
            "Chưa có dữ liệu benchmark Bước 36."
        )


# ============================================================
# TAB 6 - BẢNG DỮ LIỆU
# ============================================================

with tab6:
    st.subheader("Dữ liệu đánh giá")

    st.write(
        "Số dòng sau bộ lọc:",
        fmt_int(len(filtered))
    )

    display_df = filtered.drop(
        columns=["review_date_parsed"],
        errors="ignore"
    )

    st.dataframe(
        display_df.head(1000),
        use_container_width=True,
        hide_index=True
    )

    csv_bytes = (
        display_df
        .to_csv(index=False)
        .encode("utf-8-sig")
    )

    st.download_button(
        label="Tải dữ liệu đã lọc (CSV)",
        data=csv_bytes,
        file_name="bt10_reviews_filtered.csv",
        mime="text/csv"
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "BT10 - Dashboard hoạt động độc lập với Colab. "
    "Không chạy Spark trên Streamlit Cloud."
)
