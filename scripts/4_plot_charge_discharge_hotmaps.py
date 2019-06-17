# -*- coding: utf-8 -*-
"""
Created on Fri Jan 11 08:37:14 2019

@author: Marta
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib as mpl
import pypsa

##### 1. LOADING NETWORKS AND FILLING DATAFRAME

#version-45  (transmission=2todays, weakly homogeneous, no CO2 price, decreasing CO2 limit)
path = '/home/marta/Desktop/heavy_data_guest/PyPSA_out/version-77/postnetworks/'
flex= 'elec_central'  
line_limit='0.125'
co2_limit = '0.05'
network_name= path+'postnetwork-' +flex+'_'+ line_limit + '_' + co2_limit+ '.h5' 


network = pypsa.Network(network_name)


avhl = network.loads_t.p[network.loads.index].mean().sum()

battery_e = network.stores_t.e[network.stores.index[network.stores.index.str[3:] == 'battery']].sum(axis=1)/network.stores.e_nom_opt[network.stores.index[network.stores.index.str[3:] == 'battery']].sum()
H2_e = network.stores_t.e[network.stores.index[network.stores.index.str[3:] == 'H2 Store']].sum(axis=1)/network.stores.e_nom_opt[network.stores.index[network.stores.index.str[3:] == 'H2 Store']].sum()

battery_p0 = network.links_t.p0[network.links.index[network.links.index.str[3:] == 'battery charger']].sum(axis=1)/network.links.p_nom_opt[network.links.index[network.links.index.str[3:] == 'battery charger']].sum()

battery_p1 = - network.links_t.p0[network.links.index[network.links.index.str[3:] == 'battery discharger']].sum(axis=1)/network.links.p_nom_opt[network.links.index[network.links.index.str[3:] == 'battery discharger']].sum()

H2_p0 = network.links_t.p0[network.links.index[network.links.index.str[3:] == 'H2 Electrolysis']].sum(axis=1)/network.links.p_nom_opt[network.links.index[network.links.index.str[3:] == 'H2 Electrolysis']].sum()

H2_p1 = -network.links_t.p0[network.links.index[network.links.index.str[3:] == 'H2 Fuel Cell']].sum(axis=1)/network.links.p_nom_opt[network.links.index[network.links.index.str[3:] == 'H2 Fuel Cell']].sum()

PHS_e = network.storage_units_t.state_of_charge[network.storage_units.index[network.storage_units.carrier == 'PHS']].sum(axis=1)/(6*network.storage_units.p_nom[network.storage_units.index[network.storage_units.carrier == 'PHS']].sum())

PHS_p = -network.storage_units_t.p[network.storage_units.index[network.storage_units.carrier == 'PHS']].sum(axis=1)/network.storage_units.p_nom[network.storage_units.index[network.storage_units.carrier == 'PHS']].sum()

if  flex=='elec_central':
    CTES_e= network.stores_t.e[network.stores.index[network.stores.index.str[3:] == 'central water tank']].sum(axis=1)/network.stores.e_nom_opt[network.stores.index[network.stores.index.str[3:] == 'central water tank']].sum()
    CTES_p0 = network.links_t.p0[network.links.index[network.links.index.str[3:] == 'central water tanks charger']].sum(axis=1)/network.links.p_nom_opt[network.links.index[network.links.index.str[3:] == 'central water tanks charger']].sum()
    CTES_p1 = - network.links_t.p0[network.links.index[network.links.index.str[3:] == 'central water tanks discharger']].sum(axis=1)/network.links.p_nom_opt[network.links.index[network.links.index.str[3:] == 'central water tanks discharger']].sum()
    ITES_e= network.stores_t.e[network.stores.index[network.stores.index.str[3:] == 'urban water tank']].sum(axis=1)/network.stores.e_nom_opt[network.stores.index[network.stores.index.str[3:] == 'urban water tank']].sum()
    ITES_p0 = network.links_t.p0[network.links.index[network.links.index.str[3:] == 'urban water tanks charger']].sum(axis=1)/network.links.p_nom_opt[network.links.index[network.links.index.str[3:] == 'urban water tanks charger']].sum()
    ITES_p1 = - network.links_t.p0[network.links.index[network.links.index.str[3:] == 'urban water tanks discharger']].sum(axis=1)/network.links.p_nom_opt[network.links.index[network.links.index.str[3:] == 'urban water tanks discharger']].sum()

#%%
##### 2. PLOTTING
##### Figure power and energy level of storages
plt.style.use('seaborn-ticks')
plt.rcParams['axes.labelsize'] = 20
plt.rcParams['xtick.labelsize'] = 18
plt.rcParams['ytick.labelsize'] = 18
plt.rcParams['xtick.direction'] = 'in'
plt.rcParams['ytick.direction'] = 'in'

plt.figure(figsize=(10, 25))
gs1 = gridspec.GridSpec(5, 1)
gs1.update(hspace=0)
ax1 = plt.subplot(gs1[0,0])
ax1.set_xticklabels([])
#ax1.set_xlabel('hours')
ax1.set_yticks([-0.5, 0, 0.5, 1])
ax1.set_yticklabels(['-0.5','0', '0.5', '1'])
ax1.set_ylabel('battery')
ax1.plot(np.arange(0,8760),battery_e,linewidth=2, color='gold', label='filling level') 
ax1.plot(np.arange(0,8760),battery_p0+battery_p1,linewidth=2, color='sienna', label='power',alpha=0.8) 
ax1.set_xlim(0,720)
ax1.set_ylim(-1,1)
ax1.legend(loc='best', ncol=3, shadow=True,fancybox=True,prop={'size':18})

ax2 = plt.subplot(gs1[1,0])
ax2.set_xticklabels([])
#ax2.set_xlabel('hours')
ax2.set_yticks([-0.5, 0, 0.5, 1])
ax2.set_yticklabels(['-0.5','0', '0.5', '1'])
ax2.set_ylabel('hydrogen')
ax2.plot(np.arange(0,8760),H2_e,linewidth=2, color='m', label='filling level')    
ax2.plot(np.arange(0,8760),H2_p0+H2_p1,linewidth=2, color='pink', label='power',alpha=0.9)  
ax2.set_xlim(0,720)
ax2.set_ylim(-1,1)
ax2.legend(loc='best', ncol=3, shadow=True,fancybox=True,prop={'size':18})

ax3 = plt.subplot(gs1[2,0])
ax3.set_xlabel('hours')
ax3.set_yticks([-1, -0.5, 0, 0.5, 1])
ax3.set_yticklabels(['-1','-0.5','0', '0.5', '1'])
ax3.set_ylabel('PHS')
ax3.plot(np.arange(0,8760),PHS_e,linewidth=2, color='green', label='filling level')    
ax3.plot(np.arange(0,8760),PHS_p,linewidth=2, color='olive', label='power',alpha=0.5)  
ax3.set_xlim(0,720)
ax3.set_ylim(-1,1)
ax3.legend(loc='best', ncol=3, shadow=True,fancybox=True,prop={'size':18})
plt.savefig('figures/discharge_charge.png', dpi=300, bbox_inches='tight') 
if  flex=='elec_central':
    ax3.set_xticklabels([])
    
    ax4 = plt.subplot(gs1[3,0])
    ax4.set_xticklabels([])
    ax4.set_yticks([-0.5, 0, 0.5, 1])
    ax4.set_yticklabels(['-0.5','0', '0.5', '1'])
    ax4.set_ylabel('CTES')
    ax4.plot(np.arange(0,8760),CTES_e,linewidth=2, color='gray', label='filling level')    
    ax4.plot(np.arange(0,8760),CTES_p0+CTES_p1,linewidth=2, color='black', label='power',alpha=1)  
    ax4.set_xlim(0,720)
    ax4.set_ylim(-1,1)
    ax4.legend(loc='best', ncol=3, shadow=True,fancybox=True,prop={'size':18})
    
    ax5 = plt.subplot(gs1[4,0])
    ax5.set_yticks([-0.5, 0, 0.5, 1])
    ax5.set_yticklabels(['-0.5','0', '0.5', '1'])
    ax5.set_ylabel('ITES')
    ax5.plot(np.arange(0,8760),ITES_e,linewidth=2, color='gray', label='filling level')    
    ax5.plot(np.arange(0,8760),ITES_p0+ITES_p1,linewidth=2, color='black', label='power',alpha=1)  
    ax5.set_xlim(0,720)
    ax5.set_ylim(-1,1)
    ax5.legend(loc='best', ncol=3, shadow=True,fancybox=True,prop={'size':18})
plt.savefig('figures/discharge_charge_elec_heat.png', dpi=300, bbox_inches='tight')  

#%%
##### Figure charge and discharge storages
plt.rcParams['axes.titlesize'] = 16
plt.figure(figsize=(10, 25))
gs1 = gridspec.GridSpec(5, 21)
gs1.update(wspace=0.2, hspace=0.2)

cmap=mpl.cm.hot
norm=mpl.colors.Normalize(0, 1)
#ax1.add_patch(PolygonPatch(country_map, fc=cmap((parameters_df[parameter][country+'-onshore']-vmin)/(vmax-vmin)), ec=cmap((parameters_df[parameter][country+'-onshore']-vmin)/(vmax-vmin)), alpha=1))
#cb1=mpl.colorbar.ColorbarBase(ax2, cmap=cmap, norm=norm, orientation='vertical')

ax1 = plt.subplot(gs1[0,0:10])
ax1.set_title('Battery charge')
ax1.set_xticks([6,12,18])
ax1.set_xticklabels(['6:00','12:00','18:00'], fontsize=14)
ax1.set_yticks([0,365])
ax1.set_yticklabels(['1', '365'], fontsize=14)
ax1.set_ylabel('day', fontsize=14)
ax1.pcolor(np.array(battery_p0).reshape((365,24)), cmap=cmap, norm=norm)
ax11 = plt.subplot(gs1[0:2,20])
cb1=mpl.colorbar.ColorbarBase(ax11, cmap=cmap, norm=norm, orientation='vertical')

ax2 = plt.subplot(gs1[0,10:20])
ax2.set_title('Battery discharge')
ax2.set_xticks([6,12,18])
ax2.set_xticklabels(['6:00','12:00','18:00'], fontsize=14)
ax2.set_yticklabels([])
ax2.pcolor(np.array(-battery_p1).reshape((365,24)), cmap=cmap, norm=norm)

ax3 = plt.subplot(gs1[1,0:10])
ax3.set_xticks([6,12,18])
ax3.set_xticklabels(['6:00','12:00','18:00'], fontsize=14)
ax3.set_yticks([0,365])
ax3.set_yticklabels(['1', '365'], fontsize=14)
ax3.set_ylabel('day', fontsize=14)
ax3.pcolor(np.array(H2_p0).reshape((365,24)), cmap=cmap, norm=norm)
ax3.set_title('H$_2$ electrolysis')

ax4 = plt.subplot(gs1[1,10:20])
ax4.set_xticks([6,12,18])
ax4.set_xticklabels(['6:00','12:00','18:00'], fontsize=14)
ax4.set_yticklabels([])
ax4.pcolor(np.array(-H2_p1).reshape((365,24)), cmap=cmap, norm=norm)
ax4.set_title('H$_2$ fuel cell')
plt.savefig('figures/heatmap_charge_discharge.png', dpi=300, bbox_inches='tight')
if  flex=='elec_central':

    ax5 = plt.subplot(gs1[2,0:10])
    ax5.set_xticklabels([])
    ax5.set_yticklabels([])
    ax5.pcolor(np.array(PHS_p.clip(0)).reshape((365,24)), cmap=cmap, norm=norm)
    ax5.set_title('PHS charge')

    ax6 = plt.subplot(gs1[2,10:20])
    ax6.set_xticklabels([])
    ax6.set_yticklabels([])
    ax6.pcolor(np.array((-PHS_p).clip(0)).reshape((365,24)), cmap=cmap, norm=norm)
    ax6.set_title('PHS charge')

    ax7 = plt.subplot(gs1[3,0:10])
    ax7.set_xticks([6,12,18])
    ax7.set_xticklabels(['6:00','12:00','18:00'], fontsize=14)
    ax7.set_yticks([0,365])
    ax7.set_yticklabels(['1', '365'], fontsize=14)
    ax7.set_ylabel('day', fontsize=14)
    ax7.pcolor(np.array(ITES_p0).reshape((365,24)), cmap=cmap, norm=norm)
    ax7.set_title('ITES charge')
    
    ax8 = plt.subplot(gs1[3,10:20])
    ax8.set_xticks([6,12,18])
    ax8.set_xticklabels(['6:00','12:00','18:00'], fontsize=14)
    ax8.set_yticklabels([])
    ax8.pcolor(np.array(-ITES_p1).reshape((365,24)), cmap=cmap, norm=norm)
    ax8.set_title('ITES discharge')
    
    ax9 = plt.subplot(gs1[4,0:10])
    ax9.set_xticks([6,12,18])
    ax9.set_xticklabels(['6:00','12:00','18:00'], fontsize=14)
    ax9.set_yticks([0,365])
    ax9.set_yticklabels(['1', '365'], fontsize=14)
    ax9.set_ylabel('day', fontsize=14)
    ax9.pcolor(np.array(CTES_p0).reshape((365,24)), cmap=cmap, norm=norm)
    ax9.set_title('CTES charge')
    
    ax10 = plt.subplot(gs1[4,10:20])
    ax10.set_xticks([6,12,18])
    ax10.set_xticklabels(['6:00','12:00','18:00'], fontsize=14)
    ax10.set_yticklabels([])
    ax10.pcolor(np.array(-CTES_p1).reshape((365,24)), cmap=cmap, norm=norm)
    ax10.set_title('CTES discharge')
plt.savefig('figures/heatmap_charge_discharge_elec_heat.png', dpi=300, bbox_inches='tight')