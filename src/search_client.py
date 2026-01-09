from duckduckgo_search import DDGS
from googlesearch import search as google_search
import time
import random

class SearchClient:
    def __init__(self, max_results=3):
        self.max_results = max_results
        self.ddgs = DDGS()

    def search_book_info(self, book_name):
        """
        搜索书籍相关信息，返回汇总文本
        """
        print(f"正在联网搜索关于《{book_name}》的资料...")
        
        summary = ""
        
        # 1. 搜索简介和剧情
        query_plot = f"{book_name} 内容简介 核心剧情 详细摘要"
        print(f"执行搜索: {query_plot}")
        results_plot = self._safe_search(query_plot)
        if results_plot:
            summary += f"【{book_name} 内容简介与剧情】\n"
            for res in results_plot:
                # 统一 DuckDuckGo 和 Google 的返回格式
                # DDG: {'body': ..., 'title': ...}
                # Google: SearchResult object with .description, .title
                body = self._extract_snippet(res)
                summary += f"- {body}\n"
            summary += "\n"
        else:
            print(f"警告: 未能搜索到关于 {book_name} 的剧情简介。")

        # 2. 搜索经典语录和评价
        query_quotes = f"{book_name} 经典语录 金句 深度解读"
        print(f"执行搜索: {query_quotes}")
        results_quotes = self._safe_search(query_quotes)
        if results_quotes:
            summary += f"【{book_name} 经典语录与评价】\n"
            for res in results_quotes:
                body = self._extract_snippet(res)
                summary += f"- {body}\n"
            summary += "\n"
        else:
            print(f"警告: 未能搜索到关于 {book_name} 的语录评价。")

        if not summary:
            print(f"搜索完全失败: {book_name}")
            return None
            
        return summary

    def _extract_snippet(self, result):
        """
        从不同来源的搜索结果中提取摘要
        """
        # 如果是字典（DuckDuckGo）
        if isinstance(result, dict):
            return result.get('body') or result.get('snippet') or ""
        
        # 如果是 Google SearchResult 对象
        if hasattr(result, 'description'):
            return result.description
            
        return str(result)

    def _safe_search(self, query):
        """
        执行搜索并处理可能的异常，增加重试和多引擎回退机制
        策略：优先尝试 DuckDuckGo，失败则回退到 Google Search (googlesearch-python)
        """
        
        # --- 策略 1: DuckDuckGo ---
        backends = ['api', 'html', 'lite']
        for backend in backends:
            try:
                time.sleep(random.uniform(1, 2))
                # DDGS().text() 返回一个迭代器
                results = list(self.ddgs.text(query, max_results=self.max_results, backend=backend))
                if results:
                    return results
                else:
                    # print(f"DuckDuckGo 后端 {backend} 返回空结果...")
                    pass
            except Exception as e:
                # print(f"DuckDuckGo 后端 {backend} 搜索出错: {e}")
                pass
        
        print("DuckDuckGo 搜索失败，尝试切换到 Google 搜索...")

        # --- 策略 2: Google Search (googlesearch-python) ---
        try:
            # google_search 返回 SearchResult 对象列表 (advanced=True)
            # 增加 ssl_verify=False 以应对部分本地代理环境
            results = list(google_search(query, num_results=self.max_results, advanced=True, ssl_verify=False))
            if results:
                return results
            else:
                print("Google 搜索也返回空结果。")
        except Exception as e:
            print(f"Google 搜索出错: {e}")

        print(f"所有搜索引擎均搜索失败: {query}")
        return []

if __name__ == "__main__":
    # Test
    # client = SearchClient()
    # info = client.search_book_info("毛泽东选集")
    # print(info)
    pass
