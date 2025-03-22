import requests
import os
import re
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime, timedelta
import json
from image_storage import ImageBed
import urllib.parse
import time
import schedule
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from ua_pool import UAPool
from rate_limiter import RateLimiter

class BlogCrawler:
    """博客爬虫类"""
    
    def __init__(self, config: Dict):
        """
        初始化爬虫
        
        Args:
            config (Dict): 配置字典，包含所有配置项
        """
        # 基础URL
        self.base_url = "https://api.cuiliangblog.cn/v1/blog"
        
        # UA池配置
        self.ua_pool = UAPool()
        self.ua_change_interval = config['ua_pool']['change_interval']
        self.request_count = 0
        self.ua_lock = threading.Lock()
        
        # 加载UA文件
        ua_file = os.path.abspath(config['ua_pool']['file'])
        if not os.path.exists(ua_file):
            raise FileNotFoundError(f"UA文件不存在: {ua_file}")
        self.ua_pool.load_ua_file(ua_file)
        
        # 基础请求头
        self.base_headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'origin': 'https://www.cuiliangblog.cn',
            'referer': 'https://www.cuiliangblog.cn/'
        }
        
        # 线程池配置
        self.executor = ThreadPoolExecutor(max_workers=config['thread_pool']['max_workers'])
        
        # 限速器配置
        self.rate_limiter = RateLimiter(
            config['rate_limit']['requests_per_minute'],
            config['rate_limit']['window']
        )
        
        # 存储路径配置
        self.base_dir = os.path.abspath(config['storage']['path'])
        self.temp_dir = os.path.join(self.base_dir, "temp")
        self.markdown_dir = os.path.join(self.base_dir, "markdown")
        self.message_file = os.path.join(self.base_dir, "message.json")
        
        # 创建必要的目录
        for directory in [self.base_dir, self.temp_dir, self.markdown_dir]:
            os.makedirs(directory, exist_ok=True)
        
        # 初始化或加载消息文件
        self._init_message_file()
        
        # 监控配置
        self.check_interval = config['monitor']['interval']
        
        # 图床配置
        self.image_bed = ImageBed(config['auth']['token'])

    def _init_message_file(self):
        """初始化或加载消息文件"""
        if os.path.exists(self.message_file):
            with open(self.message_file, 'r', encoding='utf-8') as f:
                self.message_data = json.load(f)
        else:
            self.message_data = {
                "last_update": "",
                "articles": {}  # 使用字典存储所有文章，key为文章ID
            }
            self._save_message_data()

    def _save_message_data(self):
        """保存消息数据到文件"""
        self.message_data["last_update"] = datetime.now().isoformat()
        with open(self.message_file, 'w', encoding='utf-8') as f:
            json.dump(self.message_data, f, ensure_ascii=False, indent=2)

    def _get_all_articles(self) -> List[Dict]:
        """
        获取所有文章和笔记的基本信息
        
        Returns:
            List[Dict]: 所有文章和笔记的列表
        """
        print("开始获取文章列表...")
        monthly_stats = self.get_monthly_stats()
        all_articles = []
        
        if not monthly_stats:
            print("没有找到任何文章记录")
            return all_articles
            
        print(f"找到 {len(monthly_stats)} 个月份的文章记录")
        
        for month in monthly_stats.keys():
            try:
                month_articles = self.get_monthly_content(month)
                article_count = len(month_articles)
                all_articles.extend(month_articles)
                print(f"获取 {month} 的文章列表成功，共 {article_count} 篇")
            except Exception as e:
                print(f"获取 {month} 的文章列表失败: {str(e)}")
        
        total_count = len(all_articles)
        print(f"文章列表获取完成，共计 {total_count} 篇")
        return all_articles

    def _get_downloaded_ids(self) -> Set[int]:
        """
        获取已下载的文章ID集合
        
        Returns:
            Set[int]: 已下载的文章ID集合
        """
        return {int(article_id) for article_id in self.message_data["articles"].keys()}

    def _update_article_meta(self, content: Dict):
        """
        更新文章元信息
        
        Args:
            content (Dict): 文章详细信息
        """
        # 移除body内容，保存其他元信息
        article_meta = content.copy()
        article_meta.pop('body', None)
        
        self.message_data["articles"][str(content['id'])] = article_meta
        self._save_message_data()

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头（带UA轮换）"""
        with self.ua_lock:
            self.request_count += 1
            if self.request_count % self.ua_change_interval == 0:
                new_ua = self.ua_pool.get_next_ua()
            else:
                new_ua = self.ua_pool.get_random_ua()
        
        headers = self.base_headers.copy()
        headers['user-agent'] = new_ua
        return headers

    def _make_request(self, url: str, method: str = 'GET', need_rate_limit: bool = False, **kwargs) -> requests.Response:
        """
        发送请求（带限速）
        
        Args:
            url (str): 请求URL
            method (str): 请求方法
            need_rate_limit (bool): 是否需要限速
            **kwargs: 请求参数
        
        Returns:
            requests.Response: 响应对象
        """
        try:
            # 仅在需要时等待限速器
            if need_rate_limit:
                self.rate_limiter.wait()
            
            # 更新请求头
            kwargs['headers'] = self._get_headers()
            
            # 发送请求
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            print(f"请求失败: {str(e)}")
            raise

    def crawl_incremental(self, force_download: bool = False) -> List[str]:
        """增量下载文章内容（多线程版本）"""
        # 获取所有文章列表
        all_articles = self._get_all_articles()
        print(f"获取到总文章数: {len(all_articles)}")
        
        # 获取已下载的文章ID
        downloaded_ids = set() if force_download else self._get_downloaded_ids()
        print(f"已下载文章数: {len(downloaded_ids)}")
        
        # 找出需要下载的文章
        to_download = [
            article for article in all_articles 
            if article['id'] not in downloaded_ids
        ]
        print(f"需要下载文章数: {len(to_download)}")
        
        saved_files = []
        futures = []
        
        # 提交下载任务到线程池
        for article in to_download:
            future = self.executor.submit(
                self._download_single_article,
                article['id'],
                article['type']
            )
            futures.append(future)
        
        # 等待所有任务完成
        for future in as_completed(futures):
            try:
                filepath = future.result()
                if filepath:
                    saved_files.append(filepath)
                    print(f"已保存: {filepath}")
            except Exception as e:
                print(f"下载文章失败: {str(e)}")
        
        return saved_files

    def _download_single_article(self, article_id: int, article_type: str) -> Optional[str]:
        """
        下载单篇文章
        
        Args:
            article_id (int): 文章ID
            article_type (str): 文章类型
            
        Returns:
            Optional[str]: 保存的文件路径，失败返回None
        """
        try:
            # 获取文章详细内容
            detail = self.get_article_detail(article_id, article_type)
            
            # 更新文章元信息
            self._update_article_meta(detail)
            
            # 保存Markdown内容
            return self.save_markdown(detail)
            
        except Exception as e:
            print(f"处理文章失败 {article_id}: {str(e)}")
            return None

    def save_markdown(self, content: Dict) -> str:
        """
        保存文章内容为Markdown文件
        
        Args:
            content (Dict): 文章内容
            
        Returns:
            str: 保存的文件路径
        """
        # 处理文件名
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', content['title'])
        filename = f"{safe_title}_{content['id']}.md"
        filepath = os.path.join(self.markdown_dir, filename)
        
        # 处理正文中的图片
        processed_body = self._process_markdown_images(content['body'])
        
        # 保存处理后的正文内容
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(processed_body)
        
        return filepath

    def _process_markdown_images(self, content: str) -> str:
        """
        处理Markdown中的图片，下载并上传到图床
        
        Args:
            content (str): Markdown内容
            
        Returns:
            str: 处理后的Markdown内容
        """
        def replace_image(match):
            alt_text = match.group(1)
            image_url = match.group(2)
            
            try:
                # 下载图片
                temp_path = self._download_image(image_url)
                if temp_path:
                    # 上传到图床
                    new_url = self.image_bed.image_upload(temp_path)
                    # 删除临时文件
                    os.remove(temp_path)
                    return f"![{alt_text}]({new_url})"
                return match.group(0)
            except Exception as e:
                print(f"处理图片失败 {image_url}: {str(e)}")
                return match.group(0)
        
        # 匹配Markdown图片语法
        pattern = r"!\[(.*?)\]\((.*?)\)"
        return re.sub(pattern, replace_image, content)

    def _download_image(self, image_url: str) -> Optional[str]:
        """
        下载图片到临时目录
        
        Args:
            image_url (str): 图片URL
            
        Returns:
            Optional[str]: 临时文件路径，下载失败返回None
        """
        try:
            # 解析URL，获取文件名
            parsed_url = urllib.parse.urlparse(image_url)
            filename = os.path.basename(parsed_url.path)
            if not filename:
                filename = f"image_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
            
            temp_path = os.path.join(self.temp_dir, filename)
            
            # 下载图片
            response = self._make_request(image_url, need_rate_limit=True)  # 下载图片时需要限速
            if response.status_code == 200:
                with open(temp_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                return temp_path
            return None
        except Exception as e:
            print(f"下载图片失败 {image_url}: {str(e)}")
            return None

    def get_monthly_stats(self) -> Dict[str, Dict[str, int]]:
        """
        获取每月文章和笔记数量统计
        
        Returns:
            Dict[str, Dict[str, int]]: 按月份统计的文章和笔记数量
            例如: {'2025-03': {'article': 0, 'section': 1}}
        """
        url = f"{self.base_url}/classify/"
        response = self._make_request(url, need_rate_limit=False)
        if response.status_code == 200:
            return response.json()
        raise Exception(f"获取月度统计失败: {response.status_code}")

    def get_monthly_content(self, month: str) -> List[Dict]:
        """
        获取指定月份的文章和笔记列表
        
        Args:
            month (str): 月份，格式为 'YYYY-MM'
            
        Returns:
            List[Dict]: 文章和笔记列表
            例如: [{'type': 'section', 'id': 123, 'title': '标题', 'created_time': '时间'}]
        """
        url = f"{self.base_url}/classify/"
        params = {'month': month}
        response = self._make_request(url, method='GET', params=params, need_rate_limit=False)
        if response.status_code == 200:
            return response.json()
        raise Exception(f"获取月度内容失败: {response.status_code}")

    def get_article_detail(self, article_id: int, content_type: str = 'section') -> Dict:
        """
        获取文章或笔记详细内容
        
        Args:
            article_id (int): 文章或笔记ID
            content_type (str): 内容类型，'section' 或 'article'
            
        Returns:
            Dict: 文章或笔记详细信息
        """
        url = f"{self.base_url}/{content_type}/{article_id}/"
        response = self._make_request(url, need_rate_limit=True)  # 下载文章内容时需要限速
        if response.status_code == 200:
            return response.json()
        raise Exception(f"获取内容详情失败: {response.status_code}")

    def _get_latest_article_info(self) -> Tuple[int, datetime]:
        """
        获取最新文章的ID和更新时间
        
        Returns:
            Tuple[int, datetime]: (最新文章ID, 最新更新时间)
        """
        try:
            all_articles = self._get_all_articles()
            if not all_articles:
                return 0, datetime.min
                
            latest_article = max(all_articles, key=lambda x: x['created_time'])
            latest_time = datetime.fromisoformat(latest_article['created_time'].replace('Z', '+00:00'))
            return latest_article['id'], latest_time
            
        except Exception as e:
            print(f"获取最新文章信息失败: {str(e)}")
            return 0, datetime.min

    def _get_local_latest_info(self) -> Tuple[int, datetime]:
        """
        获取本地记录的最新文章信息
        
        Returns:
            Tuple[int, datetime]: (最新文章ID, 最新更新时间)
        """
        try:
            if not self.message_data["articles"]:
                return 0, datetime.min
                
            latest_local = max(
                self.message_data["articles"].values(),
                key=lambda x: x['created_time']
            )
            latest_time = datetime.fromisoformat(latest_local['created_time'].replace('Z', '+00:00'))
            return latest_local['id'], latest_time
            
        except Exception as e:
            print(f"获取本地最新记录失败: {str(e)}")
            return 0, datetime.min

    def check_updates(self) -> bool:
        """
        检查是否有新文章
        
        Returns:
            bool: 是否有更新
        """
        print("正在检查更新...")
        remote_id, remote_time = self._get_latest_article_info()
        local_id, local_time = self._get_local_latest_info()
        
        has_updates = remote_id > local_id or remote_time > local_time
        
        print("\n检查结果:")
        print(f"远程最新文章: ID={remote_id}, 时间={remote_time}")
        print(f"本地最新文章: ID={local_id}, 时间={local_time}")
        
        if has_updates:
            print("\n>>> 发现新文章！<<<")
        else:
            print("\n>>> 已是最新状态 <<<")
            
        return has_updates

    def set_check_interval(self, seconds: int):
        """
        设置检查间隔时间
        
        Args:
            seconds (int): 间隔秒数
        """
        self.check_interval = seconds

    def watch(self, auto_download: bool = True):
        """
        启动监控服务
        
        Args:
            auto_download (bool): 发现更新时是否自动下载
        """
        def check_and_download():
            try:
                if self.check_updates():
                    if auto_download:
                        print("开始下载新文章...")
                        self.crawl_incremental()
                    else:
                        print("检测到更新，但未启用自动下载")
            except Exception as e:
                print(f"检查更新时发生错误: {str(e)}")

        # 设置定时任务
        schedule.every(self.check_interval).seconds.do(check_and_download)
        
        print(f"监控服务已启动，每 {self.check_interval} 秒检查一次更新...")
        print(f"下次检查时间: {(datetime.now() + timedelta(seconds=self.check_interval)).strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 持续运行定时任务
        while True:
            try:
                schedule.run_pending()
                time.sleep(1)
            except KeyboardInterrupt:
                print("\n监控服务已停止")
                break
            except Exception as e:
                print(f"运行时发生错误: {str(e)}")
                time.sleep(self.check_interval)

    def __del__(self):
        """清理资源"""
        try:
            if hasattr(self, 'executor'):
                self.executor.shutdown(wait=True)
        except Exception as e:
            print(f"清理资源时发生错误: {str(e)}")

