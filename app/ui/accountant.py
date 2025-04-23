"""
Accountant UI module.
Handles the UI components for the accountant role.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import logging

from app.ui.common import (
    display_header,
    display_info_box,
    display_success_box,
    display_warning_box,
    display_error_box,
    show_loading_spinner
)
from app.database.queries import (
    get_budget_info,
    update_budget,
    get_budget_history,
    calculate_remaining_budget,
    get_department_spending,
    get_requests_by_status,
    get_requests_by_month,
    get_user_requests,
    get_budget_by_year,
    get_expense_data_for_year
)
from app.services.report_service import generate_budget_report

def show_accountant_dashboard():
    """Accountant main dashboard"""
    display_header("Accountant Dashboard")
    
    # Show tabs for different accountant functions
    tabs = st.tabs([
        "Budget Management", 
        "Expense Reports", 
        "Financial Analytics"
    ])
    
    # Tab 1: Budget Management
    with tabs[0]:
        show_budget_management()
    
    # Tab 2: Expense Reports
    with tabs[1]:
        show_expense_reports()
    
    # Tab 3: Financial Analytics
    with tabs[2]:
        show_financial_analytics()

def show_budget_management():
    """Display budget management interface"""
    st.subheader("Budget Management")
    
    # Show current budget info
    budget_info = get_budget_info()
    total_budget, total_expenses, remaining_budget = calculate_remaining_budget()
    
    # Create budget summary cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(
            f"""
            <div style="border-radius:10px; padding:20px; background-color:#E8F4F8; text-align:center;">
                <h3 style="margin:0; color:#1E88E5;">Total Budget</h3>
                <h1 style="margin:10px 0; color:#0D47A1;">${total_budget:,.2f}</h1>
                <p style="margin:0; color:#1976D2;">Fiscal Year {budget_info['year'] if budget_info else datetime.now().year}</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with col2:
        st.markdown(
            f"""
            <div style="border-radius:10px; padding:20px; background-color:#E8F5E9; text-align:center;">
                <h3 style="margin:0; color:#43A047;">Allocated Budget</h3>
                <h1 style="margin:10px 0; color:#2E7D32;">${total_expenses:,.2f}</h1>
                <p style="margin:0; color:#388E3C;">{total_expenses/total_budget*100:.1f}% of Total Budget</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with col3:
        st.markdown(
            f"""
            <div style="border-radius:10px; padding:20px; background-color:#{"FFF3E0" if remaining_budget < total_budget*0.2 else "FFF8E1"}; text-align:center;">
                <h3 style="margin:0; color:#{"FB8C00" if remaining_budget < total_budget*0.2 else "FFA000"};">Remaining Budget</h3>
                <h1 style="margin:10px 0; color:#{"E65100" if remaining_budget < total_budget*0.2 else "FF8F00"};">${remaining_budget:,.2f}</h1>
                <p style="margin:0; color:#{"F57C00" if remaining_budget < total_budget*0.2 else "FFB300"};">{remaining_budget/total_budget*100:.1f}% Available</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    # Budget update form
    st.subheader("Update Budget")
    
    with st.form("budget_update_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            year = st.number_input(
                "Budget Year",
                min_value=2020,
                max_value=2030,
                value=datetime.now().year,
                step=1,
                help="The fiscal year for this budget"
            )
        
        with col2:
            period = st.selectbox(
                "Budget Period",
                options=["Annual", "Q1", "Q2", "Q3", "Q4"],
                index=0,
                help="The budget period"
            )
        
        amount = st.number_input(
            "Budget Amount (USD)",
            min_value=1000,
            max_value=10000000,
            value=int(total_budget) if total_budget else 100000,
            step=1000,
            help="The total budget amount for the selected period"
        )
        
        notes = st.text_area(
            "Budget Notes",
            help="Optional notes about this budget update"
        )
        
        submitted = st.form_submit_button("Update Budget")
        
        if submitted:
            try:
                user_id = st.session_state.logged_in_user
                success = update_budget(year, period, amount, user_id)
                
                if success:
                    display_success_box("Budget updated successfully!")
                    st.experimental_rerun()
                else:
                    st.error("Failed to update budget. Please try again.")
            
            except Exception as e:
                logging.error(f"Error updating budget: {str(e)}")
                st.error(f"An error occurred: {str(e)}")
    
    # Budget history
    st.subheader("Budget History")
    
    budget_history = get_budget_history()
    
    if budget_history:
        # Prepare data for display
        history_df = pd.DataFrame(budget_history)
        
        # Format dates for display
        history_df['modified_at'] = pd.to_datetime(history_df['modified_at']).dt.strftime('%Y-%m-%d %H:%M')
        
        # Select columns for display
        display_df = history_df[[
            'year', 'period', 'amount', 'modifier_name', 'modified_at'
        ]]
        
        # Rename columns for better display
        display_df.columns = [
            'Year', 'Period', 'Amount (USD)', 'Modified By', 'Modified On'
        ]
        
        # Display the dataframe
        st.dataframe(display_df, use_container_width=True)
    else:
        display_info_box("No budget history found.")
    
    # Budget report download
    st.subheader("Download Budget Report")
    download_budget_report()

def download_budget_report():
    """Generate and download a budget report PDF"""
    # Get current year
    current_year = datetime.now().year
    
    # Get budget data
    budget_data = get_budget_by_year(current_year)
    
    if not budget_data:
        display_error_box("Budget information not found for the current year.")
        return
    
    # Get expense data
    expenses_data = get_expense_data_for_year(current_year)
    
    # Generate PDF
    try:
        pdf_buffer = generate_budget_report(budget_data, expenses_data, current_year)
        
        # Provide download link
        st.download_button(
            label="Download Budget Report",
            data=pdf_buffer,
            file_name=f"budget_report_{current_year}.pdf",
            mime="application/pdf"
        )
        
    except Exception as e:
        display_error_box(f"Error generating budget report: {str(e)}")

def show_expense_reports():
    """Display expense reports interface"""
    st.subheader("Expense Reports")
    
    # Get department spending data
    department_spending = get_department_spending()
    
    if department_spending:
        # Prepare data for display
        spending_df = pd.DataFrame(department_spending)
        
        # Rename columns for better display
        spending_df.columns = ['Department', 'Total Expense (USD)']
        
        # Sort by expense amount
        spending_df = spending_df.sort_values('Total Expense (USD)', ascending=False)
        
        # Display the dataframe
        st.dataframe(spending_df, use_container_width=True)
        
        # Create bar chart for department spending
        st.subheader("Department Spending Breakdown")
        
        fig = px.bar(
            spending_df,
            x='Department',
            y='Total Expense (USD)',
            color='Department',
            text='Total Expense (USD)',
            height=500
        )
        
        fig.update_traces(
            texttemplate='$%{text:,.2f}',
            textposition='outside'
        )
        
        fig.update_layout(
            xaxis_title="Department",
            yaxis_title="Total Expense (USD)",
            xaxis={'categoryorder': 'total descending'}
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        display_info_box("No department spending data available.")
    
    # Get recent approved requests
    recent_approved = get_user_requests(None, 'approved', 10)
    
    if recent_approved:
        st.subheader("Recently Approved Expenses")
        
        # Prepare data for display
        recent_df = pd.DataFrame(recent_approved)
        
        # Format dates for display
        recent_df['date_from'] = pd.to_datetime(recent_df['date_from']).dt.strftime('%Y-%m-%d')
        recent_df['date_to'] = pd.to_datetime(recent_df['date_to']).dt.strftime('%Y-%m-%d')
        recent_df['created_at'] = pd.to_datetime(recent_df['created_at']).dt.strftime('%Y-%m-%d')
        
        # Add total cost column
        recent_df['total_cost'] = recent_df['per_diem'] + recent_df['registration_fee'] + recent_df['visa_fee']
        
        # Get faculty names for display
        faculty_names = {}
        for req in recent_approved:
            try:
                from app.database.queries import get_user_by_id
                faculty = get_user_by_id(req['faculty_user_id'])
                if faculty:
                    faculty_names[req['faculty_user_id']] = faculty['name']
            except Exception:
                faculty_names[req['faculty_user_id']] = req['faculty_user_id']
        
        recent_df['faculty_name'] = recent_df['faculty_user_id'].map(faculty_names)
        
        # Select columns for display
        display_df = recent_df[[
            'faculty_name', 'conference_name', 'destination', 'date_from', 'date_to',
            'per_diem', 'registration_fee', 'visa_fee', 'total_cost'
        ]]
        
        # Rename columns for better display
        display_df.columns = [
            'Faculty Member', 'Conference', 'Destination', 'Start Date', 'End Date',
            'Per Diem', 'Registration Fee', 'Visa Fee', 'Total Cost'
        ]
        
        # Display the dataframe
        st.dataframe(display_df, use_container_width=True)
    else:
        display_info_box("No recently approved expenses.")

def show_financial_analytics():
    """Display financial analytics interface"""
    st.subheader("Financial Analytics")
    
    # Get monthly expense data
    monthly_data = get_requests_by_month()
    status_data = get_requests_by_status()
    
    if monthly_data:
        # Prepare data for display
        monthly_df = pd.DataFrame(monthly_data)
        
        # Create month names
        month_names = {
            1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
            7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
        }
        
        monthly_df['month_name'] = monthly_df['month'].map(month_names)
        
        # Create line chart for monthly requests
        st.subheader("Monthly Request Trends")
        
        fig = px.line(
            monthly_df,
            x='month_name',
            y='count',
            markers=True,
            line_shape='linear',
            height=400
        )
        
        fig.update_layout(
            xaxis_title="Month",
            yaxis_title="Number of Requests",
            xaxis={'categoryorder': 'array', 'categoryarray': list(month_names.values())}
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    if status_data:
        # Prepare data for display
        status_df = pd.DataFrame(status_data)
        
        # Create pie chart for request status distribution
        st.subheader("Request Status Distribution")
        
        fig = px.pie(
            status_df,
            values='count',
            names='status',
            color='status',
            color_discrete_map={
                'approved': '#28a745',
                'rejected': '#dc3545',
                'pending': '#ffc107',
                'completed': '#17a2b8'
            },
            hole=0.4
        )
        
        fig.update_layout(
            legend_title="Status",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Budget utilization over time
    st.subheader("Budget Utilization")
    
    # Get current budget information
    total_budget, total_expenses, remaining_budget = calculate_remaining_budget()
    
    # Create gauge chart for budget utilization
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=total_expenses,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Budget Utilization", 'font': {'size': 24}},
        delta={'reference': 0, 'position': "top"},
        gauge={
            'axis': {'range': [0, total_budget], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "royalblue"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, total_budget * 0.5], 'color': 'lightgreen'},
                {'range': [total_budget * 0.5, total_budget * 0.8], 'color': 'lightyellow'},
                {'range': [total_budget * 0.8, total_budget], 'color': 'lightcoral'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': total_budget * 0.9
            }
        }
    ))
    
    fig.update_layout(
        height=400,
        margin=dict(l=60, r=60, t=80, b=30)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Add budget vs expense comparison
    st.subheader("Budget vs. Expenses")
    
    budget_comparison = {
        'Category': ['Total Budget', 'Allocated Budget', 'Remaining Budget'],
        'Amount': [total_budget, total_expenses, remaining_budget]
    }
    
    budget_comp_df = pd.DataFrame(budget_comparison)
    
    fig = px.bar(
        budget_comp_df,
        x='Category',
        y='Amount',
        color='Category',
        color_discrete_map={
            'Total Budget': '#4285F4',
            'Allocated Budget': '#EA4335',
            'Remaining Budget': '#34A853'
        },
        text='Amount',
        height=400
    )
    
    fig.update_traces(
        texttemplate='$%{text:,.2f}',
        textposition='outside'
    )
    
    fig.update_layout(
        xaxis_title="",
        yaxis_title="Amount (USD)"
    )
    
    st.plotly_chart(fig, use_container_width=True)