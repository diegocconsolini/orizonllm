"""
Modern Email Templates for LiteLLM Email Service with professional styling
"""

USER_INVITATION_EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Welcome to OrizonLLM</title>
    <style>
        body, html {{
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            color: #333333;
            background-color: #f8f8f8;
            line-height: 1.5;
        }}
        .container {{
            max-width: 560px;
            margin: 20px auto;
            background-color: #ffffff;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .logo {{
            padding: 24px 0 0 24px;
            text-align: left;
        }}
        .greeting {{
            font-size: 16px;
            margin-bottom: 20px;
            color: #333333;
        }}
        .content {{
            padding: 24px 40px 32px;
        }}
        h1 {{
            font-size: 24px;
            font-weight: 600;
            margin-top: 24px;
            margin-bottom: 16px;
            color: #333333;
        }}
        p {{
            font-size: 16px;
            color: #333333;
            margin-bottom: 16px;
            line-height: 1.5;
        }}
        .intro-text {{
            margin-bottom: 24px;
        }}
        .link {{
            color: #6366f1;
            text-decoration: none;
            font-weight: 500;
        }}
        .link:hover {{
            text-decoration: underline;
        }}
        .link-with-arrow {{
            display: inline-flex;
            align-items: center;
            color: #6366f1;
            text-decoration: none;
            font-weight: 500;
            margin-bottom: 20px;
        }}
        .link-with-arrow:hover {{
            text-decoration: underline;
        }}
        .arrow {{
            margin-left: 6px;
        }}
        .divider {{
            height: 1px;
            background-color: #f1f1f1;
            margin: 24px 0;
        }}
        .btn {{
            display: inline-block;
            padding: 12px 24px;
            background-color: #5c5ce0;
            color: #ffffff !important;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 500;
            margin-top: 12px;
            text-align: center;
            font-size: 15px;
            transition: background-color 0.2s ease;
        }}
        .btn:hover {{
            background-color: #4b4bb3;
        }}
        .btn-container {{
            text-align: center;
            margin: 24px 0;
        }}
        .footer {{
            padding: 24px 40px 32px;
            text-align: left;
            color: #666;
            font-size: 14px;
        }}
        .quickstart {{
            margin-top: 32px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">
            <img src="{email_logo_url}" alt="OrizonLLM Logo" style="height: 32px; width: auto;">
        </div>
        <div class="content">
            <h1>Welcome to OrizonLLM</h1>

            <div class="greeting">
                <p>Hi {recipient_email},</p>
            </div>

            <div class="intro-text">
                <p>OrizonLLM is your enterprise AI gateway. Call 100+ LLM providers through a unified OpenAI-compatible API. Get started by accepting your invitation.</p>
            </div>

            <div class="btn-container">
                <a href="{base_url}" class="btn">Accept Invitation</a>
            </div>
            
            <div class="quickstart">
                <p>Here's a quickstart guide to get you started:</p>
            </div>
            
            <div class="divider"></div>
            
            <a href="https://api.audividi.ai/ui/" class="link-with-arrow">
                Access Admin Dashboard →
                <span class="arrow"></span>
            </a>

            <p>Manage API keys, monitor usage, and configure models through the web interface.</p>

            <div class="divider"></div>

            <a href="https://api.audividi.ai/api-reference" class="link-with-arrow">
                API Reference →
                <span class="arrow"></span>
            </a>

            <p>View all supported endpoints: /chat/completions, /embeddings, /completions and more.</p>

            <div class="divider"></div>

            <p>Thanks for joining OrizonLLM. We're here to help you and your team. If you have any questions, contact us at {email_support_contact}</p>

        </div>
        {email_footer}
    </div>
</body>
</html>
"""
