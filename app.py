import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide", page_title="Dashboard")

@st.cache_data
def load_data():
    return (
        pd.read_csv('raw_signals.csv', index_col=0),
        pd.read_csv('correlation_matrix.csv', index_col=0),
        pd.read_csv('stock_cumulative_returns.csv', index_col=0, parse_dates=True),
        pd.read_csv('portfolio_performance.csv', index_col=0, parse_dates=True),
        pd.read_csv('attribution_results.csv', index_col=0),
        pd.read_csv('stock_details.csv', index_col=0),
        pd.read_csv('parameter_search.csv')
    )

df_sig, df_corr, df_stock_nav, df_perf, df_attr, df_stocks, df_params = load_data()

st.title("Visualization Dashboard")
st.divider()

t1, t2, t3, t4 = st.tabs(["Data Exploration", "Optimization details", "Performance & Risk", "Attribution"])

with t1:
    st.subheader("Weight Distribution")
    
    st.write("**Weight: Sector > Stock (Click to Drill-Down)**")
    df_weights = pd.read_csv('PortfolioBenchmarkWeights.csv').merge(df_sig[['Industry']], left_on='ID', right_index=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.caption("Benchmark Structure")
        fig = px.sunburst(df_weights, path=['Industry', 'ID'], values='WeightBm', 
                         color='Industry', 
                         hover_data={'WeightBm': ':.2%', 'ID': True, 'Industry': True})
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.caption("Original Portfolio Structure")
        fig = px.sunburst(df_weights, path=['Industry', 'ID'], values='WeightPf', 
                         color='Industry',
                         hover_data={'WeightPf': ':.2%', 'ID': True, 'Industry': True})
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    st.write("**Alpha Signal: Expected vs. Realized Returns**")
    df_ic = df_sig[['Alpha_Signal', 'Industry']].merge(df_stocks[['Realized_Ret']], left_index=True, right_index=True)
    ic = df_ic['Alpha_Signal'].corr(df_ic['Realized_Ret'])
    st.metric("Information Coefficient (IC)", f"{ic:.3f}")
    
    fig = px.scatter(df_ic.reset_index(), x='Alpha_Signal', y='Realized_Ret', trendline="ols", 
                    color='Industry', hover_name='ID',
                    labels={'Alpha_Signal': 'Expected Return (Alpha)', 'Realized_Ret': 'Realized Return'})
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    col1, col2 = st.columns([1.2, 0.8])
    with col1:
        st.write("**Asset Cumulative Returns**")
        fig = px.line(df_stock_nav, labels={'value': 'NAV', 'Date_': 'Date'})
        fig.update_layout(hovermode="x unified", legend=dict(orientation='h', y=1.05))
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.write("**Alpha Signal (Expected Return)**")
        df_sorted = df_sig.sort_values('Alpha_Signal', ascending=True).reset_index()
        fig = px.bar(df_sorted, y='ID', x='Alpha_Signal', orientation='h', color='Industry')
        fig.update_layout(yaxis=dict(categoryorder='array', categoryarray=df_sorted['ID'].tolist()))
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.write("**Correlation Matrix**")
    fig = px.imshow(df_corr, color_continuous_scale='RdBu_r', zmin=-1, zmax=1, text_auto=".2f")
    fig.update_layout(height=700)
    st.plotly_chart(fig, use_container_width=True)

with t2:
    st.subheader("Parameter Sensitivity")
    
    metric = st.radio("Select Metric:", ['Sharpe', 'Active_Return'], horizontal=True)
    df_filtered = df_params[df_params['Lambda'] < 0.0001]
    
    pivot = df_filtered.pivot(index='Gamma', columns='Limit', values=metric)
    st.plotly_chart(px.imshow(pivot, text_auto=".2f" if metric=='Sharpe' else ".2%", 
                             color_continuous_scale='Viridis' if metric=='Sharpe' else 'RdYlGn',
                             aspect="auto"), use_container_width=True)
    
    st.divider()
    st.write("**Active Frontier (Risk vs. Return)**")
    st.plotly_chart(px.scatter(df_filtered, x='Active_Risk', y='Active_Return', 
                              color='Sharpe', size='Sharpe', hover_data=['Gamma', 'Limit'],
                              labels={'Active_Risk':'Tracking Error', 'Active_Return':'Alpha'}), 
                   use_container_width=True)

with t3:
    st.subheader("Performance vs Benchmark & Naive Alpha")
    fig = px.line(df_perf[['Benchmark', 'Original', 'Optimized', 'Naive_Alpha']])
    fig.update_layout(hovermode="x unified", title="NAV Comparison")
    st.plotly_chart(fig, use_container_width=True)
    
    st.write("**Cumulative Active Return**")
    fig = px.area(df_perf, y='Active Return')
    st.plotly_chart(fig, use_container_width=True)

with t4:
    st.subheader("Brinson-Fachler Attribution (Industry Level)")
    fig = px.bar(df_attr.reset_index(), x='Sector', y=['Selection', 'Allocation', 'Interaction'],
                barmode='group', title="Decomposition of Excess Return")
    st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    st.subheader("Stock-level Contribution Details")
    df_disp = df_stocks.reset_index()
    id_col = 'ID'
    df_disp['Position'] = df_disp['Active_Weight'].gt(0).map({True: "Overweight", False: "Underweight"})
    df_disp = df_disp.sort_values('Contribution', ascending=False)

    st.dataframe(
        df_disp[[id_col, 'Industry', 'Position', 'Active_Weight', 'Realized_Ret', 'Contribution']]
        .style.format({
            'Active_Weight': '{:+.2%}',
            'Realized_Ret': '{:.2%}',
            'Contribution': '{:+.4%}'
        })
        .background_gradient(subset=['Contribution'], cmap='RdYlGn', vmin=-0.01, vmax=0.01),
        use_container_width=True
    )
