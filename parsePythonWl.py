import sys
from unidecode import unidecode


def decode_unicode_if_necessary(string):
    if unidecode(string) != string:
        print(unidecode(string))
    
file=sys.argv[1]
mode=sys.argv[2]





if file and mode == '1':
    print(f"Processing {file}...")
    with open(file, 'r') as file:
        for line in file:
            original = line.strip()

            no_underscores = original.replace('_', ' ')
            no_underscores_collapsed = original.replace('_', '')
            slash_to_newline = original.replace('/', '\n')
            slash_to_space = original.replace('/', ' ')
            line_without_space = "".join([word for word in original.title().split(" ")])
            dash_split = "".join([word for word in line_without_space.split("-")])

            decode_unicode_if_necessary(original)
            print(original)
            if no_underscores != original:
                decode_unicode_if_necessary(no_underscores)
                print(no_underscores)
            if no_underscores_collapsed != original:
                decode_unicode_if_necessary(no_underscores_collapsed)
                print(no_underscores_collapsed)
            if slash_to_newline != original:
                print(slash_to_newline)
                decode_unicode_if_necessary(slash_to_newline)
            if slash_to_space != original:
                print(slash_to_space)
                decode_unicode_if_necessary(slash_to_space)
            if line_without_space != original:
                print(line_without_space)
                decode_unicode_if_necessary(line_without_space)
            if dash_split != original:
                print(dash_split)
                decode_unicode_if_necessary(dash_split)
    print("Done !")        
            
