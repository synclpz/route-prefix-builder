import requests, json, schedule, threading, time
from dns import resolver
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer

res = resolver.Resolver()
res.nameservers = ['1.1.1.1', '8.8.8.8']
res.timeout = 100
res.lifetime = 100

asns = [
    'as32934',  # meta/facebook
    'as15169',  # google
    'as11917',  # whatsapp
    'as13414',  # twitter
    'as53620',  # pinterest
    'as137437', # airbnb
    'as43996',  # booking
    'as13443'   # linkedin
    ]
domains = [
    'illustrator-uroki.com',
    'www.behance.net',
    'behance.net',
    #'habr.com',
    #'habrastorage.org',
    #'hsto.org',
    #'effect.habr.com',
    'www.reuters.com',
    'reuters.com',
    'edition.cnn.com',
    'cnn.com',
    'bbc.com',
    'www.bbc.com',
    'bbc.com',
    'static.files.bbci.co.uk',
    'nav.files.bbci.co.uk',
    'mybbc-analytics.files.bbci.co.uk',
    'gn-web-assets.api.bbc.com',
    'ichef.bbc.co.uk',
    'bbc.co.uk',
    'www.bbc.co.uk',
    'static.bbci.co.uk',
    'emp.bbci.co.uk',
    'cisco.com',
    'community.cisco.com',
    'nstec.com',
    'www.ntsec.com',
    'www.the-village.ru',
    'the-village.ru',
    'www.bbcrussian.com',
    'bbcrussian.com',
    'bestbuy.com',
    'support.code42.com',
    'code42.com',
    'emclient.com',
    'www.emclient.com',
    'apt.releases.hashicorp.com',
    'releases.hashicorp.com',
    'hashicorp.com'    
]
prefixes_base = ['193.0.6.150/32'] # stat.ripe.net
prefixes = []

def run(server_class=HTTPServer, handler_class=BaseHTTPRequestHandler):
  server_address = ('', 8000)
  httpd = server_class(server_address, handler_class)
  try:
      httpd.serve_forever()
  except KeyboardInterrupt:
      httpd.server_close()

class HttpGetHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        body = '\n'.join(prefixes)
        self.wfile.write(body.encode())

def init_prefixes():
    global prefixes
    prefixes = []
    prefixes.append('/ip firewall address-list remove [/ip firewall address-list find list=VPN-PREFIX-LIST]')
    prefixes.append('/ipv6 firewall address-list remove [/ipv6 firewall address-list find list=VPN-PREFIX-LIST]')

def append_prefix(p):
    global prefixes
    if ':' not in p:
        prefixes.append('/ip firewall address-list add list=VPN-PREFIX-LIST address=' + p)
    else:
        prefixes.append('/ipv6 firewall address-list add list=VPN-PREFIX-LIST address=' + p)
       

def update():
    px = []
    px.append(*prefixes_base)
    for asn in asns:
        try:
            resp = requests.get('https://stat.ripe.net/data/announced-prefixes/data.json?resource=' + asn).text
            prefixes_retrieved = json.loads(resp)["data"]["prefixes"]
            for p in prefixes_retrieved:
                px.append(p["prefix"])
        except:
            continue
    for d in domains:
        try:
            answers = res.resolve(d, "A")
            for rdata in answers:
                px.append(rdata.to_text() + "/32")
        except:
            continue
    px = list(set(px))
    init_prefixes()
    for p in px:
        append_prefix(p)

def run_continuously(interval=1):
    cease_continuous_run = threading.Event()
    class ScheduleThread(threading.Thread):
        @classmethod
        def run(cls):
            while not cease_continuous_run.is_set():
                schedule.run_pending()
                time.sleep(interval)

    continuous_thread = ScheduleThread()
    continuous_thread.start()
    return cease_continuous_run

update()
schedule.every(60).minutes.do(update)
stop_run_continuously = run_continuously(5)
run(HTTPServer, HttpGetHandler)
stop_run_continuously.set()
