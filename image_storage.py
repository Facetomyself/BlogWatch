import requests
from typing import Dict, Optional, Union

class ImageBed:
    """图床操作类"""
    
    def __init__(self, token: str, api_url: str = "http://158.178.236.241/api/index.php"):
        """
        初始化图床类
        
        Args:
            token (str): 认证token
            api_url (str): API基础URL
        """
        self.token = token
        self.api_url = api_url
        self._last_upload_response: Optional[Dict] = None

    def image_upload(self, image_path: str) -> str:
        """
        上传图片到图床
        
        Args:
            image_path (str): 图片文件路径
            
        Returns:
            str: 上传成功后的图片URL
            
        Raises:
            Exception: 上传失败时抛出异常
        """
        try:
            with open(image_path, 'rb') as f:
                files = {'image': f}
                data = {'token': self.token}
                response = requests.post(self.api_url, files=files, data=data)
                
            if response.status_code == 200:
                result = response.json()
                if result['code'] == 200:
                    self._last_upload_response = result
                    return result['url']
                raise Exception(f"上传失败: {result.get('message', '未知错误')}")
            raise Exception(f"请求失败，状态码: {response.status_code}")
        except Exception as e:
            raise Exception(f"图片上传过程出错: {str(e)}")

    def image_del(self, url: str) -> int:
        """
        删除已上传的图片
        
        Args:
            url (str): 图片URL
            
        Returns:
            int: 操作状态码
        """
        if self._last_upload_response and 'del' in self._last_upload_response:
            try:
                response = requests.get(self._last_upload_response['del'])
                return response.status_code
            except Exception as e:
                raise Exception(f"删除图片失败: {str(e)}")
        raise Exception("没有找到删除链接，请确保图片已正确上传")

    def show_thumb(self, url: str) -> str:
        """
        获取图片缩略图URL
        
        Args:
            url (str): 原图片URL
            
        Returns:
            str: 缩略图URL
        """
        if self._last_upload_response and 'thumb' in self._last_upload_response:
            return self._last_upload_response['thumb']
        raise Exception("没有找到缩略图信息，请确保图片已正确上传")

    def show_original(self, url: str) -> str:
        """
        获取原始文件名
        
        Args:
            url (str): 图片URL
            
        Returns:
            str: 原始文件名
        """
        if self._last_upload_response and 'srcName' in self._last_upload_response:
            return self._last_upload_response['srcName']
        raise Exception("没有找到原始文件名信息，请确保图片已正确上传")

# 使用示例
if __name__ == "__main__":
    token = "7ef80fab5e3a2c7990147aa665acb32f"
    image_bed = ImageBed(token)
    
    try:
        # 上传图片
        image_path = r"D:\PythonProject\JsReverse\blog\storage\DrrisonPageUseForNotion01.png"
        url = image_bed.image_upload(image_path)
        print(f"上传成功，图片URL: {url}")
        
        # 获取缩略图
        thumb_url = image_bed.show_thumb(url)
        print(f"缩略图URL: {thumb_url}")
        
        # 获取原始文件名
        original_name = image_bed.show_original(url)
        print(f"原始文件名: {original_name}")
        
        # 删除图片
        status_code = image_bed.image_del(url)
        print(f"删除状态码: {status_code}")
        
    except Exception as e:
        print(f"操作失败: {str(e)}")
