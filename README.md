```bash
export client_name=
export postal_code=
export ntds_filename=secretsdump.ntds_anon

apt update
apt install p7zip-full -y
apt install python3-pip -y
apt install vim -y
git clone https://github.com/clem9669/hashcat-rule.git --depth 1
git clone https://github.com/clem9669/wordlists.git --depth 1
git clone https://github.com/t3l3machus/psudohash.git --depth 1
git clone https://github.com/stealthsploit/OneRuleToRuleThemStill.git --depth 1
git clone https://github.com/p0dalirius/GeoWordlists.git --depth 1
cd psudohash; yes | python3 psudohash.py -w $client_name --common-paddings-after -y 1990-2030 -o ../wordlists/psudohash.txt; cd ..
pip install -r GeoWordlists/requirements.txt; GeoWordlists/GeoWordlists.py -p $postal_code -k 100 -o wordlists/geowordlist.txt
wget https://hashmob.net/api/v2/downloads/research/official/hashmob.net_2025-02-02.found.7z -O wordlists/hashmob_full.7z
cd wordlists; for f in *.7z; do 7z x "$f" && rm "$f"; done; cd ..
curl https://raw.githubusercontent.com/tarraschk/richelieu/refs/heads/master/french_passwords_top20000.txt -O wordlists/richelieu.txt
hashcat -m 1000 $ntds_filename -a3 '?a?a?a?a?a?a?a' -i
hashcat -m 1000 $ntds_filename -1 '?u?l?d' -a3 '?1?1?1?1?1?1?1?a' -i
hashcat -m 1000 $ntds_filenamen wordlists/psudohash.txt
hashcat -m 1000 $ntds_filename wordlists/geowordlist.txt
hashcat -m 1000 $ntds_filename wordlists/ -r OneRuleToRuleThemStill/OneRuleToRuleThemStill.rule --loopback
hashcat -m 1000 $ntds_filename wordlists/ -r hashcat-rule/clem9669_medium.rule --loopback
hashcat -m 1000 $ntds_filename -1 '?u?l?d' -a3 '?1?1?1?1?1?1?1?1?a' -i
hashcat -m 1000 $ntds_filename -1 '?u?l?d' -a3 '?1?1?1?1?1?1?1?1?1?a' -i
```

todo : 
- add https://github.com/p0dalirius/pyLDAPWordlistHarvester
- update hashmob wordlist to set the correct day in the url
- ajouter weakpass
- ajouter rockyou
