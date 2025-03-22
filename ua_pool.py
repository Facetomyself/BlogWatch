import random
from typing import List

class UAPool:
    """User-Agent池"""
    
    def __init__(self, ua_file: str = "ua.tet"):
        """
        初始化UA池
        
        Args:
            ua_file (str): UA文件路径
        """
        self.ua_list: List[str] = []
        self.current_index = 0
        self.load_ua_file(ua_file)
        
    def load_ua_file(self, ua_file: str):
        """加载UA文件"""
        try:
            with open(ua_file, 'r', encoding='utf-8') as f:
                self.ua_list = [line.strip() for line in f if line.strip()]
            if not self.ua_list:
                raise ValueError("UA文件为空")
        except Exception as e:
            print(f"加载UA文件失败: {str(e)}")
            # 使用默认UA
            self.ua_list = ["Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"]
    
    def get_random_ua(self) -> str:
        """随机获取一个UA"""
        return random.choice(self.ua_list)
    
    def get_next_ua(self) -> str:
        """顺序获取下一个UA"""
        ua = self.ua_list[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.ua_list)
        return ua 