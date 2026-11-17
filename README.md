# BT10 - Dashboard làm sạch dữ liệu văn bản lớn

## Công nghệ
- Apache Spark / PySpark (xử lý dữ liệu trên Google Colab)
- Python UDF và Pandas UDF
- Streamlit
- Plotly
- WordCloud

## Cấu trúc
- app.py: ứng dụng Streamlit
- requirements.txt: danh sách thư viện
- data/: dữ liệu đã xử lý
- .streamlit/config.toml: cấu hình giao diện

## Chạy ứng dụng

Cài thư viện:

    pip install -r requirements.txt

Chạy:

    streamlit run app.py

## Triển khai lên Streamlit Community Cloud

1. Tạo repository GitHub.
2. Tải nội dung thư mục streamlit_app lên repository.
3. Mở https://share.streamlit.io/
4. Chọn triển khai ứng dụng từ GitHub.
5. Chọn file chính app.py.
6. Kiểm tra giao diện và dữ liệu.

## Lưu ý
- Website không chạy Spark trực tiếp.
- Kết quả spam hiện là kết quả sơ bộ.
- Benchmark 50.000 dòng chưa thay thế benchmark 1 triệu dòng.
- Không tạo dữ liệu danh mục giả khi nguồn thiếu danh mục.
