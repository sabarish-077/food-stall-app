# Put the Django site online

GitHub stores the source code. A Python app host is also required to run Django, serve its static files, and connect a hosted MySQL database.

## Hosting environment variables

Set these as private environment variables in the app host's dashboard:

- `DEBUG=false`
- `SECRET_KEY` to a newly generated random value
- `ALLOWED_HOSTS` to the host's assigned domain name
- `CSRF_TRUSTED_ORIGINS` to the HTTPS origin, for example `https://your-app.example.com`
- `DB_ENGINE=mysql`
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, and `DB_PORT` to the hosted MySQL service's values

Use the deployment requirements file, then run `python manage.py migrate` and `python manage.py collectstatic --noinput`. Start the web service with the included `Procfile`. Never upload `.env`, `db.sqlite3`, or a database export to a public repository.
