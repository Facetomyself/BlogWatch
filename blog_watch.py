import argparse
import os
import yaml
from blog_crawler import BlogCrawler

def load_config(config_path=None):
    """加载配置文件"""
    # 默认配置
    default_config = {
        'auth': {'token': ''},
        'monitor': {
            'interval': 3600,
            'auto_download': True,
            'force_download': False
        },
        'ua_pool': {
            'file': './ua.tet',
            'change_interval': 60
        },
        'thread_pool': {'max_workers': 5},
        'rate_limit': {
            'requests_per_minute': 5,
            'window': 60
        },
        'storage': {'path': './storage'}
    }
    
    # 首先尝试加载默认的config.yaml
    default_yaml = 'config.yaml'
    if os.path.exists(default_yaml) and not config_path:
        config_path = default_yaml
        print(f"使用默认配置文件: {default_yaml}")
    
    # 如果指定了配置文件路径
    if config_path:
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
            
        print(f"加载配置文件: {config_path}")
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                file_config = yaml.safe_load(f)
                if file_config:
                    # 递归更新配置
                    def update_dict(d, u):
                        for k, v in u.items():
                            if isinstance(v, dict):
                                d[k] = update_dict(d.get(k, {}), v)
                            else:
                                d[k] = v
                        return d
                    default_config = update_dict(default_config, file_config)
                    print("配置文件加载成功")
        except Exception as e:
            print(f"加载配置文件失败: {str(e)}")
            raise
    
    # 环境变量覆盖
    env_mapping = {
        'AUTH_TOKEN': ('auth', 'token'),
        'MONITOR_INTERVAL': ('monitor', 'interval'),
        'AUTO_DOWNLOAD': ('monitor', 'auto_download'),
        'FORCE_DOWNLOAD': ('monitor', 'force_download'),
        'UA_FILE': ('ua_pool', 'file'),
        'UA_CHANGE_INTERVAL': ('ua_pool', 'change_interval'),
        'MAX_WORKERS': ('thread_pool', 'max_workers'),
        'RATE_LIMIT': ('rate_limit', 'requests_per_minute'),
        'RATE_WINDOW': ('rate_limit', 'window'),
        'STORAGE_PATH': ('storage', 'path')
    }
    
    # 记录环境变量覆盖
    env_overrides = []
    for env_key, config_path in env_mapping.items():
        if env_key in os.environ:
            value = os.environ[env_key]
            # 类型转换
            if isinstance(default_config[config_path[0]][config_path[1]], bool):
                value = value.lower() in ('true', '1', 'yes')
            elif isinstance(default_config[config_path[0]][config_path[1]], int):
                value = int(value)
            default_config[config_path[0]][config_path[1]] = value
            env_overrides.append(f"{env_key}={value}")
    
    if env_overrides:
        print("环境变量覆盖:", ", ".join(env_overrides))
    
    # 验证必要的配置项
    if not default_config['auth']['token']:
        raise ValueError("缺少必要的配置项: auth.token")
    
    return default_config

def parse_args():
    parser = argparse.ArgumentParser(description='博客文章监控下载工具')
    parser.add_argument('--config', type=str, help='配置文件路径')
    return parser.parse_args()

def main():
    args = parse_args()
    
    try:
        # 加载配置
        config_path = args.config or os.environ.get('CONFIG_PATH')
        config = load_config(config_path)
        
        print("\n当前配置信息:")
        print(f"- Token: {'*' * 8}{config['auth']['token'][-4:]}")
        print(f"- UA文件: {config['ua_pool']['file']}")
        print(f"- 存储路径: {config['storage']['path']}")
        
        # 创建爬虫实例
        crawler = BlogCrawler(config)
        
        # 首次启动检查
        print("\n执行首次检查...")
        has_updates = crawler.check_updates()
        if has_updates and config['monitor']['auto_download']:
            print("检测到更新，开始下载新文章...")
            crawler.crawl_incremental()
        elif has_updates and not config['monitor']['auto_download']:
            print("检测到更新，但自动下载已禁用")
        else:
            print("首次检查完成，未发现新文章")
        
        if config['monitor']['force_download']:
            print("\n开始强制重新下载所有文章...")
            print(f"配置信息:")
            print(f"- 最大线程数: {config['thread_pool']['max_workers']}")
            print(f"- 限速: {config['rate_limit']['requests_per_minute']}次/{config['rate_limit']['window']}秒")
            print(f"- UA更换间隔: {config['ua_pool']['change_interval']}次请求")
            crawler.crawl_incremental(force_download=True)
            return
            
        print("\n监控服务配置信息:")
        print(f"- 检查间隔: {config['monitor']['interval']}秒")
        print(f"- 自动下载: {'禁用' if not config['monitor']['auto_download'] else '启用'}")
        print(f"- 最大线程数: {config['thread_pool']['max_workers']}")
        print(f"- 限速: {config['rate_limit']['requests_per_minute']}次/{config['rate_limit']['window']}秒")
        print(f"- UA更换间隔: {config['ua_pool']['change_interval']}次请求")
        
        # 启动监控
        crawler.watch(auto_download=config['monitor']['auto_download'])
        
    except Exception as e:
        print(f"\n程序运行失败: {str(e)}")
        raise

if __name__ == "__main__":
    main() 