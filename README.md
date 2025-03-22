# 博客文章监控下载工具

这是一个用于监控和下载博客文章的Python工具，支持自动检测更新、图片存储等功能。

## 功能特点

- 自动监控博客文章更新
- 支持图片自动上传到图床
- UA池轮换机制
- 请求限速控制
- 多线程下载支持
- Docker容器化部署
- YAML配置文件支持

## 环境要求

- Python 3.9+
- Docker (可选)
- PyYAML

## 安装说明

### 方式一：直接运行

1. 克隆项目
```bash
git clone [项目地址]
cd blog
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 配置config.yaml
```bash
cp config.yaml.example config.yaml
# 编辑config.yaml设置你的配置
```

4. 运行程序
```bash
python blog_watch.py
```

### 方式二：Docker部署

1. 构建镜像
```bash
docker build -t blog-watch .
```

2. 准备配置文件
```bash
cp config.yaml.example my-config.yaml
# 编辑my-config.yaml设置你的配置
```

3. 运行容器
```bash
docker run -d \
  --name blog-watch \
  -v $(pwd)/my-config.yaml:/app/config.yaml \
  -v $(pwd)/storage:/app/storage \
  -v $(pwd)/ua.txt:/app/ua.txt \
  -e AUTH_TOKEN=your_token \
  -e MONITOR_INTERVAL=1800 \
  blog-watch
```

## 配置说明

### 配置文件 (config.yaml)

```yaml
# 认证配置
auth:
  token: ""  # 图床服务的认证token

# 监控配置
monitor:
  interval: 3600  # 检查间隔时间（秒）
  auto_download: true  # 是否自动下载
  force_download: false  # 是否强制重新下载

# UA池配置
ua_pool:
  file: "ua.txt"  # UA文件路径
  change_interval: 60  # UA更换间隔（请求次数）

# 线程池配置
thread_pool:
  max_workers: 5  # 最大线程数

# 限速配置
rate_limit:
  requests_per_minute: 5  # 每分钟最大请求数
  window: 60  # 限速时间窗口（秒）

# 存储配置
storage:
  path: "/app/storage"  # 存储路径
```

### Docker环境变量

所有配置项都可以通过环境变量覆盖，环境变量优先级高于配置文件：

| 环境变量 | 对应配置项 | 默认值 |
|----------|------------|---------|
| AUTH_TOKEN | auth.token | - |
| MONITOR_INTERVAL | monitor.interval | 3600 |
| AUTO_DOWNLOAD | monitor.auto_download | true |
| FORCE_DOWNLOAD | monitor.force_download | false |
| UA_FILE | ua_pool.file | ua.txt |
| UA_CHANGE_INTERVAL | ua_pool.change_interval | 60 |
| MAX_WORKERS | thread_pool.max_workers | 5 |
| RATE_LIMIT | rate_limit.requests_per_minute | 5 |
| RATE_WINDOW | rate_limit.window | 60 |
| STORAGE_PATH | storage.path | /app/storage |

## 使用示例

### 使用配置文件
```bash
# 直接使用配置文件运行
python blog_watch.py

# 指定配置文件路径
python blog_watch.py --config /path/to/config.yaml
```

### Docker环境变量配置
```bash
docker run -d \
  --name blog-watch \
  -v $(pwd)/storage:/app/storage \
  -e AUTH_TOKEN=your_token \
  -e MONITOR_INTERVAL=1800 \
  -e MAX_WORKERS=10 \
  -e RATE_LIMIT=10 \
  blog-watch
```

## 注意事项

1. 配置优先级：环境变量 > 命令行参数 > 配置文件 > 默认值
2. 建议将敏感信息（如token）通过环境变量传入
3. 建议将配置文件、storage目录和ua.txt文件挂载到容器外
4. 请遵守目标网站的robots.txt规则

## 常见问题

1. 如何修改配置？
   - 直接编辑config.yaml文件
   - 或通过环境变量覆盖配置
   - 或通过命令行参数指定

2. 如何更新UA池？
   - 直接编辑ua.txt文件即可
   - 确保文件已挂载到容器中

3. 如何查看运行日志？
   - 直接运行模式下查看控制台输出
   - Docker模式下使用 `docker logs blog-watch`

4. 如何停止服务？
   - 直接运行模式：Ctrl+C
   - Docker模式：`docker stop blog-watch`

## 许可证

MIT License 