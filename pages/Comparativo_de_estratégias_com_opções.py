# -*- coding: utf-8 -*-
"""
Created on Wed Mar  6 13:37:19 2024

@author: oehli
"""

import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
import pandas as pd

st.title("Comparação de estratégias usando opções")
st.caption("Autor: Klaus Colletti Oehling")

strike_venda_call_cc=0
strike_compra_put_pp=0
strike_compra_call_bcs=0
strike_venda_call_bcs=0

with st.sidebar:
    st.title("Parâmetros")
    strats = np.array(st.multiselect(
    'Selecione as estratégias que deseja comparar:',
    ['Covered Call', 'Protective Put', 'Bull Call Spread']))
    
    st.divider()
    if np.any(strats == 'Covered Call'):
        st.subheader('Covered Call')
        p_ativo_cc=st.number_input("Digite o preço corrente do ativo objeto", min_value=0.0, max_value=10000.0, step=0.001,key =0)
        premio_venda_call_cc=st.number_input("Digite o prêmio da opção referente ao ativo objeto", min_value=0.0, max_value=10000.0, step=0.001,key = 1)
        strike_venda_call_cc=st.number_input("Digite o strike da opção referente ao ativo objeto", min_value=0.0, max_value=10000.0, step=0.001,key = 2)
        st.divider()
        
    if np.any(strats == 'Protective Put'):
        st.subheader('Protective Put')
        p_ativo_pp=st.number_input("Digite o preço corrente do ativo objeto", min_value=0.0, max_value=10000.0, step=0.001,key =9)
        premio_compra_put_pp=st.number_input("Digite o prêmio da opção referente ao ativo objeto", min_value=0.0, max_value=10000.0, step=0.001,key = 3)
        strike_compra_put_pp=st.number_input("Digite o strike da opção referente ao ativo objeto", min_value=0.0, max_value=10000.0, step=0.001,key = 4)
        st.divider()
        
    if np.any(strats == 'Bull Call Spread'):
        st.subheader('Bull Call Spread')
        premio_compra_call_bcs=st.number_input("Digite o prêmio da opção referente à compra de call", min_value=0.0, max_value=10000.0, step=0.001,key = 5)
        strike_compra_call_bcs=st.number_input("Digite o strike da opção referente  à compra de call", min_value=0.0, max_value=10000.0, step=0.001,key = 6)  
        premio_venda_call_bcs=st.number_input("Digite o prêmio da opção referente à venda de call", min_value=0.0, max_value=10000.0, step=0.001,key = 7)
        strike_venda_call_bcs=st.number_input("Digite o strike da opção referente  à venda de call", min_value=0.0, max_value=10000.0, step=0.001,key = 8) 
        st.divider()
     
x_valores = np.linspace(0, 2*max(strike_venda_call_cc,strike_compra_put_pp,strike_compra_call_bcs,strike_venda_call_bcs), 1000)

def compra_call(x,s,c):
    if x <= s:
        return -c
    else:
        return x-s-c
def venda_call(x,s,c):
    if x <= s:
        return c
    else:
        return -x+s+c
def compra_put(x,s,p):
    if x <= s:
        return -x+s-p
    else:
        return -p
def venda_put(x,s,p):
    if x <= s:
        return x-s+p
    else:
        return p
def ativo_objeto(x,preco):
    return x-preco 

covcal=np.full(1000, np.nan)
protput=np.full(1000, np.nan)
bullcspread=np.full(1000, np.nan)
    
if st.button("Calcular gráfico"):
    with st.spinner('Calculando...'):

        fig=plt.figure()
    
        if np.any(strats == 'Covered Call'):
            covcal= np.array([venda_call(x,strike_venda_call_cc,premio_venda_call_cc) for x in x_valores])+np.array([ativo_objeto(x,p_ativo_cc) for x in x_valores])
            plt.plot(x_valores,covcal, label='Covered Call')
            
        if np.any(strats == 'Protective Put'):
            protput=  np.array([compra_put(x,strike_compra_put_pp,premio_compra_put_pp) for x in x_valores])+np.array([ativo_objeto(x,p_ativo_pp) for x in x_valores])
            plt.plot(x_valores,protput, label='Protective Put')

        if np.any(strats == 'Bull Call Spread'):
            bullcspread= np.array([compra_call(x,strike_compra_call_bcs,premio_compra_call_bcs) for x in x_valores]) + np.array([venda_call(x,strike_venda_call_bcs,premio_venda_call_bcs) for x in x_valores])
            plt.plot(x_valores,bullcspread, label='Bull Call Spread')
            
        plt.grid(True)
        plt.xlabel('Preço no vencimento')
        plt.ylabel('Resultado')
        plt.title('Comparação')
        plt.legend()
        st.pyplot(fig)
        
        st.divider()
        
        df = pd.DataFrame({'Preço no Vencimento': x_valores, 'Covered Call': covcal, 'Protective Put': protput, 'Bull Call Spread': bullcspread})
        df=df.set_index('Preço no Vencimento')
        st.line_chart(df)