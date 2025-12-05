import os
import datetime
from django.conf import settings
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dateutil import tz


SCOPES = ['https://www.googleapis.com/auth/calendar']


def _get_service():
    if not settings.USE_GOOGLE_CALENDAR:
        return None  # não usa Google Calendar
    sa_file = getattr(settings, "GOOGLE_SERVICE_ACCOUNT_FILE", "client_secret.json")
    credentials = service_account.Credentials.from_service_account_file(sa_file, scopes=SCOPES)
    service = build("calendar", "v3", credentials=credentials)
    return service


def verificar_disponibilidade(start_dt, end_dt):

    service = _get_service()
    if service is None:
        return True

    # converter para RFC3339 com timezone
    tzinfo = tz.gettz("America/Sao_Paulo")
    if start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=tzinfo)
    if end_dt.tzinfo is None:
        end_dt = end_dt.replace(tzinfo=tzinfo)

    time_min = start_dt.isoformat()
    time_max = end_dt.isoformat()

    events_result = service.events().list(
        calendarId=settings.GOOGLE_CALENDAR_ID,
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])
    return len(events) == 0


def criar_evento(summary, start_dt, end_dt, description=""):
    service = _get_service()
    if service is None:
        return "dummy_event_id"

    # converter para RFC3339 com timezone
    tzinfo = tz.gettz("America/Sao_Paulo")
    if start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=tzinfo)
    if end_dt.tzinfo is None:
        end_dt = end_dt.replace(tzinfo=tzinfo)

    event = {
        'summary': summary,
        'description': description,
        'start': {'dateTime': start_dt.isoformat(), 'timeZone': 'America/Sao_Paulo'},
        'end': {'dateTime': end_dt.isoformat(), 'timeZone': 'America/Sao_Paulo'},
        'reminders': {'useDefault': True},
    }

    created = service.events().insert(calendarId=settings.GOOGLE_CALENDAR_ID, body=event).execute()
    return created.get('id')
