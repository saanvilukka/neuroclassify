from PIL import Image
import glob
from pathlib import Path
import numpy as np
import cv2
import pandas as pd
import sys
from datetime import datetime
import time
import json
import getpass
username = getpass.getuser()

##### SET UP ######
namemap = {
    's1r1': 'v10f06-092_a1_F1-1',
    's1r2': 'v10f06-089_a1_F3-1',
    's2r1': 'v10f06-092_b1_M1-1',
    's2r2': 'v10f06-089_b1_M3-1',
    's3r1': 'v10f06-092_c1_F2-1',
    's3r2': 'v10f06-089_c1_F4-1',
    's4r1': 'v10f06-092_d1_M2-1',
    's4r2': 'v10f06-089_d1_M4-1',
    's5r1': 'v10f06-090_a1_F1-2',
    's5r2': 'v10f06-091_a1_F3-2',
    's6r1': 'v10f06-090_b1_M1-2',
    's6r2': 'v10f06-091_b1_M3-2',
    's7r1': 'v10f06-090_c1_F2-2',
    's7r2': 'v10f06-091_c1_F4-2',
    's8r1': 'v10f06-090_d1_M2-2',
    's8r2': 'v10f06-091_d1_M4-2',
    '1AL': 'V11L12-024_A1_1AL',
    '7AL': 'V11L12-024_B1_7AL',
    '9AL': 'V11L12-024_C1_9AL',
    '10AL': 'V11L12-024_C1_10AL',
    '1AR': 'V11U28-385_B1_1AR',
    '7AR': 'V11U28-385_B1_7AR',
    '9AR': 'V11U28-385_C1_9AR',
    '10AR': 'V11U28-385_D1_10AR',
    '22AR': 'V12N28-026_A1_22AR',
    '22AL': 'V12N28-026_B1_22AL',
    '24AR': 'V12N28-026_C1_24AR',
    '24AL': 'V12N28-026_D1_24AL',
    '19AL': 'V12U21-122_A1_19AL',
    '19AR': 'V12U21-122_B1_19AR',
    '21AL': 'V12U21-122_C1_21AL',
    '21AR': 'V12U21-122_D1_21AR',
    's1-1': 'V12U21-017_A1_s1-1',
    's1-3': 'V12U21-119-A1_s1-3',
    's1-2': 'V12U21-120-B1_s1-2',
    's2-2': 'V12U21-016_A1_s2-2',
    's2-1': 'V12U21-017_B1_s2-1',
    's2-3': 'V12U21-119-B1_s2-3',
    's3-1': 'V12U21-017_C1_s3-1',
    's3-3': 'V12U21-119-D1_s3-3',
    's3-2': 'V12U21-120-D1_s3-2',
    's4-2': 'V12U21-016_C1_s4-2',
    's4-1': 'V12U21-017_D1_s4-1',
    's4-3': 'V12U21-119-C1_s4-3',
    's5-1': 'V12U21-016_B1_s5-1',
    's5-2': 'V12U21-120-A1_s5-2',
    's6-1': 'V12U21-016_D1_s6-1',
    's6-2': 'V12U21-120-C1_s6-2'
}  

                    
namemap_int = {v: k for k, v in namemap.items()}


# REPLACE PATH HERE 
dir_path = Path(rf'C:\Users\\{username}\Box\diana_collaboration_DATA')

# REPLACE PATH HERE
preproc_path = Path(r"C:\Users\MEYERSE\Box\diana_collaboration_DATA\1_preprocessing")
#Folder to original tifs
tifs_path = preproc_path / 'Data'
barcodes_path = preproc_path / 'barcodes'
barcode_iso_path = preproc_path / 'barcodes_iso'
barcode_iso_overlap_path = preproc_path / 'barcodes_iso_overlap'

barcode_iso_paths = list(barcode_iso_overlap_path.glob('*.png'))
generated_subjects = set(['_'.join(x.stem.split('_')[:3]) for x in barcode_iso_paths])


tif_list = list(tifs_path.glob('*.tif'))

#REPLACE PATH HERE
json_path = Path(r'C:\Users\MEYERSE\Box\diana_collaboration_DATA\Spatial_info')



target_imsize = 512

#Setup variables
Image.MAX_IMAGE_PIXELS = None
# scaling_factor = 0.08473858
# scaling_factor = 0.15   # original scaling_factor = 0.08473858

target_image_width = 512
target_image_height = 512

barcode_diameter_micron = 65
barcode_pixel_radius = 94 #Fine tuned this number on 8/14/23 to match Loupe browser
# barcode_pixel_radius = 89.43834961
# barcode_pixel_radius = round(barcode_diameter_micron / (65/89.43834961))


listofdicts = []
for img in tif_list:
    img_name = img.stem

    #Process images only in our dictionary above
    if img_name not in namemap_int:
        print(f'Skipping because not in namemap: {img_name}')
        continue

    if img_name in generated_subjects:
        print(f'Skipping because already generated: {img_name}')
        continue

    #manipulate string to get it in the right format
    target_name = namemap_int[img_name]
    json_file = json_path / f'scalefactors_{target_name}_json.json'

    with open(json_file) as f:
        jload = json.load(f)

    barcode_pixel_diameter = jload['spot_diameter_fullres']
    barcode_pixel_radius = round(barcode_pixel_diameter/2)

    img_barcode_path = barcodes_path / f'{img.stem}.csv'
    colnames=['ID', 'over_tissue', 'x_coord', 'y_coord', 'x', 'y'] 
    locsdf = pd.read_csv(img_barcode_path, names=colnames, header=None)

    if locsdf['x'].iloc[0] == 'pxl_row_in_fullres':
        locsdf = locsdf.iloc[1:]
        locsdf[['x', 'y', 'x_coord', 'y_coord', 'over_tissue']] = locsdf[['x', 'y', 'x_coord', 'y_coord', 'over_tissue']].apply(pd.to_numeric)
        locsdf.reset_index(drop=True)

    #Get just barcodes over tissue
    bcdf = locsdf.loc[locsdf['over_tissue'] == 1]
    im = cv2.imread(str(img))

    print(f'Starting {img_name}')

    for idx,row in bcdf.iterrows():

        im_cropped = np.asarray([])

        left = int(row['y'] - target_image_width/2)
        right = int(row['y'] + target_image_width/2)
        bottom = int(row['x'] + target_image_height/2)
        top = int(row['x'] - target_image_height/2)

        center_x = round(target_image_width / 2)
        center_y = round(target_image_height / 2)

        im_cropped = im[top:bottom, left:right]

        im_cropped_copy = im_cropped.copy()

        
        img_barcode_mask = np.zeros(shape=[target_image_width, target_image_height], dtype=np.uint8)
        cv2.circle(img_barcode_mask, (center_y-1, center_x-1), barcode_pixel_radius, 255, -1)
        

        backtorgb = cv2.cvtColor(img_barcode_mask,cv2.COLOR_GRAY2RGB)

        added_image = cv2.addWeighted(im_cropped_copy,0.8,backtorgb,0.2,0)
        cv2.circle(added_image, (center_y-1, center_x-1), barcode_pixel_radius, (0, 0, 255), 1)

        bcd_id = row['ID']
        
        cv2.imwrite(str(barcode_iso_overlap_path / f'{img_name}_{bcd_id}.png'), added_image)


print('finished')
