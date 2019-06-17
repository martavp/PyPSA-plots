#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr  4 15:59:13 2019

@author: marta
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib as mpl
import os
import pypsa
import seaborn as sns; sns.set()


##### 1. LOADING NETWORKS AND FILLING DATAFRAME

#version-45  (transmission=2todays, weakly homogeneous, no CO2 price, decreasing CO2 limit)
path = '/home/marta/Desktop/heavy_data_guest/PyPSA_out/version-77/postnetworks/' 
line_limit='0.125' 
co2_limits=['0.6', '0.5','0.4',  '0.3',  '0.2', '0.1','0.05'] 
#co2_limits=['0.6', '0.55', '0.5', '0.45', '0.4', '0.35', '0.3', '0.25', '0.2', '0.15', '0.1', '0.075', '0.05', '0.025']

flexs = ['elec_only', 'v2g50', 'elec_central', 'elec_heat_v2g50'] 
techs=['PHS', 'hydro']

datos = pd.DataFrame(index=pd.MultiIndex.from_product([pd.Series(data=techs, name='tech',),
                                                       pd.Series(data=co2_limits, name='co2_limit',)]), 
                     columns=pd.Series(data=flexs, name='flexs',))
idx = pd.IndexSlice
#%%
for flex in flexs:
    for co2_limit in co2_limits:      
        network_name= path+'postnetwork-' +flex+'_'+ line_limit + '_' + co2_limit+ '.h5'        
        print(network_name)
        if os.path.exists(network_name): 
            network = pypsa.Network(network_name)
            
            #Hydro stores
            Hydro_storages = list(network.storage_units.index[network.storage_units.carrier == "hydro"])
            Hydro_rev=[]

            for i,storage in enumerate(Hydro_storages):
                Hydro_pn= network.storage_units_t.p[storage.split(' ')[0]+ ' hydro']             
                price = network.buses_t.marginal_price[storage.split(' ')[0]]
                Hydro_rev_=np.sum([x*y for x,y in zip(price,Hydro_pn)])
                Hydro_rev.append(Hydro_rev_)
            datos.loc[idx['hydro', co2_limit], flex] = np.sum(Hydro_rev)/1000000000.0 #G€
        
        PHS_storages = list(network.storage_units.index[network.storage_units.carrier == "PHS"])
        PHS_rev=[]
        for i,storage in enumerate(PHS_storages):
            PHS_pn= network.storage_units_t.p[storage.split(' ')[0]+ ' PHS']        
            price = network.buses_t.marginal_price[storage.split(' ')[0]]
            PHS_rev_=np.sum([x*y for x,y in zip(price,PHS_pn)])
            PHS_rev.append(PHS_rev_)
        datos.loc[idx['PHS', co2_limit], flex] = np.sum(PHS_rev)/1000000000.0 #G€
                                

# Save dataframe to pickled pandas object and csv file
datos.to_pickle('data_for_figures/hydro_revenues.pickle') 
datos.to_csv('data_for_figures/hydro_revenues.csv', sep=',')            

#%%
##### 2. PLOTTING
# Load dataframe from pickled pandas object or csv
#datos = pd.read_pickle('data_for_figures/hydro_revenues.pickle')
datos=pd.read_csv('data_for_figures/hydro_revenues.csv', sep=',', header=0, index_col=(0,1))


sns.set_style('ticks')
plt.style.use('seaborn-ticks')
plt.rcParams['xtick.direction'] = 'in'
plt.rcParams['ytick.direction'] = 'in'
fig = plt.figure(figsize=(14, 22))
gs1 = gridspec.GridSpec(5, 2)
gs1.update(wspace=0.1, hspace=0.1)
#fig.subplots_adjust(hspace=0.3)

dic_position={'PHS':(0,0), 
              'hydro':(1,0)}
dic_ylim={'PHS': 6,
          'hydro': 40}

dic_ylim0={'PHS': 0,
          'hydro': 10}

dic_title={'PHS':'PHS revenues (B€)',
          'hydro': 'Hydro revenues (B€)'}

dic_label={'elec_only':'Electricity', 
           'v2g50':'Electricity+Transport', 
           'elec_heat_v2g50': 'Electricity+Heating+Transport', 
           'elec_central':'Electricity+Heating'} 

dic_height={'elec_only':1.22, 
           'v2g50':1.11, 
           'elec_central': 1.0} 

dic_pos2={'elec_only':1.5, 
           'v2g50':1.37, 
           'elec_central': 1.3} 
xlim=0.65
dic_width={'elec_only':(xlim-784/3016-723/3016)/xlim, 
           'v2g50':(xlim-784/3016)/xlim, 
           'elec_central': (xlim-723/3016)/xlim}

co2_limits_num=[float(x) for x in co2_limits]

dic_col={'elec_only':'C0', 'v2g50':'C2', 'elec_heat_v2g50': 'black', 'elec_central':'C1'} 

techs=['PHS', 'hydro']

dic_cost={'PHS': 1.2,
          'hydro': 3.1} 
for tech in techs:
    flex='elec_heat_v2g50'
    ax0 = plt.subplot(gs1[dic_position[tech][0],dic_position[tech][1]])
    if tech == 'PHS':
        #ax0.spines['bottom'].set_color('none') 
        #ax0.set_xticks([])
        ax0.set_xlabel('')
        plt.annotate('Electricity \n + Heating \n + Transport', xy=(0.15,2.8),
        xytext=(0.2,1), fontsize=10, arrowprops=dict(arrowstyle="->", 
               color='black'))
    else:
        ax0.set_xlabel('CO$_2$ emissions (relative to 1990)')
    ax0.set_ylabel(dic_title[tech])    
    ylim=dic_ylim[tech]
    ylim0=dic_ylim0[tech]
    ax0.set_xlim(xlim, 0.)
    ax0.set_xticks([0.05, 0.2, 0.4, 0.6])
    ax0.set_xticklabels(['5%','20%','40%', '60%'])
    ax0.set_ylim(ylim0, ylim)
    ax0.spines['top'].set_color('none')  
    ax0.spines['right'].set_color('none') 
    ax0.plot(co2_limits_num, datos.loc[idx[tech, :], flex], color=dic_col[flex], linewidth=2, marker='o', label=dic_label[flex])
    #ax0.plot(co2_limits_num, dic_cost[tech]*np.ones(co2_limits_num), linewidth=2, linestyle='--', color='black', label='costs') 
    
    for flex in ['elec_only', 'v2g50', 'elec_central']:
        height = dic_height[flex]
        width = dic_width[flex] 
       
        axins=ax0.inset_axes((0.01, 0.01, width, height)) # x, y, width, height
        axins.spines['right'].set_color('none')
        axins.spines['left'].set_color('none')
        axins.spines['bottom'].set_color('none')
        if tech=='PHS':
            axins.spines['top'].set_color(dic_col[flex])
            axins.xaxis.tick_top()
            axins.xaxis.set_label_position('top')
            axins.set_xlabel(dic_label[flex], fontsize=10, color=dic_col[flex])
            axins.xaxis.set_label_coords(dic_pos2[flex], 1)
            axins.tick_params(direction='inout')
            axins.tick_params(axis='x', colors=dic_col[flex])    
            axins.set_xticks([0, 0.2, 0.4, 0.6])
            axins.set_xticklabels(['5%','20%','40%', '60%'], fontsize=9)
        else:
            axins.spines['top'].set_color('none')
            axins.set_xticks([])
        axins.set_yticks([])
        axins.patch.set_alpha(0) 
        axins.set_xlim(xlim, 0.)
        axins.set_ylim(0, ylim*height)        
        axins.plot(co2_limits_num, datos.loc[idx[tech, :], flex], color=dic_col[flex], linewidth=2, marker='o', label=dic_label[flex])
#ax0.legend(loc=(-0.1,1.01), ncol=2, shadow=True,fancybox=True,prop={'size':12})
plt.savefig('figures/PHS_hydro_revenues.png', dpi=300, bbox_inches='tight')



        




           