import os, sys, glob
from argparse import ArgumentParser

if __name__ == '__main__':

    parser = ArgumentParser()
    parser.add_argument("-i", "--input_dir", action="store", help="directory to resubmit jobs for")
    args = parser.parse_args()

    jobs = glob.glob("%s/batch/output/*"%args.input_dir)
    for job in jobs:
        root_file = glob.glob("%s/*.root"%job)[0]
        root_file_size = os.path.getsize(root_file)
        job_id = job.split("/")[-1]
        if root_file_size == 0:
            print (job_id)

