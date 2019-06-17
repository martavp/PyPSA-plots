# -*- coding: utf-8 -*-
"""
Created on 2018-11-12

@author: Marta
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import pypsa

##### 1. LOADING NETWORKS AND FILLING DATAFRAME WITH TIME SERIES
#version-45  (transmission=2todays, weakly homogeneous, no CO2 price, decreasing CO2 limit)
path = '/home/marta/Desktop/heavy_data_guest/PyPSA_out/version-77/postnetworks/' 
line_limit='0.125' 
co2_limits=['0.6','0.2','0.05'] 

flexs = ['elec_only', 'v2g50', 'elec_central', 'elec_heat_v2g50'] 
techs=['battery', 'H2', 'PHS', 'EV_battery', 'ITES', 'LTES']
#co2_lim='0.05'
datos = pd.DataFrame(index=pd.MultiIndex.from_product([pd.Series(data=techs, name='tech',),
                                                       pd.Series(data=flexs, name='flex',),
                                                       pd.Series(data=co2_limits, name='co2_limits',)]), 
                      columns=pd.Series(data=np.arange(0,8760), name='hour',))
idx = pd.IndexSlice
#%%
for flex in flexs:
    for co2_limit in co2_limits:
        network_name= path+'postnetwork-' +flex+'_'+ line_limit + '_' + co2_limit+ '.h5'   
        network = pypsa.Network(network_name)
        datos.loc[idx['battery', flex, co2_limit], :] = np.array(network.stores_t.e[network.stores.index[network.stores.index.str[3:] == 'battery']].sum(axis=1)/network.stores.e_nom_opt[network.stores.index[network.stores.index.str[3:] == 'battery']].sum())
        datos.loc[idx['H2', flex, co2_limit], :] = np.array(network.stores_t.e[network.stores.index[network.stores.index.str[3:] == 'H2 Store']].sum(axis=1)/network.stores.e_nom_opt[network.stores.index[network.stores.index.str[3:] == 'H2 Store']].sum())
        datos.loc[idx['PHS', flex, co2_limit], :] = np.array(network.storage_units_t.state_of_charge[network.storage_units.index[network.storage_units.carrier == 'PHS']].sum(axis=1)/(6*network.storage_units.p_nom[network.storage_units.index[network.storage_units.carrier == 'PHS']].sum()))
        if 'v2g' in flex:
            datos.loc[idx['EV_battery', flex, co2_limit], :] = np.array(network.stores_t.e[network.stores.index[network.stores.index.str[3:] == 'battery storage']].sum(axis=1)/network.stores.e_nom_opt[network.stores.index[network.stores.index.str[3:] == 'battery storage']].sum())
    
        if 'heat' in flex or 'central' in flex:  
            datos.loc[idx['ITES', flex, co2_limit], :] = np.array(network.stores_t.e[network.stores.index[network.stores.index.str[3:] == 'urban water tank']].sum(axis=1)/network.stores.e_nom_opt[network.stores.index[network.stores.index.str[3:] == 'urban water tank']].sum())
            datos.loc[idx['LTES', flex, co2_limit], :] = np.array(network.stores_t.e[network.stores.index[network.stores.index.str[3:] == 'central water tank']].sum(axis=1)/network.stores.e_nom_opt[network.stores.index[network.stores.index.str[3:] == 'central water tank']].sum())

# Save dataframe to pickled pandas object and csv file
datos.to_pickle('data_for_figures/storage_timeseries.pickle') 
datos.to_csv('data_for_figures/storage_timeseries.csv', sep=',')            

#%%
##### 2. PLOTTING
# Load dataframe from pickled pandas object or csv
#datos = pd.read_pickle('data_for_figures/storage_timeseries.pickle')
#plt.style.use('classic')
datos=pd.read_csv('data_for_figures/storage_timeseries.csv', sep=',', header=0, index_col=(0,1,2))


##### 2. PLOTTING
##### Figure of the Fourier transform for the PHS charging patterns

plt.style.use('seaborn-ticks')
plt.rcParams['axes.labelsize'] = 20
plt.rcParams['xtick.labelsize'] = 18
plt.rcParams['ytick.labelsize'] = 18
plt.rcParams['xtick.direction'] = 'in'
plt.rcParams['ytick.direction'] = 'in'

plt.figure(figsize=(10, 10))
gs1 = gridspec.GridSpec(10, 1)
gs1.update(wspace=0.05)

ax1 = plt.subplot(gs1[0:3,0])
ax1.set_ylabel('PHS filling level')
ax1.set_xlabel('hour')
ax1.set_xlim(0,8760)
ax1.set_ylim(0,1)

flex='elec_central' #'elec_only'

co2_limits=['0.6', '0.05',] #'0.6', 
storage_names=['PHS'] #,'battery','H2']
dic_color={'PHS':'darkgreen','battery':'lightskyblue','H2':'purple'}
storage_names=['PHS'] #,'battery','H2']
dic_color={'0.6':'olive','0.2':'darkgreen','0.05':'yellowgreen'}
dic_label={'0.6':'60%','0.2':'20%','0.05':'5%'}
dic_alpha={'0.6':1,'0.2':0.6,'0.05':1.0}
dic_linewidth={'0.6':2,'0.2':2,'0.05':2}

for i,co2_lim in enumerate(co2_limits):
    ax2 = plt.subplot(gs1[4+2*i:6+2*i,0])    
    ax2.set_xlim(1,10000)
    ax2.set_ylim(0,1.2)
    plt.axvline(x=24, color='lightgrey', linestyle='--')
    plt.axvline(x=24*7, color='lightgrey', linestyle='--')
    plt.axvline(x=24*30, color='lightgrey', linestyle='--')
    plt.axvline(x=8760, color='lightgrey', linestyle='--')   
    ax1.plot(np.arange(0,8760), datos.loc[idx['PHS', flex, float(co2_lim)], :]/np.max(datos.loc[idx['PHS', flex, float(co2_lim)], :]), 
             color=dic_color[co2_lim], alpha=dic_alpha[co2_lim], linewidth=dic_linewidth[co2_lim],
             label='CO$_2$='+dic_label[co2_lim])
    ax1.legend(loc=(0.2, 1.05), ncol=3, shadow=True,fancybox=True,prop={'size':18})
    n_years=1
    t_sampling=1 # sampling rate, 1 data per hour
    x = np.arange(1,8761*n_years, t_sampling) 
    y = np.hstack([np.array(datos.loc[idx['PHS', flex, float(co2_lim)], :])]*n_years)
    n = len(x)
    y_fft=np.fft.fft(y)/n #n for normalization    
    frq=np.arange(0,1/t_sampling,1/(t_sampling*n))        
    period=np.array([1/f for f in frq])        
    ax2.semilogx(period[1:n//2],abs(y_fft[1:n//2])**2/np.max(abs(y_fft[1:n//2])**2), color=dic_color[co2_lim],
                 linewidth=2, label='CO$_2$ = '+dic_label[co2_lim])  
    ax2.legend(loc='center right', shadow=True,fancybox=True,prop={'size':18})
    #ax2.set_yticks([0, 0.1, 0.2])
    #ax2.set_yticklabels(['0', '0.1', '0.2'])
    plt.text(26, 0.95, 'day', horizontalalignment='left', color='dimgrey', fontsize=14)
    plt.text(24*7+20, 0.95, 'week', horizontalalignment='left', color='dimgrey', fontsize=14)
    plt.text(24*30+20, 0.95, 'month', horizontalalignment='left', color='dimgrey', fontsize=14)
    if i==1:
        ax2.set_xticks([1, 10, 100, 1000, 10000])
        ax2.set_xticklabels(['1', '10', '100', '1000', '10000'])
        ax2.set_xlabel('cycling period (hours)')
    else: 
        ax2.set_xticks([])

plt.savefig('figures/Fourier_transform_PHS.png', dpi=300, bbox_inches='tight')   

plt.figure(figsize=(18, 10))
gs1 = gridspec.GridSpec(3, 2)
gs1.update(wspace=0.15)

for i,co2_lim in enumerate(co2_limits):    
    
    ax1 = plt.subplot(gs1[i,0])
    ax1.set_ylabel('PHS filling level')
    if i==0:
        ax1.set_xticklabels([])
    if i==1:
        ax1.set_xlabel('hour')
    ax1.set_xlim(0,8760)
    ax1.set_ylim(0,1.1)
    ax1.set_yticks([0, 0.5, 1])
    ax1.set_yticklabels(['0', '0.5', '1'])
    ax1.plot(np.arange(0,8760), datos.loc[idx['PHS', flex, float(co2_lim)], :]/np.max(datos.loc[idx['PHS', flex, float(co2_lim)], :]), 
             color=dic_color[co2_lim], alpha=dic_alpha[co2_lim], linewidth=dic_linewidth[co2_lim],
             label='CO$_2$='+dic_label[co2_lim])
    #ax1.legend(loc=(0.2, 1.05), ncol=3, shadow=True,fancybox=True,prop={'size':18})

    ax2 = plt.subplot(gs1[i,1])
    ax2.set_xlim(1,10000)
    ax2.set_ylim(0,1.1)
    ax2.set_yticks([0, 0.5, 1])
    ax2.set_yticklabels(['0', '0.5', '1'])
    plt.axvline(x=24, color='lightgrey', linestyle='--')
    plt.axvline(x=24*7, color='lightgrey', linestyle='--')
    plt.axvline(x=24*30, color='lightgrey', linestyle='--')
    plt.axvline(x=8760, color='lightgrey', linestyle='--')
    
    
    n_years=1
    t_sampling=1
    x = np.arange(1,8761*n_years, t_sampling)
    y = np.hstack([np.array(datos.loc[idx['PHS', flex, float(co2_lim)], :])]*n_years)
    n = len(x)
    y_fft=np.fft.fft(y)/n #n for normalization    
    frq=np.arange(0,1/t_sampling,1/(t_sampling*n))        
    period=np.array([1/f for f in frq])        
    ax2.semilogx(period[1:n//2],abs(y_fft[1:n//2])**2/np.max(abs(y_fft[1:n//2])**2), color=dic_color[co2_lim],
                 linewidth=2, label='CO$_2$ = '+dic_label[co2_lim])  #, alpha=0.5)   
    #ax2.set_ylim(0,10)
    ax2.legend(loc='center right', shadow=True,fancybox=True,prop={'size':18})
    plt.text(26, 0.95, 'day', horizontalalignment='left', color='dimgrey', fontsize=14)
    plt.text(24*7+20, 0.95, 'week', horizontalalignment='left', color='dimgrey', fontsize=14)
    plt.text(24*30+20, 0.95, 'month', horizontalalignment='left', color='dimgrey', fontsize=14)
    
    if i==1:
        ax2.set_xticks([1, 10, 100, 1000, 10000])
        ax2.set_xticklabels(['1', '10', '100', '1000', '10000'])
        ax2.set_xlabel('cycling period (hours)')
    else: 
        ax2.set_xticks([])

plt.savefig('figures/Fourier_transform_PHS_v2_elec_heat.png', dpi=300, bbox_inches='tight')   

#%% Plot  the Fourier transform for all the tecnologies

plt.figure(figsize=(20, 10))
gs1 = gridspec.GridSpec(10, 4)
gs1.update(wspace=0.2, hspace=0.1)
 

flexs=['elec_only', 'v2g50', 'elec_central', 'elec_heat_v2g50']
#flexs=['elec_only']
dic_storage_names={ 'elec_only':['PHS','battery','H2'],                  
                   'v2g50':['PHS','EV_battery','H2'],
                   'elec_central':['PHS','battery','H2', 'ITES','LTES'],
                   'elec_heat_v2g50':['PHS','EV_battery','H2', 'ITES','LTES']}
dic_color={'PHS':'yellowgreen',
           'battery':'gold',
           'H2':'purple',
           'EV_battery':'lightskyblue', 
           'LTES':'black', 
           'ITES':'brown'}
dic_label={'PHS':'PHS',
           'battery':'battery',
           'H2':'hydrogen', 
           'EV_battery':'EV battery', 
           'LTES':'CTES', 
           'ITES':'ITES'}
dic_titles={'elec_only':'Electricity', 
            'v2g50':'Electricity+Transport',
            'elec_central':'Electricity+Heating', 
            'elec_heat_v2g50':'Electricity+Transport+Heating'}
co2_lim='0.05'
for j,flex in enumerate(flexs):
    storage_names=dic_storage_names[flex]    
    for i,storage in enumerate(storage_names):    
        ax2 = plt.subplot(gs1[2*i:2+2*i,j])
        ax2.set_xlim(1,10000)
        ax2.set_ylim(0,1.2)
        plt.axvline(x=24, color='lightgrey', linestyle='--')
        plt.axvline(x=24*7, color='lightgrey', linestyle='--')
        plt.axvline(x=24*30, color='lightgrey', linestyle='--')
        plt.axvline(x=8760, color='lightgrey', linestyle='--')
    
        #timeseries_df=pd.read_csv('data_for_figures/'+storage+'_timeseries_gamma_'+str(gamma)+'.csv', sep=';', index_col=0)    
        n_years=1
        t_sampling=1
        x = np.arange(0,8760*n_years, t_sampling)
        
        y = np.hstack([np.array(datos.loc[idx[storage, flex, float(co2_lim)], :])]*n_years)
        n = len(x)
        y_fft=np.fft.fft(y)/n #n for normalization    
        frq=np.arange(0,1/t_sampling,1/(t_sampling*n))        
        period=np.array([1/f for f in frq])    

        ax2.semilogx(period[1:n//2],abs(y_fft[1:n//2])/np.max(abs(y_fft[1:n//2])), color=dic_color[storage],
                 linewidth=2, label=dic_label[storage])  #, alpha=0.5)  
        #ax2.set_ylim(0,10)        
        #ax2.set_yticks([0.0001,10])
        #ax2.set_yticklabels(['10-4', '10'])
        ax2.legend(loc='best', shadow=True,fancybox=True,prop={'size':14})
        if i==0:
            ax2.set_title(dic_titles[flex], fontsize=18)
        
        if (j in [0, 1] and i==2) or (j in [2,3] and i==4):
            ax2.set_xticks([1, 10, 100, 1000, 10000])
            ax2.set_xticklabels(['1', '10', '100', '1000', '10000'])
            ax2.set_xlabel('cycling period (hours)')
        else: 
            ax2.set_xticks([])

plt.savefig('figures/Fourier_transform_2.png', dpi=300, bbox_inches='tight') 