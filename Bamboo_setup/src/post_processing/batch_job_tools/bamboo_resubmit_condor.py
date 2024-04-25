import os, sys, glob
from argparse import ArgumentParser

if __name__ == '__main__':

    parser = ArgumentParser()
    parser.add_argument("-i", "--input_dir", action="store", help="directory to resubmit jobs for")
    args = parser.parse_args()

    job_resubmit = []
    jobs = glob.glob("%s/batch/output/*"%args.input_dir)
    for job in jobs:
        root_file = glob.glob("%s/*.root"%job)[0]
        root_file_size = os.path.getsize(root_file)
        job_id = job.split("/")[-1]
        if root_file_size == 0:
            print ("Resubmitting Job %s"%job_id)
            job_resubmit.append(job_id)
    
    job_resubmit = ','.join(job_resubmit)

    os.system("bambooHTCondorResubmit --ids=%s %s/batch/input/condor.cmd"%(job_resubmit, args.input_dir))

