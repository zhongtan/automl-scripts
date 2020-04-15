# This script downloads all the saved unisex images into a specified directory.

import os
import urllib
import csv

def download_images(urls_csv, download_dir):
  """ Download all the images in the urls csv file into the download_dir directory
  Args:
    urls_csv: (csv) file containing the image urls
    download_dir: (str) download all the images in the urls_csv into this directory
  Returns:
    Nothing
  """

  with open(urls_csv) as file:
    rows = csv.reader(file, delimiter=',')
    count = 0

    for row in rows:
      item_id = row[0]
      image_url = row[1]

      file_name = download_dir + item_id + ".jpg"

      if (os.path.isfile(file_name) == False):
        urllib.urlretrieve(image_url, file_name)
        print("Download #{}: \timage with item_id {}".format(str(count), item_id))
        count = count + 1

if __name__ == "__main__":
  root = ''   # TODO: specify your project's toplevel directory here
  unisex_urls = root + 'csv/unisex/image_url_to_matching_str.csv'
  unisex_images = root + 'data/images/clothes_shoes_all_unisex/'
  download_images(unisex_urls, unisex_images)