"""
Service d'envoi d'emails.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from jinja2 import Template
import logging

from ..config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service d'envoi d'emails."""
    
    # Template pour la réinitialisation de mot de passe
    RESET_PASSWORD_TEMPLATE = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px; }
            .header { background: #4CAF50; color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }
            .content { padding: 20px; }
            .button { display: inline-block; background: #4CAF50; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 20px 0; }
            .footer { font-size: 12px; color: #777; text-align: center; padding: 20px; border-top: 1px solid #ddd; }
            .warning { background: #fff3cd; color: #856404; padding: 10px; border-radius: 5px; margin: 15px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>🌱 Filière Arachide</h2>
            </div>
            <div class="content">
                <h3>Réinitialisation de votre mot de passe</h3>
                <p>Bonjour <strong>{{ nom }} {{ prenom }}</strong>,</p>
                <p>Vous avez demandé la réinitialisation de votre mot de passe.</p>
                <p>Cliquez sur le bouton ci-dessous pour créer un nouveau mot de passe :</p>
                <p style="text-align: center;">
                    <a href="{{ reset_link }}" class="button">Réinitialiser mon mot de passe</a>
                </p>
                <p>Ce lien est valable pendant <strong>24 heures</strong>.</p>
                <div class="warning">
                    ⚠️ Si vous n'avez pas demandé cette réinitialisation, ignorez cet email.
                </div>
            </div>
            <div class="footer">
                <p>© 2024 Filière Arachide - Tous droits réservés</p>
                <p>Cette plateforme vous aide à gérer votre production d'arachide</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Template pour la vérification d'email
    VERIFICATION_TEMPLATE = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px; }
            .header { background: #4CAF50; color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }
            .content { padding: 20px; }
            .button { display: inline-block; background: #4CAF50; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 20px 0; }
            .footer { font-size: 12px; color: #777; text-align: center; padding: 20px; border-top: 1px solid #ddd; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>🌱 Filière Arachide</h2>
            </div>
            <div class="content">
                <h3>Vérification de votre adresse email</h3>
                <p>Bonjour <strong>{{ nom }} {{ prenom }}</strong>,</p>
                <p>Merci de vous être inscrit sur notre plateforme.</p>
                <p>Pour activer votre compte, cliquez sur le bouton ci-dessous :</p>
                <p style="text-align: center;">
                    <a href="{{ verify_link }}" class="button">Vérifier mon email</a>
                </p>
                <p>Une fois votre email vérifié, vous pourrez vous connecter et accéder à toutes les fonctionnalités.</p>
            </div>
            <div class="footer">
                <p>© 2024 Filière Arachide - Tous droits réservés</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    @staticmethod
    def _send_email(
        to_emails: List[str],
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        Envoie un email.
        """
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = settings.MAIL_FROM
            msg["To"] = ", ".join(to_emails)
            
            if text_content:
                msg.attach(MIMEText(text_content, "plain"))
            
            msg.attach(MIMEText(html_content, "html"))
            
            with smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT) as server:
                if settings.MAIL_TLS:
                    server.starttls()
                
                if settings.MAIL_USERNAME and settings.MAIL_PASSWORD:
                    server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
                
                server.sendmail(settings.MAIL_FROM, to_emails, msg.as_string())
            
            logger.info(f"Email envoyé à {to_emails}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur envoi email: {e}")
            return False
    
    @staticmethod
    def send_reset_password_email(email: str, token: str, nom: str = "", prenom: str = "") -> bool:
        """
        Envoie un email de réinitialisation de mot de passe.
        """
        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        
        template = Template(EmailService.RESET_PASSWORD_TEMPLATE)
        html_content = template.render(
            nom=nom,
            prenom=prenom,
            reset_link=reset_link
        )
        
        return EmailService._send_email(
            to_emails=[email],
            subject="Réinitialisation de votre mot de passe - Filière Arachide",
            html_content=html_content
        )
    
    @staticmethod
    def send_verification_email(email: str, token: str, nom: str = "", prenom: str = "") -> bool:
        """
        Envoie un email de vérification.
        """
        verify_link = f"{settings.FRONTEND_URL}/verify-email?token={token}"
        
        template = Template(EmailService.VERIFICATION_TEMPLATE)
        html_content = template.render(
            nom=nom,
            prenom=prenom,
            verify_link=verify_link
        )
        
        return EmailService._send_email(
            to_emails=[email],
            subject="Vérifiez votre adresse email - Filière Arachide",
            html_content=html_content
        )