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

## 目录结构

```plaintext
project_root/
├── config/
│   ├── config.yaml        # 实际配置文件
│   └── config.yaml.example # 配置文件示例
├── ua/
│   └── ua.tet            # UA文件
├── storage/              # 存储目录
│   ├── markdown/         # Markdown文件存储
│   └── temp/            # 临时文件目录
├── blog_watch.py        # 主程序
├── blog_crawler.py      # 爬虫核心
├── requirements.txt     # 依赖列表
├── Dockerfile          # Docker构建文件
└── README.md          # 说明文档
```

## 安装说明

### 方式一：直接运行

1. 克隆项目
```bash
git clone https://github.com/Facetomyself/BlogWatch.git
cd blog
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 配置config.yaml
```bash
cp config/config.yaml.example config/config.yaml
# 编辑config.yaml设置你的配置
```

4. 运行程序
```bash
python blog_watch.py
```

### 方式二：Docker部署

1. 准备目录结构：
```bash
mkdir -p config ua storage
cp config.yaml.example config/config.yaml
# 编辑 config/config.yaml 设置你的配置
# 将UA文件复制到 ua/ua.tet
```

2. 构建镜像
```bash
docker build -t blog-watch .
```

3. 运行容器
```bash
docker run -d \
  --name blog-watch \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/storage:/app/storage \
  -v $(pwd)/ua:/app/ua \
  blog-watch
```

## 配置说明

### 配置文件 (config/config.yaml)

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
  file: "./ua/ua.tet"  # UA文件路径（使用相对路径）
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
  path: "./storage"  # 存储路径（使用相对路径）
```

### 环境变量配置

所有配置项都可以通过环境变量覆盖，环境变量优先级高于配置文件：

| 环境变量 | 对应配置项 | 默认值 |
|----------|------------|---------|
| AUTH_TOKEN | auth.token | - |
| MONITOR_INTERVAL | monitor.interval | 3600 |
| AUTO_DOWNLOAD | monitor.auto_download | true |
| FORCE_DOWNLOAD | monitor.force_download | false |
| UA_FILE | ua_pool.file | /app/ua/ua.tet |
| UA_CHANGE_INTERVAL | ua_pool.change_interval | 60 |
| MAX_WORKERS | thread_pool.max_workers | 5 |
| RATE_LIMIT | rate_limit.requests_per_minute | 5 |
| RATE_WINDOW | rate_limit.window | 60 |
| STORAGE_PATH | storage.path | /app/storage |

## 使用示例

### 使用配置文件
```bash
# 直接使用默认配置文件运行
python blog_watch.py

# 指定配置文件路径
python blog_watch.py --config /path/to/config.yaml
```

### 使用环境变量
```bash
# 设置环境变量
export AUTH_TOKEN="your-token"
export MONITOR_INTERVAL=1800
python blog_watch.py
```

## 注意事项

1. 配置文件现在位于 `config` 目录下
2. UA文件应命名为 `ua.tet` 并放置在 `ua` 目录下
3. 所有路径配置都使用相对路径，相对于项目根目录
4. Docker部署时需要正确挂载三个目录：
   - `config`: 配置文件目录
   - `storage`: 存储目录
   - `ua`: UA文件目录

## 常见问题

1. 如何修改配置？
   - 编辑 config/config.yaml 文件
   - 通过环境变量覆盖配置
   - 通过命令行参数指定配置文件

2. 如何查看运行日志？
   - 直接运行模式下查看控制台输出
   - Docker模式下使用 `docker logs blog-watch`

3. 如何停止服务？
   - 直接运行模式：Ctrl+C
   - Docker模式：`docker stop blog-watch`

## 许可证

MIT License 