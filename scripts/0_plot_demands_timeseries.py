
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 2018-03-07

@author: marta

Script to plot aggregated demands
"""

import pypsa
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec


path = '/home/marta/Desktop/heavy_data_guest/PyPSA_out/version-77/postnetworks/'

flex= 'elec_heat_v2g50'  
line_limit='0.125'
co2_limit = '0.05'
    
network_name = (path+'postnetwork-' +flex+'_'+ line_limit + '_' + co2_limit+ '.h5')
network = pypsa.Network(network_name)         
dem_electricity=network.loads_t.p[network.loads.index[network.loads.index.str.len() == 2]].sum(axis=1)/1000 #MWh -> GWh
dem_heat = (network.loads_t.p[network.loads.index[network.loads.index.str[3:] == 'heat']].sum(axis=1)
+network.loads_t.p[network.loads.index[network.loads.index.str[3:] == 'central heat']].sum(axis=1)
+network.loads_t.p[network.loads.index[network.loads.index.str[3:] == 'urban heat']].sum(axis=1))/1000 #MWh -> GWh   
dem_trans = network.loads_t.p[network.loads.index[network.loads.index.str[3:] == 'transport']].sum(axis=1)/1000 #MWh -> GWh            

#%%

plt.style.use('seaborn-ticks')
plt.rcParams['axes.labelsize'] = 20
plt.rcParams['xtick.labelsize'] = 18
plt.rcParams['ytick.labelsize'] = 18
plt.rcParams['xtick.direction'] = 'in'
plt.rcParams['ytick.direction'] = 'in'

plt.figure(figsize=(12, 5))
gs1 = gridspec.GridSpec(1, 3)
gs1.update(wspace=0.05)

ax1 = plt.subplot(gs1[0,0:2])
ax1.set_xlim(0,8760)
ax1.set_xlabel('1 year (hours)')
ax1.set_ylabel('GWh')

ax1.plot(np.arange(0,8760), dem_heat, color='orange',  label='heating', linewidth=2)
ax1.plot(np.arange(0,8760), dem_electricity, color='black', label='electricity', linewidth=2, alpha=0.7)
ax1.plot(np.arange(0,8760), dem_trans, color='lightskyblue',  label='transport', linewidth=2, alpha=0.8)

ax1.legend(loc=(0.1,1.0), shadow=True, fancybox=True, ncol=3, prop={'size':22}) 
ax1.set_ylim(0,1100)

ax2 = plt.subplot(gs1[0,2])
ax2.set_xlim(0,7*24)

ax2.set_xlabel('1 week (hours)')
#ax2.set_ylabel('GWh', fontsize=fs)
ax2.set_yticklabels([])
ax2.plot(np.arange(0,8760), dem_heat, color='orange', linewidth=2, label=None)
ax2.plot(np.arange(0,8760), dem_electricity, color='black',  linewidth=2, label=None)
ax2.plot(np.arange(0,8760), dem_trans, color='lightskyblue',  linewidth=2,  label=None)
#ax1.legend(loc=(0.5,0.7), shadow=True,fancybox=True,prop={'size':12})
ax2.set_ylim(0,1100)
filename='figures/demands.png'
plt.savefig(filename, dpi=300, bbox_inches='tight')



