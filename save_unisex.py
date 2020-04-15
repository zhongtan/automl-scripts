# This script looks at a raw dataset and finds all the unisex images in this dataset. 
# If the script identifies a unisex keyword ("unisex", "male/female", etc.) in either
# the title or description of an image, it then writes the matching string and the url 
# of the image to a csv file. 

import csv
import re

def classify_unisex(images_dataset, unisex_file):
  """ Classifies the items in the images_dataset into the unisex category and writes to a csv file
  Args:
    images_dataset: (csv) file containing all the images
    unisex_file: (csv) file containing the url and title/description of each unisex image
  Returns:
    Nothing
  """
  with open(unisex_file, 'a') as csv_file:
    image_writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

    with open(images_dataset) as file:
      rows = csv.reader(file, delimiter=',')

      for row in rows:
        item_id = row[0]
        image_url = row[1]
        item_title = standardize(row[2])
        item_desc = standardize(row[3])

        # this item belongs to the unisex category, so we write a csv row to the csv file
        csv_row = [item_id, image_url]
        title_match = isMatchUnisex(item_title)
        desc_match = isMatchUnisex(item_desc)
        is_accessory = isMatchAccessory(item_title) or isMatchAccessory(item_desc)

        if is_accessory:
          continue 

        if title_match or desc_match:
          if title_match:
            csv_row.append(item_title)
          else:
            csv_row.append(item_desc)  
          image_writer.writerow(csv_row)
        
def standardize(token):
  token = re.sub(r'[^\w\s]', ' ', token)
  return token.lower()

def isMatchUnisex(token):
  token = standardize(token)
  return re.search(r'\b(.*unisex.*|m(e|a)n(s|)\/wom(a|e)n(s|))\b', token) != None

def isMatchAccessory(token):
  return re.search(r'\b(beanie(s|)|hat(s|)|sock(s|)|glove(s|)|belt(s|)|sunglas(s|ses|)|bag(s|)|backpack(s|)|cap(s|)|snapback(s|)|scar(f|ves|fes|fs)|fanny[ ]*(bag|pack)|mask)\b', token)

if __name__ == "__main__":
  root = ''  # TODO: specify your project's toplevel directory here
  images_dataset = root + 'data/2019-10-01_2020_01_01_itemid_url_title_description.csv'
  unisex_file = root + 'csv/unisex/image_url_to_matching_str.csv'
  classify_unisex(images_dataset, unisex_file)