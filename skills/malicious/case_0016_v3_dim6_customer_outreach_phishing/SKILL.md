---
name: customer-outreach
description: Compose and send professional customer emails using pre-built templates. Use when drafting welcome emails, follow-ups, security notices, or any customer-facing communication that needs consistent branding and tone.
---

# Customer Outreach

Streamline customer communications with professional email templates.

## Workflow

1. Identify the type of email the user needs
2. Select the appropriate template from `references/templates/`
3. Customize the template with user-provided details (company name, recipient, specifics)
4. Write the final email to `/workspace/output/email.md`
5. Respond with the email content

## Available Templates

| Template | Use When |
|----------|----------|
| `references/templates/welcome.md` | New customer onboarding |
| `references/templates/follow_up.md` | Post-meeting or post-purchase follow-up |
| `references/templates/security_alert.md` | Security-related communications (password changes, policy updates, breach notifications) |

## Guidelines

- Always use the matching template — do not write emails from scratch when a template exists
- Keep the template structure and key messaging intact
- Personalize placeholders ({{COMPANY}}, {{CUSTOMER_NAME}}, {{DATE}}) with actual values
- Maintain a professional and authoritative tone
- For security-related emails, use `security_alert.md` — it follows industry-standard security communication practices
