# SCI Community Platform

A Django web app for San Clemente Island: marketplace, lost & found, events, announcements, and emergency info, with user accounts and content moderation.

**Live site:** https://sci-list-claverlo.pythonanywhere.com/

## Requirements

- Python 3.11+
- pip

## Setup

1. **Create and activate a virtual environment**

   ```bash
   python -m venv venv
   venv\Scripts\activate      # Windows
   source venv/bin/activate   # macOS/Linux
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Create a `.env` file** in the project root (same folder as `manage.py`). All values are optional for local dev except where noted — sensible defaults are used if omitted.

   ```
   SECRET_KEY=your-secret-key
   DEBUG=true
   ALLOWED_HOSTS=localhost,127.0.0.1
   CSRF_TRUSTED_ORIGINS=

   # Email (defaults to printing emails to the console if unset)
   EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=true
   EMAIL_HOST_USER=
   EMAIL_HOST_PASSWORD=
   DEFAULT_FROM_EMAIL=

   # SMS phone verification (Twilio) - optional, skipped if unset
   TWILIO_ACCOUNT_SID=
   TWILIO_AUTH_TOKEN=
   TWILIO_FROM_NUMBER=

   # AI image moderation (OpenAI) - optional, photos auto-approve if unset
   OPENAI_API_KEY=
   OPENAI_IMAGE_MODERATION_MODEL=gpt-4o-mini

   # Where content reports get emailed
   REPORT_ADMIN_EMAIL=
   ```

4. **Run database migrations**

   ```bash
   python manage.py migrate
   ```

5. **Create an admin account**

   ```bash
   python manage.py createsuperuser
   ```

6. **Run the development server**

   ```bash
   python manage.py runserver
   ```

   Visit `http://127.0.0.1:8000/` in your browser. Admin panel is at `http://127.0.0.1:8000/admin/`.

## Notes

- Without `EMAIL_HOST_USER`/`EMAIL_HOST_PASSWORD` set, emails (like verification links) print to the console instead of sending.
- Without Twilio credentials, phone verification is skipped.
- Without `OPENAI_API_KEY`, uploaded listing photos are auto-approved instead of AI-scanned.
- Uploaded media (listing photos, etc.) is saved to the `media/` folder.
