from ROOT import *
import multiprocessing as mp
import os
import math
import optparse
import time
import sys
import numpy as np
import root_numpy as rn

## FUNCTIONS DEFINITION

def smearing(z_hit, y_hit, energyDep_hit, options):
	Z=list(); Y=list()
	Z*=0; Y*=0
	Z.append(np.random.normal(loc=z_hit, scale=options.diff_param, size=int(energyDep_hit*opt.Conversion_Factor)))
	Y.append(np.random.normal(loc=y_hit, scale=options.diff_param, size=int(energyDep_hit*opt.Conversion_Factor)))
	return Z, Y


def AddBckg(options):
	
	if options.bckg:
		bckg_array=np.zeros((options.z_pix,options.y_pix))
		for s in range(0, options.z_pix):
			for t in range(0, options.y_pix):
				bckg_array[s][t]=np.random.normal(loc=options.noise_mean, scale=options.noise_sigma)
               
	return bckg_array 


def AddTrack(Tree, hist_list, smear_func):
	for i in range(0, Tree.numhits):
		S=smear_func(Tree.z_hits[i], Tree.y_hits[i], Tree.energyDep_hits[i], opt)
		for j in range(0, len(S[0])):
			for t in range(0, len(S[0][j])):
				hist_list[entry].Fill(S[0][j][t],S[1][j][t])
	signal_array=rn.hist2array(hist_list[entry])				
	
	return signal_array

def SaveValues(par, out):

	out.cd()
	out.mkdir('param_dir')
	param_dir.cd()

	for k,v in par.items():
		h=TH1F(k, '', 1, 0, 1)
		h.SetBinContent(1, v)
		h.Write()
	out.cd()

	return None

def SaveEventInfo(info_dict, folder, out):
	
	out.cd()
	folder.cd()

	for k,v in info_dict.items():
		h=TH1F(k, '', 1,0,1)
		h.SetBinContent(1,v)
		h.Write()
	out.cd()
	info_dict.clear()

	return None

######################################### MAIN EXECUTION ###########################################

if __name__ == "__main__":

	#CALL: python img_generator.py ConfigFile.txt -I <<INPUT_FOLDER>>

	parser = optparse.OptionParser("usage: %prog [options] arg1 arg2")

	parser.add_option("-I", "--inputfolder", dest="infolder", default=os.getcwd()+"/src", help="specify the folder containing input files")
	parser.add_option("-O", "--outputfolder", dest="outfolder", default=os.getcwd()+"/out", help="specify the output destination folder")
	
        (opt, args) = parser.parse_args()

	config = open(args[0], "r") 		#GET CONFIG FILE
	params = eval(config.read()) 		#READ CONFIG FILE

	for k,v in params.items():
		setattr(opt, k, v)

#### CODE EXECUTION ####

        run_count=1
	t0=time.time()
        
	if not os.path.exists(opt.outfolder): #CREATING OUTPUT FOLDER
            os.makedirs(opt.outfolder)
            
        for infile in os.listdir(opt.infolder): #READING INPUT FOLDER
		
		if infile.endswith('.root'):	#KEEPING .ROOT FILES ONLY

			rootfile=TFile.Open(opt.infolder+infile)
			tree=rootfile.Get('nTuple')			#GETTING NTUPLES
			
			infilename=infile[:-5]	
			outfile=TFile(opt.outfolder+'/'+infilename+'_Run'+str(run_count)+'.root', 'RECREATE') #OUTPUT NAME
       			outfile.mkdir('event_info')
	
			SaveValues(params, outfile) ## SAVE PARAMETERS OF THE RUN

			final_imgs=list();
			
			for entry in range(0, tree.GetEntries()): #RUNNING ON ENTRIES
				tree.GetEntry(entry)

				event_dict={'partID_'+str(entry): tree.pdgID_hits[0], 'E_init_'+str(entry): tree.ekin_particle[0]*1000}
				SaveEventInfo(event_dict, event_info, outfile)

				final_imgs.append(TH2F('pic_run'+str(run_count)+'_ev'+str(entry), '', opt.z_pix, -opt.z_dim*0.5, opt.z_dim*0.5, opt.y_pix, -opt.y_dim*0.5, opt.y_dim*0.5)) #smeared track with background
					
				signal=AddTrack(tree, final_imgs, smearing)
				background=AddBckg(opt)
				total=signal+background

				final_imgs[entry]=rn.array2hist(total, final_imgs[entry])

				print('%d images generated'%(entry+1))
				final_imgs[entry].Write()
			
			print('COMPLETED RUN %d'%(run_count))
                        run_count+=1
			outfile.Close()


	t1=time.time()
	print('\n')
	print('Generation took %d seconds'%(t1-t0))

