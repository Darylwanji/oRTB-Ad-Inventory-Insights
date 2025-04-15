import dagster as dg
import pandas as pd
import os
from oRTB_Ad_Inventory_Insights.Assets import simulate_ortb_traffic  # noqa: TID252
import random
from datetime import datetime

# Random seed for reproducibility
random.seed(42)

@dg.asset(deps=[simulate_ortb_traffic.run_all_simulations])
def load_ortb_bid_data() -> pd.DataFrame:
    """
    Load the oRTB bid data from a CSV file and process timestamps.
    """
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Data'))
    os.makedirs(data_dir, exist_ok=True)

    # Load the data
    input_path = os.path.join(data_dir, 'mock_ortb_traffic.csv')
    df = pd.read_csv(input_path)
    
    # Convert timestamp to datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Add temporal features
    df['year'] = df['timestamp'].dt.year
    df['month'] = df['timestamp'].dt.month
    df['day'] = df['timestamp'].dt.day
    df['hour'] = df['timestamp'].dt.hour
    df['day_of_week'] = df['timestamp'].dt.dayofweek
    
    return df

@dg.asset(deps=[load_ortb_bid_data])
def calculate_temporal_metrics(load_ortb_bid_data: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate various time-based metrics and trends.
    """
    df = load_ortb_bid_data
    
    # Yearly metrics
    yearly_metrics = df.groupby('year').agg({
        'bid_request_id': 'count',
        'won': 'sum',
        'win_price': 'mean',
        'clicked': 'sum',
        'converted': 'sum',
        'response_time_ms': 'mean'
    }).reset_index()
    
    # Calculate year-over-year growth
    yearly_metrics['bid_volume_yoy'] = yearly_metrics['bid_request_id'].pct_change() * 100
    yearly_metrics['win_rate'] = (yearly_metrics['won'] / yearly_metrics['bid_request_id']) * 100
    yearly_metrics['ctr'] = (yearly_metrics['clicked'] / yearly_metrics['won']) * 100
    yearly_metrics['conversion_rate'] = (yearly_metrics['converted'] / yearly_metrics['clicked']) * 100
    
    return yearly_metrics

@dg.asset(deps=[load_ortb_bid_data])
def calculate_seasonal_patterns(load_ortb_bid_data: pd.DataFrame) -> pd.DataFrame:
    """
    Analyze seasonal patterns in the data.
    """
    df = load_ortb_bid_data
    
    # Monthly patterns
    monthly_patterns = df.groupby(['year', 'month']).agg({
        'bid_request_id': 'count',
        'won': 'sum',
        'win_price': 'mean',
        'response_time_ms': 'mean'
    }).reset_index()
    
    # Add month-over-month metrics
    monthly_patterns['bid_volume_mom'] = monthly_patterns.groupby('year')['bid_request_id'].pct_change() * 100
    monthly_patterns['win_rate'] = (monthly_patterns['won'] / monthly_patterns['bid_request_id']) * 100
    
    return monthly_patterns

@dg.asset(deps=[load_ortb_bid_data])
def bid_rate(load_ortb_bid_data: pd.DataFrame) -> float:    
    """
    Calculate the bid rate.
    """
    bids_received = load_ortb_bid_data['bid_request_id'].nunique()
    total_bids = len(load_ortb_bid_data)
    return bids_received / total_bids if total_bids > 0 else 0

@dg.asset(deps=[load_ortb_bid_data])
def win_rate(load_ortb_bid_data: pd.DataFrame) -> float:
    """
    Calculate the win rate.
    """
    total_wins = load_ortb_bid_data['won'].sum()
    total_bids = len(load_ortb_bid_data)
    return total_wins / total_bids if total_bids > 0 else 0

@dg.asset(deps=[load_ortb_bid_data])
def eCPM(load_ortb_bid_data: pd.DataFrame) -> float:
    """
    Calculate the effective Cost Per Mille (eCPM).
    """
    total_cost = load_ortb_bid_data['win_price'].sum()
    total_impressions = load_ortb_bid_data['won'].count()
    return (total_cost / total_impressions) * 1000 if total_impressions > 0 else 0

@dg.asset(deps=[load_ortb_bid_data])
def avg_latency(load_ortb_bid_data: pd.DataFrame) -> float:
    """
    Calculate the average latency.
    """
    response_time = load_ortb_bid_data['response_time_ms']
    return response_time.mean() if not response_time.empty else 0

@dg.asset(deps=[load_ortb_bid_data, bid_rate, win_rate, eCPM, avg_latency, calculate_temporal_metrics, calculate_seasonal_patterns])
def get_all_kpis(
    load_ortb_bid_data: pd.DataFrame,
    bid_rate: float,
    win_rate: float,
    eCPM: float,
    avg_latency: float,
    calculate_temporal_metrics: pd.DataFrame,
    calculate_seasonal_patterns: pd.DataFrame
) -> None:
    """
    Consolidate and save all calculated KPIs including temporal analysis.
    """
    # Create output directory
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Data'))
    os.makedirs(output_dir, exist_ok=True)

    # Save the main KPIs
    kpi_summary = {
        'overall_metrics': {
            'bid_rate': bid_rate,
            'win_rate': win_rate,
            'eCPM': eCPM,
            'avg_latency': avg_latency,
            'total_bids': len(load_ortb_bid_data)
        }
    }

    # Save all dataframes
    load_ortb_bid_data.to_csv(os.path.join(output_dir, 'ortb_full_data.csv'), index=False)
    calculate_temporal_metrics.to_csv(os.path.join(output_dir, 'yearly_metrics.csv'), index=False)
    calculate_seasonal_patterns.to_csv(os.path.join(output_dir, 'monthly_patterns.csv'), index=False)
    
    # Save summary metrics
    pd.DataFrame([kpi_summary['overall_metrics']]).to_csv(
        os.path.join(output_dir, 'overall_kpis.csv'), index=False
    )

    # Print summary
    print("oRTB KPIs and Temporal Analysis:")
    print("========================================")
    print(f"Bid Rate: {bid_rate:.2%}")
    print(f"Win Rate: {win_rate:.2%}")
    print(f"eCPM: ${eCPM:.2f}")
    print(f"Average Latency: {avg_latency:.2f} ms")
    print(f"Total Bids: {len(load_ortb_bid_data)}")
    print("\nTemporal Analysis Files Generated:")
    print("----------------------------------------")
    print("1. ortb_full_data.csv - Complete dataset with temporal features")
    print("2. yearly_metrics.csv - Year-over-year analysis")
    print("3. monthly_patterns.csv - Monthly patterns and seasonality")
    print("4. overall_kpis.csv - Summary metrics")
    print("========================================")

