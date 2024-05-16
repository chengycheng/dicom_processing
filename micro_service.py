from flask import Flask, request, send_file

# for DICOM file processing
import pydicom
from pydicom.pixel_data_handlers.util import apply_voi_lut

# for image processing
import cv2 # opencv-python
import numpy as np

import os


app = Flask(__name__)

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        file = request.files['file']
    except KeyError:
        return 'file argument missing.', 400

    filename = file.filename

    # Save the uploaded file
    file.save(filename)

    return f'File: {filename} uploaded successfully'

@app.route('/header/<filename>', methods=['GET'])
def get_header(filename):
    """
    Retrieves the value of a specified DICOM tag from a DICOM file.

    Args:
        filename (str): The path to the DICOM file.
        Sample call:
        http://127.0.0.1:5000/header/IM000002?tag=(0008,0080)
    Returns:
        str: A string containing the tag information if found, or an error message if the tag is not found.

    Raises:
        FileNotFoundError: If the specified DICOM file is not found.
        KeyError: if query tag is not found.
    """

    # Get the tag from the query parameters
    tag = request.args.get('tag')

    # Read the DICOM file
    try:
        ds = pydicom.dcmread(filename)
    except FileNotFoundError:
        return 'File not found', 404
    
    # parse tag query values
    tag_group, tag_element = tag.strip('()').split(',')
    tag_group =  int ('0x' + tag_group , 16)
    tag_element = int ('0x' + tag_element, 16)
    
    # Check if the tag exists in the DICOM file
    try:
        tag_key = ds[tag_group, tag_element].keyword
        tag_val = ds[tag_group, tag_element].value
        return f'Tag {tag} : {tag_key} has value {tag_val}'
    except KeyError:
        return 'Tag not found', 404

@app.route('/convert/<filename>', methods=['GET'])
def convert(filename):

    def lin_stretch_img(img, low_prc, high_prc, do_ignore_minmax=True):
        """ 
        added to handle the case when the image turns out all white after conversion.
        Found from: https://stackoverflow.com/questions/74027712/converting-hand-radiograph-dicom-to-png-returns-white-bright-image
        Apply linear "stretch" - low_prc percentile goes to 0, 
        and high_prc percentile goes to 255.
        The result is clipped to [0, 255] and converted to np.uint8

        Additional feature:
        When computing high and low percentiles, ignore the minimum and maximum intensities (assumed to be outliers).
        """
        # For ignoring the outliers, replace them with the median value
        if do_ignore_minmax:
            tmp_img = img.copy()
            med = np.median(img)  # Compute median
            tmp_img[img == img.min()] = med
            tmp_img[img == img.max()] = med
        else:
            tmp_img = img

        lo, hi = np.percentile(tmp_img, (low_prc, high_prc))  # Example: 1% - Low percentile, 99% - High percentile

        if lo == hi:
            return np.full(img.shape, 128, np.uint8)  # Protection: return gray image if lo = hi.

        stretch_img = (img.astype(float) - lo) * (255/(hi-lo))  # Linear stretch: lo goes to 0, hi to 255.
        stretch_img = stretch_img.clip(0, 255).astype(np.uint8)  # Clip range to [0, 255] and convert to uint8
        return stretch_img

    # Convert the DICOM file to PNG
    try:
        ds = pydicom.dcmread(filename)
    except FileNotFoundError:
        return 'File not found', 404

    # convert DICOM pixel array to PIL Image object

    img = ds.pixel_array
    img = apply_voi_lut(img, ds, index=0)
    img = lin_stretch_img(img, 0.1, 99.9)   # Apply "linear stretching" (lower percentile 0.1 goes to 0, and percentile 99.9 to 255).

    cv2.imwrite('output.png', img)

    return send_file('output.png', mimetype='image/png')

    os.remove('output.png')

if __name__ == '__main__':
    app.run(debug=True)
