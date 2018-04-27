#!/usr/bin/env python
u"""
frontlearn_postprocess.py
by Yara Mohajerani

Post-Processing of the predictions of the neural network

TO BE COMPLETED

History
    04/2018 Written
"""
import os
import numpy as np
import imp
import sys
from glob import glob
from PIL import Image
import matplotlib.pyplot as plt
from shapely.geometry import Point, LineString


def post_process(parameters):
    glacier = parameters['GLACIER_NAME']
    n_batch = int(parameters['BATCHES'])
    n_epochs = int(parameters['EPOCHS'])
    n_layers = int(parameters['LAYERS_DOWN'])
    n_init = int(parameters['N_INIT'])
    sharpness = float(parameters['SHARPNESS'])
    contrast = float(parameters['CONTRAST'])
    drop = float(parameters['DROPOUT'])
    #-- directory setup
    #- current directory
    current_dir = os.path.dirname(os.path.realpath(__file__))
    ddir = os.path.join(current_dir,'%s.dir'%glacier)
    data_dir = os.path.join(ddir, 'data')
    trn_dir = os.path.join(data_dir,'train')
    tst_dir = os.path.join(data_dir,'test')

    #-- set up labels from parameters
    drop_str = ''
    if drop>0:
        drop_str = '_w%.1fdrop'%drop

    #-- total number of layers
    layers_tot = 2*n_layers+1

    if sharpness in ['None','none','NONE','N','n']:
        sharpness_str = ''
    else:
        sharpness_str = '_sharpness%.1f'%sharpness
    if contrast in ['None','none','NONE','N','n']:
        contrast_str = ''
    else:
        contrast_str = '_contrast%.1f'%contrast

    #-- read in output data of the neural network
    subdir = os.path.join(tst_dir,'output_%ibtch_%iepochs_%ilayers_%iinit%s%s%s'\
        %(n_batch,n_epochs,layers_tot,n_init,drop_str,sharpness_str,contrast_str))

    #-- get a list of the input files
    in_list = glob(os.path.join(subdir,'*.png'))
    n_files = len(in_list)
    w,h = np.array(Image.open(in_list[0]).convert('L')).shape
    mask = None
    #-- vectorize files
    for i in range(n_files):
        img = np.array(Image.open(in_list[i]).convert('L'))/255.

        #-- set a threshold for points that are to be identified as the front
        at = 0.8 #-- amplitude threshold
        img_flat = img.flatten()
        ind_black = np.squeeze(np.nonzero(img_flat <= at))
        ind_white = np.squeeze(np.nonzero(img_flat > at))
        img_flat[ind_black] = 0.
        img_flat[ind_white] = 1.
        img2 = img_flat.reshape(img.shape)

        #-- now draw a line through the points
        #-- first get the index of all the black points
        ind_2D = np.squeeze(np.nonzero(img2 == 0.))

        #-- get the vertical mean and std of all the points
        y_avg = np.mean(ind_2D[1,:])
        y_std = np.std(ind_2D[1,:])

        pts = []
        n_pts = len(ind_2D[0,:])
        for i in range(n_pts):
            if (int(ind_2D[1,i]) > (y_avg - y_std) and int(ind_2D[1,i]) < (y_avg + y_std)):
                pts.append(Point(int(ind_2D[0,i]),int(ind_2D[1,i])))
        frontline = LineString(pts)

        x, y = frontline.xy
        plt.plot(x,y,alpha=0.5)
        plt.imshow(np.transpose(img2),zorder=1)
        plt.plot(np.arange(w),np.ones(h)*y_avg)
        plt.gca().invert_xaxis()
        plt.gca().invert_yaxis()
        plt.show()

#-- main function to get parameters and pass them along to the postprocessing function
def main():
    if (len(sys.argv) == 1):
        sys.exit('You need to input at least one parameter file to set run configurations.')
    else:
        #-- Input Parameter Files (sys.argv[0] is the python code)
        input_files = sys.argv[1:]
        #-- for each input parameter file
        for file in input_files:
            #-- keep track of progress
            print(os.path.basename(file))
            #-- variable with parameter definitions
            parameters = {}
            #-- Opening parameter file and assigning file ID number (fid)
            fid = open(file, 'r')
            #-- for each line in the file will extract the parameter (name and value)
            for fileline in fid:
                #-- Splitting the input line between parameter name and value
                part = fileline.split()
                #-- filling the parameter definition variable
                parameters[part[0]] = part[1]
            #-- close the parameter file
            fid.close()

            #-- pass parameters to training function
            post_process(parameters)

if __name__ == '__main__':
    main()
