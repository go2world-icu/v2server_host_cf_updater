# 1. 选择Python基础镜像
FROM python:3.12-alpine3.22

# 2. 设置工作目录
WORKDIR /opt

# 3. 复制项目依赖文件到工作目录
# 建议先复制requirements.txt以便利用Docker的缓存层
#COPY requirements.txt .
# 5. 将整个项目复制到工作目录
COPY . .
# 4. 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 6. 暴露应用程序的端口
# 假设你的Python应用监听端口是8000
EXPOSE 5000

# 7. 定义容器启动时要执行的命令
# 假设你的应用入口文件是main.py
CMD ["python", "app/main.py"]