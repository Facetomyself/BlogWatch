import time
from threading import Lock
from collections import deque
from typing import Deque, Optional

class RateLimiter:
    """请求限速器"""
    
    def __init__(self, max_requests: int, time_window: int):
        """
        初始化限速器
        
        Args:
            max_requests (int): 时间窗口内最大请求数
            time_window (int): 时间窗口大小（秒）
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: Deque[float] = deque()
        self.lock = Lock()
    
    def wait(self) -> float:
        """
        等待直到可以发送请求
        
        Returns:
            float: 等待时间（秒）
        """
        with self.lock:
            now = time.time()
            
            # 移除时间窗口外的请求记录
            while self.requests and now - self.requests[0] >= self.time_window:
                self.requests.popleft()
            
            if len(self.requests) >= self.max_requests:
                # 计算需要等待的时间
                wait_time = self.time_window - (now - self.requests[0])
                if wait_time > 0:
                    time.sleep(wait_time)
                    now = time.time()
            
            self.requests.append(now)
            return now 