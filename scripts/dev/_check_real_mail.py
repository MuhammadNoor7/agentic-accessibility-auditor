import httpx

c = httpx.Client(base_url="http://127.0.0.1:8002", timeout=60)
cfg = c.get("/auth/config").json()
print("dev_show_otp", cfg["dev_show_otp"], "smtp", cfg["smtp_configured"])

email = "mnoorulhaq10@gmail.com"
r = c.post("/auth/register", json={"email": email, "password": "TestPass12", "name": "Noor"})
print("register", r.status_code)

fp = c.post("/auth/forgot-password", json={"email": email})
print("forgot", fp.status_code)
body = fp.json()
print("email_sent", body.get("email_sent"))
print("debug_code", body.get("debug_code"))
print("message", body.get("message"))
assert fp.status_code == 200
assert body.get("email_sent") is True
assert not body.get("debug_code")
print("PASS — real email sent, no on-screen debug code")
