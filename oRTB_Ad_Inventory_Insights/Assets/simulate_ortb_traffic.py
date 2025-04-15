"""
# Simulate oRTB Traffic for Ad Inventory Insights
# This script generates synthetic bid request data for an OpenRTB-compliant
# advertising system. The data includes various parameters such as ad format,
# device type, geo location, response time, bid price, and win status.
# The data spans across 15 years to provide historical trends and patterns.
"""
import random
import uuid
from datetime import datetime, timedelta
import pandas as pd
import dagster as dg
import os
from oRTB_Ad_Inventory_Insights.Assets.constants import (
    SIMULATION_CONFIG,
    AD_FORMATS,
    DEVICE_TYPES,
    GEO_LOCATIONS,
    USER_AGENTS,
    CAMPAIGN_IDS,
    DOMAINS,
    OS_LIST,
    BROWSERS,
    NETWORK_SPEEDS,
    DEVICE_TYPE_WEIGHTS,
    NETWORK_SPEED_WEIGHTS,
    TIME_RANGE,
    SIMULATION_PARAMS
)

# Set random seed for reproducibility
random.seed(SIMULATION_CONFIG['random_seed'])

# Time range configuration
END_DATE = datetime.now()
START_DATE = END_DATE - timedelta(days=TIME_RANGE['years']*365)  # 15 years ago

@dg.asset
def generate_timestamp():
    """
    Generate a random timestamp within the last 15 years, with higher probability
    during peak hours (6 PM to 10 PM).
    """
    # Generate a random date within the 15-year range
    days_range = (END_DATE - START_DATE).days
    random_days = random.randint(0, days_range)
    base_date = START_DATE + timedelta(days=random_days)
    
    # Generate hour with peak hour weighting
    hour = random.choices(
        population=list(range(24)),
        weights=[2 if h in SIMULATION_CONFIG['peak_hours'] else 1 for h in range(24)],
        k=1
    )[0]
    
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    
    return base_date + timedelta(hours=hour, minutes=minute, seconds=second)

@dg.asset(
    deps=[generate_timestamp],
)
def simulate_bid():
    timestamp = generate_timestamp()
    bid_request_id = str(uuid.uuid4())
    ad_format = random.choice(AD_FORMATS)
    device_type = random.choices(
        DEVICE_TYPES, 
        weights=[DEVICE_TYPE_WEIGHTS[dt] for dt in DEVICE_TYPES]
    )[0]
    geo = random.choice(GEO_LOCATIONS)
    user_agent = random.choice(USER_AGENTS)
    campaign_id = random.choice(CAMPAIGN_IDS)
    domain = random.choice(DOMAINS)
    os = random.choice(OS_LIST)
    browser = random.choice(BROWSERS)
    network = random.choices(
        NETWORK_SPEEDS,
        weights=[NETWORK_SPEED_WEIGHTS[ns] for ns in NETWORK_SPEEDS]
    )[0]
    device_id = uuid.uuid4().hex[:16]

    response_time_ms = round(random.gauss(
        SIMULATION_PARAMS['response_time']['mean'],
        SIMULATION_PARAMS['response_time']['std_dev']
    ))
    bid_price = round(random.uniform(
        SIMULATION_PARAMS['bid_price']['min'],
        SIMULATION_PARAMS['bid_price']['max']
    ), 2)
    floor_price = round(random.uniform(
        SIMULATION_PARAMS['floor_price']['min'],
        SIMULATION_PARAMS['floor_price']['max']
    ), 2)
    estimated_ctr = round(random.uniform(
        SIMULATION_PARAMS['ctr']['min'],
        SIMULATION_PARAMS['ctr']['max']
    ), 3)

    won = bid_price >= floor_price and (random.random() < SIMULATION_PARAMS['win_chance'])
    win_price = round(bid_price * random.uniform(0.7, 0.99), 2) if won else None

    # Simulate post-bid behavior
    click = won and (random.random() < estimated_ctr)
    conversion = click and (random.random() < SIMULATION_PARAMS['conversion_rate'])

    return {
        "bid_request_id": bid_request_id,
        "campaign_id": campaign_id,
        "ad_format": ad_format,
        "device_type": device_type,
        "device_id": device_id,
        "os": os,
        "browser": browser,
        "user_agent": user_agent,
        "geo": geo,
        "network": network,
        "domain": domain,
        "timestamp": timestamp.isoformat(),
        "response_time_ms": response_time_ms,
        "floor_price": floor_price,
        "bid_price": bid_price,
        "win_price": win_price,
        "estimated_ctr": estimated_ctr,
        "won": won,
        "clicked": click,
        "converted": conversion
    }

@dg.asset(
    deps=[simulate_bid],
)
def run_all_simulations():
    """
    Run all simulations and generate a DataFrame.
    """
    # Generate data
    data = [simulate_bid() for _ in range(SIMULATION_CONFIG['num_requests'])]
    df = pd.DataFrame(data)

    # Save or preview
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Data'))
    os.makedirs(output_dir, exist_ok=True)
    # Ensure the directory exists
    output_path = os.path.join(output_dir, 'mock_ortb_traffic.csv')
    df.to_csv(output_path, index=False)
    # Print the first few rows of the DataFrame
    print("Mock oRTB Traffic Data:")
    print("========================================")
    print(f"✅ Dataset saved to: {output_path}")
    print(df.head())
