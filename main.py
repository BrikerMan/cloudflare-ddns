import logging
from typing import Optional

import requests
import yaml
from apscheduler.schedulers.background import BlockingScheduler

logging.basicConfig(level='INFO')


class CloudFlare:

    def __init__(self, auth_email: str, auth_key: str):
        self.auth_email = auth_email
        self.auth_key = auth_key

    def _get_id_for_record(self,
                           name: str,
                           zone_id: str
                           ) -> Optional[str]:
        params = {
            'name': name,
            'match': 'all'
        }
        headers = {
            'X-Auth-Email': self.auth_email,
            'X-Auth-Key': self.auth_key,
        }
        r = requests.get(f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records',
                         params=params,
                         headers=headers)
        result = r.json()['result']
        if len(result) > 0:
            return result[0]['id']

    @staticmethod
    def get_local_ip():
        headers = {'User-Agent': 'curl/7.54'}
        r = requests.get('https://www.cip.cc', headers=headers)
        ip = r.text.splitlines()[0].split(':')[1].strip()
        logging.info(f'⛅️ Local IP: {ip}')
        return ip

    def create_or_update(self,
                         *,
                         zone_id: str,
                         name: str,
                         content: str,
                         type: str = 'A',
                         ttl: int = 120,
                         proxied: bool = False):
        record_id = self._get_id_for_record(name=name, zone_id=zone_id)
        body = {
            "type": type,
            "name": name,
            "content": content,
            "ttl": ttl,
            "proxied": proxied
        }

        headers = {
            'X-Auth-Email': self.auth_email,
            'X-Auth-Key': self.auth_key,
        }

        if record_id:
            url = f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record_id}'
            r = requests.patch(url, json=body, headers=headers)
            assert r.status_code == 200
        else:
            url = f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records'
            r = requests.post(url, json=body, headers=headers)
            assert r.status_code == 200
        logging.info(f'✅ Updated {name} to {type} {content}')

    @staticmethod
    def run_with_config(config_path: str = 'config.yaml'):
        with open(config_path, 'r') as stream:
            try:
                config = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)

        local_ip = CloudFlare.get_local_ip()

        for c in config['cloudflare']:
            cloud_flare = CloudFlare(
                auth_email=c['authentication']['auth_email'],
                auth_key=c['authentication']['auth_key'],
            )

            for record in c['subdomains']:

                if record.get('content') is None:
                    record['content'] = local_ip

                cloud_flare.create_or_update(
                    zone_id=record['zone_id'],
                    name=record['name'],
                    content=record['content']
                )


if __name__ == '__main__':
    scheduler = BlockingScheduler()
    job = scheduler.add_job(CloudFlare.run_with_config, 'interval', minutes=2)
    scheduler.start()
