# onedns

Command-line interface for [onedns.io](https://onedns.io) — enterprise DNS management powered by [dnsscienced](https://github.com/afterdarksys/dnsscienced).

## Installation

**Requirements:** Python 3.10+, `requests>=2.33.0`, `urllib3>=2.7.0`

```bash
pip install 'requests>=2.33.0' 'urllib3>=2.7.0'
curl -o /usr/local/bin/onedns https://raw.githubusercontent.com/afterdarksys/onedns-cli/main/onedns
chmod +x /usr/local/bin/onedns
```

Or clone and symlink:

```bash
git clone https://github.com/afterdarksys/onedns-cli
ln -s $PWD/onedns-cli/onedns /usr/local/bin/onedns
```

## Authentication

```bash
onedns login --api-key YOUR_API_KEY
```

API keys are stored in `~/.config/onedns/config`. Generate one at https://onedns.io/settings/api-keys.

Set `ONEDNS_URL` to override the default endpoint (useful for self-hosted deployments):

```bash
export ONEDNS_URL=https://dns.yourcompany.com
```

TLS certificates are verified. For a private certificate authority, set
`REQUESTS_CA_BUNDLE` to your CA bundle file. API redirects are refused; configure
`ONEDNS_URL` with the final trusted endpoint. Requests use a 10-second connection
timeout and a 30-second read timeout.

Saved credentials are replaced atomically with owner-only permissions (`0600`).
Run `onedns login` again to secure an existing credential file.

## Tests

Run the offline regression suite after installing `requests`:

```bash
python3 -m unittest discover -s tests -v
```

## Commands

### Auth

```
onedns login          Authenticate with an API key
onedns logout         Remove saved credentials
onedns whoami         Show current authentication status
onedns api-keys list  List API keys on your account
onedns api-keys create --name "CI"
onedns api-keys revoke <id>
```

### Zones

```
onedns zones list
onedns zones get <zone>
onedns zones create <zone>
onedns zones delete <zone>
onedns zones verify <zone>
onedns zones sync <zone>
onedns zones export <zone> [--format bind|dnsscienced]
onedns zones import <zone> --file zone.txt [--format bind|dnsscienced]
onedns zones history <zone>
```

### Records

Supports all DNS record types: A, AAAA, CNAME, MX, TXT, NS, PTR, SRV, CAA, TLSA, SSHFP, NAPTR, HTTPS, SVCB, SMIMEA, CERT, HINFO, IPSECKEY, OPENPGPKEY, URI, EUI48, EUI64, CDS, CDNSKEY, ZONEMD, CSYNC, RP, AFSDB, KX, DHCID, APL, LOC, DS, DNSKEY, and any valid DNS type.

```
onedns records list <zone> [--type A]
onedns records create <zone> --type A --name www --content 1.2.3.4 --ttl 300
onedns records update <zone> <record_id> --content 1.2.3.5
onedns records delete <zone> <record_id>
onedns records set <zone> --type CNAME --name api --content lb.example.com
```

`set` is an upsert: updates if a matching name+type exists, creates otherwise.

### DNSSEC

```
onedns dnssec enable <zone>
onedns dnssec status <zone>
onedns dnssec get-ds <zone>
```

### Zone Transfers

```
onedns transfers list <zone>
onedns transfers pull <zone>
onedns transfers push <zone>
```

### Analytics

```
onedns analytics <zone> [--days 7]
```

### Threat Intelligence

```
onedns intel reputation <zone> --domain example.com
onedns intel passive-dns <zone> --domain example.com
onedns intel malware <zone>
onedns intel subdomains <zone> --domain example.com
onedns intel summary <zone>
```

### DNS Firewall

```
onedns firewall rules list <zone>
onedns firewall rules add <zone> --domain evil.com --action block
onedns firewall rules delete <zone> <rule_id>
onedns firewall stats <zone>
```

Actions: `allow`, `block`, `nxdomain`, `drop`, `rewrite`, `redirect`

### ThreatScript

```
onedns script push <zone> --file policy.ts
onedns script delete <zone>
onedns script stats <zone>
```

### Server (dnsscienced)

```
onedns server status
onedns server stats
onedns server metrics
onedns server reload
onedns server license
```

### Cache

```
onedns cache stats
onedns cache flush [--domain example.com] [--type A]
onedns cache lookup <domain> [--type A]
onedns cache prefetch <domain> [--type A]
```

### Domains

```
onedns domains list
onedns domains check <domain>
onedns domains nameservers <domain> --ns ns1.example.com --ns ns2.example.com
onedns domains auth-code <domain>
```

### Rate Limiting

```
onedns ratelimit get
onedns ratelimit set [--qps 1000] [--burst 200] [--enabled true]
```

## Examples

```bash
# Add an A record
onedns records create example.com --type A --name @ --content 203.0.113.10

# Add MX records
onedns records create example.com --type MX --name @ --content mail.example.com --priority 10

# Add a CAA record
onedns records create example.com --type CAA --name @ --content '0 issue "letsencrypt.org"'

# Enable DNSSEC and get DS record for registrar
onedns dnssec enable example.com
onedns dnssec get-ds example.com

# Import a BIND zone file
onedns zones import example.com --file example.com.zone --format bind

# Export to dnsscienced YAML format
onedns zones export example.com --format dnsscienced > example.com.dnszone

# Block a malicious domain in the firewall
onedns firewall rules add example.com --domain malware.example.net --action nxdomain

# Check threat intelligence on a domain
onedns intel reputation example.com --domain suspicious.net
```

## Self-hosted

Point the CLI at your own dnsscienced instance:

```bash
export ONEDNS_URL=https://dns.yourcompany.com
onedns login --api-key YOUR_KEY
```

## License

MIT
