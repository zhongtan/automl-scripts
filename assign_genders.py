"""
This script reads from a csv file containing the image IDs and their corresponding classes (shoes/clothes). 
It then tries to classify each image into 1 of 3 genders: unisex, male, female by reading from a dataset
that contains the item titles and descriptions associated with this image. After classifying these images,
this script saves them in their corresponding gender folders.
"""

import csv
import urllib
import os 
import re

root = ''   # TODO: specify your project's toplevel directory here
items_csv = root + 'data/.csv' # TODO: specify the name of your dataset here, there should be item_titles and descriptions for each image

# this is a range to select which items in the dataset to classify into their genders
# for example, if I want item #30000 to #69999 (total of 40000 images), the indices would be specified as such
starting_index = 30000
ending_index = 70000

categorized_items_csv = os.path.join(root, 'csv/gs_url_to_category_labels/labels_{}_to_{}.csv'.format(starting_index, ending_index))

folder_names = {
  'clothes': {
    'male': os.path.join(root, 'data/images/clothes_shoes_gender/g_clothes_{}_to_{}/male/'.format(starting_index, ending_index)),
    'female': os.path.join(root, 'data/images/clothes_shoes_gender/g_clothes_{}_to_{}/female/'.format(starting_index, ending_index)),
    'unisex': os.path.join(root, 'data/images/clothes_shoes_gender/g_clothes_{}_to_{}/unisex/'.format(starting_index, ending_index)),
    'outliers': os.path.join(root, 'data/images/clothes_shoes_gender/g_clothes_{}_to_{}/outliers/'.format(starting_index, ending_index))
  }, 
  'shoes': {
    'male': os.path.join(root, 'data/images/clothes_shoes_gender/g_shoes_{}_to_{}/male/'.format(starting_index, ending_index)),
    'female': os.path.join(root, 'data/images/clothes_shoes_gender/g_shoes_{}_to_{}/female/'.format(starting_index, ending_index)),
    'unisex': os.path.join(root, 'data/images/clothes_shoes_gender/g_shoes_{}_to_{}/unisex/'.format(starting_index, ending_index)),
    'outliers': os.path.join(root, 'data/images/clothes_shoes_gender/g_shoes_{}_to_{}/outliers/'.format(starting_index, ending_index)) 
  }
}

items_hash = {}
categorized_items_hash = {}

class Item:
  def __init__(self, id, url, title, desc):
    self.id = id
    self.url = url
    self.title = title
    self.desc = desc

# this function removes punctuations in token and converts it into lowercase
def standardize(token):
  token = re.sub(r'[^\w\s]', '', token)
  return token.lower()

# Build a hash from the categorized items
def build_hash_from_categorized_items():
  with open(categorized_items_csv) as file:
    rows = csv.reader(file, delimiter=',')

    for row in rows:
      bucket_item_url = row[0]
      category = row[1]
      item_jpg_file = bucket_item_url.split("/")[-1]

      if item_jpg_file == '.DS_Store':
        continue

      item_id = item_jpg_file.split(".")[0]
      categorized_items_hash[item_id] = category

# Build a hash containing the mapping from item IDs to an Item object containing titles and descriptions
def build_hash_from_items():
  with open(items_csv) as file:
    rows = csv.reader(file, delimiter=',')

    for row in rows:
      item_id = row[0]
      image_url = row[1]
      item_title = standardize(row[2])
      item_desc = standardize(row[3])

      items_hash[item_id] = Item(item_id, image_url, item_title, item_desc)

def assign_gender_labels():
  count = 1

  # the items in the categorized_items_hash will be used for the training set
  for item_id in categorized_items_hash:
    if categorized_items_hash[item_id] == 'clothes':
      sort_into_clothes(items_hash[item_id], count)
    elif categorized_items_hash[item_id] == 'shoes':
      sort_into_shoes(items_hash[item_id], count)

    count += 1

def sort_into_clothes(item, count):
  sort(item, 'clothes', count)
  
def sort_into_shoes(item, count):
  sort(item, 'shoes', count)

def sort(item, item_type, count):
  item_id = item.id
  item_title = item.title
  item_desc = item.desc
  item_url = item.url
  found = False
  category = 'outlier'

  female_folder = folder_names[item_type]['female']
  male_folder = folder_names[item_type]['male']
  unisex_folder = folder_names[item_type]['unisex']
  outlier_folder = folder_names[item_type]['outliers']

  # check to see if the image exists in any one of the folders
  if (os.path.isfile(female_folder + item_id + '.jpg') or 
      os.path.isfile(male_folder + item_id + '.jpg') or 
      os.path.isfile(unisex_folder + item_id + '.jpg') or 
      os.path.isfile(outlier_folder + item_id + '.jpg')):
    print('Item with id #{} already classified'.format(item_id))
    return 

  # try to find a matching keyword in female_keywords
  if isMatchFemale(item_title) or isMatchFemale(item_desc):
    category = 'female'
    urllib.urlretrieve(item_url, female_folder + item_id + '.jpg')
    found = True

  # try to find a matching keyword in male_keywords
  if (not found):
    if isMatchMale(item_title) or isMatchMale(item_desc):
      urllib.urlretrieve(item_url, male_folder + item_id + '.jpg')
      category = 'male'
      found = True
  
  # try to find a matching keyword in unisex_keywords
  if (not found):
    if isMatchUnisex(item_title) or isMatchUnisex(item_desc):
      urllib.urlretrieve(item_url, unisex_folder + item_id + '.jpg')
      category = 'unisex'
      found = True

  # could not assign to any category
  if (not found):
    urllib.urlretrieve(item_url, outlier_folder + item_id + '.jpg')
  
  print(str(count) + "\t\t: assigned " + item_type + "\t with ID: " + item_id + " to: \t" + category)

def isMatchFemale(token):
  return re.search(r'\b(female(s|)|lad(y|ies)|girl(s|)|bra(s|)|skirt(s|)|wom(a|e)n(|\'s|s)|m(o|u)m|madam|heel(s|)|gown|cowgirl(s|)|boyfriend jeans|super[ ]*girl|junior(s|)\/wom(a|e)n)\b', token) != None

def isMatchMale(token):
  return re.search(r'\b(men(s|)|man(s|)|male(s|)|mr|boy(s|)|gentle[ ]*m(a|e)n|cowboy(s|)|play[ ]*boy)\b', token) != None

def isMatchUnisex(token):
  return re.search(r'\b(unisex|m(e|a)n(s|)\/wom(a|e)n(s|))\b', token) != None

if __name__ == "__main__":
  build_hash_from_items()
  build_hash_from_categorized_items()
  assign_gender_labels()