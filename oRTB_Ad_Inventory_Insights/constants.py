# Config
NUM_REQUESTS = 1000
PEAK_HOURS = range(18, 22)  # 6 PM to 10 PM

# Ad and targeting attributes
AD_FORMATS = ["banner", "video", "native"]
DEVICE_TYPES = ["mobile", "desktop", "tablet"]
GEO_LOCATIONS = ["US", "CA", "UK", "IN", "DE", "BR", "AU", "FR", "JP"]
USER_AGENTS = [
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)",
    "Mozilla/5.0 (Linux; Android 13; Pixel 6)",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_5)"
]
CAMPAIGN_IDS = [f"cmp_{i:03}" for i in range(1, 21)]
DOMAINS = ["example.com", "newsnet.org", "funmedia.co", "sportsbuzz.io", "shopnow.com"]
OS_LIST = ["iOS", "Android", "Windows", "macOS"]
BROWSERS = ["Chrome", "Safari", "Firefox", "Edge"]
NETWORK_SPEEDS = ["2G", "3G", "4G", "5G", "WiFi"]