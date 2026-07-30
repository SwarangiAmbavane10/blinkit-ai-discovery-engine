from discovery_engine.config.settings import Settings

def test_settings_load_defaults():
    settings = Settings()
    assert settings.PLAY_STORE_APP_ID == "com.grofers.customerapp"
    assert settings.APP_STORE_APP_ID == "1393452285"
    assert settings.LOG_LEVEL == "INFO"
    assert "blinkit" in settings.REDDIT_SEARCH_TERMS
