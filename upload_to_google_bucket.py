# Reference: https://cloud.google.com/storage/docs/uploading-objects#storage-upload-object-python

from google.cloud import storage
import os
import csv

def upload_blob(bucket_name, source_file_name, destination_blob_name):
  """Uploads a file to the bucket."""
  # bucket_name = "your-bucket-name"
  # source_file_name = "local/path/to/file"
  # destination_blob_name = "storage-object-name"

  storage_client = storage.Client()
  bucket = storage_client.bucket(bucket_name)
  blob = bucket.blob(destination_blob_name)

  if not blob.exists(storage_client):
    blob.upload_from_filename(source_file_name)

    print(
      "File {} uploaded to {}.".format(
          source_file_name, destination_blob_name
      )
    )
  else: 
    print('Image is already in the bucket folder.')

def record_missing_images(bucket_name, storage_dir, local_dir):
  client = storage.Client()
  bucket = client.bucket(bucket_name)
  missing_images = []

  file_names = ['{}{}'.format(storage_dir, f) for f in os.listdir(local_dir) if f.endswith('.jpg')]

  for file_name in file_names:
    blob = bucket.get_blob(file_name)
    if not blob.exists(client):
      missing_images.append(file_name)
  
  return missing_images

def find_mismatch_from_csv(bucket_name, csv_file):
  client = storage.Client()
  bucket = client.bucket(bucket_name)

  with open(csv_file) as file:
    rows = csv.reader(file, delimiter=',')

    for row in rows:
      url = row[0]
      file_name = '/'.join(url.split('/')[-3:])
      blob = bucket.get_blob(file_name)
      if not blob.exists(client):
        print('item with id #{} not uploaded to the bucket, upload it before continuing.'.format(file_name.split('/')[-1].split('.')[0]))
        return 
      else: 
        print('item with id #{} exists in the bucket.'.format(file_name.split('/')[-1].split('.')[0]))

def upload_dir(dir, bucket_name, blob_group, gender):
  # get all the images from this directory
  images = [f for f in os.listdir(dir) if f.endswith('.jpg')]

  # upload each image to the bucket folder
  for image in images:
    upload_blob(bucket_name, os.path.join(dir, image), os.path.join(blob_group, gender, image))

if __name__ == '__main__':
  root = ''   # TODO: specify your project's toplevel directory here
  gender_img_dir = os.path.join(root, 'data/images/clothes_shoes_gender/')
  bucket_name = 'offerup_gender_images_central1'

  starting_index = 30000 #22500
  ending_index = 70000 #30000
  
  # upload all images of clothes
  male_clothes = os.path.join(gender_img_dir, 'g_clothes_{}_to_{}/male/'.format(starting_index, ending_index))
  upload_dir(male_clothes, bucket_name, 'clothes', 'male')

  female_clothes = os.path.join(gender_img_dir, 'g_clothes_{}_to_{}/female/'.format(starting_index, ending_index))
  upload_dir(female_clothes, bucket_name, 'clothes', 'female')

  # find_mismatch_from_csv(bucket_name, os.path.join(root, 'csv/gs_url_to_category_labels/genders/clothes_gender_labels_{}_to_{}.csv'.format(starting_index, ending_index)))

  # upload all images of shoes
  male_shoes = os.path.join(gender_img_dir, 'g_shoes_{}_to_{}/male/'.format(starting_index, ending_index))
  upload_dir(male_shoes, bucket_name, 'shoes', 'male')
  female_shoes = os.path.join(gender_img_dir, 'g_shoes_{}_to_{}/female/'.format(starting_index, ending_index))
  upload_dir(female_shoes, bucket_name, 'shoes', 'female')

  # find_mismatch_from_csv(bucket_name, os.path.join(root, 'csv/gs_url_to_category_labels/genders/shoes_gender_labels_{}_to_{}.csv'.format(starting_index, ending_index)))