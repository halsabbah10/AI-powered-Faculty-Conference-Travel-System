"""
Report generation service.
Creates PDF reports for various system functions.
"""

import os
import io
import logging
from datetime import datetime
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def generate_request_pdf(request_data, faculty_data=None):
    """
    Generate a PDF report for a travel request.
    
    Args:
        request_data: Dictionary with request details
        faculty_data: Optional dictionary with faculty details
        
    Returns:
        BytesIO: PDF file as a bytes buffer
    """
    try:
        # Create a buffer to receive PDF data
        buffer = io.BytesIO()
        
        # Create the PDF object using the buffer as its "file"
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = styles['Title']
        heading_style = styles['Heading1']
        normal_style = styles['Normal']
        
        # Create custom style for data
        data_style = ParagraphStyle(
            'DataStyle',
            parent=normal_style,
            spaceAfter=6,
            fontSize=10
        )
        
        # Create the content
        content = []
        
        # Title
        content.append(Paragraph("Conference Travel Request", title_style))
        content.append(Spacer(1, 0.25 * inch))
        
        # Request ID and Date
        content.append(Paragraph(f"Request ID: {request_data['request_id']}", heading_style))
        content.append(Paragraph(f"Submission Date: {request_data['created_at'].strftime('%Y-%m-%d')}", normal_style))
        content.append(Paragraph(f"Status: {request_data['status'].upper()}", normal_style))
        content.append(Spacer(1, 0.25 * inch))
        
        # Faculty Information
        content.append(Paragraph("Faculty Information", heading_style))
        if faculty_data:
            faculty_data = [
                ["Name:", faculty_data['name']],
                ["Email:", faculty_data['email']],
                ["Department:", faculty_data['department']],
                ["Position:", faculty_data.get('position', 'N/A')]
            ]
        else:
            faculty_data = [
                ["Faculty ID:", request_data['faculty_user_id']]
            ]
        
        faculty_table = Table(faculty_data, colWidths=[2*inch, 4*inch])
        faculty_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 6)
        ]))
        content.append(faculty_table)
        content.append(Spacer(1, 0.25 * inch))
        
        # Conference Information
        content.append(Paragraph("Conference Information", heading_style))
        conference_data = [
            ["Name:", request_data['conference_name']],
            ["URL:", request_data['conference_url']],
            ["Purpose:", request_data['purpose_of_attending']],
            ["Location:", f"{request_data['city']}, {request_data['destination']}"],
            ["Dates:", f"{request_data['date_from'].strftime('%Y-%m-%d')} to {request_data['date_to'].strftime('%Y-%m-%d')}"]
        ]
        
        conference_table = Table(conference_data, colWidths=[2*inch, 4*inch])
        conference_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 6)
        ]))
        content.append(conference_table)
        content.append(Spacer(1, 0.25 * inch))
        
        # Financial Information
        content.append(Paragraph("Financial Details", heading_style))
        financial_data = [
            ["Registration Fee:", f"${request_data['registration_fee']:.2f}"],
            ["Per Diem:", f"${request_data['per_diem']:.2f}"],
            ["Visa Fee:", f"${request_data['visa_fee']:.2f}"],
            ["Total Cost:", f"${(request_data['registration_fee'] + request_data['per_diem'] + request_data['visa_fee']):.2f}"]
        ]
        
        financial_table = Table(financial_data, colWidths=[2*inch, 4*inch])
        financial_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('BACKGROUND', (0, -1), (1, -1), colors.lightblue),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold')
        ]))
        content.append(financial_table)
        content.append(Spacer(1, 0.25 * inch))
        
        # Approval Information (if applicable)
        if request_data['status'] in ['approved', 'rejected']:
            content.append(Paragraph("Approval Decision", heading_style))
            approval_data = [
                ["Decision:", request_data['status'].upper()],
                ["Decision Date:", request_data['updated_at'].strftime('%Y-%m-%d')],
                ["Notes:", request_data.get('approval_notes', 'N/A')]
            ]
            
            approval_table = Table(approval_data, colWidths=[2*inch, 4*inch])
            approval_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('PADDING', (0, 0), (-1, -1), 6)
            ]))
            content.append(approval_table)
            content.append(Spacer(1, 0.25 * inch))
        
        # Footer
        footer_text = f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} by Faculty Conference Travel System"
        content.append(Spacer(1, inch))
        content.append(Paragraph(footer_text, ParagraphStyle('footer', parent=normal_style, fontSize=8, textColor=colors.grey)))
        
        # Build the PDF
        doc.build(content)
        
        # Get the value from the buffer
        buffer.seek(0)
        return buffer
        
    except Exception as e:
        logging.error(f"Error generating PDF: {str(e)}")
        raise

def generate_budget_report(budget_data, expenses_data, year):
    """
    Generate a budget report PDF.
    
    Args:
        budget_data: Dictionary with budget information
        expenses_data: List of expense records
        year: Year for the report
        
    Returns:
        BytesIO: PDF file as a bytes buffer
    """
    try:
        # Create a buffer to receive PDF data
        buffer = io.BytesIO()
        
        # Create the PDF object
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = styles['Title']
        heading_style = styles['Heading1']
        normal_style = styles['Normal']
        
        # Create the content
        content = []
        
        # Title
        content.append(Paragraph(f"Budget Report - {year}", title_style))
        content.append(Spacer(1, 0.25 * inch))
        
        # Budget Summary
        content.append(Paragraph("Budget Summary", heading_style))
        
        # Calculate totals
        total_budget = budget_data['amount']
        total_expenses = sum(expense['total_cost'] for expense in expenses_data)
        remaining_budget = total_budget - total_expenses
        
        summary_data = [
            ["Total Budget:", f"${total_budget:.2f}"],
            ["Total Expenses:", f"${total_expenses:.2f}"],
            ["Remaining Budget:", f"${remaining_budget:.2f}"],
            ["Utilization:", f"{(total_expenses/total_budget*100):.1f}%"]
        ]
        
        summary_table = Table(summary_data, colWidths=[2*inch, 4*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 6)
        ]))
        content.append(summary_table)
        content.append(Spacer(1, 0.25 * inch))
        
        # Expense Breakdown
        content.append(Paragraph("Expense Breakdown", heading_style))
        
        # Create expense table
        if expenses_data:
            # Table headers
            expense_table_data = [["Request ID", "Faculty", "Conference", "Date", "Cost"]]
            
            # Add expense rows
            for expense in expenses_data:
                expense_table_data.append([
                    expense['request_id'],
                    expense['faculty_name'],
                    expense['conference_name'],
                    expense['date_from'].strftime('%Y-%m-%d'),
                    f"${expense['total_cost']:.2f}"
                ])
            
            # Add total row
            expense_table_data.append(["", "", "", "Total:", f"${total_expenses:.2f}"])
            
            # Create table
            expense_table = Table(expense_table_data, colWidths=[1*inch, 1.5*inch, 2*inch, 1*inch, 0.75*inch])
            expense_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('BACKGROUND', (0, -1), (-1, -1), colors.lightblue),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('ALIGN', (-1, 1), (-1, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('PADDING', (0, 0), (-1, -1), 6),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold')
            ]))
            content.append(expense_table)
        else:
            content.append(Paragraph("No expenses recorded for this period.", normal_style))
        
        content.append(Spacer(1, 0.25 * inch))
        
        # Department Breakdown
        content.append(Paragraph("Department Breakdown", heading_style))
        
        # Group expenses by department
        dept_expenses = {}
        for expense in expenses_data:
            dept = expense.get('department', 'Unknown')
            if dept not in dept_expenses:
                dept_expenses[dept] = 0
            dept_expenses[dept] += expense['total_cost']
        
        if dept_expenses:
            # Table data
            dept_table_data = [["Department", "Total Expenses", "% of Budget"]]
            
            # Add department rows
            for dept, amount in dept_expenses.items():
                dept_table_data.append([
                    dept,
                    f"${amount:.2f}",
                    f"{(amount/total_budget*100):.1f}%"
                ])
            
            # Create table
            dept_table = Table(dept_table_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
            dept_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('PADDING', (0, 0), (-1, -1), 6),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold')
            ]))
            content.append(dept_table)
        else:
            content.append(Paragraph("No department data available.", normal_style))
        
        # Footer
        footer_text = f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} by Faculty Conference Travel System"
        content.append(Spacer(1, inch))
        content.append(Paragraph(footer_text, ParagraphStyle('footer', parent=normal_style, fontSize=8, textColor=colors.grey)))
        
        # Build the PDF
        doc.build(content)
        
        # Get the value from the buffer
        buffer.seek(0)
        return buffer
        
    except Exception as e:
        logging.error(f"Error generating budget report: {str(e)}")
        raise