# This script takes each image in the current directory and labels them with their corresponding category.
# The mappings are then stored in a CSV file where the first column is the directory of the image in the 
# Google storage bucket, and the second is its corresponding category. 
#
# The script assumes that it is in the same directory as the category folders. For example, if we have a
# folder "shoes" in the same directory, the script will look into this folder for all the images and 
# label each image with the "shoes" label. 
#
# Reference: https://cloud.google.com/vision/automl/docs/prepare

import csv
import os

storage_bucket = ""    # TODO: change this to the name of your GCS bucket
write_file = os.getcwd() + "/csv/gs_url_to_category_labels/genders/shoes_gender_labels_30000_to_70000.csv"      # TODO: rename the csv file to whatever you like

def save_gender_images(images, group, gender, label):
  image_label_dict = {}

  with open(write_file, 'a') as csv_file:
    image_writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

    for image in images:
      if image == '.DS_Store':
        continue

      row = []
      image_dir = "gs://{}/{}/{}/{}".format(storage_bucket, group, gender, image)
      row.append(image_dir)
      row.append(label)
      image_writer.writerow(row)
      print("Written image " + image + "," + label)
    
    csv_file.close()

def save_clothes_shoes_images(images, label):
  if not os.path.isfile(write_file):
    with open(write_file, 'w'): pass

  with open(write_file, 'a') as csv_file:
    image_writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

    for image in images:
      if image == '.DS_Store':
        continue

      row = []
      row.append(image)
      row.append(label)
      image_writer.writerow(row)
      print("Written image " + image + "," + label)
    
    csv_file.close()

if __name__ == "__main__":
  root = ''   # TODO: specify your project's toplevel directory here

  # TODO: change the directory name as you prefer
  # save_gender_images(os.listdir(root + "data/images/clothes_shoes_gender/g_clothes_30000_to_70000/male"), "clothes", "male", "male")
  # save_gender_images(os.listdir(root + "data/images/clothes_shoes_gender/g_clothes_30000_to_70000/female"), "clothes", "female", "female")
  # save_gender_images(os.listdir(root + "data/images/unisex/clothes"), "clothes", "unisex", "clothes_unisex")

  save_gender_images(os.listdir(root + "data/images/clothes_shoes_gender/g_shoes_30000_to_70000/male"), "shoes", "male", "male")
  save_gender_images(os.listdir(root + "data/images/clothes_shoes_gender/g_shoes_30000_to_70000/female"), "shoes", "female", "female")
  # save_gender_images(os.listdir(root + "data/images/unisex/shoes"), "shoes", "unisex", "unisex")

  # save_clothes_shoes_images(os.listdir(root + "data/images/clothes_shoes/clothes_30000_to_70000"), "clothes")
  # save_clothes_shoes_images(os.listdir(root + "data/images/clothes_shoes/shoes_30000_to_70000"), "shoes")
