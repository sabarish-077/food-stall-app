# Connect the food stall app to MySQL

The app currently uses `db.sqlite3`. Keep this file until you have migrated the data into MySQL.

## 1. Create a database and app user

In MySQL Workbench, connect to your local MySQL server and run this SQL. Replace the example password with one you choose:

```sql
CREATE DATABASE foodstall_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'foodstall_user'@'127.0.0.1' IDENTIFIED BY 'choose-a-strong-password';
GRANT ALL PRIVILEGES ON foodstall_db.* TO 'foodstall_user'@'127.0.0.1';
```

## 2. Install the MySQL driver

Open PowerShell in this `backend` folder, activate the project's virtual environment, and install the optional MySQL driver:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-mysql.txt
```

## 3. Preserve the current users, menu, orders, and bookings

While the project still uses SQLite, export its data before switching:

```powershell
$env:DB_ENGINE = "sqlite"
python manage.py dumpdata --natural-foreign --natural-primary --exclude contenttypes --exclude auth.permission --indent 2 -o mysql-data.json
```

Copy `.env.example` to `.env`. In `.env`, change `DB_ENGINE` to `mysql` and enter the database username and password you created in step 1. Keep `.env` private; it is excluded from Git.

## 4. Create the tables and import the saved data

In the same PowerShell window, point this one-time command at MySQL, then create tables and load the saved data:

```powershell
$env:DB_ENGINE = "mysql"
python manage.py migrate
python manage.py loaddata mysql-data.json
```

Stop and restart the Django development server so it also reads the MySQL settings. Keep `mysql-data.json` as a backup until you confirm the menu and orders appear in the admin site.
