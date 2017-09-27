#! /usr/bin/env python3
#
# Copyright (c) 2016, 2017, Nesys Lab, Universitet i Oslo
# Author: Gergely Csúsc, Christopher Coello
#
# This software is made available under the MIT licence, see LICENCE.txt.

import sys,os
import requests
import json

# the send_query function is taken from the ecallen package
def send_query(query_base,spec_id,args):
    response = requests.get(query_base.format(spec_id),params=args)
    if response.ok:
        json_tree = response.json()
        if json_tree['success']:
            return json_tree
        else:
            exception_string = 'did not complete api query successfully'
    else:
        exception_string = 'API failure. Allen says: {}'.format(response.reason)

    # raise an exception if the API request failed
    raise ValueError(exception_string)

def allen2quicknii(series_id,get_orig,target_dir=""):
    #current folder
    cwd=os.getcwd()
    # make and get to the target dir if necessary
    if target_dir:
        if not os.path.exists(target_dir):
            os.mkdir(target_dir)
        os.chdir(target_dir)

    # create a folder with the series_id and get there
    if not os.path.exists(series_id):
        os.mkdir(series_id)
    os.chdir(series_id)

    # create originals if necessary
    if get_orig and not os.path.exists("originals"):
        os.mkdir("originals")

    # Get and save series metadata (JSON)
    json_tree = send_query("http://api.brain-map.org/api/v2/data/SectionDataSet/{}.json",series_id,{"include":"equalization,section_images"})
    with open(str(series_id)+"_info.json", "w") as f:
        json.dump(json_tree, f)

    # Check reference space ID. 9 works (coronal, right side), 10 may work (sagittal, left side)
    rsid = json_tree['msg'][0]['reference_space_id']
    if (rsid!=9):
        print("Warning: Reference space id is not 9 (it is {}), alignment may not work".format(rsid))

    # Extract and sort image metadata. Section numbering can be P->A or A->P, depending on dataset
    sec_im = json_tree['msg'][0]['section_images']
    sec_im = sorted(sec_im,key=lambda item:item['section_number'])
    first = sec_im[0]['section_number']
    last  = sec_im[-1]['section_number']
    print("Processing sections {}-{}".format(first,last))

    # Create download URL pattern with optional colour equalization
    im_allen = "http://api.brain-map.org/api/v2/image_download/"
    img_pattern = im_allen+"{}?downsample={}"
    if 'equalization' in json_tree['msg'][0]:
        eq_info = json_tree['msg'][0]['equalization']
        eq_param = "range={},{},{},{},{},{}".format(eq_info['red_lower'],eq_info['red_upper'],eq_info['green_lower'],eq_info['green_upper'],eq_info['blue_lower'],eq_info['blue_upper'])
        img_pattern = im_allen+"{}?"+eq_param+"&downsample={}"

    # URL pattern for getting coordinates
    coord_pattern = "http://api.brain-map.org/api/v2/image_to_reference/{}.json"

    xml = open("{}.xml".format(series_id),"w")
    xml.write("<?xml version='1.0' encoding='UTF-8'?>\n")
    xml.write("<series name='{}' first='{}' last='{}'>\n".format(series_id,first,last))

    # QuickNII: [456,528,320] las, Allen: pir

    for section in sec_im:
        # Section metadata
        sec_id  = section['id']
        sec_num = section['section_number']
        #
        sec_width  = section['width']
        sec_height = section['height']

        # Section corners. Request provides data in micrometers, divide by 25 to get voxels
        # top-left
        ojson = send_query(coord_pattern,sec_id,{'x':0,'y':0})
        o_p = ojson['msg']['image_to_reference']['x']/25
        o_i = ojson['msg']['image_to_reference']['y']/25
        o_r = ojson['msg']['image_to_reference']['z']/25
        # top-right
        ujson = send_query(coord_pattern,sec_id,{'x':sec_width,'y':0})
        u_p = ujson['msg']['image_to_reference']['x']/25
        u_i = ujson['msg']['image_to_reference']['y']/25
        u_r = ujson['msg']['image_to_reference']['z']/25
        # bottom-left
        vjson = send_query(coord_pattern,sec_id,{'x':0,'y':sec_height})
        v_p = vjson['msg']['image_to_reference']['x']/25
        v_i = vjson['msg']['image_to_reference']['y']/25
        v_r = vjson['msg']['image_to_reference']['z']/25

        # hard coded dimension of the 25um Allen Brain mouse template
        o = (456-o_r,528-o_p,320-o_i)
        u = (o_r-u_r,o_p-u_p,o_i-u_i)
        v = (o_r-v_r,o_p-v_p,o_i-v_i)
        xml.write("  <slice filename='{:04}_{}.jpg' nr='{}' width='{}' height='{}' anchoring='".format(sec_num,sec_id,sec_num,sec_width,sec_height))
        xml.write("ox={}&oy={}&oz={}".format(*o))
        xml.write("&ux={}&uy={}&uz={}".format(*u))
        xml.write("&vx={}&vy={}&vz={}".format(*v))
        xml.write("'/>\n")

        # Calculate downsampling rate for QuickNII-friendly images (also download-friendly)
        downsample=0
        while sec_width>=2000 and sec_height>=1800:
            downsample=downsample+1
            sec_width=sec_width/2
            sec_height=sec_height/2

        # Download and save image (downscaled)
        chunk_size = 1024
         #RGB, uint8
        file_size_dl = 0;
        image=requests.get(img_pattern.format(sec_id,downsample),stream=True)
        print("\r -- section {:04} downsampled".format(sec_num),end="",flush=True)
        with open("{}_s{:04}.jpg".format(sec_id,sec_num),"wb") as f:
            for chunk in image.iter_content(chunk_size=chunk_size):
                if chunk:
                    file_size_dl += chunk_size
                    #print("\r -- section number {:04} downsampled [{0:.3f}%]".format(sec_num,100*file_size_dl/tot_bytes),end="",flush=True)
                    f.write(chunk)
        # Download and save original
        chunk_size = 65536
        if get_orig:
            image = requests.get(img_pattern.format(sec_id,0),stream=True)
            file_size_dl = 0;
            print("\r -- section {:04} original size".format(sec_num),end="",flush=True)
            with open("originals/{}_s{:04}.jpg".format(sec_id,sec_num),"wb") as f:
                for chunk in image.iter_content(chunk_size=chunk_size):
                    if chunk:
                        file_size_dl += chunk_size
                        f.write(chunk)

    xml.write("</series>")
    xml.close()
    os.chdir(cwd)

def parse_command_line(argv):
    """Parse the script's command line."""
    import argparse
    parser = argparse.ArgumentParser(
        description="""\
Download a dataset from the Allen Institute and creates the XML file compatible
with QuickNII.

A downsample version of the images will be downloaded together with its spatial
coordinates in the Common Coordinate Framwork (CCF) space. The output will be
visible in QuickNII tool.
""")
    parser.add_argument("series_id")
    parser.add_argument("--get-orig", action="store_true",
                        help="the original size images will be downloaded "
                        "This might take a lot of time")
    parser.add_argument("--target-dir", type=str, default="",
                        help="the folder where you want to place the data. If "
                        "not specified, it will write it in the current "
                        "folder")
    args = parser.parse_args(argv[1:])
    return args


def main(argv):
    """The script's entry point."""
    args = parse_command_line(argv)
    return allen2quicknii(args.series_id,
                                     get_orig=args.get_orig,
                                     target_dir=args.target_dir) or 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
