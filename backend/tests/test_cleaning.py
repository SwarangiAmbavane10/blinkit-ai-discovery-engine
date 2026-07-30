from discovery_engine.cleaning.cleaner import ReviewCleaner

def test_remove_urls():
    text = "Visit http://example.com/xyz or check www.google.com for info"
    cleaned = ReviewCleaner.remove_urls(text)
    assert "http" not in cleaned
    assert "xyz" not in cleaned
    assert "www" not in cleaned

def test_remove_emojis():
    text = "Blinkit is extremely fast! 🚀🔥 Order received in 8 mins! 😍"
    cleaned = ReviewCleaner.remove_emojis(text)
    assert "🚀" not in cleaned
    assert "🔥" not in cleaned
    assert "😍" not in cleaned
    assert "Blinkit is extremely fast" in cleaned

def test_remove_stopwords():
    text = "This is a simple query to see if we remove standard English stopwords"
    cleaned = ReviewCleaner.remove_stopwords(text)
    words = cleaned.split()
    assert "this" not in words
    assert "is" not in words
    assert "a" not in words
    assert "simple" in words
    assert "stopwords" in words

def test_normalize_text():
    text = "  HELLO   world!  "
    cleaned = ReviewCleaner.normalize_text(text)
    assert cleaned == "hello world"
