# This script combines all the given input csv files and merges them into one single csv file.
import os

def merge_csv(merge_dir, filenames, outfile):
  files = [os.path.join(merge_dir, file) for file in filenames]

  fout = open(os.path.join(merge_dir, outfile), "a")
  for file in files:
    for line in open(file):
      fout.write(line)
      print("written: {}".format(line))
  fout.close()

if __name__ == "__main__":
  root = ''  # TODO: specify your project's toplevel directory here
  merge_dir = root + 'csv/merge_csv_files/'

  shoes_files = []  # TODO: specify which CSV files you want to merge
  merge_csv(merge_dir, shoes_files, "shoes_merged.csv")