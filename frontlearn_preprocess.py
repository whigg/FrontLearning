#!/usr/bin/env python
u"""
frontlearn_preprocess.py
by Yara Mohajerani (Last update 11/2018)

Pre-process input images to improve learning

Update History
    11/2018 Clean up
    09/2018 Don't smooth
    04/2018 Written
"""
import os
import sys
import getopt
import numpy as np
from glob import glob
from PIL import Image,ImageEnhance,ImageOps,ImageFilter

#-- read in images
def load_data(trn_dir,tst_dir):
    #-- get a list of the input files
    trn_list = glob(os.path.join(trn_dir,'images/*.png'))
    tst_list = glob(os.path.join(tst_dir,'images/*.png'))
    #-- get just the file names
    trn_files = [os.path.basename(i) for i in trn_list]
    tst_files = [os.path.basename(i) for i in tst_list]

    #-- read training data
    n = len(trn_files)
    train_img = []
    for i,f in enumerate(trn_files):
        train_img.append(Image.open(os.path.join(trn_dir,'images',f)))

    #-- also get the test data
    n_test = len(tst_files)
    test_img = []
    for i in range(n_test):
        test_img.append(Image.open(tst_list[i]))

    images = {'train':train_img,'test':test_img}
    names = {'train':trn_files,'test':tst_files}
    return [images,names]

#-- function to read and enhance the data
def enhance_images(sharpness,contrast,glacier):
    #-- directory setup
    #- current directory
    current_dir = os.path.dirname(os.path.realpath(__file__))
    main_dir = os.path.join(current_dir,'..','FrontLearning_data')
    glacier_ddir = os.path.join(main_dir,'%s.dir'%glacier)
    data_dir = os.path.join(glacier_ddir, 'data')
    trn_dir = os.path.join(data_dir,'train')
    tst_dir = os.path.join(data_dir,'test')

    #-- first read data
    images,names = load_data(trn_dir,tst_dir)
    #-- make output directory dictionary
    outdir = {}
    outdir['train'] = os.path.join(trn_dir,'images_equalize_autocontrast_smooth_edgeEnhance')
    outdir['test'] = os.path.join(tst_dir,'images_equalize_autocontrast_smooth_edgeEnhance')
    #-- loop through train and test data
    for t in ['test']:#,'train']:
        if (not os.path.isdir(outdir[t])):
            os.mkdir(outdir[t])
        #-- loop through images and ehnance
        for m,n in zip(images[t],names[t]):
            #-- first blur the images to get rid of all the noise
            '''
            sharp_obj = ImageEnhance.Sharpness(m)
            blurred = sharp_obj.enhance(sharpness)
            contr_obj = ImageEnhance.Contrast(blurred)
            final = contr_obj.enhance(contrast)
            
            contr_obj = ImageEnhance.Contrast(m)
            im = contr_obj.enhance(contrast)
            final = im.filter(ImageFilter.SMOOTH)#.filter(ImageFilter.EDGE_ENHANCE)
            '''
    
            final = ImageOps.equalize(ImageOps.autocontrast(m.convert('L'))).filter(ImageFilter.SMOOTH).filter(ImageFilter.EDGE_ENHANCE)


            #-- write image to file
            final.save(os.path.join(outdir[t],'%s'%n))

#-- main function to get user input and call sharpen function
def main():
    #-- Read the system arguments listed after the program
    long_options = ['sharpness=','contrast=','glacier=']
    optlist,arglist = getopt.getopt(sys.argv[1:],'=S:C:G:',long_options)

    sharpness= 0.1
    contrast = 4
    glacier = 'greenland_training'
    for opt, arg in optlist:
        if opt in ('-S','--sharpness'):
            sharpness = np.float(arg)
        elif opt in ('-C','--contrast'):
            contrast = np.float(arg)
        elif opt in ('-G','--glacier'):
            glacier = arg

    enhance_images(sharpness,contrast,glacier)

if __name__ == '__main__':
    main()
