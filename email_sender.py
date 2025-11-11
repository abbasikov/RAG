from datetime import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from typing import Dict

class EmailSender:
    def __init__(self, sendgrid_api_key: str, sender_email: str, recipient_email: str):
        """Initialize SendGrid email sender"""
        self.sg = SendGridAPIClient(sendgrid_api_key)
        self.sender_email = sender_email
        self.recipient_email = recipient_email

    def format_user_data_email(self, user_data: Dict) -> str:
        """Format user data into an HTML email"""
        html_content = f"""
        <html>
            <head>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        line-height: 1.6;
                        color: #333;
                    }}
                    .container {{
                        max-width: 600px;
                        margin: 0 auto;
                        padding: 20px;
                        background-color: #f4f4f4;
                    }}
                    .header {{
                        background-color: #1a73e8;
                        color: white;
                        padding: 20px;
                        text-align: center;
                        border-radius: 5px 5px 0 0;
                    }}
                    .content {{
                        background-color: white;
                        padding: 30px;
                        border-radius: 0 0 5px 5px;
                    }}
                    .data-row {{
                        margin: 15px 0;
                        padding: 10px;
                        background-color: #f9f9f9;
                        border-left: 4px solid #1a73e8;
                    }}
                    .label {{
                        font-weight: bold;
                        color: #1a73e8;
                    }}
                    .value {{
                        margin-top: 5px;
                        color: #333;
                    }}
                    .footer {{
                        margin-top: 20px;
                        text-align: center;
                        color: #666;
                        font-size: 12px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>New User Data Collected</h2>
                        <p>Stock Market Chatbot - User Information</p>
                    </div>
                    <div class="content">
                        <div class="data-row">
                            <div class="label">Session ID:</div>
                            <div class="value">{user_data.get('session_id', 'N/A')}</div>
                        </div>
                        <div class="data-row">
                            <div class="label">Name:</div>
                            <div class="value">{user_data.get('name', 'N/A')}</div>
                        </div>
                        <div class="data-row">
                            <div class="label">Email Address:</div>
                            <div class="value">{user_data.get('email', 'N/A')}</div>
                        </div>
                        <div class="data-row">
                            <div class="label">Income Level:</div>
                            <div class="value">{user_data.get('income', 'N/A')}</div>
                        </div>
                        <div class="data-row">
                            <div class="label">Collected At:</div>
                            <div class="value">{user_data.get('collected_at', 'N/A')}</div>
                        </div>
                    </div>
                    <div class="footer">
                        <p>This data was collected from the Stock Market Chatbot</p>
                        <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    </div>
                </div>
            </body>
        </html>
        """
        return html_content

    def send_user_data(self, user_data: Dict) -> bool:
        """Send user data via email"""
        try:
            # Format email content
            html_content = self.format_user_data_email(user_data)

            # Create email
            message = Mail(
                from_email=self.sender_email,
                to_emails=self.recipient_email,
                subject=f"New User Data - {user_data.get('name', 'Unknown')}",
                html_content=html_content
            )

            # Send email
            response = self.sg.send(message)

            if response.status_code in [200, 201, 202]:
                print(f"Email sent successfully! Status: {response.status_code}")
                return True
            else:
                print(f"Email failed with status: {response.status_code}")
                return False

        except Exception as e:
            print(f"Error sending email: {e}")
            return False

    def send_plain_text(self, subject: str, text: str) -> bool:
        """Send a plain text email"""
        try:
            message = Mail(
                from_email=self.sender_email,
                to_emails=self.recipient_email,
                subject=subject,
                plain_text_content=text
            )

            response = self.sg.send(message)

            if response.status_code in [200, 201, 202]:
                print(f"Email sent successfully! Status: {response.status_code}")
                return True
            else:
                print(f"Email failed with status: {response.status_code}")
                return False

        except Exception as e:
            print(f"Error sending email: {e}")
            return False
