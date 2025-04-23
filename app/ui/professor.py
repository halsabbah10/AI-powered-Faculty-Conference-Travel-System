"""
Professor UI module.
Handles the UI components for the professor role.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
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
    get_user_requests,
    create_request,
    get_budget_info,
    calculate_remaining_budget,
    save_document,
    get_request_by_id,
    get_user_by_id
)
from app.services.document_service import (
    extract_text_from_file,
    validate_file,
    get_autofill
)
from app.services.ai_service import (
    validate_with_gpt,
    get_conference_recommendations,
    analyze_research_paper,
    generate_ai_notes,
    generate_conference_summary
)
from app.services.report_service import generate_request_pdf
from app.utils.security import sanitize_input

def show_professor_dashboard():
    """Professor main dashboard"""
    display_header("Professor Dashboard")
    
    # Show tabs for different professor functions
    tabs = st.tabs([
        "Submit Request", 
        "My Requests", 
        "Conference Recommendations",
        "Research Analysis"
    ])
    
    # Tab 1: Submit Request
    with tabs[0]:
        show_request_submission_form()
    
    # Tab 2: My Requests
    with tabs[1]:
        show_my_requests()
    
    # Tab 3: Conference Recommendations
    with tabs[2]:
        show_conference_recommendations()
    
    # Tab 4: Research Analysis
    with tabs[3]:
        show_research_analysis()

def show_request_submission_form():
    """Display the conference travel request submission form"""
    st.subheader("Submit Conference Travel Request")
    
    # Check budget availability
    total_budget, total_expenses, remaining_budget = calculate_remaining_budget()
    
    if remaining_budget <= 0:
        display_warning_box(
            "⚠️ The conference travel budget has been fully allocated. "
            "Your request can still be submitted but approval may be delayed."
        )
    else:
        display_info_box(
            f"Current remaining budget: ${remaining_budget:,.2f} "
            f"(Used: ${total_expenses:,.2f} of ${total_budget:,.2f})"
        )
    
    # Auto-fill feature with uploaded research paper
    autofill_col1, autofill_col2 = st.columns([3, 1])
    
    with autofill_col1:
        research_paper_for_autofill = st.file_uploader(
            "Upload your research paper for auto-filling form fields",
            type=["pdf", "docx"],
            key="autofill_paper"
        )
    
    autofill_data = None
    if research_paper_for_autofill:
        with autofill_col2:
            if st.button("Auto-fill Form", key="btn_autofill"):
                with show_loading_spinner("Analyzing paper to auto-fill form..."):
                    autofill_data = get_autofill(research_paper_for_autofill)
                if autofill_data:
                    st.success("Form fields auto-filled based on your paper")
                else:
                    st.error("Could not extract information for auto-filling")
    
    # Main request form
    with st.form("request_form", clear_on_submit=False):
        # Conference details
        st.markdown("### Conference Details")
        conf_name = st.text_input(
            "Conference Name",
            value=autofill_data.get('conference_name', '') if autofill_data else '',
            help="Enter the full name of the conference"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            purpose = st.selectbox(
                "Purpose of Attending",
                options=["Attending a Conference", "Presenting at a Conference"],
                help="Select your primary purpose for attending"
            )
        
        with col2:
            index_type = st.selectbox(
                "Conference Index",
                options=["Scopus", "IEEE", "Web of Science", "PubMed", "MEDLINE", "ACM", "None"],
                help="Select the academic index this conference is listed in"
            )
        
        conf_url = st.text_input(
            "Conference URL",
            help="Enter the official conference website URL"
        )
        
        # Travel details
        st.markdown("### Travel Information")
        col1, col2 = st.columns(2)
        with col1:
            destination = st.text_input(
                "Destination Country",
                value=autofill_data.get('location', '').split(',')[-1].strip() if autofill_data and ',' in autofill_data.get('location', '') else '',
                help="Enter the country where the conference is held"
            )
        
        with col2:
            city = st.text_input(
                "City",
                value=autofill_data.get('location', '').split(',')[0].strip() if autofill_data and ',' in autofill_data.get('location', '') else '',
                help="Enter the city where the conference is held"
            )
        
        col1, col2 = st.columns(2)
        with col1:
            date_from = st.date_input(
                "Start Date",
                value=datetime.now() + timedelta(days=30),
                help="Select the first day of your travel"
            )
        
        with col2:
            date_to = st.date_input(
                "End Date",
                value=datetime.now() + timedelta(days=35),
                help="Select the last day of your travel"
            )
        
        # Financial information
        st.markdown("### Financial Information")
        col1, col2, col3 = st.columns(3)
        with col1:
            per_diem = st.number_input(
                "Per Diem (USD)",
                min_value=0,
                value=200,
                help="Daily allowance for accommodation and meals"
            )
        
        with col2:
            registration_fee = st.number_input(
                "Registration Fee (USD)",
                min_value=0,
                value=500,
                help="Conference registration fee"
            )
        
        with col3:
            visa_fee = st.number_input(
                "Visa Fee (USD)",
                min_value=0,
                value=0,
                help="Visa application fee if applicable"
            )
        
        # Document uploads
        st.markdown("### Required Documents")
        research_paper = st.file_uploader(
            "Research Paper",
            type=["pdf", "docx"],
            help="Upload your research paper for the conference"
        )
        
        acceptance_letter = st.file_uploader(
            "Acceptance Letter",
            type=["pdf", "docx"],
            help="Upload the conference acceptance letter"
        )
        
        # Notes and additional information
        st.markdown("### Additional Information")
        notes = st.text_area(
            "Additional Notes",
            help="Any additional information or special requirements"
        )
        
        # Submit button
        submitted = st.form_submit_button("Submit Request")
        
        if submitted:
            # Validate required fields
            if not conf_name or not destination or not city:
                st.error("Please fill in all required fields")
                return
            
            if date_from > date_to:
                st.error("End date must be after start date")
                return
            
            # Validate required documents
            if not research_paper or not acceptance_letter:
                st.error("Please upload both the research paper and acceptance letter")
                return
            
            # First validate the documents
            with show_loading_spinner("Validating documents..."):
                # Extract text from documents
                try:
                    paper_text = extract_text_from_file(research_paper)
                    acceptance_text = extract_text_from_file(acceptance_letter)
                    
                    # Generate summaries using AI
                    conference_summary = generate_conference_summary(acceptance_text, conf_name)
                    research_summary = "Research paper uploaded and validated."
                    notes_summary = generate_ai_notes(conf_name, purpose, index_type, destination, city)
                    url_summary = "Conference URL verified."
                    
                    # Validate with AI
                    validation_result = validate_with_gpt(
                        conf_name, paper_text, acceptance_text, index_type, conf_url
                    )
                    
                    is_valid = validation_result.get('valid', False)
                    
                    if not is_valid:
                        st.error("Document validation failed. Please check your documents and try again.")
                        st.write(validation_result.get('observations', ''))
                        return
                    
                except Exception as e:
                    logging.error(f"Error processing documents: {str(e)}")
                    st.error(f"Error processing documents: {str(e)}")
                    return
            
            # Create request data
            request_data = {
                'conference_name': sanitize_input(conf_name),
                'purpose_of_attending': purpose,
                'conference_url': sanitize_input(conf_url),
                'url_summary': url_summary,
                'destination': sanitize_input(destination),
                'city': sanitize_input(city),
                'date_from': date_from,
                'date_to': date_to,
                'per_diem': per_diem,
                'registration_fee': registration_fee,
                'visa_fee': visa_fee,
                'conference_summary': conference_summary,
                'research_summary': research_summary,
                'notes_summary': notes_summary,
                'index_type': index_type
            }
            
            # Save request to database
            user_id = st.session_state.logged_in_user
            
            try:
                request_id = create_request(user_id, request_data)
                
                if request_id:
                    # Save uploaded documents
                    save_document(
                        request_id,
                        research_paper.name,
                        "research_paper",
                        research_paper.getvalue(),
                        research_paper.size
                    )
                    
                    save_document(
                        request_id,
                        acceptance_letter.name,
                        "acceptance_letter",
                        acceptance_letter.getvalue(),
                        acceptance_letter.size
                    )
                    
                    display_success_box("Your conference travel request has been submitted successfully!")
                    st.balloons()
                else:
                    st.error("Failed to submit request. Please try again.")
            
            except Exception as e:
                logging.error(f"Error submitting request: {str(e)}")
                st.error(f"An error occurred: {str(e)}")

def show_my_requests():
    """Display list of user's submitted requests"""
    st.subheader("My Requests")
    
    # Filter options
    col1, col2 = st.columns([1, 3])
    with col1:
        status_filter = st.selectbox(
            "Filter by Status",
            options=["All", "Pending", "Approved", "Rejected", "Completed"]
        )
    
    # Get user requests
    user_id = st.session_state.logged_in_user
    
    with show_loading_spinner("Loading your requests..."):
        if status_filter == "All":
            requests = get_user_requests(user_id)
        else:
            requests = get_user_requests(user_id, status_filter.lower())
    
    if not requests:
        display_info_box("You have no requests matching the selected filter.")
        return
    
    # Prepare data for display
    requests_df = pd.DataFrame(requests)
    
    # Format dates for display
    requests_df['created_at'] = pd.to_datetime(requests_df['created_at']).dt.strftime('%Y-%m-%d')
    requests_df['date_from'] = pd.to_datetime(requests_df['date_from']).dt.strftime('%Y-%m-%d')
    requests_df['date_to'] = pd.to_datetime(requests_df['date_to']).dt.strftime('%Y-%m-%d')
    
    # Add total cost column
    requests_df['total_cost'] = requests_df['per_diem'] + requests_df['registration_fee'] + requests_df['visa_fee']
    
    # Select columns for display
    display_df = requests_df[[
        'request_id', 'conference_name', 'destination', 'city',
        'date_from', 'date_to', 'status', 'total_cost', 'created_at'
    ]]
    
    # Rename columns for better display
    display_df.columns = [
        'Request ID', 'Conference', 'Country', 'City',
        'Start Date', 'End Date', 'Status', 'Total Cost (USD)', 'Submitted On'
    ]
    
    # Color code status values
    def highlight_status(val):
        if val == 'approved':
            return 'background-color: #d4edda; color: #155724'
        elif val == 'rejected':
            return 'background-color: #f8d7da; color: #721c24'
        elif val == 'pending':
            return 'background-color: #fff3cd; color: #856404'
        elif val == 'completed':
            return 'background-color: #d1ecf1; color: #0c5460'
        return ''
    
    # Display the dataframe
    st.dataframe(
        display_df.style.applymap(highlight_status, subset=['Status']),
        use_container_width=True
    )
    
    # Add a chart showing request status distribution
    status_counts = requests_df['status'].value_counts().reset_index()
    status_counts.columns = ['Status', 'Count']
    
    if len(status_counts) > 1:
        st.subheader("Request Status Distribution")
        fig = px.pie(
            status_counts,
            values='Count',
            names='Status',
            color='Status',
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
    
    # Add download PDF functionality
    st.subheader("Download Request Report")
    request_id = st.text_input("Enter Request ID", help="Provide the ID of the request to download its report")
    if request_id and st.button("Download PDF Report"):
        download_request_pdf(request_id)

def download_request_pdf(request_id):
    """Generate and download a PDF report for a request"""
    # Get request data
    request_data = get_request_by_id(request_id)
    
    if not request_data:
        display_error_box("Request not found.")
        return
    
    # Get faculty data
    faculty_data = get_user_by_id(request_data['faculty_user_id'])
    
    # Generate PDF
    try:
        pdf_buffer = generate_request_pdf(request_data, faculty_data)
        
        # Provide download link
        st.download_button(
            label="Download PDF Report",
            data=pdf_buffer,
            file_name=f"request_{request_id}.pdf",
            mime="application/pdf"
        )
        
    except Exception as e:
        display_error_box(f"Error generating PDF: {str(e)}")

def show_conference_recommendations():
    """Display conference recommendation tools"""
    st.subheader("Conference Recommendations")
    
    display_info_box(
        "Upload your research paper to get personalized conference recommendations "
        "based on your research topic, methodology, and field of study."
    )
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        paper = st.file_uploader(
            "Upload your research paper",
            type=["pdf", "docx"],
            key="recommendation_paper"
        )
    
    with col2:
        field = st.selectbox(
            "Field of Study",
            options=[
                "Computer Science",
                "Engineering",
                "Business",
                "Medicine",
                "Social Sciences",
                "Natural Sciences",
                "Humanities",
                "Other"
            ]
        )
    
    if paper and st.button("Get Recommendations", key="btn_recommendations"):
        with show_loading_spinner("Analyzing your paper and finding suitable conferences..."):
            try:
                # Extract text from paper
                paper_text = extract_text_from_file(paper)
                
                # Get recommendations
                recommendations = get_conference_recommendations(paper_text, field)
                
                if recommendations.get('success'):
                    st.success("Analysis complete! Here are your recommended conferences:")
                    
                    # Display recommendations
                    for i, rec in enumerate(recommendations.get('recommendations', [])):
                        with st.expander(f"{i+1}. {rec.get('name')}", expanded=i==0):
                            st.markdown(f"**Index:** {rec.get('index')}")
                            st.markdown(f"**Quality Tier:** {rec.get('tier')}")
                            st.markdown(f"**Subject Alignment:** {rec.get('alignment')}")
                            st.markdown(f"**Justification:** {rec.get('justification')}")
                else:
                    st.error(recommendations.get('error', 'Failed to generate recommendations'))
                    
            except Exception as e:
                logging.error(f"Error getting conference recommendations: {str(e)}")
                st.error(f"An error occurred: {str(e)}")

def show_research_analysis():
    """Display research paper analysis tools"""
    st.subheader("Research Paper Analysis")
    
    display_info_box(
        "Upload your research paper to receive feedback, analysis, and suggestions for improvement "
        "before submitting to a conference."
    )
    
    paper = st.file_uploader(
        "Upload your research paper",
        type=["pdf", "docx"],
        key="analysis_paper"
    )
    
    if paper and st.button("Analyze Paper", key="btn_analyze"):
        with show_loading_spinner("Analyzing your research paper..."):
            try:
                # Extract text from paper
                paper_text = extract_text_from_file(paper)
                
                # Analyze paper
                analysis_result = analyze_research_paper(paper_text)
                
                if analysis_result.get('success'):
                    st.success("Analysis complete!")
                    
                    # Display analysis results in tabs
                    analysis_tabs = st.tabs([
                        "Strengths", 
                        "Areas for Improvement", 
                        "Recommendations"
                    ])
                    
                    with analysis_tabs[0]:
                        st.subheader("Key Strengths")
                        strengths = analysis_result.get('strengths', [])
                        if isinstance(strengths, list):
                            for i, strength in enumerate(strengths):
                                st.markdown(f"**{i+1}.** {strength}")
                        else:
                            st.markdown(strengths)
                    
                    with analysis_tabs[1]:
                        st.subheader("Areas for Improvement")
                        improvements = analysis_result.get('improvements', [])
                        if isinstance(improvements, list):
                            for i, improvement in enumerate(improvements):
                                st.markdown(f"**{i+1}.** {improvement}")
                        else:
                            st.markdown(improvements)
                    
                    with analysis_tabs[2]:
                        st.subheader("Recommendations")
                        st.markdown(analysis_result.get('recommendations', ''))
                        
                        # Display readiness score with gauge
                        readiness = analysis_result.get('readiness', 0)
                        if isinstance(readiness, int) or isinstance(readiness, float):
                            st.subheader("Publication Readiness Score")
                            
                            # Create gauge chart
                            gauge_chart = {
                                "data": [
                                    {
                                        "type": "indicator",
                                        "mode": "gauge+number",
                                        "value": readiness,
                                        "title": {"text": "Publication Readiness"},
                                        "gauge": {
                                            "axis": {"range": [0, 10]},
                                            "bar": {"color": "#2563EB"},
                                            "steps": [
                                                {"range": [0, 3], "color": "#EF4444"},
                                                {"range": [3, 7], "color": "#F59E0B"},
                                                {"range": [7, 10], "color": "#10B981"}
                                            ],
                                            "threshold": {
                                                "line": {"color": "black", "width": 2},
                                                "thickness": 0.75,
                                                "value": 7
                                            }
                                        }
                                    }
                                ],
                                "layout": {
                                    "height": 300,
                                    "margin": {"t": 40, "r": 25, "l": 25, "b": 25}
                                }
                            }
                            
                            import plotly.graph_objects as go
                            from plotly.subplots import make_subplots
                            
                            fig = go.Figure(gauge_chart["data"], gauge_chart["layout"])
                            st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error(analysis_result.get('error', 'Failed to analyze paper'))
                    
            except Exception as e:
                logging.error(f"Error analyzing research paper: {str(e)}")
                st.error(f"An error occurred: {str(e)}")