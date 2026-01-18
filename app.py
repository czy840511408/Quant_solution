import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# Page Config
st.set_page_config(layout="wide", page_title="Institutional Portfolio Analytics")

# CSS for better styling
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# Data Loader
@st.cache_data
def load_data():
    perf = pd.read_csv('portfolio_performance.csv', parse_dates=['Date'], index_col='Date')
    attr = pd.read_csv('attribution_results.csv', index_col=0)
    weights = pd.read_csv('sector_weights.csv', index_col=0)
    return perf, attr, weights

if not os.path.exists('portfolio_performance.csv'):
    st.error("Missing data files. Please run the export block in your notebook first.")
    st.stop()

df_perf, df_attr, df_weights = load_data()

# --- SIDEBAR ---
st.sidebar.title("Configuration")
date_range = st.sidebar.date_input("Analysis Period", 
                                   value=(df_perf.index.min(), df_perf.index.max()),
                                   min_value=df_perf.index.min(),
                                   max_value=df_perf.index.max())

# --- MAIN HEADER ---
st.title("📈 Portfolio Performance & Attribution")
st.caption(f"Analysis Period: {date_range[0]} to {date_range[1]}")

# --- KEY METRICS ---
m1, m2, m3, m4 = st.columns(4)
final_nav_opt = df_perf['Optimized'].iloc[-1]
final_nav_bm = df_perf['Benchmark'].iloc[-1]

m1.metric("Total Return (Opt)", f"{(final_nav_opt-1):.2%}")
m2.metric("Benchmark Return", f"{(final_nav_bm-1):.2%}")
m3.metric("Active Return (Alpha)", f"{(final_nav_opt/final_nav_bm-1):.2%}", 
          delta=f"{(final_nav_opt/final_nav_bm - df_perf['Original'].iloc[-1]/final_nav_bm):.2%} vs Orig")
m4.metric("Volatility (Ann.)", f"{(df_perf['Optimized'].pct_change().std() * (252**0.5)):.2%}")

# --- TABS SYSTEM ---
tab1, tab2, tab3 = st.tabs(["📊 Performance", "🎯 Brinson Attribution", "⚖️ Portfolio Composition"])

with tab1:
    st.subheader("Cumulative Performance")
    fig_nav = px.line(df_perf, y=['Benchmark', 'Original', 'Optimized'],
                      labels={'value': 'NAV', 'Date': 'Date'},
                      color_discrete_map={'Benchmark': '#94a3b8', 'Original': '#cbd5e1', 'Optimized': '#2563eb'})
    fig_nav.update_layout(hovermode="x unified", legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig_nav, use_container_width=True)

    st.subheader("Alpha Evolution (Active Return vs Benchmark)")
    fig_alpha = px.area(df_perf, x=df_perf.index, y='Optimized_Alpha', 
                        title="Alpha Evolution",
                        labels={'Optimized_Alpha': 'Alpha (%)'})
    st.plotly_chart(fig_alpha, use_container_width=True)

with tab2:
    st.subheader("Brinson-Fachler Attribution Analysis")
    col_a, col_b = st.columns([1, 3])
    
    with col_a:
        view_type = st.radio("View Effect:", ['Total', 'Allocation', 'Selection', 'Interaction'])
        st.info("Selection Effect usually dominates in high-conviction tech portfolios.")

    with col_b:
        fig_attr = px.bar(df_attr.reset_index(), x='SEIndustryGroup', y=view_type,
                          title=f"{view_type} Effect by Sector",
                          color=view_type, color_continuous_scale='RdYlGn')
        st.plotly_chart(fig_attr, use_container_width=True)
    
    st.dataframe(df_attr.style.format("{:.2%}").background_gradient(cmap='RdYlGn'))

with tab3:
    st.subheader("Sector Exposure Comparison")
    df_w_plot = df_weights.reset_index().melt(id_vars='Industry', var_name='Type', value_name='Weight')
    fig_w = px.bar(df_w_plot, x='Industry', y='Weight', color='Type', 
                   barmode='group', color_discrete_map={'Benchmark': '#94a3b8', 'Original': '#cbd5e1', 'Optimized': '#2563eb'})
    st.plotly_chart(fig_w, use_container_width=True)
    
    st.subheader("Active Weight (Over/Underweight)")
    df_weights['Active_Weight'] = df_weights['Optimized'] - df_weights['Benchmark']
    fig_aw = px.bar(df_weights.reset_index(), x='Industry', y='Active_Weight',
                    color='Active_Weight', color_continuous_scale='Geyser')
    st.plotly_chart(fig_aw, use_container_width=True)