# Color Palette
PALETTE = {
    "background": "#FAFAFA",
    "primary": "#D7263D",     # Red
    "secondary": "#1B998B",   # Teal
    "tertiary": "#2E294E",    # Deep Purple
    "text": "#2E2E2E",
    "grid": "#DADADA"
}

# Metric colors using the palette
METRIC_COLORS = {
    'bid_rate': PALETTE['primary'],    
    'win_rate': PALETTE['secondary'],   
    'ecpm': PALETTE['tertiary'],      
    'latency': PALETTE['primary'],     
    'volume': PALETTE['secondary']     
}

# Background colors using the palette
BG_COLORS = {
    'light': PALETTE['background'],
    'lighter': '#FFFFFF',
    'grid': PALETTE['grid']
}

# Dashboard Configuration
DASHBOARD_CONFIG = {
    'port': 8501,
    'timeout': 30,  # seconds
    'display_columns': [
        'date', 
        'ad_format', 
        'device_type', 
        'os', 
        'geo', 
        'bid_request_id', 
        'bid_price', 
        'won', 
        'response_time_ms'
    ]
}

# Color scales for heatmaps
COLOR_SCALES = {
    'bid_rate': [
        [0, PALETTE['tertiary']],    
        [0.5, PALETTE['background']], 
        [1, PALETTE['primary']]      
    ],
    'win_rate': [
        [0, PALETTE['tertiary']],
        [0.5, PALETTE['background']],
        [1, PALETTE['secondary']]
    ],
    'ecpm': [
        [0, PALETTE['tertiary']],
        [0.5, PALETTE['background']],
        [1, PALETTE['primary']]
    ],
    'latency': [
        [0, PALETTE['primary']],     
        [0.5, PALETTE['background']], 
        [1, PALETTE['tertiary']]     
    ]
}

# KPI Options
KPI_OPTIONS = {
    "bid_rate": "Bid Rate",
    "win_rate": "Win Rate",
    "ecpm": "eCPM",
    "latency": "Latency"
}

# Streamlit Configuration
STREAMLIT_CONFIG = {
    'page_title': "Inventory Metrics Dashboard",
    'page_icon': "📊",
    'layout': "wide"
}

# Custom CSS Template
CSS_TEMPLATE = """
    <style>
        .stMetric {{
            background-color: {background} !important;
        }}
        .stMetric > div {{
            color: {primary} !important;
        }}
        .stMetric label {{
            color: {tertiary} !important;
        }}
        .stSelectbox label, .stMultiSelect label {{
            color: {secondary} !important;
        }}
        .stRadio label {{
            color: {secondary} !important;
        }}
        .stMarkdown {{
            color: {text} !important;
        }}
    </style>
"""

# Simulation Configuration
SIMULATION_CONFIG = {
    'num_requests': 6000,
    'peak_hours': range(18, 22),  # 6 PM to 10 PM
    'random_seed': 42
}

# Ad and Targeting Attributes
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

# Device Type Weights for Simulation
DEVICE_TYPE_WEIGHTS = {
    'mobile': 0.6,
    'desktop': 0.3,
    'tablet': 0.1
}

# Network Speed Weights for Simulation
NETWORK_SPEED_WEIGHTS = {
    '2G': 1,
    '3G': 2,
    '4G': 5,
    '5G': 3,
    'WiFi': 8
}

# Time Range Configuration
TIME_RANGE = {
    'years': 15  # Number of years of historical data to simulate
}

# Simulation Parameters
SIMULATION_PARAMS = {
    'response_time': {
        'mean': 120,
        'std_dev': 30
    },
    'bid_price': {
        'min': 0.1,
        'max': 5.0
    },
    'floor_price': {
        'min': 0.1,
        'max': 2.0
    },
    'ctr': {
        'min': 0.01,
        'max': 0.2
    },
    'win_chance': 0.25,
    'conversion_rate': 0.1
} 