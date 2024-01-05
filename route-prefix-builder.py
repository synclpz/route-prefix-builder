import requests, json, schedule, threading, time
from dns import resolver
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer
from aggregate_prefixes import aggregate_prefixes

res = resolver.Resolver()
res.nameservers = ['1.1.1.1', '8.8.8.8']
res.timeout = 100
res.lifetime = 100

asns = [
    'as32934',    # meta/facebook
    'as54115',    # meta/facebook
    'as63293',    # meta/facebook
    'as149642',   # meta/facebook
    'as15169',    # google
    'as11917',    # whatsapp
    'as13414',    # twitter
    'as53620',    # pinterest
    'as137437',   # airbnb
    'as43996',    # booking
    'as13443',    # linkedin
    'as55163',    # linkedin
    'as40793',    # linkedin
    'as30427',    # linkedin
    'as20366',    # linkedin
    'as202745',   # linkedin
    'as20049',    # linkedin
    'as197613',   # linkedin
    'as14413',    # linkedin
    'as137709',   # linkedin
    'as132466',   # linkedin
    'as8068',     # ms
    'as8069',     # ms
    'as8070',     # ms
    'as8071',     # ms
    'as8075',     # ms
    'as16509',    # amazon
    'as13335'     # cloudflare
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
    'less.works',
    'torproject.org',
    'bridges.torproject.org',
    'squareup.com'
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
        body = '\n'.join(prefixes).encode()
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)    

def update():
    global prefixes
    px = []
    px6 = []
    px.append(*prefixes_base)
    for asn in asns:
        try:
            resp = requests.get('https://stat.ripe.net/data/announced-prefixes/data.json?resource=' + asn).text
            prefixes_retrieved = json.loads(resp)["data"]["prefixes"]
            for pref in prefixes_retrieved:
                p = pref["prefix"]
                if ':' not in p:
                    px.append(p)
                else:
                    px6.append(p)
        except:
            continue
    for d in domains:
        try:
            answers = res.resolve(d, "A")
            for rdata in answers:
                px.append(rdata.to_text() + "/32")
        except:
            continue
    prefixes = []
    prefixes.append('# Total v4 collected: ' + str(len(px)))
    prefixes.append('# Total v6 collected: ' + str(len(px6)))
    px = list(aggregate_prefixes(px))
    px6 = list(aggregate_prefixes(px6))
    prefixes.append('# Aggregated v4: ' + str(len(px)))
    prefixes.append('# Aggregated v6: ' + str(len(px6)))
    prefixes.append('/ip firewall address-list remove [/ip firewall address-list find list=VPN-PREFIX-LIST]')
    for p in px:
        prefixes.append('/ip firewall address-list add list=VPN-PREFIX-LIST address=' + str(p))
    prefixes.append('/ipv6 firewall address-list remove [/ipv6 firewall address-list find list=VPN-PREFIX-LIST]')
    for p6 in px6:
        prefixes.append('/ipv6 firewall address-list add list=VPN-PREFIX-LIST address=' + str(p6))

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
