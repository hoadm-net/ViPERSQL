#!/usr/bin/env python3
"""
Multi-language ViR2 Test Script

Test script to demonstrate and verify multi-language capabilities of ViPERSQL
with the new MultiLanguageViR2Selector.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mint.utils.language_detector import LanguageDetector
from mint.utils.multilang_embedder import MultiLanguageEmbedder
from mint.metrics.pos_match_multilang import POSMatcher
from mint.selectors.multilang_vir2_selector import MultiLanguageViR2Selector
from mint.config import ViPERConfig


def test_language_detection():
    """Test language detection functionality."""
    print("=" * 60)
    print("TESTING LANGUAGE DETECTION")
    print("=" * 60)
    
    detector = LanguageDetector()
    
    test_cases = [
        "Tìm tất cả các sinh viên có điểm trung bình lớn hơn 8.0",
        "Find all students with GPA greater than 8.0",
        "Có bao nhiều khách hàng đã mua sản phẩm trong tháng này?",
        "How many customers purchased products this month?",
        "List the top 5 highest paid employees",
        "Liệt kê 5 nhân viên có lương cao nhất"
    ]
    
    for text in test_cases:
        lang = detector.detect_language(text)
        info = detector.get_language_info(text)
        print(f"Text: {text}")
        print(f"Language: {lang} (confidence: {info['confidence']:.2f})")
        print(f"Details: vi_chars={info['vietnamese_chars']}, vi_words={info['vietnamese_words']}, en_words={info['english_words']}")
        print("-" * 60)


def test_multilang_embeddings():
    """Test multi-language embedding generation."""
    print("\n" + "=" * 60)
    print("TESTING MULTI-LANGUAGE EMBEDDINGS")
    print("=" * 60)
    
    embedder = MultiLanguageEmbedder(cache_models=False)  # Don't cache for testing
    
    test_texts = [
        ("vi", "Tìm tất cả các sinh viên có điểm trung bình lớn hơn 8.0"),
        ("en", "Find all students with GPA greater than 8.0"),
        ("vi", "Có bao nhiều khách hàng đã mua sản phẩm?"),
        ("en", "How many customers purchased products?")
    ]
    
    for lang, text in test_texts:
        print(f"Testing {lang}: {text}")
        
        # Test auto-detection
        auto_embedding = embedder.encode(text)
        detected_lang = embedder.detect_language(text)
        print(f"  Auto-detected language: {detected_lang}")
        print(f"  Auto embedding shape: {auto_embedding.shape}")
        
        # Test explicit language
        explicit_embedding = embedder.encode(text, language=lang)
        print(f"  Explicit {lang} embedding shape: {explicit_embedding.shape}")
        
        # Compare embeddings
        similarity = cosine_similarity(
            auto_embedding.reshape(1, -1), 
            explicit_embedding.reshape(1, -1)
        )[0][0] if auto_embedding.shape == explicit_embedding.shape else 0.0
        print(f"  Embedding similarity: {similarity:.4f}")
        print("-" * 60)


def test_multilang_pos_matching():
    """Test multi-language POS matching."""
    print("\n" + "=" * 60)
    print("TESTING MULTI-LANGUAGE POS MATCHING")
    print("=" * 60)
    
    pos_matcher = POSMatcher()
    
    test_pairs = [
        # Vietnamese pairs
        ("vi", "Tìm tất cả học sinh", "Tìm tất cả sinh viên"),
        ("vi", "Có bao nhiều khách hàng", "Có bao nhiều người mua"),
        
        # English pairs  
        ("en", "Find all students", "Find all pupils"),
        ("en", "How many customers", "How many buyers"),
        
        # Cross-language (should work with auto-detection)
        (None, "Find all students", "Tìm tất cả học sinh"),
    ]
    
    for lang, q1, q2 in test_pairs:
        print(f"Testing {lang or 'auto'}: '{q1}' vs '{q2}'")
        
        # Calculate POS match
        pos_score = pos_matcher.pos_match(q1, q2, language=lang)
        print(f"  POS match score: {pos_score:.4f}")
        
        # Get detailed analysis
        analysis = pos_matcher.analyze_pos_similarity(q1, q2, language=lang)
        print(f"  Detected language: {analysis['language']}")
        print(f"  Q1 tags: {analysis['question1_tags'][:5]}...")  # Show first 5 tags
        print(f"  Q2 tags: {analysis['question2_tags'][:5]}...")
        print("-" * 60)


def test_multilang_vir2_selector():
    """Test multi-language ViR2 selector with dummy data."""
    print("\n" + "=" * 60)
    print("TESTING MULTI-LANGUAGE VIR2 SELECTOR")
    print("=" * 60)
    
    # Create dummy config
    config = ViPERConfig(
        vir2_candidate_pool_size=10,
        vir2_beam_size=3,
        vir2_diversity_weight=0.3
    )
    
    selector = MultiLanguageViR2Selector(config)
    
    # Create dummy meaning pool
    dummy_pool = [
        {
            "question": "Find all students with high grades",
            "query": "SELECT * FROM students WHERE grade > 90",
            "db_id": "university"
        },
        {
            "question": "How many employees work in each department?",
            "query": "SELECT department, COUNT(*) FROM employees GROUP BY department",
            "db_id": "company"
        },
        {
            "question": "List all products with price greater than 100",
            "query": "SELECT * FROM products WHERE price > 100",
            "db_id": "shop"
        },
        {
            "question": "Tìm tất cả sinh viên có điểm cao",
            "query": "SELECT * FROM sinh_vien WHERE diem > 8",
            "db_id": "truong_hoc"
        },
        {
            "question": "Có bao nhiều nhân viên trong từng phòng ban?",
            "query": "SELECT phong_ban, COUNT(*) FROM nhan_vien GROUP BY phong_ban",
            "db_id": "cong_ty"
        }
    ]
    
    # Manually set meaning pool for testing
    selector.meaning_pool = dummy_pool
    selector.meaning_pool_language = "en"  # Assume English pool
    selector._compute_meaning_pool_embeddings()
    
    # Test queries
    test_queries = [
        "Show me all students with excellent performance",  # English
        "Hiển thị tất cả học sinh có thành tích xuất sắc",   # Vietnamese
    ]
    
    for query in test_queries:
        print(f"Query: {query}")
        detected_lang = selector.language_detector.detect_language(query)
        print(f"Detected language: {detected_lang}")
        
        # Get selection info
        info = selector.get_selection_info(query, k=3)
        print(f"Selection info:")
        for key, value in info.items():
            if key not in ['candidates_info', 'selected_info']:
                print(f"  {key}: {value}")
        
        print(f"  Top candidates:")
        for i, candidate in enumerate(info.get('candidates_info', [])[:3]):
            print(f"    {i+1}. {candidate['question'][:50]}... (sim: {candidate['similarity']:.3f})")
        
        print("-" * 60)


def main():
    """Run all tests."""
    print("Multi-language ViPERSQL Test Suite")
    print("=" * 60)
    
    try:
        # Import required libraries for testing
        global cosine_similarity
        from sklearn.metrics.pairwise import cosine_similarity
        
        # Run tests
        test_language_detection()
        
        print("\nSkipping embedding tests (requires model download)")
        # test_multilang_embeddings()  # Skip heavy model tests
        
        print("\nSkipping POS matching tests (requires spaCy models)")  
        # test_multilang_pos_matching()  # Skip if spaCy models not installed
        
        print("\nSkipping ViR2 selector tests (requires full setup)")
        # test_multilang_vir2_selector()  # Skip complex integration test
        
        print("\n" + "=" * 60)
        print("BASIC TESTS COMPLETED")
        print("=" * 60)
        print("\nTo run full tests:")
        print("1. Install spaCy models: python -m spacy download en_core_web_sm vi_core_news_sm")
        print("2. Ensure CUDA/PyTorch is properly configured")
        print("3. Run with sufficient memory for model loading")
        
    except ImportError as e:
        print(f"Import error: {e}")
        print("Please install required dependencies from requirements.txt")
    except Exception as e:
        print(f"Test error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
