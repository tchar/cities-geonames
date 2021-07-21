import os
import argparse
from db import create_db

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output-dir', default='out')
    parser.add_argument('-f', '--full', action='store_true')
    return parser.parse_args()

def main():
    args = parse_args()
    output_dir = args.output_dir
    full = args.full

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    create_db(output_dir, full=full)

if __name__ == '__main__':
    main()