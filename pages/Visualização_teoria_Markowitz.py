import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import scipy.optimize as opt
import streamlit as st

st.title("Teoria de Markowitz")
st.subheader("Ativos disponíveis: Ações negociadas na BOVESPA, BYMA e BMV")
st.caption("Autor: Klaus Colletti Oehling")

with st.sidebar:
    st.title("Parâmetros")
    with st.spinner('Carregando...'):
        retorno=pd.read_excel('dadosparamarkowitz.xlsx', engine='openpyxl')
        retorno.columns=retorno.iloc[2,:]
        retorno.columns=retorno.columns.str.replace('Retorno','')
        retorno.columns=retorno.columns.str.replace('do fechamento','')
        retorno.columns=retorno.columns.str.strip()
        retorno.columns=retorno.columns.str.replace('em 1 meses','')
        retorno.columns=retorno.columns.str.replace('Em moeda orig','')
        retorno.columns=retorno.columns.str.strip()
        retorno.columns=retorno.columns.str.replace('ajust p/ prov','')
        retorno.columns=retorno.columns.str.strip()
        retorno=retorno.iloc[3:,:]
        retorno=retorno.melt(id_vars='Data')
        retorno.columns=['Data','variable','value']
        retorno.value=retorno.value.replace('-',np.nan)
        retorno.value=pd.to_numeric(retorno.value)
        retorno=retorno.pivot_table(columns='variable',index='Data',values='value')
        retorno=retorno/100
        
    nomes = list(retorno.columns)
    sel_acoes = np.array(st.multiselect(
        'Selecione as ações que deseja combinar:',
        nomes))
    ret=retorno.iloc[:,0:2]
    ret=retorno[sel_acoes]
    ativos_num=ret.shape[1]
    
    rf=st.number_input("Selecione o risk free mensal:", min_value=0.000, max_value=1.000, step=0.001)
    A= st.number_input("Selecione um valor para o índice de aversão ao risco (A):", min_value=0.01, max_value=100.00, step=0.01)
    st.divider()

if st.button("Calcular gráficos e dados"):
    with st.spinner('Calculando...'):
        r=ret.mean()
        v=ret.cov()
        c=ret.corr()
    
        mu=[]
        sigma=[]
        for i in range(10000):
            pesos = np.random.dirichlet(np.ones(ativos_num), size=1)
            pesos = pesos[0]
            mu.append(np.sum(r*pesos))
            sigma.append(float(np.sqrt(pesos*(pesos*np.asmatrix(v)).T)))  
        mu=np.asmatrix(np.array(mu))
        sigma=np.asmatrix(np.array(sigma))
        dados=pd.concat([pd.DataFrame(mu).T,pd.DataFrame(sigma).T], axis=1)
        dados.columns=['Média','Desvio Padrão']
        dados['Sharpe']=(dados['Média']-rf)/dados['Desvio Padrão']
    
        def infos(pesos):
            pesos = np.array(pesos)
            ret = np.sum(r*pesos)
            sig = float(np.sqrt(pesos*(pesos*np.asmatrix(v)).T))
            shar = float((ret-rf)/sig)
            return {'Retorno': ret, 'Risco': sig, 'Sharpe': shar}
        def maximizar_sharpe(pesos):  
            return -infos(pesos)['Sharpe'] 
        def minimizar_risco(pesos):  
            return infos(pesos)['Risco'] 
        def maximizar_retorno(pesos): 
            return -infos(pesos)['Retorno']
        def minimizar_retorno(pesos): 
            return infos(pesos)['Retorno']
    
        constraints = ({'type' : 'eq', 'fun': lambda x: np.sum(x) -1})
        initializer = ativos_num * [1./ativos_num,]
        bounds = tuple((0,1) for x in range(ativos_num))
        sharpe_max=opt.minimize(maximizar_sharpe,
                                        initializer,
                                        method = 'SLSQP',
                                        bounds = bounds,
                                        constraints = constraints)
        pesos_otimos=sharpe_max['x']
        dados_port_otimo=infos(pesos_otimos)
    
        ret_max=opt.minimize(maximizar_retorno,
                                        initializer,
                                        method = 'SLSQP',
                                        bounds = bounds,
                                        constraints = constraints)
        ret_max=-ret_max['fun']
        ret_min=opt.minimize(minimizar_retorno,
                                        initializer,
                                        method = 'SLSQP',
                                        bounds = bounds,
                                        constraints = constraints)
        ret_min=ret_min['fun']
    
        min_var=opt.minimize(minimizar_risco,
                                    initializer,
                                    method = 'SLSQP',
                                    bounds = bounds,
                                    constraints = constraints)
        pesos_min_var=min_var['x']
        dados_port_min=infos(pesos_min_var)
    
        intervalo_retornos = np.linspace(ret_min,
                                        ret_max,70)
        fronteira = []
        for intervalo_retorno in intervalo_retornos:
            constraints = ({'type':'eq','fun': lambda x: infos(x)['Retorno']-intervalo_retorno},
                        {'type':'eq','fun': lambda x: np.sum(x)-1})
            fronteira_valores = opt.minimize(minimizar_risco,
                                initializer,
                                method = 'SLSQP',
                                bounds = bounds,
                                constraints = constraints)
            fronteira.append(fronteira_valores['fun'])
        fronteira = np.array(fronteira)
    
        sig=np.arange(0,0.1,0.001)
        medi=np.zeros(100)
        for i in range(0,100):
            medi[i]=-sharpe_max['fun']*sig[i] + rf
    
        def linha_utilidade(A):
            segmento=((dados_port_otimo['Retorno']-rf)**2+(dados_port_otimo['Risco'])**2)**(1/2)
            sig_uti=infos(pesos_otimos)['Sharpe']/A
            ret_uti=infos(pesos_otimos)['Sharpe']*sig_uti + rf
            u=ret_uti-A*0.5*sig_uti**2
            uti=np.zeros(100)
            for i in range(0,100):
                uti[i]=A*0.5*sig[i]**2 + u
            segmento2=((ret_uti-rf)**2+sig_uti**2)**(1/2)
            peso_port=segmento2/segmento
            peso_rf=1-peso_port
            dados_port_A=pd.DataFrame([infos(pesos_otimos)['Retorno']*peso_port + peso_rf*rf,infos(pesos_otimos)['Risco']*peso_port]).T
            dados_port_A.columns=['Retorno médio','Desvio Padrão']
            dados_port_A['Sharpe']=(dados_port_A['Retorno médio']-rf)/dados_port_A['Desvio Padrão']
            
            pesos_otimos_finais=pd.DataFrame([(pesos_otimos*peso_port)])
            pesos_otimos_finais.columns=ret.columns
            pesos_otimos_finais['Risk Free']=peso_rf
            return {'Pesos': pesos_otimos_finais, 'Imagem utilidade': uti, 'Infos': dados_port_A, 'Risk Free': peso_rf, 'Portfolio': peso_port}
    
        plt.figure()
        plt.rcParams["font.family"] = "Times New Roman"
        plt.plot(sig,medi, color='black')
        plt.plot(fronteira,intervalo_retornos, color='black')
        plt.plot(sig,linha_utilidade(2)['Imagem utilidade'], color='grey')
        plt.scatter(dados['Desvio Padrão'],dados['Média'],c=dados['Sharpe'], cmap='binary',s=1)
        plt.xlim(0,max(dados['Desvio Padrão'])*1.1)
        
        if ret_min>rf:
            lim_inf=rf*0.9
        else:
            lim_inf=ret_min*0.9
    
        if ret_max>rf:
            lim_sup=ret_max*1.1
        else:
            lim_sup=rf*1.1
    
        plt.ylim(lim_inf,lim_sup)
        plt.xlabel('Risco (Desvio Padrão)')
        plt.ylabel('Retorno Esperado')
        plt.title('Otimização',fontweight="bold")   
        st.pyplot(plt)  
        st.divider()
        
        st.subheader("Mínimo desvio padrão")
        st.write(f"Retorno = {round(dados_port_min['Retorno']*100,4)}%")
        st.write(f"Desvio padrão = {round(dados_port_min['Risco']*100,4)}%")
        st.write(f"Sharpe = {round(dados_port_min['Sharpe'],4)}")
        st.write("A alocação é:")
        for i in range(0,ativos_num):
            st.write(f"{ret.columns[i]} - {round(pesos_min_var[i]*100,4)}%")
        st.divider()
    
        st.subheader("Máximo sharpe")
        st.write(f"Retorno = {round(dados_port_otimo['Retorno']*100,4)}%")
        st.write(f"Desvio padrão = {round(dados_port_otimo['Risco']*100,4)}%")
        st.write(f"Sharpe = {round(dados_port_otimo['Sharpe'],4)}")
        st.write("A alocação é:")
        for i in range(0,ativos_num):
            st.write(f"{ret.columns[i]} - {round(pesos_otimos[i]*100,4)}%")
        st.divider()
        
        st.subheader(f"Carteira ótima dado A = {A}")
        st.write(f"Retorno = {round(linha_utilidade(A)['Infos']['Retorno médio'][0]*100,4)}%")
        st.write(f"Desvio padrão = {round(linha_utilidade(A)['Infos']['Desvio Padrão'][0]*100,4)}%")
        st.write(f"Sharpe = {round(linha_utilidade(A)['Infos']['Sharpe'][0],4)}")
        st.write(f"A alocação é {round(linha_utilidade(A)['Portfolio']*100,4)}% no portfólio e {round(linha_utilidade(A)['Risk Free']*100,4)}% no risk free")
        st.write("Portanto, a alocação final é:")
        st.write(f"Risk free - {round(linha_utilidade(A)['Pesos']['Risk Free'][0]*100,4)}%")
        for i in range(0,ativos_num):
            st.write(f"{ret.columns[i]} - {round(linha_utilidade(A)['Pesos'][ret.columns[i]][0]*100,4)}%")
        st.divider()