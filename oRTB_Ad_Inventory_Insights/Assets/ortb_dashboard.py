import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import pandas as pd
import dagster as dg
from oRTB_Ad_Inventory_Insights.Assets.ortb_kpis import (
    load_ortb_bid_data,
    calc_bid_rate,
    calc_win_rate,
    eCPM,
    avg_latency,
    get_all_kpis
)
from oRTB_Ad_Inventory_Insights.Assets.simulate_ortb_traffic import run_all_simulations
from oRTB_Ad_Inventory_Insights.Assets.constants import (
    PALETTE,
    METRIC_COLORS,
    BG_COLORS,
    DASHBOARD_CONFIG,
    COLOR_SCALES,
    KPI_OPTIONS,
    STREAMLIT_CONFIG,
    CSS_TEMPLATE
)
import subprocess
import sys
import os
import time
import webbrowser

# Define the Streamlit app function
def create_streamlit_app():
    # Page config with custom theme
    st.set_page_config(
        page_title=STREAMLIT_CONFIG['page_title'],
        page_icon=STREAMLIT_CONFIG['page_icon'],
        layout=STREAMLIT_CONFIG['layout']
    )

    # Custom CSS for consistent theme
    st.markdown(
        CSS_TEMPLATE.format(
            background=PALETTE['background'],
            primary=PALETTE['primary'],
            secondary=PALETTE['secondary'],
            tertiary=PALETTE['tertiary'],
            text=PALETTE['text']
        ),
        unsafe_allow_html=True
    )

    # Load data
    @st.cache_data
    def load_data():
        df = load_ortb_bid_data()
        df['date'] = pd.to_datetime(df['timestamp']).dt.date
        return df

    df = load_data()

    # Sidebar filters
    st.sidebar.header("Filters")

    # Date range
    date_min = df['date'].min() if not df.empty else datetime.now().date() - timedelta(days=30)
    date_max = df['date'].max() if not df.empty else datetime.now().date()
    date_range = st.sidebar.date_input(
        "Date Range",
        value=(date_min, date_max),
        min_value=date_min,
        max_value=date_max
    )

    # Other filters
    ad_format = st.sidebar.multiselect(
        "Ad Format",
        options=df['ad_format'].unique(),
        default=df['ad_format'].unique()
    )

    device_type = st.sidebar.multiselect(
        "Device Type",
        options=df['device_type'].unique(),
        default=df['device_type'].unique()
    )

    os_type = st.sidebar.multiselect(
        "Operating System",
        options=df['os'].unique(),
        default=df['os'].unique()
    )

    geo = st.sidebar.multiselect(
        "Geography",
        options=df['geo'].unique(),
        default=df['geo'].unique()
    )

    # KPI selector
    st.sidebar.header("KPI Selection")
    kpi_selector = st.sidebar.radio(
        "Select KPI for Analysis:",
        options=["bid_rate", "win_rate", "ecpm", "latency"],
        format_func=lambda x: {
            "bid_rate": "Bid Rate",
            "win_rate": "Win Rate",
            "ecpm": "eCPM",
            "latency": "Latency"
        }[x]
    )

    # Filter data
    @st.cache_data
    def filter_data(df, date_range, ad_format, device_type, os_type, geo):
        return df[
            (df['date'] >= date_range[0]) &
            (df['date'] <= date_range[1]) &
            (df['ad_format'].isin(ad_format)) &
            (df['device_type'].isin(device_type)) &
            (df['os'].isin(os_type)) &
            (df['geo'].isin(geo))
        ]

    filtered_df = filter_data(df, date_range, ad_format, device_type, os_type, geo)

    # Calculate KPIs
    def calculate_kpis(data):
        bid_rate = calc_bid_rate(data)
        win_rate = calc_win_rate(data)
        ecpm = eCPM(data)
        latency = avg_latency(data)
        return bid_rate, win_rate, ecpm, latency

    bid_rate, win_rate, ecpm, latency = calculate_kpis(filtered_df)

    # Main dashboard
    st.title("Inventory Metrics Dashboard")

    # KPI metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    metric_style = {"backgroundColor": PALETTE['background'], "color": PALETTE['primary'], "padding": "1rem"}

    with col1:
        st.metric(
            "Bid Rate",
            f"{bid_rate:.2%}",
            delta=None,
            help="Percentage of bid requests that received bids"
        )

    with col2:
        st.metric(
            "Win Rate",
            f"{win_rate:.2%}",
            delta=None,
            help="Percentage of bids that won auctions"
        )

    with col3:
        st.metric(
            "eCPM",
            f"${ecpm:.2f}",
            delta=None,
            help="Effective Cost Per Mille (per thousand impressions)"
        )

    with col4:
        st.metric(
            "Latency",
            f"{latency:.1f} ms",
            delta=None,
            help="Average response time in milliseconds"
        )

    # Time series plot
    st.subheader("KPI Trends Over Time")
    
    # Prepare the data
    daily_data = filtered_df.groupby('date').agg({
        'bid_request_id': 'count',
        'bid_price': 'sum',
        'won': 'sum',
        'response_time_ms': 'mean'
    }).reset_index()

    # Calculate metrics and normalize them for better visualization
    daily_data['bid_rate'] = daily_data['won'] / daily_data['bid_request_id']
    daily_data['win_rate'] = daily_data['won'] / daily_data['bid_request_id']
    daily_data['ecpm'] = (daily_data['bid_price'] * daily_data['won']) / (daily_data['bid_request_id'] / 1000)
    
    # Create the main figure
    fig = go.Figure()

    # Add traces for each metric with gradient fills
    fig.add_trace(go.Scatter(
        x=daily_data['date'],
        y=daily_data['bid_rate'],
        name='Bid Rate',
        mode='lines',
        line=dict(width=2, color=METRIC_COLORS['bid_rate']),
        stackgroup='one',
        groupnorm='percent',  # Normalize to percentages
        hovertemplate='Date: %{x}<br>Bid Rate: %{y:.1%}<extra></extra>'
    ))

    fig.add_trace(go.Scatter(
        x=daily_data['date'],
        y=daily_data['win_rate'],
        name='Win Rate',
        mode='lines',
        line=dict(width=2, color=METRIC_COLORS['win_rate']),
        stackgroup='one',
        hovertemplate='Date: %{x}<br>Win Rate: %{y:.1%}<extra></extra>'
    ))

    # Add eCPM as a separate line on secondary y-axis
    fig.add_trace(go.Scatter(
        x=daily_data['date'],
        y=daily_data['ecpm'],
        name='eCPM',
        mode='lines',
        line=dict(width=3, color=METRIC_COLORS['ecpm']),
        yaxis='y2',
        hovertemplate='Date: %{x}<br>eCPM: $%{y:.2f}<extra></extra>'
    ))

    # Update layout with modern styling
    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='center',
            x=0.5,
            bgcolor=BG_COLORS['lighter'],
            bordercolor=BG_COLORS['grid']
        ),
        paper_bgcolor=BG_COLORS['lighter'],
        plot_bgcolor=BG_COLORS['light'],
        hovermode='x unified',
        margin=dict(t=80, r=50, b=50, l=50),
        yaxis=dict(
            title='Rate Distribution',
            showgrid=True,
            gridcolor=BG_COLORS['grid'],
            tickformat='.0%',
            range=[0, 100]  # For percentage view
        ),
        yaxis2=dict(
            title='eCPM ($)',
            overlaying='y',
            side='right',
            showgrid=False,
            tickprefix='$'
        ),
        xaxis=dict(
            title='Date',
            showgrid=True,
            gridcolor=BG_COLORS['grid']
        )
    )

    # Add range selector and slider
    fig.update_xaxes(
        rangeslider_visible=True,
        rangeselector=dict(
            buttons=list([
                dict(count=7, label="1W", step="day", stepmode="backward"),
                dict(count=1, label="1M", step="month", stepmode="backward"),
                dict(count=6, label="6M", step="month", stepmode="backward"),
                dict(count=1, label="1Y", step="year", stepmode="backward"),
                dict(step="all", label="All")
            ]),
            bgcolor=BG_COLORS['lighter']
        )
    )

    st.plotly_chart(fig, use_container_width=True)

    # Device and Geography distributions
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Device Type Distribution")
        device_data = filtered_df['device_type'].value_counts()
        fig_device = go.Figure(data=[
            go.Pie(
                labels=device_data.index,
                values=device_data.values,
                hole=0.4,
                marker=dict(colors=[PALETTE['primary'], PALETTE['secondary'], PALETTE['tertiary']])
            )
        ])
        fig_device.update_layout(
            paper_bgcolor=PALETTE['background'],
            plot_bgcolor=PALETTE['background'],
            font=dict(color=PALETTE['text'])
        )
        st.plotly_chart(fig_device, use_container_width=True)

    with col2:
        st.subheader("Geography Distribution")
        geo_data = filtered_df['geo'].value_counts().head(10)
        fig_geo = go.Figure(data=[
            go.Bar(
                x=geo_data.index,
                y=geo_data.values,
                marker_color=PALETTE['primary']
            )
        ])
        fig_geo.update_layout(
            paper_bgcolor=PALETTE['background'],
            plot_bgcolor=PALETTE['background'],
            xaxis_title="Country",
            yaxis_title="Count",
            yaxis_gridcolor=PALETTE['grid'],
            font=dict(color=PALETTE['text'])
        )
        st.plotly_chart(fig_geo, use_container_width=True)

    # Performance Metrics
    st.subheader("Performance Metrics")
    
    # Create time-based performance metrics
    performance_data = filtered_df.groupby('hour').agg({
        'response_time_ms': 'mean',
        'won': 'sum',
        'bid_request_id': 'count'
    }).reset_index()
    
    performance_data['win_rate'] = performance_data['won'] / performance_data['bid_request_id']
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_performance = make_subplots(specs=[[{"secondary_y": True}]])
        
        fig_performance.add_trace(
            go.Scatter(
                x=performance_data['hour'],
                y=performance_data['response_time_ms'],
                name="Latency",
                line=dict(color=PALETTE['primary'], width=2)
            ),
            secondary_y=False
        )
        
        fig_performance.add_trace(
            go.Scatter(
                x=performance_data['hour'],
                y=performance_data['win_rate'],
                name="Win Rate",
                line=dict(color=PALETTE['secondary'], width=2)
            ),
            secondary_y=True
        )
        
        fig_performance.update_layout(
            title='Hourly Performance Metrics',
            xaxis_title='Hour of Day',
            paper_bgcolor=PALETTE['background'],
            plot_bgcolor=PALETTE['background'],
            font=dict(color=PALETTE['text']),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                bgcolor=PALETTE['background'],
                bordercolor=PALETTE['grid']
            ),
            hovermode='x unified'
        )
        
        fig_performance.update_yaxes(
            title_text="Latency (ms)",
            secondary_y=False,
            gridcolor=PALETTE['grid'],
            tickfont=dict(color=PALETTE['text'])
        )
        fig_performance.update_yaxes(
            title_text="Win Rate",
            secondary_y=True,
            gridcolor=PALETTE['grid'],
            tickformat='.1%',
            tickfont=dict(color=PALETTE['text'])
        )
        fig_performance.update_xaxes(
            gridcolor=PALETTE['grid'],
            tickfont=dict(color=PALETTE['text'])
        )
        
        st.plotly_chart(fig_performance, use_container_width=True)

    with col2:
        # Prepare data for violin plot
        filtered_df['year'] = pd.to_datetime(filtered_df['timestamp']).dt.year
        
        # Create violin plot
        fig_violin = go.Figure()
        
        # Add violin plot - simplified to just show the distribution shape
        fig_violin.add_trace(go.Violin(
            x=filtered_df['year'],
            y=filtered_df['response_time_ms'],
            name='Latency Distribution',
            box=dict(visible=False),  # Hide box plot
            meanline=dict(visible=False),  # Hide mean line
            points=False,  # Hide outlier points
            line_color=METRIC_COLORS['latency'],
            fillcolor=f"rgba{tuple(list(int(METRIC_COLORS['latency'].lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) + [0.5])}",
            opacity=0.8,
            hovertemplate="Year: %{x}<br>" +
                         "Latency: %{y:.1f}ms<br>" +
                         "<extra></extra>"
        ))
        
        # Update layout
        fig_violin.update_layout(
            title={
                'text': 'Latency Distribution by Year',
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top'
            },
            xaxis_title='Year',
            yaxis_title='Latency (ms)',
            paper_bgcolor=BG_COLORS['lighter'],
            plot_bgcolor=BG_COLORS['light'],
            showlegend=False,
            hovermode='closest',
            xaxis=dict(
                showgrid=True,
                gridcolor=BG_COLORS['grid'],
                tickmode='array',
                ticktext=[str(year) for year in sorted(filtered_df['year'].unique())],
                tickvals=sorted(filtered_df['year'].unique())
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor=BG_COLORS['grid'],
                zeroline=False
            ),
            violingap=0.2,
            violinmode='overlay',
            margin=dict(t=50, r=20, b=50, l=50)
        )
        
        st.plotly_chart(fig_violin, use_container_width=True)

    # Heatmap
    st.subheader("KPI Heatmap by Geo & Device")
    heatmap_data = filtered_df.groupby(['geo', 'device_type']).agg({
        'bid_request_id': 'count',
        'bid_price': 'sum',
        'won': 'sum',
        'response_time_ms': 'mean'
    }).reset_index()

    heatmap_data['bid_rate'] = heatmap_data['won'] / heatmap_data['bid_request_id']
    heatmap_data['win_rate'] = heatmap_data['won'] / heatmap_data['bid_request_id']
    heatmap_data['ecpm'] = (heatmap_data['bid_price'] * heatmap_data['won']) / (heatmap_data['bid_request_id'] / 1000)
    heatmap_data['latency'] = heatmap_data['response_time_ms']

    # Calculate volume for size reference
    heatmap_data['volume'] = heatmap_data['bid_request_id'] / heatmap_data['bid_request_id'].sum()

    # Update color scales for heatmap
    color_scales = {
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

    # Create custom hover text
    def create_hover_text(row):
        if kpi_selector == 'bid_rate':
            return f"Geo: {row['geo']}<br>" + \
                   f"Device: {row['device_type']}<br>" + \
                   f"Bid Rate: {row['bid_rate']:.1%}<br>" + \
                   f"Volume: {row['volume']:.1%}"
        elif kpi_selector == 'win_rate':
            return f"Geo: {row['geo']}<br>" + \
                   f"Device: {row['device_type']}<br>" + \
                   f"Win Rate: {row['win_rate']:.1%}<br>" + \
                   f"Volume: {row['volume']:.1%}"
        elif kpi_selector == 'ecpm':
            return f"Geo: {row['geo']}<br>" + \
                   f"Device: {row['device_type']}<br>" + \
                   f"eCPM: ${row['ecpm']:.2f}<br>" + \
                   f"Volume: {row['volume']:.1%}"
        else:  # latency
            return f"Geo: {row['geo']}<br>" + \
                   f"Device: {row['device_type']}<br>" + \
                   f"Latency: {row['latency']:.1f}ms<br>" + \
                   f"Volume: {row['volume']:.1%}"

    heatmap_data['hover_text'] = heatmap_data.apply(create_hover_text, axis=1)

    fig_heatmap = go.Figure(data=go.Heatmap(
        x=heatmap_data['device_type'],
        y=heatmap_data['geo'],
        z=heatmap_data[kpi_selector],
        text=heatmap_data['hover_text'],
        hoverongaps=False,
        hoverinfo='text',
        colorscale=color_scales[kpi_selector],
        showscale=True
    ))
    
    fig_heatmap.update_layout(
        paper_bgcolor=BG_COLORS['lighter'],
        plot_bgcolor=BG_COLORS['light'],
        xaxis_title="Device Type",
        yaxis_title="Geography",
        title={
            'text': f"{kpi_selector.replace('_', ' ').title()} Distribution by Geo & Device",
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        margin=dict(t=60, r=20, b=40, l=80),
        xaxis={'side': 'bottom'},
        yaxis={'side': 'left'}
    )

    # Format colorbar based on metric type
    if kpi_selector in ['bid_rate', 'win_rate']:
        fig_heatmap.update_layout(
            coloraxis_colorbar=dict(
                title=dict(
                    text=f"{kpi_selector.replace('_', ' ').title()} %",
                    side='right'
                ),
                tickformat='.1%',
                len=0.75,
                thickness=20,
                x=1.02
            )
        )
    elif kpi_selector == 'ecpm':
        fig_heatmap.update_layout(
            coloraxis_colorbar=dict(
                title=dict(
                    text='eCPM ($)',
                    side='right'
                ),
                tickprefix='$',
                len=0.75,
                thickness=20,
                x=1.02
            )
        )
    else:  # latency
        fig_heatmap.update_layout(
            coloraxis_colorbar=dict(
                title=dict(
                    text='Latency (ms)',
                    side='right'
                ),
                len=0.75,
                thickness=20,
                x=1.02
            )
        )

    # Add annotations for extreme values
    max_val = heatmap_data[kpi_selector].max()
    min_val = heatmap_data[kpi_selector].min()
    max_idx = heatmap_data[kpi_selector].idxmax()
    min_idx = heatmap_data[kpi_selector].idxmin()

    annotations = []
    if kpi_selector in ['bid_rate', 'win_rate']:
        annotations.extend([
            dict(
                x=heatmap_data.iloc[max_idx]['device_type'],
                y=heatmap_data.iloc[max_idx]['geo'],
                text=f'Max: {max_val:.1%}',
                showarrow=True,
                arrowhead=2,
                arrowsize=1,
                arrowwidth=2,
                ax=40,
                ay=-40
            ),
            dict(
                x=heatmap_data.iloc[min_idx]['device_type'],
                y=heatmap_data.iloc[min_idx]['geo'],
                text=f'Min: {min_val:.1%}',
                showarrow=True,
                arrowhead=2,
                arrowsize=1,
                arrowwidth=2,
                ax=-40,
                ay=40
            )
        ])
    elif kpi_selector == 'ecpm':
        annotations.extend([
            dict(
                x=heatmap_data.iloc[max_idx]['device_type'],
                y=heatmap_data.iloc[max_idx]['geo'],
                text=f'Max: ${max_val:.2f}',
                showarrow=True,
                arrowhead=2,
                arrowsize=1,
                arrowwidth=2,
                ax=40,
                ay=-40
            ),
            dict(
                x=heatmap_data.iloc[min_idx]['device_type'],
                y=heatmap_data.iloc[min_idx]['geo'],
                text=f'Min: ${min_val:.2f}',
                showarrow=True,
                arrowhead=2,
                arrowsize=1,
                arrowwidth=2,
                ax=-40,
                ay=40
            )
        ])
    else:  # latency
        annotations.extend([
            dict(
                x=heatmap_data.iloc[max_idx]['device_type'],
                y=heatmap_data.iloc[max_idx]['geo'],
                text=f'Max: {max_val:.1f}ms',
                showarrow=True,
                arrowhead=2,
                arrowsize=1,
                arrowwidth=2,
                ax=40,
                ay=-40
            ),
            dict(
                x=heatmap_data.iloc[min_idx]['device_type'],
                y=heatmap_data.iloc[min_idx]['geo'],
                text=f'Min: {min_val:.1f}ms',
                showarrow=True,
                arrowhead=2,
                arrowsize=1,
                arrowwidth=2,
                ax=-40,
                ay=40
            )
        ])

    fig_heatmap.update_layout(annotations=annotations)
    st.plotly_chart(fig_heatmap, use_container_width=True)

    # Raw Data
    st.subheader("Raw Data")
    st.dataframe(
        filtered_df[DASHBOARD_CONFIG['display_columns']],
        use_container_width=True,
        hide_index=True
    )

@dg.asset(
    deps=[get_all_kpis],
    output_required=False
)
def launch_ortb_dashboard():
    """Launch the oRTB Dashboard using Streamlit"""
    dashboard_path = os.path.abspath(__file__)
    port = DASHBOARD_CONFIG['port']
    
    try:
        # Kill any existing Streamlit processes on the port
        if sys.platform == 'darwin':  # macOS
            os.system(f"lsof -ti tcp:{port} | xargs kill -9")
        elif sys.platform == 'win32':  # Windows
            os.system(f"taskkill /F /PID $(netstat -ano | findstr :{port})")
        else:  # Linux
            os.system(f"fuser -k {port}/tcp")

        # Use Python executable from current environment
        python_path = sys.executable
        streamlit_cmd = [
            python_path, 
            "-m", 
            "streamlit", 
            "run", 
            dashboard_path,
            "--server.port", str(port),
            "--server.address", "localhost",
            "--server.headless", "true",
            "--browser.serverAddress", "localhost",
            "--browser.serverPort", str(port)
        ]
        
        # Launch Streamlit process
        process = subprocess.Popen(
            streamlit_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Wait for Streamlit to start (with timeout)
        start_time = time.time()
        timeout = DASHBOARD_CONFIG['timeout']
        dashboard_url = f"http://localhost:{port}"
        
        while time.time() - start_time < timeout:
            if process.poll() is not None:
                # Process ended prematurely
                stdout, stderr = process.communicate()
                raise dg.DagsterError(f"Streamlit process failed to start:\nStdout: {stdout}\nStderr: {stderr}")
            
            # Try to open the URL
            try:
                import requests
                response = requests.get(dashboard_url)
                if response.status_code == 200:
                    print(f"\n✨ Dashboard is running at {dashboard_url}")
                    print("Keep this terminal window open to maintain the dashboard.")
                    # Open the dashboard in the default browser
                    webbrowser.open(dashboard_url)
                    
                    # Keep the process running
                    while True:
                        if process.poll() is not None:
                            break
                        time.sleep(1)
                    
                    return
            except requests.exceptions.ConnectionError:
                time.sleep(1)
                continue
        
        # If we get here, we timed out
        process.kill()
        raise dg.DagsterError(f"Timed out waiting for Streamlit to start after {timeout} seconds")
        
    except Exception as e:
        raise dg.DagsterError(f"Failed to launch dashboard: {str(e)}")

# Only create and run the Streamlit app if this file is run directly
if __name__ == "__main__":
    create_streamlit_app()