HOSTNAME = ""
PORT = 24000

SECURE_MODE = True
SSL_CERT = "certificate file path here"
SSL_KEY = " private key file path here"

THROTTLE_MAX_USES = 2
THROTTLE_COOLDOWN = 120 # time to wait before request bucket starts refilling, in seconds
THROTTLE_DECAY = 60 # interval at which the bucket refills, in seconds

MESSAGE_TIMEOUT = 5

FILENAME = "guestbook.html"
NEXT_ENTRY_MARKER = "<!-- NEXT ENTRY HERE -->"
ENTRY_HTML = """{next_entry}
<div class="gb-entry">
    <span class="gb-name">{name}</span> <span class="timestamp">{time}</span><br>
    <span class="gb-message">{message}</span>
</div>
"""
