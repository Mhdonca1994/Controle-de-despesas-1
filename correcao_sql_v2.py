#!/usr/bin/env python3
"""
Script de Correção SQL - Portal de Despesas
Corrige consultas SQL ambíguas (ambiguous column name)
Resolve: Erro "ambiguous column name: grupo_id"
"""

import os
import re
import shutil
from datetime import datetime

def fazer_backup_arquivo(caminho_arquivo):
    """Faz backup do arquivo antes de modificar"""
    if os.path.exists(caminho_arquivo):
        backup_path = f"{caminho_arquivo}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(caminho_arquivo, backup_path)
        print(f"   📄 Backup criado: {backup_path}")
        return backup_path
    return None

def corrigir_consultas_especificas(conteudo):
    """Corrige consultas específicas conhecidas por causar problemas"""
    
    # Lista de correções específicas baseadas em erros comuns
    consultas_especificas = [
        # Consulta típica que causa erro ambíguo
        {
            'buscar': 'WHERE grupo_id',
            'substituir': 'WHERE d.grupo_id',
            'descricao': 'Corrigir WHERE grupo_id para d.grupo_id'
        },
        {
            'buscar': 'AND grupo_id',
            'substituir': 'AND d.grupo_id',
            'descricao': 'Corrigir AND grupo_id para d.grupo_id'
        },
        {
            'buscar': 'ORDER BY grupo_id',
            'substituir': 'ORDER BY d.grupo_id',
            'descricao': 'Corrigir ORDER BY grupo_id para d.grupo_id'
        },
        {
            'buscar': 'GROUP BY grupo_id',
            'substituir': 'GROUP BY d.grupo_id',
            'descricao': 'Corrigir GROUP BY grupo_id para d.grupo_id'
        },
        {
            'buscar': 'WHERE user_id',
            'substituir': 'WHERE d.user_id',
            'descricao': 'Corrigir WHERE user_id para d.user_id'
        },
        {
            'buscar': 'AND user_id',
            'substituir': 'AND d.user_id',
            'descricao': 'Corrigir AND user_id para d.user_id'
        },
        {
            'buscar': 'ORDER BY user_id',
            'substituir': 'ORDER BY d.user_id',
            'descricao': 'Corrigir ORDER BY user_id para d.user_id'
        }
    ]
    
    correcoes = []
    conteudo_modificado = conteudo
    
    for consulta in consultas_especificas:
        buscar = consulta['buscar'].strip()
        substituir = consulta['substituir'].strip()
        descricao = consulta['descricao']
        
        if buscar in conteudo_modificado:
            # Contar quantas vezes vai substituir
            count = conteudo_modificado.count(buscar)
            conteudo_modificado = conteudo_modificado.replace(buscar, substituir)
            correcoes.append(f"✅ {descricao} ({count}x)")
    
    if correcoes:
        return conteudo_modificado, correcoes
    else:
        return None, []

def adicionar_prefixos_tabela(conteudo):
    """Adiciona prefixos de tabela automaticamente em consultas SQL"""
    
    consultas_corrigidas = []
    linhas = conteudo.split('\n')
    linhas_modificadas = []
    
    for i, linha in enumerate(linhas):
        linha_original = linha
        
        # Se a linha contém uma consulta SQL com FROM e JOIN
        if ('FROM' in linha.upper() and 'JOIN' in linha.upper()) or \
           (i > 0 and 'JOIN' in linhas[i-1].upper() and any(col in linha for col in ['grupo_id', 'user_id', 'categoria_id'])):
            
            # Substituições específicas para colunas ambíguas
            substituicoes = {
                'ON grupo_id = ': 'ON d.grupo_id = ',
                'ON user_id = ': 'ON d.user_id = ',
                '= grupo_id': '= d.grupo_id',
                '= user_id': '= d.user_id'
            }
            
            for buscar, substituir in substituicoes.items():
                if buscar in linha:
                    linha = linha.replace(buscar, substituir)
                    if linha != linha_original:
                        consultas_corrigidas.append(f"Linha {i+1}: {buscar} → {substituir}")
        
        linhas_modificadas.append(linha)
    
    conteudo_novo = '\n'.join(linhas_modificadas)
    
    if consultas_corrigidas:
        return conteudo_novo, consultas_corrigidas
    else:
        return None, []

def corrigir_arquivo_main():
    """Corrige o arquivo main.py"""
    
    caminho_main = 'src/main.py'
    
    if not os.path.exists(caminho_main):
        print(f"❌ Arquivo não encontrado: {caminho_main}")
        print("💡 Certifique-se de executar este script na pasta raiz do projeto")
        return False
    
    print(f"🔧 Corrigindo arquivo: {caminho_main}")
    
    # Fazer backup
    backup_path = fazer_backup_arquivo(caminho_main)
    
    # Ler conteúdo
    with open(caminho_main, 'r', encoding='utf-8') as f:
        conteudo = f.read()
    
    print("   📖 Arquivo lido com sucesso")
    
    # Aplicar correções
    todas_correcoes = []
    conteudo_corrigido = conteudo
    
    # Método 1: Correções específicas
    resultado1, correcoes1 = corrigir_consultas_especificas(conteudo_corrigido)
    if resultado1:
        conteudo_corrigido = resultado1
        todas_correcoes.extend(correcoes1)
    
    # Método 2: Adicionar prefixos automaticamente
    resultado2, correcoes2 = adicionar_prefixos_tabela(conteudo_corrigido)
    if resultado2:
        conteudo_corrigido = resultado2
        todas_correcoes.extend(correcoes2)
    
    # Se houve correções, salvar arquivo
    if todas_correcoes:
        with open(caminho_main, 'w', encoding='utf-8') as f:
            f.write(conteudo_corrigido)
        
        print("   💾 Arquivo corrigido e salvo")
        print(f"\n📋 Correções aplicadas:")
        for correcao in todas_correcoes:
            print(f"   {correcao}")
        
        return True
    else:
        print("   ℹ️ Nenhuma correção SQL automática foi necessária")
        print("   💡 O erro pode estar em uma consulta específica que precisa de correção manual")
        
        # Mostrar sugestões de correção manual
        print(f"\n🔍 Procure por estas linhas problemáticas no arquivo:")
        print("   - Consultas que fazem JOIN entre tabelas")
        print("   - Uso de 'grupo_id' sem prefixo de tabela (d.grupo_id)")
        print("   - Linha ~188 onde o erro está ocorrendo")
        
        return False

def mostrar_exemplo_correcao():
    """Mostra exemplos de como corrigir manualmente"""
    
    print("\n" + "="*60)
    print("   EXEMPLOS DE CORREÇÃO MANUAL")
    print("="*60)
    
    exemplos = [
        {
            'problema': '''SELECT d.*, g.nome 
FROM despesas d 
JOIN grupos g ON grupo_id = g.id''',
            'solucao': '''SELECT d.*, g.nome 
FROM despesas d 
JOIN grupos g ON d.grupo_id = g.id''',
            'explicacao': 'Adicionar prefixo d. antes de grupo_id no JOIN'
        },
        {
            'problema': '''SELECT * FROM despesas d 
JOIN categorias c ON d.categoria_id = c.id 
WHERE grupo_id = 1''',
            'solucao': '''SELECT * FROM despesas d 
JOIN categorias c ON d.categoria_id = c.id 
WHERE d.grupo_id = 1''',
            'explicacao': 'Adicionar prefixo d. antes de grupo_id no WHERE'
        },
        {
            'problema': '''ORDER BY grupo_id, data''',
            'solucao': '''ORDER BY d.grupo_id, d.data''',
            'explicacao': 'Adicionar prefixos de tabela em ORDER BY'
        }
    ]
    
    for i, exemplo in enumerate(exemplos, 1):
        print(f"\n🔸 Exemplo {i}: {exemplo['explicacao']}")
        print("❌ Problemático:")
        print(f"   {exemplo['problema']}")
        print("✅ Corrigido:")
        print(f"   {exemplo['solucao']}")

def mostrar_instrucoes_manuais():
    """Mostra instruções para correção manual da linha específica"""
    
    print("\n" + "="*60)
    print("   INSTRUÇÕES DE CORREÇÃO MANUAL")
    print("="*60)
    
    print(f"\n🎯 Para corrigir o erro na linha ~188:")
    print("   1. Abra o arquivo src/main.py")
    print("   2. Procure pela linha que contém a consulta SQL problemática")
    print("   3. Identifique consultas que fazem JOIN entre tabelas")
    print("   4. Adicione prefixos de tabela nas colunas ambíguas")
    
    print(f"\n🔍 Procure por padrões como:")
    print("   - FROM despesas d JOIN ...")
    print("   - WHERE grupo_id = ...")
    print("   - ORDER BY grupo_id ...")
    print("   - ON grupo_id = ...")
    
    print(f"\n🔧 Como corrigir:")
    print("   - Mude: WHERE grupo_id = 1")
    print("   - Para:  WHERE d.grupo_id = 1")
    print()
    print("   - Mude: ON grupo_id = g.id")
    print("   - Para:  ON d.grupo_id = g.id")
    print()
    print("   - Mude: ORDER BY grupo_id")
    print("   - Para:  ORDER BY d.grupo_id")

if __name__ == '__main__':
    print("=" * 60)
    print("   CORREÇÃO SQL - PORTAL DE DESPESAS")
    print("=" * 60)
    print()
    
    if corrigir_arquivo_main():
        print("\n✅ Correções aplicadas com sucesso!")
        print("🚀 Teste o portal novamente")
    else:
        print("\n⚠️ Correções automáticas não foram suficientes")
        print("📝 Será necessário correção manual")
        
        mostrar_exemplo_correcao()
        mostrar_instrucoes_manuais()
    
    input("\nPressione Enter para continuar...")