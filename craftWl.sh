#!/bin/bash

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if git is installed
if ! command_exists git; then
    echo "Installing git..."
    sudo apt update
    sudo apt install git -y
fi

if ! command_exists pip; then
    echo "Installing pip..."
    sudo apt install python3-pip -y
fi
if ! command_exists aria2c; then
    echo "Installing aria2c..."
    sudo apt install aria2 -y
fi


if ! command_exists 7z; then
    echo "Installing ripgrep..."
    apt install p7zip-full p7zip-rar -y
fi
# Clone the repository if it doesn't exist
if ! command_exists duplicut; then
    echo "Cloning duplicut repository..."
    git clone https://github.com/nil0x42/duplicut
    cd duplicut/ && make && sudo make install
    cd ..
fi

# Install necessary packages if they are not already installed
packages=("jq" "wget" "lbzip2" "python3" "lrzip")
for package in "${packages[@]}"; do
    if ! command_exists $package; then
        echo "Installing $package..."
        sudo apt install $package -y
    fi
done

if ! command_exists rg; then
    echo "Installing ripgrep..."
    wget  https://github.com/BurntSushi/ripgrep/releases/download/14.1.1/ripgrep_14.1.1-1_amd64.deb -O /tmp/ripgrep.deb && sudo dpkg -i /tmp/ripgrep.deb
fi
# Install unidecode using pip if it is not already installed
if ! python3 -c "import unidecode" &> /dev/null; then
    echo "Installing unidecode..."
    pip install unidecode
fi

if ! command_exists cargo; then
    echo "Installing cargo rust"
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
fi
if ! command_exists cracken; then
    echo "Installing cargo cracken"
    cargo install cracken
fi


echo "All necessary components are installed."


# --- Prebuilt Wordlists ---

# Clem
git clone --depth 1 https://github.com/clem9669/wordlists.git

cd wordlists
find . -type f -not -path './.git/*' -not -path './.git' -not -name '.gitignore' -exec bash -c '
  for f; do
    if [ "$f" != "./.git" ]; then
      mv -- "$f" .
    fi
  done
' _ {} +
rm immatriculation.7z phone_number_fr.7z phone_number_fr_33.7z private_ip_*
wordlist_hashmob=$(curl https://hashmob.net/api/v2/downloads/research/official | jq '.[] | select(.name == "HashMob Combined Full").file_name' -r)
aria2c --max-connection-per-server=16 --min-split-size=20M --split=16 https://hashmob.net/api/v2/downloads/research/official/$wordlist_hashmob -o hashmob_full.7z
7z x "*.7z"
rm *.7z
mkdir processed/
cat * > processed/clem_hashmob_full
# Cleanup
find . ! -name 'clem_hashmob_full' -type f -exec rm -f {} +

# --- Fin prebuilt wordlists ---

# Build combinaison phrases

cd cust_phrases
cracken -w verb_vow -w det -w nouns "j'?w1 ?w2 ?w3" -o poc_vow && cracken -w verb_cons -w det -w nouns "je ?w1 ?w2 ?w3" -o poc_cons
mv poc_cons phrases_fr_custom
cat poc_vow >> phrases_fr_custom
rm poc_vow
sed -i "/l' /d" phrases_fr_custom
mv phrases_fr_custom /root/serve/
cd ../
# Recup wikipedia (mots et titres)
wget -O- https://dumps.wikimedia.your.org/frwiki/latest/frwiki-latest-pages-articles.xml.bz2 | LC_ALL=C lbunzip2 -dc -v | tee >(rg -o '\b[[:alnum:]]{4,}\b' | duplicut -o fr_wordlist_wki.wiki.tmp) | rg -o '(?<=title>)[^<]+' --pcre2 | duplicut -o fr_wki.title.tmp
# Recup Wiktionary fr / en
wget -O- https://dumps.wikimedia.org/frwiktionary/latest/frwiktionary-latest-pages-articles.xml.bz2 | LC_ALL=C lbunzip2 -dc -v | tee >(rg -o '\b[[:alnum:]]{4,}\b' | duplicut -o fr_wordlist_wiktionnary.wiki.tmp) | rg -o '(?<=title>)[^<]+' --pcre2 | duplicut -o fr_wiktionnary.title.tmp
wget -O- https://dumps.wikimedia.org/enwiktionary/latest/enwiktionary-latest-pages-articles.xml.bz2 | LC_ALL=C lbunzip2 -dc -v | tee >(rg -o '\b[[:alnum:]]{4,}\b' | duplicut -o en_wordlist_wiktionnary.wiki.tmp) | rg -o '(?<=title>)[^<]+' --pcre2 | duplicut -o en_wiktionnary.title.tmp
wget -O- https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-all-titles.gz | zcat | awk -F$'\t' '{ if ($1 != 3) print $2 }' | duplicut -o en_wki.title.tmp


echo "Processing wiki content (Hit key at any time to see duplicut progress)..."
cat *.wiki.tmp > full_wiki_content_fr_en
rm *.wiki.tmp
duplicut full_wiki_content_fr_en -o processed/full_wiki_content_fr_en_dedupe
rm full_wiki_content_fr_en

echo "Processing wiki titles"
cat *.title.tmp | duplicut -o all_wiki_titles
rm *.title.tmp
python3 ../parsePythonWl.py all_wiki_titles 1 > all_wiki_titles_full_parsed.txt
rm all_wiki_titles
duplicut all_wiki_titles_full_parsed.txt -o processed/all_wiki_titles_full_dedupe
rm all_wiki_titles_full_parsed.txt

echo "Wiki done, doing data.gouv.fr now"
# Final files : processed/full_wiki_content_fr_en_dedupe     processed/all_wiki_titles_full_dedupe 

# Liste des noms d'entreprises
wget -O- https://www.data.gouv.fr/fr/datasets/r/0835cd60-2c2a-497b-bc64-404de704ce89 | funzip | cut -d ',' -f6,10 | tr ',' '\n' | grep -Pv '^$' | duplicut -o entreprises_cust.txt.tmp

# Liste des rues etc
wget -O- --retry-connrefused --waitretry=1 --read-timeout=20 --timeout=5 -t 0 https://adresse.data.gouv.fr/data/ban/adresses/latest/csv/adresses-france.csv.gz | zcat | awk -F';' '{print $5 | duplicut -o "rues_cust.txt.tmp"; print $6 | duplicut -o "code_postal_cust.txt"; print $8 | duplicut -o "villes_cust.txt.tmp"}'

echo "Processing all data.gouv.fr files"
python3 ../parsePythonWl.py rues_cust.txt.tmp 1 | duplicut -o rues_cust.txt
python3 ../parsePythonWl.py villes_cust.txt.tmp 1 | duplicut -o villes_cust.txt
python3 ../parsePythonWl.py entreprises_cust.txt.tmp 1 | duplicut -o entreprises_cust.txt

awk -F"[ ']" '{for(i=1; i<=NF; i++) print $i}' rues_cust.txt.tmp >> rues_cust.txt
awk -F"[ ']" '{for(i=1; i<=NF; i++) print $i}' villes_cust.txt.tmp >> villes_cust.txt
awk -F"[ ']" '{for(i=1; i<=NF; i++) print $i}' entreprises_cust.txt.tmp >> entreprises_cust.txt
echo "Done, cleanup..."

# Cleanup 2
rm *.txt.tmp

# Liste des noms / prenoms
wget -O- https://www.insee.fr/fr/statistiques/fichier/3536630/noms2008dep_txt.zip | funzip | cut -d$'\t' -f1 | duplicut -o noms_cust.txt
wget -O- https://static.data.gouv.fr/resources/liste-de-prenoms-et-patronymes/20181014-162921/patronymes.csv | cut -d ',' -f 1 >> noms_cust.txt
wget -O- https://www.insee.fr/fr/statistiques/fichier/7633685/nat2022_csv.zip | funzip | cut -d ';' -f2 | duplicut -o prenoms_cust.txt

# Liste des acteurs
wget -O- https://datasets.imdbws.com/name.basics.tsv.gz | zcat | cut -d$'\t' -f2 | duplicut -o acteurs_cust.txt.tmp
#Liste titres films
wget -O- https://datasets.imdbws.com/title.akas.tsv.gz | zcat | cut -d$'\t' -f3 | duplicut -o films_cust.txt.tmp
#Liste des persos fictifs
wget -O- https://datasets.imdbws.com/title.principals.tsv.gz | zcat | cut -d$'\t' -f6 | sed -E 's/^\["(.*)"\]$/\1/' | grep -v "\\N" | jq -R '.' -r | duplicut -o characters_fictif_cust.txt.tmp


echo "Parsing actors / movies / characters"
python3 ../parsePythonWl.py acteurs_cust.txt.tmp 1 | duplicut -o acteurs_cust.txt 
python3 ../parsePythonWl.py films_cust.txt.tmp 1 | duplicut -o films_cust.txt 
python3 ../parsePythonWl.py characters_fictif_cust.txt.tmp 1 | duplicut -o characters_fictif_cust.txt
echo "Done..."

rm *.txt.tmp


# THX Clem
curl -s 'https://trends.google.com/trends/trendingsearches/daily/rss?geo=FR' | xmllint --xpath "//item/title" - | sed -e 's/<[^>]*>//g' >> news_FR.txt
curl -s 'https://trends.google.com/trends/trendingsearches/daily/rss?geo=BE' | xmllint --xpath "//item/title" - | sed -e 's/<[^>]*>//g' >> news_BE.txt
curl -s 'https://trends.google.com/trends/trendingsearches/daily/rss?geo=CH' | xmllint --xpath "//item/title" - | sed -e 's/<[^>]*>//g' >> news_CH.txt
curl -s 'https://trends.google.com/trending/rss?geo=FR' | xmllint --xpath "//item/title" - | sed -e 's/<[^>]*>//g' >> news_FR.txt
curl -s 'https://trends.google.com/trending/rss?geo=BE' | xmllint --xpath "//item/title" - | sed -e 's/<[^>]*>//g' >> news_BE.txt
curl -s 'https://trends.google.com/trending/rss?geo=CH' | xmllint --xpath "//item/title" - | sed -e 's/<[^>]*>//g' >> news_CH.txt

echo "Deduplicating all files ..."
for f in ./*; do
    echo "Processing $f"
    duplicut "$f" -o "$f.dedupe"
    rm "$f"
done
echo "Done..."

cat *.dedupe > full_wl_cust.cated.txt
rm *.dedupe

duplicut full_wl_cust.cated.txt -o processed/output_sns

rm *.txt

cd processed/
echo "Combining everything to one big wordlist"

cat output_sns  full_wiki_content_fr_en_dedupe all_wiki_titles_full_dedupe > clem_hashmob_full
duplicut clem_hashmob_full -o full_dedupe
echo "Done..."

rm clem_hashmob_full

echo "Compressing..."
lrzip -b full_dedupe -v
rm full_dedupe full_wiki_content_fr_en_dedupe all_wiki_titles_full_dedupe
mv full_dedupe.lrz /root/serve/
mv output_sns /root/serve/
cd ../../
rm -rf wordlists/
