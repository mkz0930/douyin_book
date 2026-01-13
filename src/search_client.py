try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS
from googlesearch import search as google_search
import time
import random
import re
from difflib import SequenceMatcher

class SearchClient:
    def __init__(self, max_results=3, min_snippet_length=20, similarity_threshold=0.8, 
                 search_timeout=10, retry_attempts=2, max_summary_length=2000):
        """初始化搜索客户端
        
        Args:
            max_results: 每次查询的最大结果数
            min_snippet_length: 摘要最小长度
            similarity_threshold: 去重相似度阈值
            search_timeout: 单次搜索超时（秒）
            retry_attempts: 搜索重试次数
            max_summary_length: 汇总文本最大长度
        """
        self.max_results = max_results
        self.min_snippet_length = min_snippet_length
        self.similarity_threshold = similarity_threshold
        self.search_timeout = search_timeout
        self.retry_attempts = retry_attempts
        self.max_summary_length = max_summary_length
        self.ddgs = DDGS()
        
        # 广告关键词列表
        self.ad_keywords = ['购买', '优惠', '促销', '打折', '特价', '包邮', 
                           '限时', '抢购', '秒杀', '立即购买', '加入购物车',
                           'buy', 'sale', 'discount', 'shop now']

    def search_book_info(self, book_name):
        """
        搜索书籍相关信息，返回汇总文本（优化版）
        
        改进：
        - 结果过滤：过滤低质量内容
        - 去重处理：移除重复内容
        - 结构化汇总：改善输出格式
        - 长度控制：确保不超过限制
        """
        print(f"正在联网搜索关于《{book_name}》的资料...")
        
        all_sections = {}
        
        # 1. 搜索简介和剧情
        query_plot = f"{book_name} 内容简介 核心剧情 详细摘要"
        print(f"执行搜索: {query_plot}")
        results_plot = self._safe_search(query_plot)
        if results_plot:
            # 提取、过滤、去重
            snippets = [self._extract_snippet(res) for res in results_plot]
            filtered = self._filter_results(snippets, book_name)
            deduplicated = self._deduplicate_results(filtered)
            
            if deduplicated:
                all_sections['content'] = deduplicated
                print(f"[简介] 获取到 {len(deduplicated)} 条有效结果")
            else:
                print(f"警告: 过滤后未能获取有效的剧情简介。")
        else:
            print(f"警告: 未能搜索到关于 {book_name} 的剧情简介。")

        # 2. 搜索经典语录和评价
        query_quotes = f"{book_name} 经典语录 金句 深度解读"
        print(f"执行搜索: {query_quotes}")
        results_quotes = self._safe_search(query_quotes)
        if results_quotes:
            snippets = [self._extract_snippet(res) for res in results_quotes]
            filtered = self._filter_results(snippets, book_name)
            deduplicated = self._deduplicate_results(filtered)
            
            if deduplicated:
                all_sections['quotes'] = deduplicated
                print(f"[语录] 获取到 {len(deduplicated)} 条有效结果")
            else:
                print(f"警告: 过滤后未能获取有效的语录评价。")
        else:
            print(f"警告: 未能搜索到关于 {book_name} 的语录评价。")

        if not all_sections:
            print(f"搜索完全失败: {book_name}")
            return None
        
        # 结构化汇总
        summary = self._format_structured_summary(all_sections, book_name)
        
        # 长度控制
        if len(summary) > self.max_summary_length:
            print(f"警告: 汇总文本过长({len(summary)}字符)，将进行截断")
            summary = self._truncate_summary(summary, self.max_summary_length)
            
        return summary

    def _extract_snippet(self, result):
        """
        从不同来源的搜索结果中提取摘要
        """
        snippet = ""
        
        # 如果是字典（DuckDuckGo）
        if isinstance(result, dict):
            snippet = result.get('body') or result.get('snippet') or ""
        # 如果是 Google SearchResult 对象
        elif hasattr(result, 'description'):
            snippet = result.description
        else:
            snippet = str(result)
        
        # 清理文本
        snippet = snippet.strip()
        return snippet

    def _safe_search(self, query):
        """
        执行搜索并处理可能的异常，增加重试和多引擎回退机制（优化版）
        
        改进：
        - 增加重试机制
        - 更好的异常处理
        - 详细的日志记录
        """
        
        # --- 策略 1: DuckDuckGo ---
        backends = ['auto', 'html', 'lite']
        for backend in backends:
            for attempt in range(self.retry_attempts):
                try:
                    # 随机延时避免反爬
                    time.sleep(random.uniform(1, 3))
                    
                    # DDGS().text() 返回一个迭代器
                    results = list(self.ddgs.text(query, max_results=self.max_results, backend=backend))
                    if results:
                        print(f"✓ DuckDuckGo({backend}) 搜索成功，返回 {len(results)} 条结果")
                        return results
                except Exception as e:
                    if attempt < self.retry_attempts - 1:
                        print(f"DuckDuckGo({backend}) 尝试 {attempt+1}/{self.retry_attempts} 失败，重试中...")
                    else:
                        print(f"DuckDuckGo({backend}) 所有尝试失败: {str(e)[:50]}")
        
        print("DuckDuckGo 搜索失败，尝试切换到 Google 搜索...")

        # --- 策略 2: Google Search (googlesearch-python) ---
        for attempt in range(self.retry_attempts):
            try:
                time.sleep(random.uniform(1, 3))
                # google_search 返回 SearchResult 对象列表 (advanced=True)
                results = list(google_search(query, num_results=self.max_results, advanced=True, ssl_verify=False))
                if results:
                    print(f"✓ Google 搜索成功，返回 {len(results)} 条结果")
                    return results
            except Exception as e:
                if attempt < self.retry_attempts - 1:
                    print(f"Google 尝试 {attempt+1}/{self.retry_attempts} 失败，重试中...")
                else:
                    print(f"Google 所有尝试失败: {str(e)[:50]}")

        print(f"✗ 所有搜索引擎均搜索失败: {query}")
        return []

    def _filter_results(self, snippets, book_name):
        """
        过滤低质量搜索结果
        
        过滤标准：
        - 内容长度不足
        - 包含广告关键词
        - 不包含书名关键词
        """
        filtered = []
        book_name_clean = book_name.replace('《', '').replace('》', '').strip()
        
        for snippet in snippets:
            if not snippet or len(snippet) < self.min_snippet_length:
                continue
            
            # 检查是否包含广告关键词
            has_ad = any(keyword in snippet for keyword in self.ad_keywords)
            if has_ad:
                continue
            
            # 检查是否与书名相关（宽松检查，避免过度过滤）
            # 对于短书名，放宽要求
            if len(book_name_clean) > 2:
                # 长书名需要包含部分书名内容
                has_book_ref = book_name_clean[:3] in snippet or book_name_clean[-3:] in snippet
            else:
                # 短书名跳过此检查
                has_book_ref = True
            
            if has_book_ref:
                filtered.append(snippet)
        
        return filtered
    
    def _deduplicate_results(self, snippets):
        """
        去除重复和高度相似的内容
        
        策略：
        - 完全重复：直接去除
        - 高度相似（>相似度阈值）：保留较长的
        - 包含关系：保留较长的
        """
        if not snippets:
            return []
        
        unique_snippets = []
        
        for snippet in snippets:
            is_duplicate = False
            
            for i, existing in enumerate(unique_snippets):
                # 计算相似度
                similarity = self._calculate_similarity(snippet, existing)
                
                if similarity > self.similarity_threshold:
                    # 高度相似，保留较长的
                    if len(snippet) > len(existing):
                        unique_snippets[i] = snippet
                    is_duplicate = True
                    break
                
                # 检查包含关系
                if snippet in existing or existing in snippet:
                    # 保留较长的
                    if len(snippet) > len(existing):
                        unique_snippets[i] = snippet
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_snippets.append(snippet)
        
        return unique_snippets
    
    def _calculate_similarity(self, text1, text2):
        """
        计算两个文本的相似度（使用 SequenceMatcher）
        
        返回 0-1 之间的相似度分数
        """
        return SequenceMatcher(None, text1, text2).ratio()
    
    def _format_structured_summary(self, sections, book_name):
        """
        将搜索结果组织为结构化格式
        
        格式：
        【书籍基本信息】
        书名：xxx
        
        【内容简介】
        - xxx
        
        【核心观点/经典片段】
        - xxx
        """
        summary_parts = []
        
        # 书籍基本信息
        summary_parts.append("【书籍基本信息】")
        summary_parts.append(f"书名：《{book_name}》")
        summary_parts.append("")
        
        # 内容简介
        if 'content' in sections:
            summary_parts.append("【内容简介】")
            for item in sections['content'][:3]:  # 最多3条
                # 长度控制：每条最多800字符
                item_truncated = item[:800] if len(item) > 800 else item
                summary_parts.append(f"- {item_truncated}")
            summary_parts.append("")
        
        # 核心观点/经典片段
        if 'quotes' in sections:
            summary_parts.append("【核心观点/经典片段】")
            for item in sections['quotes'][:3]:  # 最多3条
                # 长度控制：每条最多600字符
                item_truncated = item[:600] if len(item) > 600 else item
                summary_parts.append(f"- {item_truncated}")
            summary_parts.append("")
        
        return "\n".join(summary_parts)
    
    def _truncate_summary(self, summary, max_length):
        """
        智能截断汇总文本，确保不超过最大长度
        
        策略：保留完整的段落，避免在句子中间截断
        """
        if len(summary) <= max_length:
            return summary
        
        # 在最后一个完整段落处截断
        truncated = summary[:max_length]
        
        # 找到最后一个换行符
        last_newline = truncated.rfind('\n')
        if last_newline > max_length * 0.8:  # 如果截断位置合理
            truncated = truncated[:last_newline]
        
        truncated += "\n\n[注: 内容过长已截断]\n"
        return truncated

if __name__ == "__main__":
    # Test
    # client = SearchClient()
    # info = client.search_book_info("小王子")
    # print(info)
    pass
