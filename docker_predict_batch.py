import base64
import io
import json
import numpy as np
import os
import requests
import csv
from datetime import datetime

root = '' # TODO: specify your project's toplevel directory here
marginal_scores_csv = root + 'csv/marginal_scores/scores.csv'   # used for logging marginal results (automl model struggles to classify with a high accuracy)
encodings = []  # store the image encodings so that an image could be written to a directory later

def container_predict(image_dir, image_filenames, save_dict, ip_address='localhost', port_number=8501, generate_json=False):
    """Sends a prediction request to TFServing docker container REST API.
    # Directly taken from:
    # https://cloud.google.com/vision/automl/docs/containers-gcs-tutorial?hl=en_US#container-predict-example-python
    Args:
        image_dir: (str) Name of images folder
        image_filenames: (list) List of filenames of the images to get a prediction for
        save_dict: (dict) Dictionary containing the directory paths of folders to save the image into
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
            
            # record the images that have "not-so-great" scores
            if best_score > 0.5 and best_score < 0.75:
                image_writer = csv.writer(write_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                image_writer.writerow([image_keys[indx], best_label, best_score])

            # saves the images into their directories
            if best_label == "clothes":
                with open(os.path.join(save_dict['clothes'], str(image_filenames[indx])), "wb") as fh:
                    fh.write(base64.b64decode(encodings[indx]))
            elif best_label == "shoes":
                with open(os.path.join(save_dict['shoes'], str(image_filenames[indx])), 'wb') as fh:
                    fh.write(base64.b64decode(encodings[indx]))

def format_response(resp, delta_time):
    """ Formats the predictions into a more readable format
    Args:
        resp: (object) response returned by the service
        delta_time: time taken for the model to make a prediction
    Returns:
        Nothing but prints the predictions in a readable format
    """
    preds = resp['predictions'][0]
    best_score_indx = np.argmax(preds['scores'])
    best_score = np.max(preds['scores'])
    best_label = preds['labels'][best_score_indx]

    print("{}: {} - {}, total time: {}".format(preds['key'], best_label, best_score, delta_time))

    return best_label, best_score

if __name__ == "__main__":
    unisex_dir = root + 'data/images/clothes_shoes_all_unisex'

    unisex_save = {
        'clothes': "{}data/images/unisex/clothes".format(root),
        'shoes': "{}data/images/unisex/shoes".format(root)
    }

    filenames = [f for f in os.listdir(unisex_dir) if f.endswith('jpg')]
    container_predict(unisex_dir, filenames, unisex_save)