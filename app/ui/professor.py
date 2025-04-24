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
from app.ui.components import FormBuilder, form_builder
from app.services.service_provider import ServiceProvider
from app.utils.error_handling import handle_exceptions

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

@handle_exceptions(show_error_to_user=True, default_message="Error submitting request")
def show_request_submission_form():
    """Display the conference travel request submission form"""
    st.subheader(t("professor.submit_request", "Submit Conference Travel Request"))
    
    # Define form fields
    form_fields = [
        {
            'name': 'section_conference', 
            'type': 'section', 
            'label': t("professor.conference_info", "Conference Information"),
            'description': t("professor.conference_desc", "Enter details about the conference you wish to attend.")
        },
        {
            'name': 'conference_name', 
            'type': 'text', 
            'label': t("professor.conference_name", "Conference Name"),
            'required': True,
            'validators': [Validator.required(), Validator.min_length(3)]
        },
        {
            'name': 'conference_url', 
            'type': 'text', 
            'label': t("professor.conference_url", "Conference Website URL"),
            'required': True,
            'validators': [Validator.required(), Validator.url()]
        },
        {
            'name': 'section_location', 
            'type': 'section', 
            'label': t("professor.location", "Location")
        },
        {
            'name': 'destination', 
            'type': 'text', 
            'label': t("professor.destination", "Destination Country"),
            'required': True,
            'validators': [Validator.required()]
        },
        {
            'name': 'city', 
            'type': 'text', 
            'label': t("professor.city", "City"),
            'required': True,
            'validators': [Validator.required()]
        },
        {
            'name': 'section_dates', 
            'type': 'section', 
            'label': t("professor.travel_dates", "Travel Dates")
        },
        {
            'name': 'date_from', 
            'type': 'date', 
            'label': t("professor.date_from", "From Date"),
            'required': True,
            'default': datetime.now() + timedelta(days=30),
            'validators': [Validator.required()]
        },
        {
            'name': 'date_to', 
            'type': 'date', 
            'label': t("professor.date_to", "To Date"),
            'required': True,
            'default': datetime.now() + timedelta(days=35),
            'validators': [Validator.required()]
        },
        {
            'name': 'section_budget', 
            'type': 'section', 
            'label': t("professor.budget_info", "Budget Information")
        },
        {
            'name': 'registration_fee', 
            'type': 'number', 
            'label': t("professor.registration_fee", "Registration Fee (USD)"),
            'required': True,
            'min': 0,
            'default': 0,
            'validators': [Validator.required(), Validator.min_value(0)]
        },
        {
            'name': 'accommodation_cost', 
            'type': 'number', 
            'label': t("professor.accommodation", "Accommodation Cost (USD)"),
            'required': True,
            'min': 0,
            'default': 0,
            'validators': [Validator.required(), Validator.min_value(0)]
        },
        {
            'name': 'transportation_cost', 
            'type': 'number', 
            'label': t("professor.transportation", "Transportation Cost (USD)"),
            'required': True,
            'min': 0,
            'default': 0,
            'validators': [Validator.required(), Validator.min_value(0)]
        },
        {
            'name': 'per_diem', 
            'type': 'number', 
            'label': t("professor.per_diem", "Per Diem (USD)"),
            'required': True,
            'min': 0,
            'default': 0,
            'validators': [Validator.required(), Validator.min_value(0)]
        },
        {
            'name': 'visa_fee', 
            'type': 'number', 
            'label': t("professor.visa_fee", "Visa Fee (USD)"),
            'required': False,
            'min': 0,
            'default': 0,
            'validators': [Validator.min_value(0)]
        },
        {
            'name': 'section_other', 
            'type': 'section', 
            'label': t("professor.additional_info", "Additional Information")
        },
        {
            'name': 'purpose_of_attending', 
            'type': 'textarea', 
            'label': t("professor.purpose", "Purpose of Attending"),
            'required': True,
            'validators': [Validator.required(), Validator.min_length(20)]
        },
        {
            'name': 'documents', 
            'type': 'file', 
            'label': t("professor.documents", "Upload Documents"),
            'multiple': True,
            'accept': ['pdf', 'docx', 'doc'],
            'help': t("professor.documents_help", "Upload conference invitation, abstract, or other supporting documents")
        }
    ]
    
    # Handle form submission
    submitted, form_data = form_builder.create_form(
        "travel_request_form",
        form_fields,
        submit_label=t("buttons.submit_request", "Submit Request"),
        on_submit=handle_form_submission,
        columns=2  # Use 2 columns for better layout
    )
    
    if submitted:
        display_success_box(t("professor.request_submitted", "Request submitted successfully"))
        st.balloons()  # Celebratory balloons!

def handle_form_submission(form_data):
    """
    Handle form submission with service provider.
    
    Args:
        form_data: Form data dictionary
        
    Returns:
        bool: Success status
    """
    # Validate date range
    if form_data['date_from'] > form_data['date_to']:
        display_error_box(t("validation.date_range", "End date must be after start date"))
        return False
    
    # Calculate total cost
    total_cost = (
        form_data['registration_fee'] +
        form_data['accommodation_cost'] +
        form_data['transportation_cost'] +
        form_data['per_diem'] +
        form_data['visa_fee']
    )
    
    # Prepare request data
    request_data = {
        'faculty_user_id': st.session_state.logged_in_user,
        'conference_name': form_data['conference_name'],
        'conference_url': form_data['conference_url'],
        'destination': form_data['destination'],
        'city': form_data['city'],
        'date_from': form_data['date_from'].strftime("%Y-%m-%d"),
        'date_to': form_data['date_to'].strftime("%Y-%m-%d"),
        'registration_fee': form_data['registration_fee'],
        'accommodation_cost': form_data['accommodation_cost'],
        'transportation_cost': form_data['transportation_cost'],
        'per_diem': form_data['per_diem'],
        'visa_fee': form_data['visa_fee'],
        'total_cost': total_cost,
        'purpose_of_attending': form_data['purpose_of_attending'],
        'status': 'pending',
        'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Save request using repository
    request_repo = ServiceProvider.db_repository(RequestRepository)
    request_id = request_repo.create(request_data)
    
    if not request_id:
        display_error_box(t("error.request_creation", "Failed to create request"))
        return False
    
    # Process documents if any
    documents = form_data.get('documents', [])
    if documents:
        doc_repo = ServiceProvider.db_repository(DocumentRepository)
        
        for doc in documents:
            # Extract file information
            file_name = doc.name
            file_content = doc.getvalue()
            file_type = doc.type
            
            # Save document
            doc_repo.add_document(
                request_id=request_id,
                file_name=file_name,
                file_type=file_type,
                file_content=file_content
            )
    
    # Create notification for approval authorities
    notification_service = ServiceProvider.service(NotificationService)
    
    # Find approval authorities
    user_repo = ServiceProvider.db_repository(UserRepository)
    approvers = user_repo.find_all(where="role = %s", params=("approval",))
    
    # Notify each approver
    for approver in approvers:
        notification_service.create_notification(
            user_id=approver['user_id'],
            message=f"New travel request from {st.session_state.user_name} for {form_data['conference_name']}",
            notification_type="info",
            related_id=request_id
        )
    
    return True

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