import argparse
import re
import os
from datetime import datetime

def create_new_tag(tag, update_major):
    if not (re.match(r'^v\d+\.\d+$', tag)):
        raise Exception(f'tag: {tag} is not giving in the correct format e.i v0.0')
    
    # Notice that this could make a tag version of three digits become two digits
    # e.i 3.2.1 -> 3.3
    digits_tags = (re.match(r'^v\d+\.\d+', tag)).group()[1::].split('.')
    if len(digits_tags) != 2:
        raise Exception(f'tag: {tag} must contain two version digits')
    
    major_num = int(digits_tags[0])
    minor_num = int(digits_tags[1])
    if update_major:
        print(f"Label detected to update major version")
        major_num += 1
        minor_num = 0
    else:
        minor_num += 1
    return f"v{major_num}.{minor_num}"

def store_tag(tag):
    with open(os.environ['GITHUB_OUTPUT'], 'a') as fh:
        print(f'new_tag={tag}', file=fh)

def update_file_with_tag(f_name, old_tag, new_tag, replace_dates=True):
    if os.path.isfile(f_name):
        try:
            with open(f_name, "r",encoding="utf-8") as f:
                data = f.read()
            data = data.replace(old_tag, new_tag)
            if replace_dates:
                date_re = r"\d{4}-\d{2}-\d{2}"
                today = datetime.today().strftime('%Y-%m-%d')
                data = re.sub(date_re, today, data)
            with open(f_name, "w",encoding="utf-8") as f:
                f.write(data)
        except Exception as e:
            print(e)
    else:
        print(f"Warning: {f_name} doest exist at the current path {os.getcwd()}")

def main(args):
    tag = args.tag
    new_tag = "v2.0"
    if not tag:
        print(f"Warning: a latest release with a tag does not exist in current repository, starting from {new_tag}")
    else:
        new_tag = create_new_tag(tag,args.update_major_ver)
        print(f"Repository with tag: {tag}, creating a new tag with: {new_tag}")
        update_file_with_tag(".zenodo.json", tag, new_tag)
        update_file_with_tag("CITATION.cff", tag, new_tag)
        update_file_with_tag("README.md", tag, new_tag, replace_dates=False)
    store_tag(new_tag)

def run():
    args = parser.parse_args()
    main(args)


def str_to_bool(value):
    if value.lower() == "true":
        return True
    elif value.lower() == "false":
        return False
    else:
        raise Exception(
            f"Error: value {value} as argument is not accepted\n"
            f"retry with true or false"
        )
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--tag", type=str,
        help="Require: latest tag",
        required=True
    )
    parser.add_argument(
        "--update_major_ver", type=str_to_bool,
        help="Require: boolean to update the major tag number",
        required=True
    )
    run()