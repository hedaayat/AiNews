"""Email delivery for summaries."""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from ainews.config import Settings
from ainews.models.summary import DailySummary


class EmailDelivery:
    """Sends summaries via email."""

    def __init__(self, settings: Settings):
        """Initialize email delivery.

        Args:
            settings: Application settings.
        """
        self.settings = settings

    def send_summary(
        self,
        summary: DailySummary,
        recipients: list[str] | None = None,
    ) -> bool:
        """Send a summary via email.

        Args:
            summary: The summary to send.
            recipients: Override recipients. Defaults to settings.email_to.

        Returns:
            True if sent successfully.
        """
        recipients = recipients or self.settings.email_to
        if not recipients:
            print("No recipients configured")
            return False

        if not self.settings.smtp_username or not self.settings.smtp_password:
            print("SMTP credentials not configured")
            return False

        try:
            # Build email
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"AI News Summary - {summary.date.isoformat()}"
            msg["From"] = self.settings.email_from
            msg["To"] = ", ".join(recipients)

            # Plain text version
            text_content = self._format_plain_text(summary)
            msg.attach(MIMEText(text_content, "plain"))

            # HTML version
            html_content = self._format_html(summary)
            msg.attach(MIMEText(html_content, "html"))

            # Send email
            with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port) as server:
                server.starttls()
                server.login(self.settings.smtp_username, self.settings.smtp_password)
                server.sendmail(
                    self.settings.email_from,
                    recipients,
                    msg.as_string(),
                )

            # Mark as delivered
            summary.mark_delivered()
            return True

        except Exception as e:
            print(f"Error sending email: {e}")
            return False

    def _format_plain_text(self, summary: DailySummary) -> str:
        """Format summary as plain text."""
        lines = [
            f"AI News Summary for {summary.date.isoformat()}",
            "=" * 50,
            "",
            summary.summary_text,
            "",
        ]

        if summary.key_topics:
            lines.extend([
                "Key Topics:",
                "-" * 20,
            ])
            for topic in summary.key_topics:
                lines.append(f"  - {topic}")
            lines.append("")

        if summary.notable_stories:
            lines.extend([
                "Notable Stories:",
                "-" * 20,
            ])
            for story in summary.notable_stories:
                lines.extend([
                    f"  * {story.title}",
                    f"    Source: {story.source}",
                    f"    {story.brief}",
                    f"    {story.url}",
                    "",
                ])

        lines.extend([
            "-" * 50,
            f"Summary based on {summary.article_count} articles",
            f"Generated at {summary.generated_at.isoformat()}",
        ])

        return "\n".join(lines)

    def _format_html(self, summary: DailySummary) -> str:
        """Format summary as HTML."""
        notable_html = ""
        if summary.notable_stories:
            stories_html = ""
            for story in summary.notable_stories:
                stories_html += f"""
                <div style="margin-bottom: 15px; padding: 10px; background: #f5f5f5; border-radius: 5px;">
                    <strong><a href="{story.url}" style="color: #2563eb;">{story.title}</a></strong>
                    <br><small style="color: #666;">Source: {story.source}</small>
                    <br>{story.brief}
                </div>
                """
            notable_html = f"""
            <h3 style="color: #1f2937; border-bottom: 1px solid #e5e7eb; padding-bottom: 5px;">
                Notable Stories
            </h3>
            {stories_html}
            """

        topics_html = ""
        if summary.key_topics:
            topics_list = "".join(
                f'<span style="display: inline-block; background: #dbeafe; color: #1e40af; padding: 3px 8px; margin: 2px; border-radius: 3px; font-size: 12px;">{topic}</span>'
                for topic in summary.key_topics
            )
            topics_html = f"""
            <div style="margin: 15px 0;">
                <strong>Key Topics:</strong> {topics_list}
            </div>
            """

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; color: #1f2937;">
            <h1 style="color: #111827; font-size: 24px; margin-bottom: 5px;">
                AI News Summary
            </h1>
            <p style="color: #6b7280; margin-top: 0;">
                {summary.date.strftime("%A, %B %d, %Y")}
            </p>

            {topics_html}

            <div style="line-height: 1.6; margin: 20px 0;">
                {summary.summary_text.replace(chr(10), '<br>')}
            </div>

            {notable_html}

            <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
            <p style="color: #9ca3af; font-size: 12px;">
                Summary based on {summary.article_count} articles<br>
                Generated by AiNews using {summary.model_used}
            </p>
        </body>
        </html>
        """
