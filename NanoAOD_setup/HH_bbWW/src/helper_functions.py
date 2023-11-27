import pandas as pd

def reset_log_file():
    log_file = open("log_file.txt",'w')
    log_file.close()

def print_twice(*args,**kwargs):
    print(*args,**kwargs)
    with open("log_file.txt", "a") as f: 
        print(file=f,*args,**kwargs)

def output_csv(df, outFileName):
    npy = df.AsNumpy()
    df = pd.DataFrame(npy)
    df.to_csv(outFileName)

