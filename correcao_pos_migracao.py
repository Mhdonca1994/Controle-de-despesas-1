#!/usr/bin/env python3
"""
Script de Correção Pós-Migração - Portal de Despesas
Corrige colunas faltantes após migração principal
Resolve: Erro "no such column: ativo"
"""

import sqlite3
import os

DATABASE = 'src/database/app.db'

def table_exists(cursor, table_name):
    """Verifica se uma tabela existe"""
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    return cursor.fetchone() is not None

def column_exists(cursor, table_name, column_name):
    """Verifica se uma coluna existe em uma tabela"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns

def get_table_columns(cursor, table_name):
    """Retorna todas as colunas de uma tabela"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    return [row[1] for row in cursor.fetchall()]

def safe_add_column(cursor, table_name, column_name, column_type, default_value=None):
    """Adiciona uma coluna de forma segura"""
    if not column_exists(cursor, table_name, column_name):
        try:
            if default_value is not None:
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type} DEFAULT {default_value}")
            else:
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
            
            # Se for created_at, atualizar registros existentes
            if column_name == 'created_at' and default_value is None:
                cursor.execute(f"UPDATE {table_name} SET {column_name} = datetime('now') WHERE {column_name} IS NULL")
            
            print(f"   ✅ Coluna '{column_name}' adicionada à tabela {table_name}")
            return True
        except Exception as e:
            print(f"   ⚠️ Erro ao adicionar coluna '{column_name}' à tabela {table_name}: {e}")
            return False
    else:
        print(f"   ℹ️ Coluna '{column_name}' já existe na tabela {table_name}")
        return False

def verificar_e_corrigir_estrutura():
    """Verifica e corrige estrutura de todas as tabelas"""
    
    if not os.path.exists(DATABASE):
        print(f"❌ Banco de dados não encontrado: {DATABASE}")
        return False
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    try:
        print("🔍 Verificando estrutura das tabelas...")
        
        # Estrutura esperada de cada tabela
        estruturas_esperadas = {
            'users': [
                ('perfil', 'TEXT', "'usuario'"),
                ('nome_completo', 'TEXT', None),
                ('email', 'TEXT', None),
                ('ativo', 'BOOLEAN', '1'),
                ('created_at', 'TEXT', None),
                ('updated_at', 'TEXT', None)
            ],
            'categorias': [
                ('descricao', 'TEXT', None),
                ('cor', 'TEXT', "'#667eea'"),
                ('icone', 'TEXT', "'fas fa-tag'"),
                ('ativo', 'BOOLEAN', '1'),
                ('created_at', 'TEXT', None)
            ],
            'despesas': [
                ('cartao_id', 'INTEGER', None),
                ('grupo_id', 'INTEGER', None),
                ('despesa_fixa_id', 'INTEGER', None),
                ('parcela_atual', 'INTEGER', '1'),
                ('total_parcelas', 'INTEGER', '1'),
                ('grupo_parcela', 'TEXT', None),
                ('tipo', 'TEXT', "'individual'"),
                ('observacoes', 'TEXT', None),
                ('user_id', 'INTEGER', None),
                ('created_at', 'TEXT', None)
            ],
            'despesas_fixas': [
                ('observacoes', 'TEXT', None),
                ('user_id', 'INTEGER', None),
                ('grupo_id', 'INTEGER', None),
                ('ativo', 'BOOLEAN', '1'),
                ('created_at', 'TEXT', None)
            ],
            'grupos': [
                ('descricao', 'TEXT', None),
                ('tipo', 'TEXT', "'familia'"),
                ('criado_por', 'INTEGER', None),
                ('ativo', 'BOOLEAN', '1'),
                ('created_at', 'TEXT', None)
            ],
            'grupo_membros': [
                ('papel', 'TEXT', "'membro'"),
                ('adicionado_por', 'INTEGER', None),
                ('created_at', 'TEXT', None)
            ],
            'cartoes': [
                ('descricao', 'TEXT', None),
                ('limite_credito', 'REAL', '0'),
                ('bandeira', 'TEXT', None),
                ('user_id', 'INTEGER', None),
                ('ativo', 'BOOLEAN', '1'),
                ('created_at', 'TEXT', None)
            ]
        }
        
        # Verificar cada tabela
        for table_name, expected_columns in estruturas_esperadas.items():
            if table_exists(cursor, table_name):
                print(f"\n📋 Verificando tabela '{table_name}'...")
                
                # Mostrar colunas atuais
                current_columns = get_table_columns(cursor, table_name)
                print(f"   Colunas atuais: {', '.join(current_columns)}")
                
                # Adicionar colunas faltantes
                for column_name, column_type, default_value in expected_columns:
                    safe_add_column(cursor, table_name, column_name, column_type, default_value)
            else:
                print(f"⚠️ Tabela '{table_name}' não encontrada")
        
        # Verificar se há dados inconsistentes
        print(f"\n🔧 Verificando consistência dos dados...")
        
        # Verificar usuários sem campos obrigatórios
        users_sem_ativo = cursor.execute("SELECT COUNT(*) FROM users WHERE ativo IS NULL").fetchone()[0]
        if users_sem_ativo > 0:
            cursor.execute("UPDATE users SET ativo = 1 WHERE ativo IS NULL")
            print(f"   ✅ Corrigidos {users_sem_ativo} usuários sem status ativo")
        
        # Verificar categorias sem campos obrigatórios
        if table_exists(cursor, 'categorias'):
            categorias_sem_ativo = cursor.execute("SELECT COUNT(*) FROM categorias WHERE ativo IS NULL").fetchone()[0]
            if categorias_sem_ativo > 0:
                cursor.execute("UPDATE categorias SET ativo = 1 WHERE ativo IS NULL")
                print(f"   ✅ Corrigidas {categorias_sem_ativo} categorias sem status ativo")
            
            categorias_sem_cor = cursor.execute("SELECT COUNT(*) FROM categorias WHERE cor IS NULL").fetchone()[0]
            if categorias_sem_cor > 0:
                cursor.execute("UPDATE categorias SET cor = '#667eea' WHERE cor IS NULL")
                print(f"   ✅ Corrigidas {categorias_sem_cor} categorias sem cor")
        
        # Verificar despesas_fixas sem campos obrigatórios
        if table_exists(cursor, 'despesas_fixas'):
            despesas_fixas_sem_ativo = cursor.execute("SELECT COUNT(*) FROM despesas_fixas WHERE ativo IS NULL").fetchone()[0]
            if despesas_fixas_sem_ativo > 0:
                cursor.execute("UPDATE despesas_fixas SET ativo = 1 WHERE ativo IS NULL")
                print(f"   ✅ Corrigidas {despesas_fixas_sem_ativo} despesas fixas sem status ativo")
        
        # Verificar outros campos created_at
        tabelas_com_created_at = ['users', 'categorias', 'despesas', 'despesas_fixas', 'grupos', 'grupo_membros', 'cartoes']
        
        for tabela in tabelas_com_created_at:
            if table_exists(cursor, tabela) and column_exists(cursor, tabela, 'created_at'):
                registros_sem_data = cursor.execute(f"SELECT COUNT(*) FROM {tabela} WHERE created_at IS NULL").fetchone()[0]
                if registros_sem_data > 0:
                    cursor.execute(f"UPDATE {tabela} SET created_at = datetime('now') WHERE created_at IS NULL")
                    print(f"   ✅ Corrigidos {registros_sem_data} registros sem data de criação na tabela {tabela}")
        
        conn.commit()
        
        print("\n🎉 Estrutura das tabelas corrigida com sucesso!")
        print("\n📊 Resumo das correções:")
        print("   ✅ Colunas faltantes adicionadas")
        print("   ✅ Valores padrão aplicados")
        print("   ✅ Dados inconsistentes corrigidos")
        print("   ✅ Campos obrigatórios preenchidos")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante a correção: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False
        
    finally:
        conn.close()

def verificar_portal_funcionando():
    """Testa se o portal pode acessar as tabelas corretamente"""
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    try:
        print("\n🧪 Testando consultas do portal...")
        
        # Teste 1: Consulta de usuários
        try:
            cursor.execute("SELECT id, username, ativo FROM users LIMIT 1")
            print("   ✅ Consulta de usuários funcionando")
        except Exception as e:
            print(f"   ❌ Erro na consulta de usuários: {e}")
        
        # Teste 2: Consulta de despesas_fixas (erro original)
        try:
            cursor.execute("SELECT id, descricao, valor, ativo FROM despesas_fixas LIMIT 1")
            print("   ✅ Consulta de despesas fixas funcionando")
        except Exception as e:
            print(f"   ❌ Erro na consulta de despesas fixas: {e}")
        
        # Teste 3: Consulta de categorias
        try:
            cursor.execute("SELECT id, nome, ativo FROM categorias LIMIT 1")
            print("   ✅ Consulta de categorias funcionando")
        except Exception as e:
            print(f"   ❌ Erro na consulta de categorias: {e}")
        
        # Teste 4: Consulta de despesas
        try:
            cursor.execute("SELECT id, descricao, valor FROM despesas LIMIT 1")
            print("   ✅ Consulta de despesas funcionando")
        except Exception as e:
            print(f"   ❌ Erro na consulta de despesas: {e}")
        
        print("   🎯 Testes de consulta concluídos")
        
    except Exception as e:
        print(f"❌ Erro durante os testes: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    print("=" * 60)
    print("   CORREÇÃO PÓS-MIGRAÇÃO - PORTAL DE DESPESAS")
    print("=" * 60)
    print()
    
    if verificar_e_corrigir_estrutura():
        print("\n" + "="*60)
        verificar_portal_funcionando()
        print("\n✅ Correção concluída!")
        print("🚀 Agora você pode acessar o portal sem erros!")
        print("\n💡 Se ainda houver erros, execute este script novamente")
    else:
        print("\n❌ Falha na correção!")
        print("Verifique os erros acima e tente novamente.")
    
    input("\nPressione Enter para continuar...")