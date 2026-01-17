"""
数据获取基类
提供通用的HTTP请求和错误处理功能
"""

import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

import requests
import pandas as pd

from config import config
from utils.logger import get_logger


class BaseFetcher(ABC):
    """数据获取基类"""
    
    def __init__(self, source_name: str):
        """
        初始化获取器
        
        Args:
            source_name: 数据源名称
        """
        self.source_name = source_name
        self.logger = get_logger()
        self.timeout = config.FETCH_TIMEOUT
        self.max_retries = config.MAX_RETRIES
        
        # 数据源状态
        self.status = {
            'name': source_name,
            'type': 'CSV',
            'status': '未运行',
            'count': 0,
            'total': 0,
            'error': '',
            'response_time': 0
        }
    
    def fetch_csv(self, url: str, encoding: str = 'utf-8') -> Optional[pd.DataFrame]:
        """
        从URL获取CSV数据
        
        Args:
            url: CSV文件URL
            encoding: 文件编码
            
        Returns:
            DataFrame或None（失败时）
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                self.logger.info(f"📥 [{self.source_name}] 尝试下载 (第{attempt}次)...")
                
                start_time = time.time()
                
                response = requests.get(
                    url,
                    timeout=self.timeout,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                )
                response.raise_for_status()
                
                elapsed_time = int((time.time() - start_time) * 1000)
                self.status['response_time'] = elapsed_time
                
                # 尝试检测编码
                if response.encoding:
                    encoding = response.encoding
                
                # 解析CSV
                from io import StringIO
                df = pd.read_csv(StringIO(response.text), encoding=encoding)
                
                self.logger.info(f"✅ [{self.source_name}] 下载成功: {len(df)} 行, {elapsed_time}ms")
                
                self.status['status'] = '正常'
                self.status['total'] = len(df)
                
                return df
                
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"⚠️ [{self.source_name}] 请求失败 (第{attempt}次): {str(e)}")
                self.status['error'] = str(e)
                
                if attempt < self.max_retries:
                    wait_time = 2 ** attempt  # 指数退避
                    self.logger.info(f"   等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
            
            except Exception as e:
                self.logger.error(f"❌ [{self.source_name}] 解析失败: {str(e)}")
                self.status['status'] = '异常'
                self.status['error'] = str(e)
                return None
        
        # 所有重试都失败
        self.status['status'] = '异常'
        self.logger.error(f"❌ [{self.source_name}] 下载失败，已重试 {self.max_retries} 次")
        return None
    
    def fetch_json(self, url: str) -> Optional[Dict]:
        """
        从URL获取JSON数据
        
        Args:
            url: JSON API URL
            
        Returns:
            JSON数据或None（失败时）
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                self.logger.info(f"📥 [{self.source_name}] 请求API (第{attempt}次)...")
                
                start_time = time.time()
                
                response = requests.get(
                    url,
                    timeout=self.timeout,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Accept': 'application/json'
                    }
                )
                response.raise_for_status()
                
                elapsed_time = int((time.time() - start_time) * 1000)
                self.status['response_time'] = elapsed_time
                
                data = response.json()
                
                self.logger.info(f"✅ [{self.source_name}] API请求成功, {elapsed_time}ms")
                self.status['status'] = '正常'
                
                return data
                
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"⚠️ [{self.source_name}] 请求失败 (第{attempt}次): {str(e)}")
                self.status['error'] = str(e)
                
                if attempt < self.max_retries:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
            
            except Exception as e:
                self.logger.error(f"❌ [{self.source_name}] 解析失败: {str(e)}")
                self.status['status'] = '异常'
                self.status['error'] = str(e)
                return None
        
        self.status['status'] = '异常'
        return None
    
    @abstractmethod
    def fetch(self) -> List[Dict]:
        """
        获取数据（子类必须实现）
        
        Returns:
            记录列表
        """
        pass
    
    @abstractmethod
    def transform(self, raw_data) -> List[Dict]:
        """
        转换原始数据为标准格式（子类必须实现）
        
        Args:
            raw_data: 原始数据
            
        Returns:
            标准格式的记录列表
        """
        pass
    
    def get_status(self) -> Dict:
        """获取数据源状态"""
        return self.status
