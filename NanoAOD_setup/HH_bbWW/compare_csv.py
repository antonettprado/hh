import pandas as pd
import csv

# Reading Abhisek's csv file ======================================================
datta = pd.read_csv('output_data.csv')

NEvent = datta['NEvent'].to_numpy()
is_e = datta[' is_e'].to_numpy()
is_mu = datta[' is_mu'].to_numpy()
is_ee = datta[' is_ee'].to_numpy()
is_mumu = datta[' is_mumu'].to_numpy()
is_emu = datta[' is_emu'].to_numpy()

sl_e_events_datta = []
sl_mu_events_datta = []
sl_events_datta = []
dl_ee_events_datta = []
dl_mumu_events_datta = []
dl_emu_events_datta = []
dl_events_datta = []
for idx in range(len(NEvent)):
    if is_e[idx] == 1:
        sl_e_events_datta.append(NEvent[idx])
    if is_mu[idx] == 1:
        sl_mu_events_datta.append(NEvent[idx])
    if is_e[idx] == 1 or is_mu[idx] == 1:
        sl_events_datta.append(NEvent[idx])
    if is_ee[idx] == 1:
        dl_ee_events_datta.append(NEvent[idx])
    if is_mumu[idx] == 1:
        dl_mumu_events_datta.append(NEvent[idx])
    if is_emu[idx] == 1:
        dl_emu_events_datta.append(NEvent[idx])
    if is_ee[idx] == 1 or is_mumu[idx] == 1 or is_emu[idx] == 1:
        dl_events_datta.append(NEvent[idx])

print('Datta_csv: ')
print('\tsl_e events: ' + str(len(sl_e_events_datta)))
print('\tsl_mu events: ' + str(len(sl_mu_events_datta)))
print('------> Total SL events: ' + str(len(sl_events_datta)))
print()
print('\tdl_ee events: ' + str(len(dl_ee_events_datta)))
print('\tdl_mumu events: ' + str(len(dl_mumu_events_datta)))
print('\tdl_emu events: ' + str(len(dl_emu_events_datta)))
print('------> Total DL events: ' + str(len(dl_events_datta)))
# print('======> Total events: ' + str(len(sl_events_datta) + len(dl_events_datta)))
print('=============================================')


# Reading Antonett's csv files =====================================================
prado_sl_e = pd.read_csv('data_sl_e.csv')
prado_sl_mu = pd.read_csv('data_sl_mu.csv')
sl_e_events_prado = prado_sl_e['event'].to_numpy()
sl_mu_events_prado = prado_sl_mu['event'].to_numpy()

sl_events_prado = []
for event in sl_e_events_prado:
    sl_events_prado.append(event)
for event in sl_mu_events_prado:
    sl_events_prado.append(event)

prado_dl_ee = pd.read_csv('data_dl_ee.csv')
prado_dl_mumu = pd.read_csv('data_dl_mumu.csv')
prado_dl_emu = pd.read_csv('data_dl_emu.csv')
dl_ee_events_prado = prado_dl_ee['event'].to_numpy()
dl_mumu_events_prado = prado_dl_mumu['event'].to_numpy()
dl_emu_events_prado = prado_dl_emu['event'].to_numpy()

dl_events_prado = []
for event in dl_ee_events_prado:
    dl_events_prado.append(event)
for event in dl_mumu_events_prado:
    dl_events_prado.append(event)
for event in dl_emu_events_prado:
    dl_events_prado.append(event)


print('Prado_csv: ')
print('\tsl_e events: ' + str(len(sl_e_events_prado)))
print('\tsl_mu events: ' + str(len(sl_mu_events_prado)))
print('------> Total SL events: ' + str(len(sl_events_prado)))
print()
print('\tdl_ee events: ' + str(len(dl_ee_events_prado)))
print('\tdl_mumu events: ' + str(len(dl_mumu_events_prado)))
print('\tdl_emu events: ' + str(len(dl_emu_events_prado)))
print('------> Total DL events: ' + str(len(dl_events_prado)))
print()

# -----------------------------------------------------------------

sl_e_prado_extra_events = []
for e_event_prado in sl_e_events_prado:
    if e_event_prado not in sl_e_events_datta:
        sl_e_prado_extra_events.append(e_event_prado)

print('sl_e events in prado_csv and NOT in datta_csv: ' + str(len(sl_e_prado_extra_events)) )
print(sl_e_prado_extra_events[0:10])
print()

sl_e_datta_extra_events = []
for e_event_datta in sl_e_events_datta:
    if e_event_datta not in sl_e_events_prado:
        sl_e_datta_extra_events.append(e_event_datta)

print('sl_e events in datta_csv and NOT in prado_csv: ' + str(len(sl_e_datta_extra_events)) )
print(sl_e_datta_extra_events[0:10])
print()

# -----------------------------------------------------------------
sl_mu_prado_extra_events = []
for mu_event_prado in sl_mu_events_prado:
    if mu_event_prado not in sl_mu_events_datta:
        sl_mu_prado_extra_events.append(mu_event_prado)

print('sl_mu events in prado_csv and NOT in datta_csv: ' + str(len(sl_mu_prado_extra_events)) )
print(sl_mu_prado_extra_events[0:10])
print()

sl_mu_datta_extra_events = []
for mu_event_datta in sl_mu_events_datta:
    if mu_event_datta not in sl_mu_events_prado:
        sl_mu_datta_extra_events.append(mu_event_datta)

print('sl_mu events in datta_csv and NOT in prado_csv: ' + str(len(sl_mu_datta_extra_events)) )
print(sl_mu_datta_extra_events[0:10])
print()

# -----------------------------------------------------------------
dl_ee_prado_extra_events = []
for ee_event_prado in dl_ee_events_prado:
    if ee_event_prado not in dl_ee_events_datta:
        dl_ee_prado_extra_events.append(ee_event_prado)

print('dl_ee events in prado_csv and NOT in datta_csv: ' + str(len(dl_ee_prado_extra_events)) )
print(dl_ee_prado_extra_events[0:10])
print()

dl_ee_datta_extra_events = []
for ee_event_datta in dl_ee_events_datta:
    if ee_event_datta not in dl_ee_events_prado:
        dl_ee_datta_extra_events.append(ee_event_datta)

print('dl_ee events in datta_csv and NOT in prado_csv: ' + str(len(dl_ee_datta_extra_events)) )
print(dl_ee_datta_extra_events[0:10])
print()

# -----------------------------------------------------------------
dl_mumu_prado_extra_events = []
for mumu_event_prado in dl_mumu_events_prado:
    if mumu_event_prado not in dl_mumu_events_datta:
        dl_mumu_prado_extra_events.append(mumu_event_prado)

print('dl_mumu events in prado_csv and NOT in datta_csv: ' + str(len(dl_mumu_prado_extra_events)) )
print(dl_mumu_prado_extra_events[0:10])
print()


dl_mumu_datta_extra_events = []
for mumu_event_datta in dl_mumu_events_datta:
    if mumu_event_datta not in dl_mumu_events_prado:
        dl_mumu_datta_extra_events.append(mumu_event_datta)

print('dl_mumu events in datta_csv and NOT in prado_csv: ' + str(len(dl_mumu_datta_extra_events)) )
print(dl_mumu_datta_extra_events[0:10])
print()

# -----------------------------------------------------------------
dl_emu_prado_extra_events = []
for emu_event_prado in dl_emu_events_prado:
    if emu_event_prado not in dl_emu_events_datta:
        dl_emu_prado_extra_events.append(emu_event_prado)

print('dl_emu events in prado_csv and NOT in datta_csv: ' + str(len(dl_emu_prado_extra_events)) )
print(dl_emu_prado_extra_events[0:10])
print()


dl_emu_datta_extra_events = []
for emu_event_datta in dl_emu_events_datta:
    if emu_event_datta not in dl_emu_events_prado:
        dl_emu_datta_extra_events.append(emu_event_datta)

print('dl_emu events in datta_csv and NOT in prado_csv: ' + str(len(dl_emu_datta_extra_events)) )
print(dl_emu_datta_extra_events[0:10])
print()









