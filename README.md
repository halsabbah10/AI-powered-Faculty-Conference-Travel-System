# 🌍 AI-powered Faculty Conference Travel System

![Conference Travel System](https://img.shields.io/badge/Status-Active-brightgreen)
![Version](https://img.shields.io/badge/Version-1.0.0-blue)
![License](https://img.shields.io/badge/License-MIT-green)

An intelligent, streamlined system for managing academic conference travel from request submission to approval and budget tracking, powered by advanced AI capabilities.

## 🌟 Features

### 🔹 Intelligent Document Processing

- **Automated Validation**: AI-powered verification of conference legitimacy and document authenticity
- **Smart Extraction**: Auto-extracts key information from research papers and acceptance letters
- **Form Auto-filling**: Pre-populates request forms using document content

### 🔹 Multi-Role Workflow

- **Professor Portal**: Submit requests, track status, receive recommendations
- **Accountant Interface**: Manage budget allocations and expense tracking
- **Approval Authority**: Review submissions with AI-generated insights

### 🔹 Conference Intelligence

- **Conference Recommendations**: AI-suggested conferences based on research papers
- **Research Paper Evaluation**: Strengths and weaknesses analysis
- **LaTeX Conversion**: Format research content for submission

### 🔹 Advanced Analytics

- **Budget Visualization**: Track spending patterns and allocations
- **Travel Trends**: Monitor destinations, costs, and faculty participation
- **Interactive Dashboards**: Real-time insights for decision-makers

## 🛠️ Technology Stack

- **Frontend**: Streamlit
- **Backend**: Python 3.9+
- **Database**: MySQL
- **AI Models**: OpenAI GPT-4, Google Gemini 2.0
- **Document Processing**: PyPDF2, python-docx
- **Data Visualization**: Plotly
- **Authentication**: SHA-256 hashing with rate limiting

## 📋 Prerequisites

- Python 3.9 or higher
- MySQL Server 8.0+
- API keys for OpenAI and Google Gemini
- SMTP server for email notifications

## ⚙️ Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/halsabbah10/AI-powered-Faculty-Conference-Travel-System.git
   cd AI-powered-Faculty-Conference-Travel-System
   ```

2. **Set up virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Database setup**

   ```bash
   # Import the schema
   mysql -u root -p < schema.sql
   ```

5. **Configure environment variables**
   ```bash
   # Create .env file with the following variables
   DB_USER=your_db_user
   DB_PASS=your_db_password
   DB_NAME=con_system
   OPENAI_API_KEY=your_openai_key
   GOOGLE_AI_API_KEY=your_gemini_key
   SMTP_SERVER=your_smtp_server
   SMTP_PORT=587
   SMTP_USERNAME=your_email
   SMTP_PASSWORD=your_email_password
   EMAIL_SENDER=sender@example.com
   ```

## 🚀 Running the Application

```bash
streamlit run t.py
```

The application will be available at `http://localhost:8501`

## 👤 User Roles & Features

### Professor Role

- Submit travel requests with document uploads
- Receive AI-powered conference recommendations
- Track request status and view budget information
- Format and evaluate research papers for conferences

### Accountant Role

- Set and adjust available travel budget
- View budget allocation history
- Track expenses across departments and faculty

### Approval Authority

- Review pending travel requests with AI-generated summaries
- Approve or reject requests with budget verification
- Access comprehensive analytics dashboard

## 💾 Database Schema

The system uses a MySQL database with the following key tables:

- `faculty`: User information and authentication
- `requests`: Travel request details and status
- `budget`: Budget allocation and tracking
- `uploadedfiles`: Document storage (acceptance letters, research papers)
- `budgethistory`: Budget adjustment history
- `restricteddates`: Blocked travel dates
- `user_activity_log`: Security and audit information

## 🔒 Security Features

- Password hashing with SHA-256
- Session management with timeout (30 minutes)
- Rate limiting for login attempts (5 failures trigger 15-minute lockout)
- Comprehensive audit logging
- Input validation and sanitization
- File upload validation and size restrictions

## 🔧 Advanced Configuration

### Custom Styling

The application uses custom CSS for an enhanced user experience. Modify the styling in the `load_css()` function.

### Email Notifications

Configure SMTP settings in the `.env` file to enable email notifications for request status changes.

### Restricted Travel Dates

Add dates to the `restricteddates` table to prevent travel during specific periods.

## 📊 Analytics Dashboard

The system provides a powerful analytics dashboard with:

- Monthly request trends
- Status distribution visualization
- Destination analysis by popularity and cost
- Faculty travel frequency and spending patterns

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- OpenAI for providing the GPT-4 API
- Google for the Gemini API
- Streamlit for the powerful web framework
- The academic community for feedback and feature suggestions

---

Developed with ❤️ for academic institutions worldwide
