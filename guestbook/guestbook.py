# The worst guestbook script you have ever seen ever in your life, by riff

# actually, now that i stopped using socket like an idiot, it looks better.
# there's still definitely a better way to do it, but i would rather swiss-army-
# knife it with py3 than try to wrestle apache into doing my bidding.

# plus, i don't actually know what kind of cross-site restrictions might
# get in my way if i try to submit a form to a backend of another origin.
# websocket might actually be my safest bet!

#pip3 install websockets
import websockets, asyncio, time, json, ssl
from guestbook_config import *

clientUses = {}
# let me think here. how would i do stateful rate limits?
# so, i could have a bucket tallying uses, and a timestamp...?
# and then, when a client attempts a use, it reduces the uses by
# (time - tstamp - cooldown) / decayRate, clamped between 0 and maxUses
# if the uses are still maxed out, decline the request

def attemptUse(addr): # returns True if rate limit checks pass, False otherwise
    if not addr in clientUses:
        clientUses[addr] = {
            'uses': 0,
            'timestamp': time.time()
            }
    clu = clientUses[addr]
    elapsed = time.time() - clu['timestamp']
    clu['uses'] -= min(THROTTLE_MAX_USES, max(0, # clamp between 0 and max
                int((elapsed - THROTTLE_COOLDOWN) / THROTTLE_DECAY) ))

    clu['timestamp'] = time.time()
    result = False
    if clu['uses'] < THROTTLE_MAX_USES:
        clu['uses'] += 1
        result = True

    clientUses[addr] = clu
    return result


def htmSanitize(s):
    # this feels ugly
    return s.replace("<", "&lt;").replace(">", "&gt;").replace("&", "&amp;").replace("\"", "&quot;").replace("\n", "<br \\>")

def amendHTML(name, msg): # because who needs a database, right?
    with open(FILENAME, 'r') as f:
        gb_html = f.read()
    entry = ENTRY_HTML.format(
        name = htmSanitize(name),
        time = int(time.time()),
        message = htmSanitize(msg),
        next_entry = NEXT_ENTRY_MARKER
        )
    gb_html = gb_html.replace(NEXT_ENTRY_MARKER, entry)
    with open(FILENAME, 'w') as f:
        f.write(gb_html)

# just realized i gutted the message queue thread in the switch to websockets
# from pure sockets and threads
# i need that back so i can avoid write collisions
# (note to self: is there an async implementation of this?)
# (note to self 2: yes!!!! use asyncio.lock and that will do the same thing)

htmWriteLock = asyncio.Lock() # forces one-at-a-time access!

async def handle_ws(websocket):
    print("Got connection from", websocket.remote_address)
    try:
        message = await asyncio.wait_for(websocket.recv(), MESSAGE_TIMEOUT)
        print("Got message:", message)
        info = json.loads(message)

        if len(info['name']) == 0 or len(info['name']) == 0:
            await websocket.send("Fields cannot be empty.")

        else:
            if not attemptUse(websocket.remote_address[0]):
                await websocket.send("You are posting too fast.")
                await websocket.close()
                return
            # functionally equivalent to acquiring a lock & releasing when done
            async with htmWriteLock:
                amendHTML(info['name'], info['msg'])
            await asyncio.sleep(0.5) # maybe apache needs some time to react?
            await websocket.send("OK")

    except TimeoutError:
        print(websocket.remote_address, "sent no data; connection timed out")
    finally:
        await websocket.close()

if SECURE_MODE:
    ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_ctx.load_cert_chain(SSL_CERT, keyfile=SSL_KEY)

async def ws_server():
    print("Starting websocket listen server")
    async with websockets.serve(handle_ws, HOSTNAME, PORT,
                    ssl = ssl_ctx if SECURE_MODE else None):
        print("Server started (probably)")
        await asyncio.Future()  # run forever

asyncio.run(ws_server())
