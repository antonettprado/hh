import os, sys, glob
import argparse
import yaml
import ROOT

if __name__ == "__main__":

    # Parsing arguments
    parser = argparse.ArgumentParser(description="Make datacards")
    parser.add_argument("-i", "--input_dir", action="store", dest="input_dir", help="input_dir = input directory containing results")
    parser.add_argument("-f", "--cat_disc_filename", action="store", dest="cat_disc_filename", help="cat_disc_filename = filename for yml file containing categories and discriminants")
    args = parser.parse_args()

    input_dir = args.input_dir + "/datacards"
    output_dir = args.input_dir + "/fit_results"
    if not os.path.exists(output_dir):
        os.system("mkdir %s"%os.path.abspath(output_dir))
    print ("Fits for results in: %s"%input_dir)
    print ("Fit results stored in: %s\n"%output_dir)

    with open(args.cat_disc_filename,'r') as yaml_file:
        cat_disc_yaml_data = yaml.safe_load(yaml_file)
    
    for channel in cat_disc_yaml_data["Channels"]:
        print ("  Channel: %s"%channel)
        channel_dir = input_dir + "/" + channel
        discriminant_list = cat_disc_yaml_data["Channels"][channel]
        output_dir_sel_cat = output_dir + "/" + channel
        if not os.path.exists(output_dir_sel_cat):
            os.system("mkdir %s"%os.path.abspath(output_dir_sel_cat))

        for discriminant in discriminant_list:
            print ("    Discriminant: %s"%discriminant)
            discriminant_dir = channel_dir + "/" + discriminant
            output_dir_sel_cat_disc = output_dir_sel_cat + "/" + discriminant
            if not os.path.exists(output_dir_sel_cat_disc):
                os.system("mkdir %s"%os.path.abspath(output_dir_sel_cat_disc))

            datacard_file = glob.glob("%s/*.txt"%discriminant_dir)[0]
            fit_results_filename = output_dir_sel_cat_disc + "/" + datacard_file.split("/")[-1].split(".txt")[0] + "_fit_results.txt"
            fit_results_file = open(fit_results_filename, "w")
            fit_results_file.write("Fit results for Channel: %s, Discirminant: %s, Datacard: %s\n\n"%(channel, discriminant, datacard_file))
            fit_results_file.close()
            print ("      Running for datacard: %s\n"%datacard_file)

            # Convert datacard to workspace
            print ("        Convert datacard to workspace\n\n")
            os.system("combineTool.py -M T2W -m 125.38 -v 3 -i %s"%datacard_file)
            workspace_file = datacard_file.split(".txt")[0] + ".root"
            
            # Expected A-priori Asymptotic Limits for Blinded Fit
            fit_results_file = open(fit_results_filename, "a")
            fit_results_file.write("Calculating A-priori Expected Asymptotic Limits for Blinded Fit\n\n")
            fit_results_file.close()
            print ("        Calculating A-priori Expected Asymptotic Limits for Blinded Fit ")
            os.system("combine -M AsymptoticLimits --mass 125 --minosAlgo stepping --cminDefaultMinimizerStrategy 0 --cminDefaultMinimizerTolerance 1e-2 --X-rtd MINIMIZER_analytic --run blind %s >> %s"%(workspace_file, fit_results_filename)) 
            fit_results_file = open(fit_results_filename, "a")
            fit_results_file.write("\n\n")
            fit_results_file.close()
            os.system("mv higgsCombineTest.AsymptoticLimits.mH125.root %s/higgsCombineTest.AsymptoticLimits.mH125_blinded_fit.root"%output_dir)

            # Expected and Observed Asymptotic Limits for Unblinded Fit
            fit_results_file = open(fit_results_filename, "a")
            fit_results_file.write("Expected and Observed Asymptotic Limits for Unblinded Fit\n\n")
            fit_results_file.close()
            print ("        Expected and Observed Asymptotic Limits for Unblinded Fit ")
            os.system("combine -M AsymptoticLimits --mass 125 --minosAlgo stepping --cminDefaultMinimizerStrategy 0 --cminDefaultMinimizerTolerance 1e-2 --X-rtd MINIMIZER_analytic --run both %s >> %s"%(workspace_file, fit_results_filename)) 
            fit_results_file = open(fit_results_filename, "a")
            fit_results_file.write("\n\n")
            fit_results_file.close()
            os.system("mv higgsCombineTest.AsymptoticLimits.mH125.root %s/higgsCombineTest.AsymptoticLimits.mH125_unblinded_fit.root"%output_dir)

            # Fit Results and Normalization for Blinded Fit
            fit_results_file = open(fit_results_filename, "a")
            fit_results_file.write("Calculating Fit Results and Normalization for Blinded Fit\n\n")
            fit_results_file.close()
            print ("        Calculating Fit Results and Normalization for Blinded Fit ")
            os.system("combine -M FitDiagnostics --mass 125 --cminDefaultMinimizerStrategy 0 --cminDefaultMinimizerTolerance 1e-2 --X-rtd MINIMIZER_analytic --saveNormalization --setParameters r=1 --setParameterRanges r=-100,100 -t -1 %s >> %s"%(workspace_file, fit_results_filename)) 
            fit_results_file = open(fit_results_filename, "a")
            fit_results_file.write("\n\n")
            fit_results_file.close()

            fit_file_blinded = ROOT.TFile("fitDiagnosticsTest.root")
            fit_norm_prefit = fit_file_blinded.Get("norm_prefit")
            fit_norm_s = fit_file_blinded.Get("norm_fit_s")
            fit_norm_b = fit_file_blinded.Get("norm_fit_b")
            iter = fit_norm_s.createIterator()
            normalizations = {}
            while True:
                norm_s = iter.Next()
                if norm_s == None: 
                    break
                norm_b = fit_norm_b.find(norm_s.GetName())
                norm_p = fit_norm_prefit.find(norm_s.GetName())
                process_name   = norm_s.GetName().split("/")[1]
                if process_name not in normalizations:
                    normalizations[process_name] = {}
                normalizations[process_name]["prefit"] = norm_p.getVal()
                normalizations[process_name]["s"] = norm_s.getVal()
                normalizations[process_name]["b"] = norm_b.getVal()
            fit_results_file = open(fit_results_filename, "a")
            fit_results_file.write("Normalizations: \n")
            for process_name in normalizations:
                print ("%s: \n"%process_name)
                print ("  pre_fit: %.4f\n"%normalizations[process_name]["prefit"])
                print ("  S+B fit: %.4f, mu: %.4f\n"%(normalizations[process_name]["s"], normalizations[process_name]["s"]/normalizations[process_name]["prefit"])) 
                print ("  B-only fit: %.4f, mu: %.4f\n"%(normalizations[process_name]["b"], normalizations[process_name]["b"]/normalizations[process_name]["prefit"])) 
            fit_results_file.write("\n\n")
            fit_results_file.close()
            fit_file_unblinded.Close()
            os.system("mv fitDiagnosticsTest.root %s/fitDiagnosticsTest_blinded_fit.root"%output_dir)

            # Fit Results and Normalization for Unblinded Fit
            fit_results_file = open(fit_results_filename, "a")
            fit_results_file.write("Calculating Fit Results and Normalization for Unblinded Fit\n\n")
            fit_results_file.close()
            print ("        Calculating Fit Results and Normalization for Unblinded Fit ")
            os.system("combine -M FitDiagnostics --mass 125 --cminDefaultMinimizerStrategy 0 --cminDefaultMinimizerTolerance 1e-2 --X-rtd MINIMIZER_analytic --saveNormalization --setParameters r=1 --setParameterRanges r=-100,100 %s >> %s"%(workspace_file, fit_results_filename)) 
            fit_results_file = open(fit_results_filename, "a")
            fit_results_file.write("\n\n")
            fit_results_file.close()

            fit_file_unblinded = ROOT.TFile("fitDiagnosticsTest.root")
            fit_norm_prefit = fit_file_unblinded.Get("norm_prefit")
            fit_norm_s = fit_file_unblinded.Get("norm_fit_s")
            fit_norm_b = fit_file_unblinded.Get("norm_fit_b")
            iter = fit_norm_s.createIterator()
            normalizations = {}
            while True:
                norm_s = iter.Next()
                if norm_s == None: 
                    break
                norm_b = fit_norm_b.find(norm_s.GetName())
                norm_p = fit_norm_prefit.find(norm_s.GetName())
                process_name   = norm_s.GetName().split("/")[1]
                if process_name not in normalizations:
                    normalizations[process_name] = {}
                normalizations[process_name]["prefit"] = norm_p.getVal()
                normalizations[process_name]["s"] = norm_s.getVal()
                normalizations[process_name]["b"] = norm_b.getVal()
            fit_results_file = open(fit_results_filename, "a")
            fit_results_file.write("Normalizations: \n")
            for process_name in normalizations:
                print ("%s: \n"%process_name)
                print ("  pre_fit: %.4f\n"%normalizations[process_name]["prefit"])
                print ("  S+B fit: %.4f, mu: %.4f\n"%(normalizations[process_name]["s"], normalizations[process_name]["s"]/normalizations[process_name]["prefit"])) 
                print ("  B-only fit: %.4f, mu: %.4f\n"%(normalizations[process_name]["b"], normalizations[process_name]["b"]/normalizations[process_name]["prefit"])) 
            fit_results_file.write("\n\n")
            fit_results_file.close()
            fit_file_unblinded.Close()
            os.system("mv fitDiagnosticsTest.root %s/fitDiagnosticsTest_unblinded_fit.root"%output_dir)
















    



