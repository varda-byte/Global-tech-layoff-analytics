import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore")

# ── ML Libraries ──
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import joblib
import os

# ════════════════════════════════════
# PAGE 6 — 🔮 ML LAYOFF TREND PREDICTOR
# ════════════════════════════════════

# ── NOTE: Add this to your sidebar radio options ──
# "🔮 ML Predictor"
# Then call this file's render_ml_page() inside your main app.

# ── HOW TO INTEGRATE ──
# 1. pip install scikit-learn joblib
# 2. Save this file as ml_predictor.py in your project folder
# 3. In your main app.py, add:
#       from ml_predictor import render_ml_page
#       elif page == "🔮 ML Predictor":
#           render_ml_page(run_query)


# ─────────────────────────────────────
# HELPER: Load & prepare data from DB
# ─────────────────────────────────────
@st.cache_data(ttl=3600)
def load_training_data(_run_query):
    """
    Pulls layoff data from your MySQL DB and engineers features for ML.
    Adjust the query if your table/column names differ.
    """
    df = _run_query("""
        SELECT 
            c.company_name,
            i.industry_name,
            l.country,
            e.employees_laid_off,
            e.percentage_laid_off,
            e.layoff_date,
            YEAR(e.layoff_date)  AS year,
            MONTH(e.layoff_date) AS month,
            QUARTER(e.layoff_date) AS quarter
        FROM layoff_events e
        JOIN companies  c ON e.company_id  = c.company_id
        JOIN industries i ON c.industry_id = i.industry_id
        JOIN locations  l ON c.location_id = l.location_id
        WHERE e.employees_laid_off IS NOT NULL
          AND e.layoff_date IS NOT NULL
        ORDER BY e.layoff_date
    """)
    return df


def engineer_features(df):
    """Create ML-ready feature matrix from raw layoff data."""
    df = df.copy()

    # Encode categoricals
    le_industry = LabelEncoder()
    le_country  = LabelEncoder()

    df["industry_enc"] = le_industry.fit_transform(df["industry_name"].astype(str))
    df["country_enc"]  = le_country.fit_transform(df["country"].astype(str))

    # Rolling aggregates (lag features) — industry-level monthly totals
    df["layoff_date"] = pd.to_datetime(df["layoff_date"])
    monthly = (
        df.groupby(["industry_name", "year", "month"])["employees_laid_off"]
        .sum()
        .reset_index()
        .rename(columns={"employees_laid_off": "monthly_industry_total"})
    )
    df = df.merge(monthly, on=["industry_name", "year", "month"], how="left")

    # Feature: is recession period (2022-2023 big layoff wave)
    df["recession_wave"] = df["year"].isin([2022, 2023]).astype(int)

    # Feature: quarter cyclicality (sine/cos encoding)
    df["quarter_sin"] = np.sin(2 * np.pi * df["quarter"] / 4)
    df["quarter_cos"] = np.cos(2 * np.pi * df["quarter"] / 4)

    # Feature: month cyclicality
    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)

    feature_cols = [
        "industry_enc", "country_enc",
        "year", "month", "quarter",
        "recession_wave",
        "quarter_sin", "quarter_cos",
        "month_sin", "month_cos",
        "monthly_industry_total"
    ]

    return df, feature_cols, le_industry, le_country


# ─────────────────────────────────────
# HELPER: Train model
# ─────────────────────────────────────
def train_model(df, feature_cols, model_type="Random Forest"):
    X = df[feature_cols].fillna(0)
    y = df["employees_laid_off"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    models = {
        "Random Forest":        RandomForestRegressor(n_estimators=200, max_depth=10, random_state=42, n_jobs=-1),
        "Gradient Boosting":    GradientBoostingRegressor(n_estimators=150, learning_rate=0.08, max_depth=5, random_state=42),
        "Linear Regression":    LinearRegression(),
    }

    model = models[model_type]
    scaler = StandardScaler()

    if model_type == "Linear Regression":
        X_train_s = scaler.fit_transform(X_train)
        X_test_s  = scaler.transform(X_test)
        model.fit(X_train_s, y_train)
        y_pred = model.predict(X_test_s)
    else:
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

    mae  = mean_absolute_error(y_test, y_pred)
    r2   = r2_score(y_test, y_pred)

    return model, scaler, mae, r2, y_test, y_pred, X_train, X_test


# ─────────────────────────────────────
# HELPER: Predict future months
# ─────────────────────────────────────
def predict_future(model, scaler, le_industry, le_country,
                   industry, country, months_ahead, model_type):
    predictions = []
    today = datetime.today()

    known_industries = list(le_industry.classes_)
    known_countries  = list(le_country.classes_)

    if industry not in known_industries:
        st.warning(f"Industry '{industry}' not in training data. Using closest match.")
        industry = known_industries[0]
    if country not in known_countries:
        st.warning(f"Country '{country}' not in training data. Using closest match.")
        country = known_countries[0]

    for i in range(1, months_ahead + 1):
        future_date = today + timedelta(days=30 * i)
        y = future_date.year
        m = future_date.month
        q = (m - 1) // 3 + 1

        row = {
            "industry_enc":          le_industry.transform([industry])[0],
            "country_enc":           le_country.transform([country])[0],
            "year":                  y,
            "month":                 m,
            "quarter":               q,
            "recession_wave":        int(y in [2022, 2023]),
            "quarter_sin":           np.sin(2 * np.pi * q / 4),
            "quarter_cos":           np.cos(2 * np.pi * q / 4),
            "month_sin":             np.sin(2 * np.pi * m / 12),
            "month_cos":             np.cos(2 * np.pi * m / 12),
            "monthly_industry_total": 0,   # unknown future; set to 0
        }
        X_pred = pd.DataFrame([row])

        if model_type == "Linear Regression":
            X_pred_s = scaler.transform(X_pred)
            pred = model.predict(X_pred_s)[0]
        else:
            pred = model.predict(X_pred)[0]

        predictions.append({
            "month":      future_date.strftime("%b %Y"),
            "date":       future_date,
            "predicted":  max(0, int(pred)),
            "lower":      max(0, int(pred * 0.75)),   # naive confidence band
            "upper":      max(0, int(pred * 1.25)),
        })

    return pd.DataFrame(predictions)


# ─────────────────────────────────────
# MAIN RENDER FUNCTION
# ─────────────────────────────────────
def render_ml_page(run_query):
    st.title("🔮 ML Layoff Trend Predictor")
    st.markdown("Predict future layoff volumes by industry & country using machine learning.")
    st.markdown("---")

    # ── Load Data ──
    with st.spinner("Loading data from database..."):
        try:
            raw_df = load_training_data(run_query)
        except Exception as e:
            st.error(f"❌ DB Error: {e}")
            st.info("Make sure your MySQL connection is active and table names match.")
            return

    if raw_df.empty:
        st.warning("No data found. Check your DB query.")
        return

    df, feature_cols, le_industry, le_country = engineer_features(raw_df)

    # ── Sidebar Controls ──
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔮 ML Settings")

    model_type = st.sidebar.selectbox(
        "Model",
        ["Random Forest", "Gradient Boosting", "Linear Regression"],
        index=0
    )

    industry_options = sorted(raw_df["industry_name"].dropna().unique().tolist())
    country_options  = sorted(raw_df["country"].dropna().unique().tolist())

    selected_industry = st.sidebar.selectbox("Industry to Predict", industry_options)
    selected_country  = st.sidebar.selectbox("Country to Predict", country_options)
    months_ahead      = st.sidebar.slider("Months to Forecast", 1, 24, 6)

    # ── Section 1: Model Performance ──
    st.subheader("📈 Model Training & Accuracy")

    with st.spinner(f"Training {model_type} model..."):
        model, scaler, mae, r2, y_test, y_pred, X_train, X_test = train_model(
            df, feature_cols, model_type
        )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Model",          model_type)
    col2.metric("Training Rows",  f"{len(X_train):,}")
    col3.metric("MAE",            f"{mae:,.0f} employees")
    col4.metric("R² Score",       f"{r2:.3f}")

    # Actual vs Predicted scatter
    fig_acc = go.Figure()
    fig_acc.add_trace(go.Scatter(
        x=y_test.values[:200], y=y_pred[:200],
        mode="markers",
        marker=dict(color="#6366f1", size=5, opacity=0.6),
        name="Predictions"
    ))
    max_val = max(y_test.max(), max(y_pred))
    fig_acc.add_trace(go.Scatter(
        x=[0, max_val], y=[0, max_val],
        mode="lines",
        line=dict(color="#f43f5e", dash="dash"),
        name="Perfect Fit"
    ))
    fig_acc.update_layout(
        title="Actual vs Predicted (test set, first 200 points)",
        xaxis_title="Actual Layoffs",
        yaxis_title="Predicted Layoffs",
        height=380
    )
    st.plotly_chart(fig_acc, use_container_width=True)

    st.markdown("---")

    # ── Section 2: Feature Importance (RF / GB only) ──
    if model_type in ["Random Forest", "Gradient Boosting"]:
        st.subheader("🧠 Feature Importance")
        importance_df = pd.DataFrame({
            "Feature":   feature_cols,
            "Importance": model.feature_importances_
        }).sort_values("Importance", ascending=True)

        fig_imp = px.bar(
            importance_df, x="Importance", y="Feature",
            orientation="h",
            color="Importance",
            color_continuous_scale="Purples",
            title="Which factors drive layoff predictions?"
        )
        fig_imp.update_layout(height=380, showlegend=False)
        st.plotly_chart(fig_imp, use_container_width=True)
        st.markdown("---")

    # ── Section 3: Future Forecast ──
    st.subheader(f"🔭 Forecast: {selected_industry} · {selected_country} · Next {months_ahead} months")

    forecast_df = predict_future(
        model, scaler, le_industry, le_country,
        selected_industry, selected_country,
        months_ahead, model_type
    )

    # Ribbon chart with confidence band
    fig_forecast = go.Figure()
    fig_forecast.add_trace(go.Scatter(
        x=forecast_df["month"], y=forecast_df["upper"],
        mode="lines", line=dict(width=0),
        showlegend=False, name="Upper Bound"
    ))
    fig_forecast.add_trace(go.Scatter(
        x=forecast_df["month"], y=forecast_df["lower"],
        mode="lines", line=dict(width=0),
        fill="tonexty",
        fillcolor="rgba(99,102,241,0.15)",
        showlegend=True, name="Confidence Band (±25%)"
    ))
    fig_forecast.add_trace(go.Scatter(
        x=forecast_df["month"], y=forecast_df["predicted"],
        mode="lines+markers",
        line=dict(color="#6366f1", width=3),
        marker=dict(size=8),
        name="Predicted Layoffs"
    ))
    fig_forecast.update_layout(
        title=f"Predicted Monthly Layoffs — {selected_industry} ({selected_country})",
        xaxis_title="Month",
        yaxis_title="Estimated Employees Laid Off",
        height=420,
        hovermode="x unified"
    )
    st.plotly_chart(fig_forecast, use_container_width=True)

    # Forecast table
    st.subheader("📋 Forecast Table")
    display_df = forecast_df[["month", "predicted", "lower", "upper"]].rename(columns={
        "month":     "Month",
        "predicted": "Predicted Layoffs",
        "lower":     "Lower Estimate",
        "upper":     "Upper Estimate"
    })
    st.dataframe(display_df.style.highlight_max(subset=["Predicted Layoffs"], color="#fde68a"),
                 use_container_width=True)

    # Risk badge
    avg_pred = forecast_df["predicted"].mean()
    st.markdown("---")
    if avg_pred > 5000:
        st.error(f"🔴 **HIGH RISK** — Avg predicted layoffs: {avg_pred:,.0f}/month for this segment.")
    elif avg_pred > 1000:
        st.warning(f"🟡 **MODERATE RISK** — Avg predicted layoffs: {avg_pred:,.0f}/month for this segment.")
    else:
        st.success(f"🟢 **LOW RISK** — Avg predicted layoffs: {avg_pred:,.0f}/month for this segment.")

    # ── Section 4: Historical Trend for context ──
    st.markdown("---")
    st.subheader("📉 Historical Trend — " + selected_industry)

    hist = raw_df[raw_df["industry_name"] == selected_industry].copy()
    hist["layoff_date"] = pd.to_datetime(hist["layoff_date"])
    hist_monthly = (
        hist.groupby(hist["layoff_date"].dt.to_period("M"))["employees_laid_off"]
        .sum()
        .reset_index()
    )
    hist_monthly["layoff_date"] = hist_monthly["layoff_date"].dt.to_timestamp()

    fig_hist = px.area(
        hist_monthly, x="layoff_date", y="employees_laid_off",
        title=f"Monthly Layoffs — {selected_industry} (Historical)",
        color_discrete_sequence=["#f43f5e"]
    )
    fig_hist.update_layout(height=320)
    st.plotly_chart(fig_hist, use_container_width=True)
