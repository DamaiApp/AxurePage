## 使用 Python 3.9 作為基底映像
#FROM python:3.9
#
## 設定工作目錄
#WORKDIR /app
#
## 安裝 Flask, GitPython, shortuuid
#RUN pip install flask werkzeug gitpython shortuuid requests
#
## 安裝 Git
#RUN apt-get update && apt-get install -y git
#
## 複製 Flask 程式碼到容器
#COPY app.py /app/app.py
#
## 開放 Flask API 端口
#EXPOSE 5000
#
## 運行 Flask
#CMD ["python", "app.py"]

#======上方為local測試用，下方為GCP用======

# 使用官方 Python 3.9 作為基礎映像
FROM python:3.9

# 設定工作目錄
WORKDIR /app

# 複製應用程式
COPY . /app

# 安裝 Flask 及必要套件
RUN pip install flask werkzeug gitpython shortuuid requests

# 安裝 Git（Cloud Run 容器預設沒有）
RUN apt-get update && apt-get install -y git

# 設定 Flask 運行埠號（Cloud Run 預設使用 8080）
ENV PORT=8080

# 執行 Flask 應用
CMD ["python", "app.py"]