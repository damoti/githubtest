## Setup

create a github account for your test user
setup 2FA, on step "2. Scan this barcode with your app." click "enter this text code" to get the OTP key.

generate a temporary key:
```
>>> from pyotp import TOTP
>>> TOTP('thetextcode').now()
'012340'
```

