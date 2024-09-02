from website import create_app
import time
import pyotp
import qrcode

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
