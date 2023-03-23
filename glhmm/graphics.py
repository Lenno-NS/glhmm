#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Basic graphics - Gaussian Linear Hidden Markov Model
@author: Diego Vidaurre 2023
"""
import numpy as np
import seaborn as sb
import matplotlib.pyplot as plt
import pandas as pd

from . import utils
# import utils



def show_trans_prob_mat(hmm,only_active_states=False,show_diag=True,show_colorbar=True):

    P = np.copy(hmm.P)
    if only_active_states:
        P = P[hmm.active_states,hmm.active_states]
        
    K = P.shape[0]

    if not show_diag:
        for k in range(P.shape[0]):
            P[k,k] = 0
            P[k,:] = P[k,:] / np.sum(P[k,:])

    _,ax = plt.subplots()
    g = sb.heatmap(ax=ax,data=P,\
        cmap='bwr',xticklabels=np.arange(K), yticklabels=np.arange(K),
        square=True,cbar=show_colorbar)
    for k in range(K):
        g.plot([0, K],[k, k], '-k')
        g.plot([k, k],[0, K], '-k')

    ax.axhline(y=0, color='k',linewidth=4)
    ax.axhline(y=K, color='k',linewidth=4)
    ax.axvline(x=0, color='k',linewidth=4)
    ax.axvline(x=K, color='k',linewidth=4)


def show_Gamma(Gamma,tlim=None,Hz=1,palette='Oranges'):

    T,K = Gamma.shape

    x = np.round(np.linspace(0.0, 256-1, K)).astype(int)
    cmap = plt.get_cmap('plasma').colors
    cols = np.zeros((K,3))
    for k in range(K):
        cols[k,:] = cmap[x[k]]

    if tlim is None:
        df = pd.DataFrame(Gamma, index=np.arange(T)/Hz)
    else:
        T = tlim[1] - tlim[0]
        df = pd.DataFrame(Gamma[tlim[0]:tlim[1],:], index=np.arange(T)/Hz)
    df = df.divide(df.sum(axis=1), axis=0)
    ax = df.plot(kind='area', stacked=True,ylim=(0,1),legend=False,
            color=cols)

    ax.set_ylabel('Percent (%)')
    ax.margins(0,0)

    plt.show()


def show_temporal_statistic(Gamma,indices,statistic='FO',type_plot='barplot'):
    # """ Box plots of a given temporal statistic s, which can be:
    #   s = utils.get_FO(Gamma,indices)
    #   s = utils.get_switching_rate(Gamma,indices)
    #   s,_,_ = utils.get_life_times(vpath,indices)
    #   s = utils.get_FO_entropy(Gamma,indices)
    # """

    s = eval("utils.get_" + statistic)(Gamma,indices)
    if statistic not in ["FO","switching_rate","FO_entropy"]:
        raise Exception("statistic has to be 'FO','switching_rate' or 'FO_entropy'") 
    N,K = s.shape

    sb.set(style='whitegrid')
    if type_plot=='boxplot':
        if N < 10:
            raise Exception("Too few sessions for a boxplot; use barplot") 
        sb.boxplot(data=s,palette='plasma')
    elif type_plot=='barplot':
        sb.barplot(data=np.concatenate((s,s)),palette='plasma', errorbar=None)
    elif type_plot=='matrix':
        if N < 2:
            raise Exception("There is only one session; use barplot") 
        fig,ax = plt.subplots()
        labels_x = np.round(np.linspace(0,N,5)).astype(int)
        pos_x = np.linspace(0,N,5)
        if K > 10: labels_y = np.linspace(0,K-1,5)
        else: labels_y = np.arange(K)
        im = plt.imshow(s.T,aspect='auto')
        plt.xticks(pos_x, labels_x)
        plt.yticks(labels_y, labels_y)
        ax.set_xlabel('Sessions')
        ax.set_ylabel('States')
        fig.tight_layout()


def show_beta(hmm,only_active_states=False,X=None,Y=None,show_average=None):

    if show_average is None:
        show_average = not ((X is None) or (Y is None))
    
    K = hmm.hyperparameters["K"]
    beta = hmm.get_betas()

    if only_active_states:
        idx = np.where(hmm.active_states)[0]
        beta = beta[:,:,idx]
    else:
        idx = np.arange(K)

    (p,q,K) = beta.shape

    if show_average:
        Yr = np.copy(Y)
        Yr -= np.expand_dims(np.mean(Y,axis=0), axis=0)   
        b0 = np.linalg.inv(X.T @ X) @ (X.T @ Yr)
        K += 1
        B = np.zeros((p,q,K))
        B[:,:,0:K-1] = beta
        B[:,:,-1] = b0 
    else:
        B = beta

    Bstar1 = np.zeros((p,q,K,K))
    for k in range(K): Bstar1[:,:,k,:] = B
    Bstar2 = np.zeros((p,q,K,K))
    for k in range(K): Bstar2[:,:,:,k] = B   

    I1 = np.zeros((p,q,K,K),dtype=object)
    for j in range(q): I1[:,j,:,:] = str(j)
    I2 = np.zeros((p,q,K,K),dtype=object)
    for k in range(K): 
        if show_average and (k==(K-1)): 
            I2[:,:,k,:] = 'Average'
        else:
            I2[:,:,k,:] = 'State ' + str(k)
    I3 = np.zeros((p,q,K,K),dtype=object)
    for k in range(K): 
        if show_average and (k==(K-1)): 
            I3[:,:,:,k] = 'Average'
        else:
            I3[:,:,:,k] = 'State ' + str(k)

    Bstar1 = np.expand_dims(np.reshape(Bstar1,p*q*K*K,order='F'),axis=0)
    Bstar2 = np.expand_dims(np.reshape(Bstar2,p*q*K*K,order='F'),axis=0)
    I1 = np.expand_dims(np.reshape(I1,p*q*K*K,order='F'),axis=0)
    I2 = np.expand_dims(np.reshape(I2,p*q*K*K,order='F'),axis=0)
    I3 = np.expand_dims(np.reshape(I3,p*q*K*K,order='F'),axis=0)

    B = np.concatenate((Bstar1,Bstar2,I1,I2,I3),axis=0).T
    df = pd.DataFrame(B,columns=('x','y','Variable','beta x','beta y'))

    sb.relplot(x='x', 
        y='y', 
        hue='Variable', 
        col="beta x", row="beta y",
        data=df,
        palette='cool', 
        height=8)
    

    def show_r2(r2=None,hmm=None,Gamma=None,X=None,Y=None,indices=None,show_average=False):

        if r2 is None:
            if (Y is None) or (indices is None):
                raise Exception("Y and indices (and maybe X) has to be specified if r2 is not provided")
            r2 = hmm.get_r2(X,Y,Gamma,indices)

        if show_average:
            if (Y is None) or (indices is None):
                raise Exception("Y and indices (and maybe X) has to be specified if the average is to computed") 

                r20 = hmm.get_r2(X,Y,Gamma,indices)

                for j in range(N):

                    tt_j = range(indices[j,0],indices[j,1])

                    if X is not None:
                        Xj = np.copy(X[tt_j,:])

                    d = np.copy(Y[tt_j,:])
                    if self.hyperparameters["model_mean"] == 'shared':
                        d -= np.expand_dims(self.mean[0]['Mu'],axis=0)
                    if self.hyperparameters["model_beta"] == 'shared':
                        d -= (Xj @ self.beta[0]['Mu'])
                    for k in range(K):
                        if self.hyperparameters["model_mean"] == 'state': 
                            d -= np.expand_dims(self.mean[k]['Mu'],axis=0) * np.expand_dims(Gamma[:,k],axis=1)
                        if self.hyperparameters["model_beta"] == 'state':
                            d -= (Xj @ self.beta[k]['Mu']) * np.expand_dims(Gamma[:,k],axis=1)
                    d = np.sum(d**2,axis=0)

                    d0 = np.copy(Y[tt_j,:])
                    if self.hyperparameters["model_mean"] != 'no':
                        d0 -= np.expand_dims(m,axis=0)
                    d0 = np.sum(d0**2,axis=0)

                    r2[j,:] = 1 - (d / d0)
