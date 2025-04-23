"""
Budget forecasting service.
Provides functions for predicting future budget needs.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from statsmodels.tsa.arima.model import ARIMA
from sklearn.linear_model import LinearRegression
import logging

def forecast_budget_needs(historical_data, forecast_months=6):
    """
    Forecast budget needs for upcoming months.
    
    Args:
        historical_data: List of dictionaries with 'month', 'year', and 'amount' keys
        forecast_months: Number of months to forecast
        
    Returns:
        dict: Forecast results
    """
    try:
        # Convert to pandas DataFrame
        df = pd.DataFrame(historical_data)
        
        # Ensure data is sorted chronologically
        df['date'] = pd.to_datetime(df['year'].astype(str) + '-' + df['month'].astype(str) + '-01')
        df = df.sort_values('date')
        
        # Set date as index
        df.set_index('date', inplace=True)
        
        # Check if we have enough data
        if len(df) < 4:
            return {
                "success": False,
                "message": "Insufficient historical data for accurate forecasting",
                "forecast": []
            }
            
        # Simple time series forecasting with ARIMA
        try:
            # Fit ARIMA model
            model = ARIMA(df['amount'], order=(1, 1, 1))
            model_fit = model.fit()
            
            # Generate forecast
            last_date = df.index[-1]
            forecast_index = pd.date_range(start=last_date + timedelta(days=32), periods=forecast_months, freq='MS')
            forecast = model_fit.forecast(steps=forecast_months)
            
            # Create forecast result
            forecast_data = []
            for i, date in enumerate(forecast_index):
                forecast_data.append({
                    "year": date.year,
                    "month": date.month,
                    "forecasted_amount": max(0, round(forecast[i], 2))  # Ensure positive values
                })
            
            return {
                "success": True,
                "message": "Forecast generated successfully",
                "forecast": forecast_data,
                "confidence_level": "medium"
            }
            
        except Exception as e:
            logging.warning(f"ARIMA forecast failed: {str(e)}. Falling back to simpler model.")
            
            # Fallback to simpler linear regression
            df['month_num'] = range(1, len(df) + 1)
            X = df[['month_num']]
            y = df['amount']
            
            model = LinearRegression()
            model.fit(X, y)
            
            # Generate future month numbers
            future_months = range(len(df) + 1, len(df) + forecast_months + 1)
            
            # Generate forecast
            last_date = df.index[-1]
            forecast_index = pd.date_range(start=last_date + timedelta(days=32), periods=forecast_months, freq='MS')
            forecast = model.predict([[month] for month in future_months])
            
            # Create forecast result
            forecast_data = []
            for i, date in enumerate(forecast_index):
                forecast_data.append({
                    "year": date.year,
                    "month": date.month,
                    "forecasted_amount": max(0, round(forecast[i], 2))  # Ensure positive values
                })
            
            return {
                "success": True,
                "message": "Forecast generated using linear regression",
                "forecast": forecast_data,
                "confidence_level": "low"
            }
            
    except Exception as e:
        logging.error(f"Error forecasting budget: {str(e)}")
        return {
            "success": False,
            "message": f"Error forecasting budget: {str(e)}",
            "forecast": []
        }

def analyze_spending_patterns(historical_data):
    """
    Analyze spending patterns and identify trends.
    
    Args:
        historical_data: List of spending records with dates and amounts
        
    Returns:
        dict: Analysis results
    """
    try:
        # Convert to pandas DataFrame
        df = pd.DataFrame(historical_data)
        
        # Ensure we have date column
        if 'date' not in df.columns and 'month' in df.columns and 'year' in df.columns:
            df['date'] = pd.to_datetime(df['year'].astype(str) + '-' + df['month'].astype(str) + '-01')
        elif 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        else:
            return {
                "success": False,
                "message": "Date information missing in historical data",
                "analysis": {}
            }
        
        # Extract month and year components
        df['month'] = df['date'].dt.month
        df['year'] = df['date'].dt.year
        
        # Monthly analysis
        monthly_avg = df.groupby('month')['amount'].mean().to_dict()
        
        # Find peak spending months
        peak_month = max(monthly_avg.items(), key=lambda x: x[1])
        low_month = min(monthly_avg.items(), key=lambda x: x[1])
        
        # Year-over-year analysis
        if len(df['year'].unique()) > 1:
            yearly_growth = {}
            years = sorted(df['year'].unique())
            for i in range(1, len(years)):
                prev_year = years[i-1]
                curr_year = years[i]
                prev_amount = df[df['year'] == prev_year]['amount'].sum()
                curr_amount = df[df['year'] == curr_year]['amount'].sum()
                
                if prev_amount > 0:
                    growth_pct = ((curr_amount - prev_amount) / prev_amount) * 100
                    yearly_growth[f"{prev_year}-{curr_year}"] = round(growth_pct, 2)
        else:
            yearly_growth = None
        
        # Identify any anomalies (amounts more than 2 standard deviations from mean)
        mean_amount = df['amount'].mean()
        std_amount = df['amount'].std()
        threshold = mean_amount + (2 * std_amount)
        
        anomalies = df[df['amount'] > threshold].to_dict('records')
        
        # Season trends
        df['season'] = df['month'].apply(lambda m: 
            'Winter' if m in [12, 1, 2] else
            'Spring' if m in [3, 4, 5] else
            'Summer' if m in [6, 7, 8] else 'Fall'
        )
        
        seasonal_avg = df.groupby('season')['amount'].mean().to_dict()
        
        # Return analysis results
        return {
            "success": True,
            "message": "Analysis completed successfully",
            "analysis": {
                "monthly_averages": {k: round(v, 2) for k, v in monthly_avg.items()},
                "peak_spending_month": {
                    "month": peak_month[0],
                    "average_amount": round(peak_month[1], 2)
                },
                "lowest_spending_month": {
                    "month": low_month[0],
                    "average_amount": round(low_month[1], 2)
                },
                "yearly_growth": yearly_growth,
                "anomalies_count": len(anomalies),
                "seasonal_trends": {k: round(v, 2) for k, v in seasonal_avg.items()}
            }
        }
        
    except Exception as e:
        logging.error(f"Error analyzing spending patterns: {str(e)}")
        return {
            "success": False,
            "message": f"Error analyzing spending patterns: {str(e)}",
            "analysis": {}
        }