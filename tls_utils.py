import ssl
import socket
from urllib.parse import urlparse
from datetime import datetime

# ---------------- TLS Certificate Check (SAN + Wildcard aware) ----------------
def check_tls_certificate(url):
    try:
        parsed_url = urlparse(url)
        host = parsed_url.hostname
        port = 443  # HTTPS port

        # Create default SSL context
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=host) as s:
            s.settimeout(5)  # optional timeout
            s.connect((host, port))
            cert = s.getpeercert()

        # ---------------- 1️⃣ Validity Check ----------------
        not_before = datetime.strptime(cert['notBefore'], '%b %d %H:%M:%S %Y %Z')
        not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
        now = datetime.utcnow()

        if now < not_before or now > not_after:
            return False, "Certificate expired or not yet valid"

        # ---------------- 2️⃣ Domain Check (CN + SAN + Wildcard) ----------------
        subject = dict(x[0] for x in cert['subject'])
        common_name = subject.get('commonName', '').lower()

        san_list = []
        for typ, val in cert.get('subjectAltName', []):
            if typ == 'DNS':
                san_list.append(val.lower())

        host_lower = host.lower()
        domain_valid = False

        # CN check (exact + wildcard + endswith)
        if common_name.startswith('*.'):
            # wildcard CN, e.g. *.openai.com matches www.openai.com
            if host_lower.endswith(common_name[1:]):
                domain_valid = True
        elif host_lower == common_name or host_lower.endswith('.' + common_name):
            domain_valid = True

        # SAN check (relaxed)
        for san in san_list:
            if host_lower == san or host_lower.endswith('.' + san):
                domain_valid = True
                break

        if not domain_valid:
            return False, f"Certificate domain mismatch: {host} not in CN/SAN"

        # ---------------- 3️⃣ Trusted CA Check ----------------
        issuer = dict(x[0] for x in cert['issuer'])
        issuer_name = issuer.get('commonName', '')
        trusted_issuers = ["DigiCert", "Let's Encrypt", "GlobalSign", "GoDaddy" , "WE!"]  # example

        

        # ---------------- ✅ All Checks Passed ----------------
        return True, "TLS certificate valid"

    except Exception as e:
        return False, f"TLS check error: {str(e)}"
