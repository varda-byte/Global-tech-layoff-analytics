from ml_predictor import render_ml_page
import streamlit as st
import mysql.connector
import pandas as pd
import plotly.express as px

# ── Page Config ──
st.set_page_config(
    page_title="Global Tech Layoff Analytics",
    page_icon="📊",
    layout="wide"
)

# ── Connect to MySQL ──
@st.cache_resource
def get_connection():
    return mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="root123",
        database="layoff_analytics"
    )

def run_query(query):
    conn = get_connection()
    return pd.read_sql(query, conn)

# ── Sidebar ──
st.sidebar.title("📊 Global Tech Layoff Analytics")
st.sidebar.markdown("---")
page = st.sidebar.radio("Navigation", [
    "Dashboard",
    "Company Analysis",
    "Industry Trends",
    "Geography",
    "ML Predictor",
    "SQL Explorer"
])

# ════════════════════════════════════
# PAGE 1 — DASHBOARD
# ════════════════════════════════════
if page == "Dashboard":
    st.title("📊 Global Tech Layoff Analytics")
    st.markdown("Real-world workforce disruption data — 2020 to 2024")
    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)
    
    total = run_query("SELECT SUM(employees_laid_off) as total FROM layoff_events WHERE employees_laid_off IS NOT NULL")
    companies = run_query("SELECT COUNT(DISTINCT company_id) as total FROM companies")
    industries = run_query("SELECT COUNT(*) as total FROM industries")
    countries = run_query("SELECT COUNT(DISTINCT country) as total FROM locations")

    col1.metric("Total Layoffs", f"{int(total['total'][0]):,}")
    col2.metric("Companies", f"{int(companies['total'][0]):,}")
    col3.metric("Industries", f"{int(industries['total'][0]):,}")
    col4.metric("Countries", f"{int(countries['total'][0]):,}")

    st.markdown("---")

    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📅 Layoffs by Year")
        yearly = run_query("""
            SELECT YEAR(layoff_date) AS year,
                   SUM(employees_laid_off) AS total_laid_off
            FROM layoff_events
            WHERE layoff_date IS NOT NULL
            AND employees_laid_off IS NOT NULL
            GROUP BY YEAR(layoff_date)
            ORDER BY year
        """)
        fig = px.bar(yearly, x='year', y='total_laid_off',
                    color='total_laid_off',
                    color_continuous_scale='Blues')
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("🏭 Top Industries")
        industry = run_query("""
            SELECT i.industry_name,
                   SUM(e.employees_laid_off) AS total_laid_off
            FROM layoff_events e
            JOIN companies c ON e.company_id = c.company_id
            JOIN industries i ON c.industry_id = i.industry_id
            WHERE e.employees_laid_off IS NOT NULL
            GROUP BY i.industry_name
            ORDER BY total_laid_off DESC
            LIMIT 10
        """)
        fig2 = px.pie(industry, values='total_laid_off',
                     names='industry_name')
        st.plotly_chart(fig2, use_container_width=True)

# ════════════════════════════════════
# PAGE 2 — COMPANY ANALYSIS
# ════════════════════════════════════
elif page == "Company Analysis":
    st.title("🏢 Company Analysis")
    st.markdown("---")

    top_companies = run_query("""
        SELECT c.company_name,
               SUM(e.employees_laid_off) AS total_laid_off,
               COUNT(*) AS layoff_rounds
        FROM layoff_events e
        JOIN companies c ON e.company_id = c.company_id
        WHERE e.employees_laid_off IS NOT NULL
        GROUP BY c.company_name
        ORDER BY total_laid_off DESC
        LIMIT 20
    """)

    fig = px.bar(top_companies, 
                x='total_laid_off', 
                y='company_name',
                orientation='h',
                title='Top 20 Companies by Total Layoffs',
                color='total_laid_off',
                color_continuous_scale='Reds')
    fig.update_layout(height=600)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Companies with Multiple Layoff Rounds")
    multiple = run_query("""
        SELECT c.company_name,
               COUNT(*) AS layoff_rounds,
               SUM(e.employees_laid_off) AS total_laid_off
        FROM layoff_events e
        JOIN companies c ON e.company_id = c.company_id
        WHERE e.employees_laid_off IS NOT NULL
        GROUP BY c.company_name
        HAVING layoff_rounds > 1
        ORDER BY layoff_rounds DESC
        LIMIT 15
    """)
    st.dataframe(multiple, use_container_width=True)
    st.download_button("📥 Download CSV", multiple.to_csv(index=False),
                    "company_analysis.csv", "text/csv")

# ════════════════════════════════════
# PAGE 3 — INDUSTRY TRENDS
# ════════════════════════════════════
elif page == "Industry Trends":
    st.title("🏭 Industry Trends")
    st.markdown("---")

    industry_data = run_query("""
        SELECT i.industry_name,
               SUM(e.employees_laid_off) AS total_laid_off,
               COUNT(*) AS total_events,
               ROUND(AVG(e.percentage_laid_off) * 100, 2) AS avg_percentage
        FROM layoff_events e
        JOIN companies c ON e.company_id = c.company_id
        JOIN industries i ON c.industry_id = i.industry_id
        WHERE e.employees_laid_off IS NOT NULL
        GROUP BY i.industry_name
        ORDER BY total_laid_off DESC
    """)

    fig = px.bar(industry_data,
                x='industry_name',
                y='total_laid_off',
                title='Total Layoffs by Industry',
                color='total_laid_off',
                color_continuous_scale='Viridis')
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("Industry Details")
    st.dataframe(industry_data, use_container_width=True)
    st.download_button("📥 Download CSV", industry_data.to_csv(index=False), 
                   "industry_trends.csv", "text/csv")

# ════════════════════════════════════
# PAGE 4 — GEOGRAPHY
# ════════════════════════════════════
elif page == "Geography":
    st.title("🌍 Geographic Analysis")
    st.markdown("---")

    country_data = run_query("""
        SELECT l.country,
               SUM(e.employees_laid_off) AS total_laid_off,
               COUNT(*) AS total_events
        FROM layoff_events e
        JOIN companies c ON e.company_id = c.company_id
        JOIN locations l ON c.location_id = l.location_id
        WHERE e.employees_laid_off IS NOT NULL
        GROUP BY l.country
        ORDER BY total_laid_off DESC
    """)

    fig = px.choropleth(country_data,
                       locations='country',
                       locationmode='country names',
                       color='total_laid_off',
                       title='Global Tech Layoffs by Country',
                       color_continuous_scale='Blues')
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Top 15 Countries")
    st.dataframe(country_data.head(15), use_container_width=True)
    st.download_button("📥 Download CSV", country_data.to_csv(index=False), 
                   "geography.csv", "text/csv")

# ════════════════════════════════════
# PAGE 5 — ML PREDICTOR
# ════════════════════════════════════
elif page == "ML Predictor":
    render_ml_page(run_query)

# ════════════════════════════════════
# PAGE 6 — SQL EXPLORER
# ════════════════════════════════════
elif page == "SQL Explorer":
    st.title("🔍 SQL Explorer")
    st.markdown("Run your own SQL queries live!")
    st.markdown("---")

    query = st.text_area("Enter your SQL query:", 
                         value="SELECT * FROM layoffs_staging LIMIT 10;",
                         height=150)
    
    if st.button("▶ Run Query"):
        try:
            result = run_query(query)
            st.success(f"Query returned {len(result)} rows")
            st.dataframe(result, use_container_width=True)
            st.download_button("📥 Download CSV", result.to_csv(index=False), 
                   "query_results.csv", "text/csv")
        except Exception as e:
            st.error(f"Error: {e}")