import sys
from unidecode import unidecode


def decode_unicode_if_necessary(string):
    if unidecode(string) != string:
        print(unidecode(string))
    
file=sys.argv[1]
mode=sys.argv[2]

# Mode 1 = Numbers
# Mode 2 = Cut and capitalize ("HELLO WORLD" > "HelloWorld")
year_seperators = ['', '_', '-', '@']



if file and mode == '1':
    with open(file, 'r') as file:
        for line in file:
            for y in str(range(0, 10000)):
                for x in year_seperators:
                    print(f"{line.strip()}{x}{y}")

if file and mode == '2':
    with open(file, 'r') as file:
        for line in file:
            line = line.strip()
            decode_unicode_if_necessary(line)
            line_without_space = "".join([word for word in line.title().split(" ")])
            print(f'{line_without_space}')
            decode_unicode_if_necessary(line_without_space)
            if '-' in line:
                dash_split = "".join([word for word in line_without_space.split("-")])
                print(f'{dash_split}')
                decode_unicode_if_necessary(dash_split)
            

