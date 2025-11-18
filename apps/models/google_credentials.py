from django.db import models


class GoogleCalendarCredentials(models.Model):  # TODO change import style
    user = models.OneToOneField('apps.User', models.CASCADE, related_name='google_calendar_credentials')
    token = models.CharField(max_length=255)
    refresh_token = models.CharField(max_length=255, null=True, blank=True)
    token_uri = models.CharField(max_length=255)
    client_id = models.CharField(max_length=255)
    client_secret = models.CharField(max_length=255)
    scopes = models.TextField()

    def __str__(self):
        return f"Credentials for {self.user.email}"
