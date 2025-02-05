```bash
export client_name=
export postal_code=

apt update
apt install p7zip-full -y
apt install python3-pip -y
apt install vim -y
git clone https://github.com/clem9669/hashcat-rule.git
git clone https://github.com/clem9669/wordlists.git
git clone https://github.com/t3l3machus/psudohash.git
git clone https://github.com/stealthsploit/OneRuleToRuleThemStill.git
git clone https://github.com/p0dalirius/GeoWordlists.git
cd psudohash; yes | python3 psudohash.py -w $client_name --common-paddings-after -y 1990-2030 -o ../wordlists/psudohash.txt; cd ..
pip install -r GeoWordlists/requirements.txt; GeoWordlists/GeoWordlists.py -p $postal_code -k 100 -o wordlists/geowordlist.txt
cd wordlists; for f in *.7z; do 7z x "$f" && rm "$f"; done; cd ..
curl https://raw.githubusercontent.com/tarraschk/richelieu/refs/heads/master/french_passwords_top20000.txt -O wordlists/richelieu.txt
hashcat -m 1000 secretsdump.ntds_anon -a3 '?a?a?a?a?a?a?a' -i
hashcat -m 1000 secretsdump.ntds_anon -1 '?u?l?d' -a3 '?1?1?1?1?1?1?1?1?a' -i
hashcat -m 1000 secretsdump.ntds_anon wordlists/psudohash.txt
hashcat -m 1000 secretsdump.ntds_anon wordlists/geowordlist.txt
hashcat -m 1000 secretsdump.ntds_anon wordlists/ -r OneRuleToRuleThemStill/OneRuleToRuleThemStill.rule --loopback
hashcat -m 1000 secretsdump.ntds_anon wordlists/ -r hashcat-rule/clem9669_medium.rule --loopback
```

