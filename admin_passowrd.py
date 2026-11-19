# Run ONCE to choose your admin username and password:  python set_admin_password.py
import getpass
from auth import save_credentials

username = input("Choose an admin username: ").strip()
password = getpass.getpass("Choose a strong password (10+ characters): ")
if not username or len(password) < 10:
    raise SystemExit("Username is empty or password is shorter than 10 characters. Run again.")
if password != getpass.getpass("Type the password again: "):
    raise SystemExit("Passwords did not match. Run again.")
save_credentials(username, password)
print("Saved! Only this username and password can open the admin panel.")