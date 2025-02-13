module.exports = {
  apps: [
    {
      name: "django-server",
      script: "bash",
      args: "-c 'pipenv run python manage.py runserver 0.0.0.0:8000'",
      cwd: "/root/youtubeAnalyzer/django_project",
      exec_mode: "fork",
      env: {
        PYTHONUNBUFFERED: "1",
      },
    },
  ],
};
