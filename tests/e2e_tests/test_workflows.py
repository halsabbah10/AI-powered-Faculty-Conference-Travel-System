"""
End-to-end testing module.
Tests complete user workflows using Playwright.
"""

import os
import pytest
import asyncio
from playwright.async_api import async_playwright, Page, expect
from datetime import datetime, timedelta

# Test config
BASE_URL = os.getenv("TEST_APP_URL", "http://localhost:8501")
PROFESSOR_USER = "test_prof"
PROFESSOR_PASS = "testpass"
APPROVER_USER = "test_appr"
APPROVER_PASS = "testpass"
ACCOUNTANT_USER = "test_acct"
ACCOUNTANT_PASS = "testpass"

@pytest.fixture(scope="module")
async def browser():
    """Launch browser for testing."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        yield browser
        await browser.close()

@pytest.fixture
async def page(browser):
    """Create a new page for each test."""
    page = await browser.new_page()
    yield page
    await page.close()

async def login(page, username, password):
    """Log in to the application."""
    await page.goto(f"{BASE_URL}")
    await page.wait_for_load_state("networkidle")
    
    # Fill login form
    await page.fill("[data-testid='user_id_input']", username)
    await page.fill("[data-testid='password_input']", password)
    await page.click("text=Login")
    
    # Wait for dashboard to load
    await page.wait_for_selector("text=Faculty Conference Travel System", timeout=10000)

@pytest.mark.asyncio
async def test_professor_submission_workflow(page):
    """Test the complete professor request submission workflow."""
    # Login as professor
    await login(page, PROFESSOR_USER, PROFESSOR_PASS)
    
    # Navigate to request submission tab
    await page.click("text=Submit Request")
    await page.wait_for_selector("text=Conference Information")
    
    # Fill request form
    conference_name = f"Test Conference {datetime.now().strftime('%Y%m%d%H%M%S')}"
    await page.fill("[data-testid='conference_name']", conference_name)
    await page.fill("[data-testid='conference_url']", "https://test-conference.com")
    await page.fill("[data-testid='purpose_of_attending']", "Presenting research")
    await page.select_option("[data-testid='destination']", "United States")
    await page.fill("[data-testid='city']", "New York")
    
    # Set dates (30 days from now, for 5 days)
    future_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    end_date = (datetime.now() + timedelta(days=35)).strftime("%Y-%m-%d")
    await page.fill("[data-testid='date_from']", future_date)
    await page.fill("[data-testid='date_to']", end_date)
    
    # Set financial information
    await page.fill("[data-testid='registration_fee']", "500")
    await page.fill("[data-testid='per_diem']", "200")
    await page.fill("[data-testid='visa_fee']", "0")
    
    # Upload test document
    await page.set_input_files(
        "[data-testid='conference_doc']", 
        "./e2e_tests/test_files/test_document.pdf"
    )
    
    # Submit form
    await page.click("text=Submit Request")
    
    # Verify success message
    await page.wait_for_selector("text=Request submitted successfully")
    
    # Verify request appears in My Requests tab
    await page.click("text=My Requests")
    await page.wait_for_selector(f"text={conference_name}")

@pytest.mark.asyncio
async def test_approval_workflow(page):
    """Test the complete approval workflow."""
    # First submit a request as professor
    await test_professor_submission_workflow(page)
    
    # Logout
    await page.click("text=Logout")
    await page.wait_for_selector("text=Login")
    
    # Login as approver
    await login(page, APPROVER_USER, APPROVER_PASS)
    
    # Navigate to pending requests
    await page.click("text=Pending Requests")
    
    # Find and click on the most recent request
    await page.click("tr:last-child td:first-child a")
    await page.wait_for_selector("text=Request Details")
    
    # Review request
    await page.click("text=Approve")
    await page.fill("[data-testid='approval_notes']", "Approved for conference attendance")
    
    # Submit approval
    await page.click("text=Submit Decision")
    
    # Verify success message
    await page.wait_for_selector("text=Request approved successfully")

@pytest.mark.asyncio
async def test_budget_management_workflow(page):
    """Test the budget management workflow."""
    # Login as accountant
    await login(page, ACCOUNTANT_USER, ACCOUNTANT_PASS)
    
    # Navigate to budget management
    await page.click("text=Budget Management")
    await page.wait_for_selector("text=Current Budget")
    
    # Record current budget amount
    current_budget_text = await page.text_content("text=Current Budget: $>> span")
    current_budget = float(current_budget_text.replace(",", ""))
    
    # Update budget
    new_budget = current_budget + 10000
    await page.fill("[data-testid='budget_amount']", str(new_budget))
    await page.fill("[data-testid='budget_notes']", "Increasing budget for testing")
    
    # Submit budget update
    await page.click("text=Update Budget")
    
    # Verify success message
    await page.wait_for_selector("text=Budget updated successfully")
    
    # Verify new budget amount is displayed
    updated_budget_text = await page.text_content("text=Current Budget: $>> span")
    updated_budget = float(updated_budget_text.replace(",", ""))
    
    assert updated_budget == new_budget, f"Budget not updated correctly. Expected {new_budget}, got {updated_budget}"

if __name__ == "__main__":
    # For manual test running
    asyncio.run(pytest.main(["-xvs", __file__]))