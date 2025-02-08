import subprocess
import shutil
import os
import sys
from pathlib import Path
import requests
from unidecode import unidecode
from vocab import verbs_vow, verbs_cons, det, nouns
from wiki_downloader import download_wiki
import tempfile
import re
from lxml import etree

def concat_files(output_file, input_files, buffer_size=1024 * 1024):
    """Concatenate multiple files into one output file using a specified buffer size."""
    with open(output_file, 'wb') as wfd:
        for f in input_files:
            with open(f, 'rb') as fd:
                while True:
                    buf = fd.read(buffer_size)
                    if not buf:
                        break
                    wfd.write(buf)

def process_feed(url, outfile):
    """
    Fetches the RSS feed from `url`, extracts all <item>/<title> text,
    and appends the titles to the file `outfile`.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        tree = etree.fromstring(response.content)
        titles = tree.xpath("//item/title/text()")
        if titles:
            with open(outfile, "a", encoding="utf-8") as f:
                for title in titles:
                    f.write(title + "\n")
    except Exception as e:
        print(f"Error processing {url}: {e}")


def awkEquivalentSplitByQuote(filename):
    """
    Reads the file 'filename' line by line, splits each line on spaces or apostrophes,
    and then appends all non-empty tokens to the same file.
    
    Note: Since reading and writing to the same file concurrently can be tricky,
    we first write the tokens to a temporary file and then append that temporary file
    to the original file.
    """
    # Create a temporary file in text mode.
    print(f"Splliting file {filename} by quotes")
    temp_fd, temp_path = tempfile.mkstemp(text=True)
    try:
        with os.fdopen(temp_fd, 'w', encoding='utf-8') as temp_file, \
             open(filename, 'r', encoding='utf-8') as infile:
            for line in infile:
                # Remove leading/trailing whitespace
                line = line.strip()
                if not line:
                    continue
                # Split on space or apostrophe (and optionally on quotes, if needed)
                # The regex below splits on any sequence of space, single or double quotes.
                tokens = re.split(r"[ '\"]+", line)
                for token in tokens:
                    if token:
                        temp_file.write(token + "\n")
        # Now open the original file in append mode and add the tokens from the temp file.
        with open(filename, 'a', encoding='utf-8') as outfile, \
             open(temp_path, 'r', encoding='utf-8') as temp_file:
            for token_line in temp_file:
                outfile.write(token_line)
    finally:
        # Remove the temporary file.
        os.remove(temp_path)
        print("Done !")

def command_exists(cmd):
    """Check if a command exists in system path"""
    return shutil.which(cmd) is not None

def run_command(command, shell=True):
    """Run a system command and handle errors"""
    try:
        if isinstance(command, str) and not shell:
            command = command.split()
        subprocess.run(command, check=True, shell=shell)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {command}")
        print(f"Error message: {str(e)}")
        return False

def install_package(package):
    """Install a package using apt"""
    print(f"Installing {package}...")
    return run_command(f"sudo apt install {package} -y", shell=True)

def setup_cargo_env():
    """Setup cargo environment variables"""
    cargo_bin = os.path.expanduser("~/.cargo/bin")
    if os.path.exists(cargo_bin):
        if cargo_bin not in os.environ["PATH"]:
            os.environ["PATH"] = f"{cargo_bin}:{os.environ['PATH']}"
    return True

def checkInstalledPackages():
    # Check if script is run with sudo
    if os.geteuid() != 0:
        print("This script must be run with sudo privileges")
        sys.exit(1)

    # Install initial dependencies
    run_command("sudo apt install libssl-dev pkg-config libxml2 -y", shell=True)

    # Install git if not present
    if not command_exists("git"):
        print("Installing git...")
        run_command("sudo apt update", shell=True)
        install_package("git")

    # Install pip if not present
    if not command_exists("pip"):
        print("Installing pip...")
        install_package("python3-pip")

    # Install aria2c if not present
    if not command_exists("aria2c"):
        print("Installing aria2c...")
        install_package("aria2")

    # Install 7z if not present
    if not command_exists("7z"):
        print("Installing 7zip...")
        install_package("p7zip-full")
        install_package("p7zip-rar")

    # Install duplicut if not present
    if not command_exists("duplicut"):
        print("Cloning duplicut repository...")
        run_command("git clone https://github.com/nil0x42/duplicut")
        os.chdir("duplicut")
        run_command("make")
        run_command("sudo make install")
        os.chdir("..")

    # Install various packages
    packages = ["jq", "wget", "lbzip2", "python3", "lrzip"]
    for package in packages:
        if not command_exists(package):
            install_package(package)

    # Install ripgrep if not present
    if not command_exists("rg"):
        print("Installing ripgrep...")
        run_command("wget https://github.com/BurntSushi/ripgrep/releases/download/14.1.1/ripgrep_14.1.1-1_amd64.deb -O /tmp/ripgrep.deb")
        run_command("sudo dpkg -i /tmp/ripgrep.deb")

    # Install unidecode if not present
    try:
        import unidecode
    except ImportError:
        print("Installing unidecode...")
        run_command("pip install unidecode")

    # Install cargo if not present
    if not command_exists("cargo"):
        print("Installing cargo rust...")
        run_command('curl --proto "=https" --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y', shell=True)
        # Update environment variables
        setup_cargo_env()

    # Install cracken if not present
    if not command_exists("cracken"):
        print("Installing cargo cracken...")
        run_command("cargo install cracken")

def getWordlistHashmob():
    result = requests.get("https://hashmob.net/api/v2/downloads/research/official").json()
    for x in result:
        if x["name"] == "HashMob Combined Full":
            return x["file_name"]

def doInstallClem(dir):
    """Clone and process wordlists repository"""
    # Create directory if it doesn't exist
    wordlist_dir = Path(dir)
    wordlist_dir.mkdir(parents=True, exist_ok=True)

    # Change to the wordlist directory
    os.chdir(wordlist_dir)

    # Clone the repository
    print(f"Cloning wordlists repository ({dir})...")
    run_command("git clone --depth 1 https://github.com/clem9669/wordlists.git")

    # Change to the cloned directory
    os.chdir("wordlists")

    # Move all files except .git related ones to the parent directory
    print("Processing files...")
    for root, dirs, files in os.walk(".", topdown=True):
        # Skip .git directory
        if '.git' in dirs:
            dirs.remove('.git')

        for file in files:
            if file != '.gitignore':
                source = Path(root) / file
                destination = Path(".") / file
                try:
                    shutil.move(str(source), str(destination))
                except Exception as e:
                    print(f"Error moving {source}: {e}")

    # Remove specified files
    files_to_remove = [
    "immatriculation.7z",
    "phone_number_fr.7z",
    "phone_number_fr_33.7z"
    ]

    # Add private_ip files to removal list
    private_ip_files = list(Path(".").glob("private_ip_*"))
    files_to_remove.extend([f.name for f in private_ip_files])

    print("Removing specified files...")
    for file in files_to_remove:
        try:
            if os.path.exists(file):
                os.remove(file)
                print(f"Removed {file}")
        except Exception as e:
            print(f"Error removing {file}: {e}")

def doInstallHashmob(dir):
    wordlist_dir = Path(f"{dir}/wordlists")
    wordlist_dir.mkdir(parents=True, exist_ok=True)
    os.chdir(wordlist_dir)
    list_hashmob = getWordlistHashmob()
    print(f'Downloading hashmob {list_hashmob}')
    run_command(f"aria2c --max-connection-per-server=16 --min-split-size=20M --split=16 https://hashmob.net/api/v2/downloads/research/official/{list_hashmob} -o hashmob_full.7z")
    print("Done !")
    
def uncompressAndRemove7z(dir):
    wordlist_dir = Path(dir)
    os.chdir(wordlist_dir)
    print(f"Unzipping files in dir {dir}")
    
    zfiles = list(Path(".").glob("*.7z"))
    for zfile in zfiles:
        print(f"Extracting {zfile}")
        # Etrangement, probablement donc est codé 7zip
        # ce dernier n'accepte pas les args comme ça, il faut utiliser os.system()
        os.system(f"7z x '{str(zfile)}'")
        print("ok")
        
    print(f"Done now, removing {zfiles}")
    for file in zfiles:
        try:
            if os.path.exists(file):
                os.remove(file)
                print(f"Removed {file}")
        except Exception as e:
            print(f"Error removing {file}: {e}")
   
def catAndRemoveFilesInDir(dir, outfile):
    '''
    cd to the input param "dir", list all files and cat them
    to "outfile" then remove files that were cated. Then remove duplicates from result
    '''
    wordlist_dir = Path(dir)
    os.chdir(wordlist_dir)
    files_to_cat = [str(x) for x in Path(".").iterdir() if x.is_file()]
    print(f"Running cat on {files_to_cat}")
    concat_files(f"{outfile}.temp", files_to_cat)
    print("Done cating")
    print(f"Removing {files_to_cat}")
    for file in files_to_cat:
        try:
            if os.path.exists(file):
                os.remove(file)
                print(f"Removed {file}")
        except Exception as e:
            print(f"Error removing {file}: {e}")

    print("Done removing files")
    print(f"Deduping {outfile}.temp with duplicut")
    run_command(f"duplicut {outfile}.temp -o {outfile}")
    os.remove(f"{outfile}.temp")
    print("Dedupe done")


def writeTempBasePhrases():
    """
    Write temp files holding the necessary wordlists for custom phrases gen, then
    return the path in which those wordlists are
    """
    tmp = "/tmp/cust_vocab/"
    tmp_path = Path(tmp)
    tmp_path.mkdir(parents=True, exist_ok=True)
    os.chdir(tmp_path)
    with open("det", "w") as det_file:
        det_file.write(det)
    with open("verb_cons", "w") as verbs_cons_file:
        verbs_cons_file.write(verbs_cons)
    with open("verb_vow", "w") as verbs_vow_file:
        verbs_vow_file.write(verbs_vow)
    with open("nouns", "w") as nouns_file:
        nouns_file.write(nouns)
    return tmp
    
def buildCustPhrases(dir):
    vocab_dir = writeTempBasePhrases()
    wordlist_dir = Path(dir)
    os.chdir(wordlist_dir)
    run_command(f'cracken -w {vocab_dir}verb_vow -w {vocab_dir}det -w {vocab_dir}nouns "j\'?w1 ?w2 ?w3" -o lst_vow && cracken -w {vocab_dir}verb_cons -w {vocab_dir}det -w {vocab_dir}nouns "je ?w1 ?w2 ?w3" -o lst_cons')
    print("Generated worlists for custom_phrases_fr")
    shutil.rmtree(vocab_dir)
    print("Removed temp vocab")
    print(f"Cating together both files")
    concat_files("phrases_cust_fr", ["lst_vow", "lst_cons"])
    os.remove("lst_cons")
    os.remove("lst_vow")

def decode_unicode_if_necessary(string):
    if unidecode(string) != string:
        print(unidecode(string))

def processFileOutput(filename):
    print(f"Processing {filename}...")
    new_filename = filename + ".new"

    with open(filename, 'r') as fin, open(new_filename, 'w') as fout:
        for line in fin:
            original = line.strip()
            # Create a list of transformations
            # Note: Using original.title().split() removes spaces entirely.
            # If you really want to join the title-cased words without a space, this is fine.
            no_underscores = original.replace('_', ' ')
            no_underscores_collapsed = original.replace('_', '')
            slash_to_newline = original.replace('/', '\n')
            slash_to_space = original.replace('/', ' ')
            line_without_space = "".join(original.title().split())
            dash_split = "".join(line_without_space.split("-"))

            # List the output variants in order; first always original
            outputs = [original]
            # Only add a transformation if it differs from the original.
            for variant in (no_underscores, no_underscores_collapsed,
                            slash_to_newline, slash_to_space,
                            line_without_space, dash_split):
                if variant != original:
                    outputs.append(variant)

            # Process and write each variant
            for text in outputs:
                decode_unicode_if_necessary(text)
                fout.write(text + "\n")
    print(f"Done with {filename}")

    # Remove the old file and rename the new file to the original file name.
    os.remove(filename)
    os.rename(new_filename, filename)
    print("Done!")
            
def downloadAndParseWiki(dir):
    wordlist_dir = Path(dir)
    os.chdir(wordlist_dir)
    print(f"Downloading and parsing wiki in {dir}")
    download_wiki(dir) # On télécharge les deux wiki ('full_wiki_titles' et 'full_wiki_content_dedupe')
    processFileOutput('full_wiki_titles')
    print(f"Cating together both files")
    concat_files("wiki_content.tmp", ["full_wiki_titles", "full_wiki_content_dedupe"])
    os.remove("full_wiki_content_dedupe")
    os.remove("full_wiki_titles") # On se retrouve avec wiki_content qu'il faut dedupe
    run_command(f"duplicut wiki_content.tmp -o wiki_content")
    os.remove("wiki_content.tmp")


def processCustData(dir):
    wordlist_dir = Path(dir)
    os.chdir(wordlist_dir)

    #Part 1 entreprises et rues
    # Nom d'entreprises
    run_command("wget -O- https://www.data.gouv.fr/fr/datasets/r/0835cd60-2c2a-497b-bc64-404de704ce89 | funzip | cut -d ',' -f6,10 | tr ',' '\\n' | grep -Pv '^$' | duplicut -o entreprises_cust.txt")
    # Nom rue / villes / code post
    run_command("wget -O- --retry-connrefused --waitretry=1 --read-timeout=20 --timeout=5 -t 0 https://adresse.data.gouv.fr/data/ban/adresses/latest/csv/adresses-france.csv.gz | zcat | awk -F';' '{print $5 | duplicut -o \"rues_cust.txt\"; print $6 | duplicut -o \"code_postal_cust.txt\"; print $8 | duplicut -o \"villes_cust.txt\"}'")
    
    # on fait notre tambouille avec les fichiers
    awkEquivalentSplitByQuote("entreprises_cust.txt")
    processFileOutput("entreprises_cust.txt")
    awkEquivalentSplitByQuote("rues_cust.txt")
    processFileOutput("rues_cust.txt")
    awkEquivalentSplitByQuote("villes_cust.txt")
    processFileOutput("villes_cust.txt")
    
    # Part 2 Noms prénoms
    run_command("wget -O- https://www.insee.fr/fr/statistiques/fichier/3536630/noms2008dep_txt.zip | funzip | cut -d$'\\t' -f1 | duplicut -o noms_cust.txt")
    run_command("wget -O- https://static.data.gouv.fr/resources/liste-de-prenoms-et-patronymes/20181014-162921/patronymes.csv | cut -d ',' -f 1 >> noms_cust.txt")
    run_command("wget -O- https://www.insee.fr/fr/statistiques/fichier/7633685/nat2022_csv.zip | funzip | cut -d ';' -f2 | duplicut -o prenoms_cust.txt")

    # Part 3 acteurs /films
    run_command("wget -O- https://datasets.imdbws.com/name.basics.tsv.gz | zcat | cut -d$'\t' -f2 | duplicut -o acteurs_cust.txt")
    processFileOutput("acteurs_cust.txt")
    run_command("wget -O- https://datasets.imdbws.com/title.akas.tsv.gz | zcat | cut -d$'\t' -f3 | duplicut -o films_cust.txt")
    processFileOutput("films_cust.txt")
    run_command("wget -O- https://datasets.imdbws.com/title.principals.tsv.gz | zcat | cut -d$'\\t' -f6 | sed -E 's/^\\[\"(.*)\"\\]$/\\1/' | grep -v \"\\\\N\" | jq -R '.' -r | duplicut -o characters_fictif_cust.txt")
    processFileOutput("characters_fictif_cust.txt")

    # Part 4 news
    feeds = [
        ("https://trends.google.com/trends/trendingsearches/daily/rss?geo=FR", "news_FR.txt"),
        ("https://trends.google.com/trends/trendingsearches/daily/rss?geo=BE", "news_BE.txt"),
        ("https://trends.google.com/trends/trendingsearches/daily/rss?geo=CH", "news_CH.txt"),
        ("https://trends.google.com/trending/rss?geo=FR", "news_FR.txt"),
        ("https://trends.google.com/trending/rss?geo=BE", "news_BE.txt"),
        ("https://trends.google.com/trending/rss?geo=CH", "news_CH.txt"),
    ]
    
    for url, outfile in feeds:
        process_feed(url, outfile)


    txt_files = list(Path(".").glob("*.txt"))
    print(f"Cating together {' '.join(txt_files)}")
    concat_files("custom_wl_combined", txt_files)
    for file in txt_files:
        try:
            if os.path.exists(file):
                os.remove(file)
                print(f"Removed {file}")
        except Exception as e:
            print(f"Error removing {file}: {e}")
    print("Cleaned up files")
    print(f"Running duplicut on it")
    run_command("duplicut custom_wl_combined -o custom_wl_dedupe")
    os.remove("custom_wl_combined")
    print("Done")

def finalStage(dir, mvdir):
    wordlist_dir = Path(dir)
    os.chdir(wordlist_dir)
    run_command(f"mv phrases_cust_fr {mvdir}")
    run_command(f"mv custom_wl_dedupe {mvdir}")
    print("Moved first part to public dir, now cating ...")
    concat_files("output_hashmob_clem", [f"{mvdir}custom_wl_dedup", f"{mvdir}phrases_cust_fr", "wiki_content"])
    os.remove("wiki_content")
    print("Cat ok, duplicuting")
    run_command(f"duplicut output_hashmob_clem -o output_full")
    os.remove("output_hashmob_clem")
    print("Duplicut done, zipping")
    run_command("lrzip -b output_full -v")
    os.remove("output_full")
    run_command(f"mv output_full.lrz {mvdir}")
    print("All done !")

checkInstalledPackages()
DIR = "/tmp/wordlist_processing"
FINAL_DIR = "/var/www/html/"

doInstallClem(DIR) # On installe clem
doInstallHashmob(DIR) # On installe hmob

uncompressAndRemove7z(f"{DIR}/wordlists") # On un-7z tout (hashmob + les compressée de clem)

catAndRemoveFilesInDir(f"{DIR}/wordlists", "output_hashmob_clem") # cat + dedupe + rm dans "output_hashmob_clem"
# File dans wordlists : output_hashmob_clem

buildCustPhrases(f"{DIR}/wordlists") # Crée le dict des phrases custom sous le fichier "phrases_cust_fr" dans le directory en question
# File dans wordlists : output_hashmob_clem phrases_cust_fr

downloadAndParseWiki(f"{DIR}/wordlists") # On a les wikipedia ici
# File dans wordlists : output_hashmob_clem phrases_cust_fr wiki_content

processCustData("{DIR}/wordlists") # On process toutes les data custom
# file dans wordlist : output_hashmob_clem phrases_cust_fr wiki_content custom_wl_dedupe

finalStage("{DIR}/wordlists", FINAL_DIR)
