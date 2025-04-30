import uproot
import numpy as np
import mplhep as hep
import matplotlib.pyplot as plt


def get_hists(dc: str):
    with uproot.open(dc) as f:
        hists = { n.strip(';1') : (f[n].values(), np.arange(0,len(f[n].axis().edges()))) for n in f.classnames() }
    sig = hists.pop('ggHH_kl_1_kt_1_hbbhww')
    asimov = hists.pop('asimov')
    bkg_hists = { k:v for k,v in hists.items() if not k.startswith('ggHH')}
    return sig, bkg_hists

def get_color_dict(test_dc) -> dict[str, str]:
    mplcolors = plt.rcParams['axes.prop_cycle'].by_key()['color']
    names = list(get_hists(test_dc)[1].keys())
    colors = { names[i]: mplcolors[i%len(mplcolors)] for i in range(len(names)) }
    return colors

def main() -> None:
    signal_dc: str = "/afs/cern.ch/user/s/scrossle/bamboodev/hh/fits/fits/multi_HH_ttbar_tW/era_2022EE/SL_res_3j_2b_DNN_HH/scoreHH.root"
    ttbar_dc: str = "/afs/cern.ch/user/s/scrossle/bamboodev/hh/fits/fits/multi_HH_ttbar_tW/era_2022EE/SL_res_3j_2b_DNN_ttbar/scorettbar.root"
    tW_dc: str = "/afs/cern.ch/user/s/scrossle/bamboodev/hh/fits/fits/multi_HH_ttbar_tW/era_2022EE/SL_res_3j_2b_DNN_tW/scoretW.root"

    colors = get_color_dict(signal_dc)
    signal_multiplier = 100 
    fig, axs = plt.subplots(3,1, figsize=(14,40))
    hep.style.use('CMS')

    for ax, dc in zip(axs, [signal_dc, ttbar_dc, tW_dc]):
        sig, bkg_hists = get_hists(dc)
        bkg_names = sorted(bkg_hists.keys(), key=lambda k: np.sum(bkg_hists[k][0]))
        bkg_values = [ bkg_hists[k] for k in bkg_names ]
        hist_objects = hep.histplot(bkg_values, ax=ax, histtype='fill', label=bkg_names, stack=True, alpha=0.8,)
        for artist, bkg in zip(hist_objects, bkg_names):
            artist.stairs.set(color=colors.get(bkg, 'tab:blue'))

        hep.histplot((sig[0]*signal_multiplier, sig[1]), ax=ax, label=f'HH*{signal_multiplier}', lw=3, color='k')
        hep.cms.label(loc=0, ax=ax, label='Work in Progress', year='2022', com='13.6')
        ax.set_ylabel('Events')
        ax.set_yscale('log')
        ax.set_xlim(0,sig[1][-1])
        ax.set_ylim(None, ax.get_ylim()[1]*10)
        ax.legend(ncol=(len(bkg_names)+1)//2)
    axs[0].set_xlabel(r'DNN HH score bin / a.u.')
    axs[1].set_xlabel(r'DNN t$\bar t$ score bin / a.u.')
    axs[2].set_xlabel(r'DNN tW score bin / a.u.')

    plt.savefig('test.pdf')


if __name__=="__main__":
    main()
