#!/bin/bash

sudo apt install wget aria2 lbzip2 ripgrep python3 python3-pip lzip -y
pip install unidecode

git clone --depth 1 https://github.com/clem9669/wordlists.git

cd wordlists
find . -type f -not -path './.git/*' -not -path './.git' -not -name '.gitignore' -exec bash -c '
  for f; do
    if [ "$f" != "./.git" ]; then
      mv -- "$f" .
    fi
  done
' _ {} +

wordlist_hashmob=$(curl https://hashmob.net/api/v2/downloads/research/official | jq '.[] | select(.name == "HashMob Combined Full").file_name' -r)
aria2c --max-connection-per-server=16 --min-split-size=20M --split=16 https://hashmob.net/api/v2/downloads/research/official/$wordlist_hashmob -o hashmob_full.7z
7z x "*.7z"
rm *.7z
mkdir processed/
cat * > processed/clem_hashmob_full
# Cleanup
find . ! -name 'clem_hashmob_full' -type f -exec rm -f {} +
# Recup wikipedia (mots et titres)
wget -O- https://dumps.wikimedia.your.org/frwiki/latest/frwiki-latest-pages-articles.xml.bz2 | LC_ALL=C lbunzip2 -dc -v | tee >(rg -o '\b[[:alnum:]]{4,}\b' > fr_wordlist_wki.txt.tmp) | rg -o '(?<=title>)[^<]+' --pcre2 > fr_title_wki.txt.tmp

# aria2c --max-connection-per-server=16 --min-split-size=20M --split=16 https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-pages-articles.xml.bz2
# LC_ALL enwiki-latest-pages-articles.xml.bz2 -v | tee >(rg -o '\b[[:alnum:]]{4,}\b' > en_wordlist_wki.txt.tmp) | rg -o '(?<=title>)[^<]+' --pcre2 > en_title_wki.txt.tmp

rm *.bz2

# Liste des noms d'entreprises
wget -O- https://www.data.gouv.fr/fr/datasets/r/0835cd60-2c2a-497b-bc64-404de704ce89 | funzip | cut -d ',' -f6,10 | tr ',' '\n' | grep -Pv '^$' > entreprises_cust.txt.tmp

# Liste des rues etc
wget -O- --retry-connrefused --waitretry=1 --read-timeout=20 --timeout=5 -t 0 https://adresse.data.gouv.fr/data/ban/adresses/latest/csv/adresses-france.csv.gz | zcat | awk -F';' '{print $5 > "rues_cust.txt.tmp"; print $6 > "code_postal_cust.txt"; print $8 > "villes_cust.txt.tmp"}'

python3 ../parsePythonWl.py fr_title_wki.txt.tmp 2 > fr_title_wki.txt && cat fr_title_wki.txt.tmp >> fr_title_wki.txt
python3 ../parsePythonWl.py en_title_wki.txt.tmp 2 > en_title_wki.txt && cat en_title_wki.txt.tmp >> en_title_wki.txt
python3 ../parsePythonWl.py rues_cust.txt.tmp 2 > rues_cust.txt
python3 ../parsePythonWl.py villes_cust.txt.tmp 2 > villes_cust.txt
python3 ../parsePythonWl.py entreprises_cust.txt.tmp 2 > entreprises_cust.txt

awk -F"[ ']" '{for(i=1; i<=NF; i++) print $i}' rues_cust.txt.tmp >> rues_cust.txt && cat rues_cust.txt.tmp >> rues_cust.txt
awk -F"[ ']" '{for(i=1; i<=NF; i++) print $i}' villes_cust.txt.tmp >> villes_cust.txt && cat villes_cust.txt.tmp >> villes_cust.txt
awk -F"[ ']" '{for(i=1; i<=NF; i++) print $i}' entreprises_cust.txt.tmp >> entreprises_cust.txt && cat entreprises_cust.txt.tmp >> entreprises_cust.txt

#Premier cleanup
rm *.tmp

# Liste des noms / prenoms
wget -O- https://www.insee.fr/fr/statistiques/fichier/3536630/noms2008dep_txt.zip | funzip | cut -d$'\t' -f1 > noms_cust.txt
wget -O- https://static.data.gouv.fr/resources/liste-de-prenoms-et-patronymes/20181014-162921/patronymes.csv | cut -d ',' -f 1 >> noms_cust.txt
wget -O- https://www.insee.fr/fr/statistiques/fichier/7633685/nat2022_csv.zip | funzip | cut -d ';' -f2 > prenoms_cust.txt

# Liste des acteurs
wget -O- https://datasets.imdbws.com/name.basics.tsv.gz | zcat | cut -d$'\t' -f2 > acteurs_cust.txt.tmp
#Liste titres films
wget -O- https://datasets.imdbws.com/title.akas.tsv.gz | zcat | cut -d$'\t' -f3 > films_cust.txt.tmp
#Liste des persos fictifs
wget -O- https://datasets.imdbws.com/title.principals.tsv.gz | zcat | cut -d$'\t' -f6 | sed -E 's/^\["(.*)"\]$/\1/' | grep -v "\\N" | jq -R '.' -r > characters_fictif_cust.txt.tmp

python3 ../parsePythonWl.py acteurs_cust.txt.tmp 2 > acteurs_cust.txt && cat acteurs_cust.txt.tmp >> acteurs_cust.txt
python3 ../parsePythonWl.py films_cust.txt.tmp 2 > films_cust.txt && cat films_cust.txt.tmp >> films_cust.txt
python3 ../parsePythonWl.py characters_fictif_cust.txt.tmp 2 > characters_fictif_cust.txt && cat characters_fictif_cust.txt.tmp >> characters_fictif_cust.txt


rm *.tmp


# THX Clem
curl -s 'https://trends.google.com/trends/trendingsearches/daily/rss?geo=FR' | xmllint --xpath "//item/title" - | sed -e 's/<[^>]*>//g' >> news_FR.txt
curl -s 'https://trends.google.com/trends/trendingsearches/daily/rss?geo=BE' | xmllint --xpath "//item/title" - | sed -e 's/<[^>]*>//g' >> news_BE.txt
curl -s 'https://trends.google.com/trends/trendingsearches/daily/rss?geo=CH' | xmllint --xpath "//item/title" - | sed -e 's/<[^>]*>//g' >> news_CH.txt
curl -s 'https://trends.google.com/trending/rss?geo=FR' | xmllint --xpath "//item/title" - | sed -e 's/<[^>]*>//g' >> news_FR.txt
curl -s 'https://trends.google.com/trending/rss?geo=BE' | xmllint --xpath "//item/title" - | sed -e 's/<[^>]*>//g' >> news_BE.txt
curl -s 'https://trends.google.com/trending/rss?geo=CH' | xmllint --xpath "//item/title" - | sed -e 's/<[^>]*>//g' >> news_CH.txt


for f in ./*; do
    echo "Processing $f"
    duplicut "$f" -o "$f.dedupe"
    rm "$f"
done


cat *.dedupe > full_wl_cust.cated.txt
rm *.dedupe
duplicut full_wl_cust.cated.txt -o output_sns
rm *.txt
mv output_sns ./processed
cd processed/
cat output_sns clem_hashmob_full > full_not_dedupe
rm output_sns clem_hashmob_full
duplicut full_not_dedupe -o full_dedupe
rm full_not_dedupe
lrzip -b full_dedupe -v
rm full_dedupe
