# src/fetchers/__init__.py
"""数据获取模块"""
from .base_fetcher import BaseFetcher
from .ontario_fetcher import OntarioFetcher
from .bc_fetcher import BCFetcher
from .acecqa_fetcher import ACECQAFetcher

__all__ = ['BaseFetcher', 'OntarioFetcher', 'BCFetcher', 'ACECQAFetcher']
