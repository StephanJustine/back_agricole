"""
Service de notifications.
"""
import logging
from typing import List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

from ..config import settings

logger = logging.getLogger(__name__)


class NotificationService:
    """Service d'envoi de notifications."""
    
    @staticmethod
    async def send_email(
        to_emails: List[str],
        subject: str,
        body: str,
        html: Optional[str] = None
    ) -> bool:
        """
        Envoie un email.
        """
        try:
            if not settings.MAIL_USERNAME or not settings.MAIL_PASSWORD:
                logger.warning("Email non configuré")
                return False
            
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = settings.MAIL_FROM
            msg["To"] = ", ".join(to_emails)
            
            msg.attach(MIMEText(body, "plain"))
            if html:
                msg.attach(MIMEText(html, "html"))
            
            with smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT) as server:
                if settings.MAIL_TLS:
                    server.starttls()
                server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
                server.sendmail(settings.MAIL_FROM, to_emails, msg.as_string())
            
            logger.info(f"Email envoyé à {to_emails}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur envoi email: {e}")
            return False
    
    @staticmethod
    async def send_alerte_maladie(
        email: str,
        parcelle_nom: str,
        culture_variete: str,
        maladie_type: str,
        gravite: int,
        recommandations: str
    ) -> bool:
        """
        Envoie une alerte pour une maladie grave.
        """
        subject = f"🔴 ALERTE MALADIE - {parcelle_nom}"
        body = f"""
        ALERTE MALADIE GRAVE DÉTECTÉE !
        
        Parcelle: {parcelle_nom}
        Culture: {culture_variete}
        Maladie: {maladie_type}
        Gravité: {gravite}/5
        
        Recommandations:
        {recommandations}
        
        Veuillez intervenir rapidement.
        """
        
        return await NotificationService.send_email(
            to_emails=[email],
            subject=subject,
            body=body
        )