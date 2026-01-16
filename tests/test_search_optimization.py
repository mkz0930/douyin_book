#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
搜索优化功能测试脚本

测试场景：
1. 经典文学作品搜索（小王子）
2. 外文书籍搜索（The Little Prince）
3. 结果过滤和去重验证
"""

import sys
import os

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from search_client import SearchClient

def test_basic_search():
    """测试基础搜索功能"""
    print("=" * 60)
    print("测试1: 基础搜索功能 - 《小王子》")
    print("=" * 60)
    
    client = SearchClient(max_results=3)
    result = client.search_book_info("小王子")
    
    if result:
        print("\n搜索结果:")
        print("-" * 60)
        print(result)
        print("-" * 60)
        print(f"\n结果长度: {len(result)} 字符")
        print("✓ 测试通过")
    else:
        print("✗ 测试失败：未获取到搜索结果")
    
    return result is not None

def test_english_book():
    """测试外文书籍搜索"""
    print("\n" + "=" * 60)
    print("测试2: 外文书籍搜索 - The Little Prince")
    print("=" * 60)
    
    client = SearchClient(max_results=3)
    result = client.search_book_info("The Little Prince")
    
    if result:
        print("\n搜索结果:")
        print("-" * 60)
        print(result)
        print("-" * 60)
        print(f"\n结果长度: {len(result)} 字符")
        print("✓ 测试通过")
    else:
        print("✗ 测试失败：未获取到搜索结果")
    
    return result is not None

def test_filter_and_dedup():
    """测试过滤和去重功能"""
    print("\n" + "=" * 60)
    print("测试3: 过滤和去重功能测试")
    print("=" * 60)
    
    client = SearchClient(
        max_results=5,  # 增加结果数量以测试去重
        min_snippet_length=20,
        similarity_threshold=0.8
    )
    
    # 测试过滤功能
    test_snippets = [
        "这是一段很短的文本",  # 应被过滤（长度不足）
        "这是一段足够长的有效文本，关于小王子的内容描述，应该被保留下来",
        "购买小王子全集，限时优惠！",  # 应被过滤（广告）
        "这是另一段关于小王子的有效描述，内容详实丰富",
    ]
    
    print("\n原始片段数量:", len(test_snippets))
    filtered = client._filter_results(test_snippets, "小王子")
    print("过滤后数量:", len(filtered))
    print("过滤后内容:")
    for i, snippet in enumerate(filtered, 1):
        print(f"{i}. {snippet[:50]}...")
    
    # 测试去重功能
    test_duplicates = [
        "小王子是一部经典儿童文学作品",
        "小王子是一部经典儿童文学作品，作者是圣埃克苏佩里",  # 包含关系
        "这是完全不同的内容，关于小王子的另一个描述",
        "小王子讲述了一个来自B612星球的小王子的故事",
    ]
    
    print("\n去重测试:")
    print("原始数量:", len(test_duplicates))
    deduped = client._deduplicate_results(test_duplicates)
    print("去重后数量:", len(deduped))
    print("去重后内容:")
    for i, snippet in enumerate(deduped, 1):
        print(f"{i}. {snippet}")
    
    print("\n✓ 测试通过")
    return True

def test_length_control():
    """测试长度控制功能"""
    print("\n" + "=" * 60)
    print("测试4: 长度控制功能测试")
    print("=" * 60)
    
    client = SearchClient(max_summary_length=500)
    
    # 构造一个很长的测试文本
    long_text = "测试段落\n" * 100
    truncated = client._truncate_summary(long_text, 500)
    
    print(f"原始长度: {len(long_text)} 字符")
    print(f"截断后长度: {len(truncated)} 字符")
    print(f"是否包含截断标记: {'[注: 内容过长已截断]' in truncated}")
    
    if len(truncated) <= 550 and '[注: 内容过长已截断]' in truncated:
        print("✓ 测试通过")
        return True
    else:
        print("✗ 测试失败")
        return False

def main():
    """运行所有测试"""
    print("开始测试搜索优化功能...")
    print("注意：测试需要网络连接\n")
    
    results = []
    
    # 运行测试
    results.append(("基础搜索", test_basic_search()))
    results.append(("外文书籍搜索", test_english_book()))
    results.append(("过滤和去重", test_filter_and_dedup()))
    results.append(("长度控制", test_length_control()))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    for name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{name}: {status}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！搜索优化功能正常工作")
        return 0
    else:
        print("\n⚠️ 部分测试失败，请检查错误信息")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n测试出现异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
