"""Envoi d'email via SMTP (Gmail par défaut).

Sur Gmail, utilisez un « mot de passe d'application » (App Password),
pas votre mot de passe habituel : https://myaccount.google.com/apppasswords
"""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from .config import get_secret


def smtp_configured() -> bool:
    return bool(
        (get_secret("SMTP_USER") or get_secret("GMAIL_ADDRESS"))
        and (get_secret("SMTP_PASSWORD") or get_secret("GMAIL_APP_PASSWORD"))
    )


def send_reset_email(to_email: str, reset_url: str) -> bool:
    host = str(get_secret("SMTP_HOST", "smtp.gmail.com"))
    port = int(get_secret("SMTP_PORT", "587"))
    user = get_secret("SMTP_USER") or get_secret("GMAIL_ADDRESS")
    password = get_secret("SMTP_PASSWORD") or get_secret("GMAIL_APP_PASSWORD")
    sender = get_secret("SMTP_FROM") or user

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Réinitialisation de votre mot de passe"
    msg["From"] = sender
    msg["To"] = to_email
    text = f"Réinitialisez votre mot de passe : {reset_url}\nCe lien expire dans 1 heure."
    html = f"""
      <div style="font-family:Arial,sans-serif;font-size:15px;color:#0A0A0A">
        <h2 style="color:#002FA7">Réinitialisation du mot de passe</h2>
        <p>Vous avez demandé la réinitialisation de votre mot de passe.</p>
        <p><a href="{reset_url}" style="display:inline-block;background:#002FA7;color:#fff;padding:12px 20px;text-decoration:none">Réinitialiser mon mot de passe</a></p>
        <p style="color:#4B5563;font-size:13px">Ce lien expire dans 1 heure. Si vous n'êtes pas à l'origine de cette demande, ignorez cet email.</p>
      </div>
    """
    msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(host, port, timeout=20) as server:
            server.starttls()
            server.login(user, password)
            server.sendmail(sender, [to_email], msg.as_string())
        return True
    except Exception as e:
        print(f"[EMAIL] Échec envoi: {e}")
        return False
