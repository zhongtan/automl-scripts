import csv
import urllib
import numpy as np
import requests
import os
import io
import re
import base64
import json
from datetime import datetime

root = ''   # TODO: specify your project's toplevel directory here
images_dir = root + 'data/images/'
clothes_shoes_dir = images_dir + 'clothes_shoes/'
marginal_scores_csv = root + 'csv/marginal_scores/scores.csv'
encodings = []

def get_urls_and_image_names(data):
  """
  Build and return a dictionary containing the urls, names, titles and descriptions 
  of all the items in the given dataset.
  Args:
      data: CSV file containing the IDs, download urls, titles and descriptions of items
  Returns:
      item dictionary containing information retrieved from the given dataset
  """

  items = {
    "urls": [],
    "names": [],
    "titles": [],
    "descs": []
  }

  with open(data) as file:
    rows = csv.reader(file, delimiter=',')

    for row in rows:
      item_id = row[0]
      image_url = row[1]
      item_title = row[2]
      item_desc = row[3]
      
      image_name = item_id + ".jpg"
      items["urls"].append(image_url)
      items["names"].append(image_name)
      items["titles"].append(standardize(item_title))
      items["descs"].append(standardize(item_desc))

    return items

def standardize(token):
  token = re.sub(r'[^\w\s]', '', token)
  return token.lower()

def download_shoes_clothes_images_regex(items, start, end, download_folders):
  """
  Classify all the images from start to end index in the item dictionary into the clothes or shoes categories
  and then download them into their appropriate given folders. If an image is an accessory (belts, hats, etc.), 
  ignore it. If an image could not be classified, put it into the outliers folder.
  Args:
    items: dictionary containing the item urls, names (in .jpg format), titles and descriptions
    start: starting index
    end: ending index
    download_folders: dictionary containing the clothes/shoes/outliers directory paths
  Returns:
    Nothing
  """
  
  urls = items['urls']
  image_names = items['names']
  item_titles = items['titles']
  item_descs = items['descs']

  shoes_folder = download_folders['shoes']
  clothes_folder = download_folders['clothes']
  outliers_folder = download_folders['outliers']

  for i in range(starting_index, ending_index):
    url = urls[i]
    item_title = item_titles[i]
    item_desc = item_descs[i]
    category = 'shoes'
    found = False

    # try to match into the shoe category
    if (isMatchShoe(item_title) or isMatchShoe(item_desc)):
      urllib.urlretrieve(url, shoes_folder + image_names[i])
      found = True
      
    # try to match into the clothes category
    if (found == False):
      if (isMatchClothes(item_title) or isMatchClothes(item_desc)):
        urllib.urlretrieve(url, clothes_folder + image_names[i])
        category = 'clothes'
        found = True

    # if the item is an accessory, just skip it
    if (isMatchAccessory(item_title) or isMatchAccessory(item_desc)):
      continue

    # unable to find a matching
    if (found == False):
      category = 'outliers'
      urllib.urlretrieve(url, outliers_folder + image_names[i])
    
    print("Downloaded image[" + str(i) + "], \tmatched to: " + category)

def download_shoes_clothes_images_docker(items, start, end, tmp_dir, folders, ip_address='localhost', port_number=8501):
  """Sends a prediction request to TFServing docker container REST API.
  # Directly taken from:
  # https://cloud.google.com/vision/automl/docs/containers-gcs-tutorial?hl=en_US#container-predict-example-python
  Args:
      items: dictionary containing the item urls, names, titles and descriptions
      start: starting index
      end: ending index
      tmp_dir: temporary directory to store all the images from the starting index to the ending index
      folders: dictionary containing the clothes/shoes/outliers directory paths
      ip_address: (str) Server's IP address (uses "localhost" as default)
      port_number: (int) The port number on your device to accept REST API calls (uses 8501 as default
      -- this port must be the same as the one used when starting the docker container
      (cf. https://cloud.google.com/vision/automl/docs/containers-gcs-tutorial?hl=en_US#run_the_docker_container))
  Returns:
      The response of the prediction request.
  """

  # images from the starting index to the ending index of the original dataset
  urls = [items['urls'][i] for i in range(start, end)]
  image_names = [items['names'][i] for i in range(start, end)]
  image_titles = [items['titles'][i] for i in range(start, end)]
  image_descs = [items['descs'][i] for i in range(start, end)]

  # folders that contain the already classified items
  shoes_folder = folders['shoes']
  clothes_folder = folders['clothes']
  outliers_folder = folders['outliers']

  if not os.path.isdir(tmp_dir):
    os.mkdir(tmp_dir)

  filenames = []

  for i in range(len(urls)):
    if (isFile(os.path.join(shoes_folder, image_names[i])) or
        isFile(os.path.join(clothes_folder, image_names[i])) or
        isFile(os.path.join(outliers_folder, image_names[i]))):
      print('Item with ID #{} has already been classified and will be skipped.'.format(image_names[i].split('.')[0]))
      continue
    
    if (isMatchAccessory(image_titles[i]) or 
        isMatchAccessory(image_descs[i])):
      print('Item with ID #{} is an accessory, it will not be used in the training set and will be skipped.'.format(image_names[i].split('.')[0]))
      continue

    if (os.path.isfile(tmp_dir + image_names[i])):
      print('Item with ID #{} is already in the temporary directory but has not been classified and it will be added.'.format(image_names[i].split('.')[0]))
    else:
      urllib.urlretrieve(urls[i], tmp_dir + image_names[i])
      print('Downloaded image #{} with item id {} into the temporary directory'.format(start + i, image_names[i].split('.')[0]))
    filenames.append(image_names[i])

  container_predict(tmp_dir, filenames, folders, ip_address, port_number)

  # os.rmdir(tmp_dir)

def container_predict(image_dir, image_filenames, save_dict, ip_address='localhost', port_number=8501, generate_json=False):
  """Sends a prediction request to TFServing docker container REST API.
  # Directly taken from:
  # https://cloud.google.com/vision/automl/docs/containers-gcs-tutorial?hl=en_US#container-predict-example-python
  Args:
      image_dir: (str) Name of images folder
      image_filenames: (list) List of filenames of the images to get a prediction for
      ip_address: (str) Server's IP address (uses "localhost" as default)
      port_number: (int) The port number on your device to accept REST API calls (uses 8501 as default
      -- this port must be the same as the one used when starting the docker container
      (cf. https://cloud.google.com/vision/automl/docs/containers-gcs-tutorial?hl=en_US#run_the_docker_container))
      generate_json: (bool) Flag indicating whether a json file containing the base64 encoded images
      should be created or not
  Returns:
      The response of the prediction request.
  """
  all_instances = []

  # Names of the folders
  clothes_folder = save_dict['clothes']
  shoes_folder = save_dict['shoes']

  # String keys to identify the images to process
  image_keys = [image_filename.split('.')[0] for image_filename in image_filenames]

  for indx in range(len(image_filenames)):
    img_filename = os.path.join(image_dir, image_filenames[indx])

    # Convert image to base 64 encoding
    with io.open(img_filename, 'rb') as image_file:
      encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
      encodings.append(encoded_image)

      # Add the base 64 conversion to the list of input to get a prediction for
      current_instance = {'image_bytes': {'b64': str(encoded_image)}, 'key': image_keys[indx]}
      all_instances.append(current_instance)
  
  instances = {'instances': all_instances}
  if generate_json:
      with open(os.path.join(image_dir, 'base64_encodings.json'), 'w') as outfile:
          json.dump(instances, outfile)
  
  # This example shows sending requests in the same server that you start
  # docker containers. If you would like to send requests to other servers,
  # please change localhost to IP of other servers.
  url = 'http://{}:{}/v1/models/default:predict'.format(ip_address, port_number)

  # calculate the total time for how long the prediction took for each image
  with open(marginal_scores_csv, "w") as write_file:
    for indx in range(len(all_instances)):
      instance = {'instances': [all_instances[indx]]}
      time_start = datetime.now()
      response = requests.post(url, data=json.dumps(instance))
      time_end = datetime.now()

      delta_time = round((time_end - time_start).total_seconds(), 3)
      best_label, best_score = format_response(response.json(), delta_time)

      # record the images that have "not-so-great" scores and skip them
      if best_score > 0.5 and best_score < 0.75:
        image_writer = csv.writer(write_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        image_writer.writerow([image_keys[indx], best_label, best_score])
        continue

      # saves the images into their directories
      if best_label == "clothes":
        with open(os.path.join(clothes_folder, str(image_filenames[indx])), "wb") as fh:
          fh.write(base64.b64decode(encodings[indx]))
      elif best_label == "shoes":
        with open(os.path.join(shoes_folder, str(image_filenames[indx])), 'wb') as fh:
          fh.write(base64.b64decode(encodings[indx]))

def format_response(resp, delta_time):
    """ Formats the predictions into a more readable format
    Args:
        resp: (object) response returned by the service
    Returns:
        Nothing but prints the predictions in a readable format
    """
    try:
      preds = resp['predictions'][0]
    except KeyError:
      print('Error')

    best_score_indx = np.argmax(preds['scores'])
    best_score = np.max(preds['scores'])
    best_label = preds['labels'][best_score_indx]

    print("{}: {} - {}, total time: {}".format(preds['key'], best_label, best_score, delta_time))

    return best_label, best_score

def isMatchShoe(token):
  return re.search(r'\b(shoe(s|)|ultra[ ]*boost|flip|heel(s|)|sneaker(s|)|slipper(s|)|boot(s|ies|)|loafer(s|)|sandal(s|)|balance|box|puma|kyrie|vans|converse|air|foot|vapor|wedge|yeezy(s|)|air[ ]*jordan(s|)|slip[ ]*on(s|)|croc(s|))\b', token)

def isMatchClothes(token):
  return re.search(r'\b(button(ed|)|constume(s|)|poncho(s|)|windbreaker(s|)|blouse(s|)|legging(s|)|chaps|gown(s|)|jogger(s|)|dres(ses|es|ess|s|sess)|top(s|)|short(s|)|jersey(s|)|tuxedo|shirt(s|)|kimono(s|)|pajama(s|)|hoodie(s|)|pant(s|)|jean(s|)|jacket(s|)|blazer(s|)|cloth(es|ing|)|vest|coat(s|)|tee(s|)|tshirt|denim|kors|tie(s|)|bape|sweater(s|)|sweat[ ]*shirt|sleeve|polo|suit|sock(s|)|wallet|cotton|wool|lululemon|fabric|peacoat)\b', token)

def isMatchAccessory(token):
  return re.search(r'\b(beanie(s|)|hat(s|)|glove(s|)|belt(s|))\b', token)

def isFile(path):
  return os.path.isfile(path)

def removeItemsWithMarginalScores(folder_names):
  shoes_folder = folder_names['shoes']
  clothes_folder = folder_names['clothes']

  with open(marginal_scores_csv) as file:
    rows = csv.reader(file, delimiter=',')

    for row in rows:
      item_id = row[0]
      assigned_label = row[1]

      if assigned_label == 'clothes':
        try:
          os.remove(clothes_folder + '{}.jpg'.format(item_id))
        except OSError:
          print('Error: {}.jpg file is not found'.format(item_id))
      elif assigned_label == 'shoes':
        try:
          os.remove(shoes_folder + '{}.jpg'.format(item_id))
        except OSError:
          print('Error: {}.jpg file is not found'.format(item_id))

if __name__ == "__main__":
  starting_index = 30000 #33480
  ending_index = 70000 #50000

  folders = {
    'shoes': clothes_shoes_dir + 'shoes_{}_to_{}/'.format(starting_index, ending_index),
    'clothes': clothes_shoes_dir + 'clothes_{}_to_{}/'.format(starting_index, ending_index),
    'outliers': clothes_shoes_dir + 'outliers_{}_to_{}/'.format(starting_index, ending_index)
  }

  items = get_urls_and_image_names(root + 'data/2019-10-01_2020_01_01_itemid_url_title_description.csv')
  download_shoes_clothes_images_docker(items, 30000, 70000, root + 'tmp/', folders)
  # removeItemsWithMarginalScores(download_folders) 