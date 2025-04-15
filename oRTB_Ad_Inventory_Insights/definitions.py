from dagster import Definitions
from oRTB_Ad_Inventory_Insights.Assets.simulate_ortb_traffic import run_all_simulations
from oRTB_Ad_Inventory_Insights.Assets.ortb_kpis import (
    load_ortb_bid_data,
    calculate_temporal_metrics,
    calculate_seasonal_patterns,
    bid_rate,
    win_rate,
    eCPM,
    avg_latency,
    get_all_kpis,
)
from oRTB_Ad_Inventory_Insights.Assets.ortb_dashboard import launch_ortb_dashboard

# Define assets
simulate_ortb_traffic_assets = [run_all_simulations]
ortb_kpis_assets = [
    load_ortb_bid_data,
    calculate_temporal_metrics,
    calculate_seasonal_patterns,
    bid_rate,
    win_rate,
    eCPM,
    avg_latency,
    get_all_kpis,
]
ortb_dashboard_assets = [launch_ortb_dashboard]

# Create Dagster definitions
defs = Definitions(
    assets=[
        *simulate_ortb_traffic_assets,
        *ortb_kpis_assets,
        *ortb_dashboard_assets,
    ]
)
