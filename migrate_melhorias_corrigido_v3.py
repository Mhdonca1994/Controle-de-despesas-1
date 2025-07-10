#!/usr/bin/env python3
"""
Script de Migração CORRIGIDO v3 - Melhorias do Portal de Despesas
Implementa: Casa em Ordem, Despesas Fixas, Cartões de Crédito e Gestão de Usuários
Resolve: Erro "FOREIGN KEY constraint failed"
"""

import sqlite3
import hashlib
from datetime import datetime
import os

DATABASE = 'src/database/app.db'

def hash_password(password):
    """Gera hash da senha usando SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

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

def cleanup_temp_tables(cursor):
    """Remove tabelas temporárias de migrações anteriores incompletas"""
    temp_tables = ['users_new', 'despesas_new', 'categorias_new']
    
    for table in temp_tables:
        if table_exists(cursor, table):
            print(f"   🧹 Removendo tabela temporária: {table}")
            cursor.execute(f"DROP TABLE {table}")

def migrate_users_table(cursor):
    """Migra a tabela de usuários de forma segura"""
    
    # Primeiro, limpar qualquer tabela temporária de migração anterior
    cleanup_temp_tables(cursor)
    
    if not table_exists(cursor, 'users'):
        # Criar tabela nova
        cursor.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                perfil TEXT DEFAULT 'usuario',
                nome_completo TEXT,
                email TEXT,
                ativo BOOLEAN DEFAULT 1,
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        print("   ✅ Tabela users criada")
        return
    
    # Verificar se precisa migrar tabela existente
    needs_migration = False
    new_columns = ['nome_completo', 'email', 'ativo', 'created_at', 'updated_at']
    
    for column in new_columns:
        if not column_exists(cursor, 'users', column):
            needs_migration = True
            break
    
    if needs_migration:
        print("   🔄 Migrando tabela users existente...")
        
        # Garantir que não existe tabela temporária
        if table_exists(cursor, 'users_new'):
            print("   🧹 Removendo tabela temporária anterior...")
            cursor.execute('DROP TABLE users_new')
        
        # DESABILITAR FOREIGN KEYS TEMPORARIAMENTE
        cursor.execute("PRAGMA foreign_keys = OFF")
        
        # Criar tabela temporária com nova estrutura
        cursor.execute('''
            CREATE TABLE users_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                perfil TEXT DEFAULT 'usuario',
                nome_completo TEXT,
                email TEXT,
                ativo BOOLEAN DEFAULT 1,
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        
        # Copiar dados existentes
        cursor.execute('''
            INSERT INTO users_new (id, username, password_hash, perfil, nome_completo, email, ativo, created_at, updated_at)
            SELECT 
                id, 
                username, 
                password_hash, 
                COALESCE(perfil, 'usuario'),
                CASE 
                    WHEN username = 'master' THEN 'Administrador Master'
                    WHEN username = 'daniela' THEN 'Daniela Silva'
                    WHEN username = 'paulo' THEN 'Paulo Santos'
                    ELSE username
                END,
                CASE 
                    WHEN username = 'master' THEN 'admin@portal.com'
                    WHEN username = 'daniela' THEN 'daniela@email.com'
                    WHEN username = 'paulo' THEN 'paulo@email.com'
                    ELSE NULL
                END,
                1,
                datetime('now'),
                datetime('now')
            FROM users
        ''')
        
        # Verificar se a cópia foi bem-sucedida
        old_count = cursor.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        new_count = cursor.execute('SELECT COUNT(*) FROM users_new').fetchone()[0]
        
        if old_count != new_count:
            raise Exception(f"Erro na migração: dados perdidos ({old_count} -> {new_count})")
        
        # Remover tabela antiga e renomear nova
        cursor.execute('DROP TABLE users')
        cursor.execute('ALTER TABLE users_new RENAME TO users')
        
        # REABILITAR FOREIGN KEYS
        cursor.execute("PRAGMA foreign_keys = ON")
        
        print("   ✅ Tabela users migrada com sucesso")
    else:
        print("   ✅ Tabela users já está atualizada")

def safe_add_column(cursor, table_name, column_name, column_type, default_value=None):
    """Adiciona uma coluna de forma segura"""
    if not column_exists(cursor, table_name, column_name):
        if default_value is not None:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type} DEFAULT {default_value}")
        else:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
        
        # Se for created_at, atualizar registros existentes
        if column_name == 'created_at' and default_value is None:
            cursor.execute(f"UPDATE {table_name} SET {column_name} = datetime('now') WHERE {column_name} IS NULL")
        
        print(f"   ➕ Coluna '{column_name}' adicionada à tabela {table_name}")
        return True
    return False

def migrate_categorias_table(cursor):
    """Migra a tabela de categorias de forma segura"""
    
    if not table_exists(cursor, 'categorias'):
        cursor.execute('''
            CREATE TABLE categorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                descricao TEXT,
                cor TEXT DEFAULT '#667eea',
                icone TEXT DEFAULT 'fas fa-tag',
                ativo BOOLEAN DEFAULT 1,
                created_at TEXT
            )
        ''')
        print("   ✅ Tabela categorias criada")
        return
    
    # Verificar e adicionar colunas faltantes
    columns_to_add = [
        ('descricao', 'TEXT', None),
        ('cor', 'TEXT', "'#667eea'"),
        ('icone', 'TEXT', "'fas fa-tag'"),
        ('ativo', 'BOOLEAN', '1'),
        ('created_at', 'TEXT', None)
    ]
    
    for column_name, column_type, default_val in columns_to_add:
        safe_add_column(cursor, 'categorias', column_name, column_type, default_val)
    
    print("   ✅ Tabela categorias atualizada")

def insert_categoria_safe(cursor, nome, descricao, cor, icone):
    """Insere categoria verificando quais colunas existem"""
    
    # Verificar se categoria já existe
    existe = cursor.execute('SELECT id FROM categorias WHERE nome = ?', (nome,)).fetchone()
    if existe:
        return
    
    # Verificar quais colunas existem
    columns = get_table_columns(cursor, 'categorias')
    
    # Preparar dados baseado nas colunas existentes
    insert_columns = ['nome']
    insert_values = [nome]
    placeholders = ['?']
    
    if 'descricao' in columns:
        insert_columns.append('descricao')
        insert_values.append(descricao)
        placeholders.append('?')
    
    if 'cor' in columns:
        insert_columns.append('cor')
        insert_values.append(cor)
        placeholders.append('?')
    
    if 'icone' in columns:
        insert_columns.append('icone')
        insert_values.append(icone)
        placeholders.append('?')
    
    if 'ativo' in columns:
        insert_columns.append('ativo')
        insert_values.append(1)
        placeholders.append('?')
    
    if 'created_at' in columns:
        insert_columns.append('created_at')
        insert_values.append(datetime.now().isoformat())
        placeholders.append('?')
    
    # Montar e executar query
    query = f"INSERT INTO categorias ({', '.join(insert_columns)}) VALUES ({', '.join(placeholders)})"
    cursor.execute(query, insert_values)

def migrate_database():
    """Executa todas as migrações necessárias"""
    print("🔄 Iniciando migração das melhorias...")
    
    # Criar diretório do banco se não existir
    os.makedirs('src/database', exist_ok=True)
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    try:
        # NÃO HABILITAR FOREIGN KEYS NO INÍCIO - será feito seletivamente
        
        # Começar transação
        cursor.execute("BEGIN TRANSACTION")
        
        # 1. MIGRAR TABELA DE USUÁRIOS (sem foreign keys)
        print("📊 [1/8] Migrando tabela de usuários...")
        migrate_users_table(cursor)
        
        # 2. CRIAR TABELA DE GRUPOS (CASA EM ORDEM)
        print("🏠 [2/8] Criando sistema Casa em Ordem...")
        
        if not table_exists(cursor, 'grupos'):
            cursor.execute('''
                CREATE TABLE grupos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    descricao TEXT,
                    tipo TEXT DEFAULT 'familia',
                    criado_por INTEGER,
                    ativo BOOLEAN DEFAULT 1,
                    created_at TEXT,
                    FOREIGN KEY (criado_por) REFERENCES users (id)
                )
            ''')
            print("   ✅ Tabela grupos criada")
        
        if not table_exists(cursor, 'grupo_membros'):
            cursor.execute('''
                CREATE TABLE grupo_membros (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    grupo_id INTEGER,
                    user_id INTEGER,
                    papel TEXT DEFAULT 'membro',
                    adicionado_por INTEGER,
                    created_at TEXT,
                    FOREIGN KEY (grupo_id) REFERENCES grupos (id),
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (adicionado_por) REFERENCES users (id),
                    UNIQUE(grupo_id, user_id)
                )
            ''')
            print("   ✅ Tabela grupo_membros criada")
        
        # 3. CRIAR TABELA DE CARTÕES DE CRÉDITO
        print("💳 [3/8] Criando sistema de cartões de crédito...")
        
        if not table_exists(cursor, 'cartoes'):
            cursor.execute('''
                CREATE TABLE cartoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    descricao TEXT,
                    dia_vencimento INTEGER NOT NULL,
                    dia_fechamento INTEGER NOT NULL,
                    limite_credito REAL DEFAULT 0,
                    bandeira TEXT,
                    user_id INTEGER,
                    ativo BOOLEAN DEFAULT 1,
                    created_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            print("   ✅ Tabela cartoes criada")
        
        # 4. MIGRAR TABELA DE CATEGORIAS
        print("🏷️ [4/8] Migrando tabela de categorias...")
        migrate_categorias_table(cursor)
        
        # 5. CRIAR TABELA DE DESPESAS FIXAS
        print("📅 [5/8] Criando sistema de despesas fixas...")
        
        if not table_exists(cursor, 'despesas_fixas'):
            cursor.execute('''
                CREATE TABLE despesas_fixas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    descricao TEXT NOT NULL,
                    valor REAL NOT NULL,
                    dia_vencimento INTEGER NOT NULL,
                    categoria_id INTEGER,
                    pagador TEXT,
                    forma_pagamento TEXT,
                    observacoes TEXT,
                    user_id INTEGER,
                    grupo_id INTEGER,
                    ativo BOOLEAN DEFAULT 1,
                    created_at TEXT,
                    FOREIGN KEY (categoria_id) REFERENCES categorias (id),
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (grupo_id) REFERENCES grupos (id)
                )
            ''')
            print("   ✅ Tabela despesas_fixas criada")
        
        # 6. MIGRAR TABELA DE DESPESAS
        print("💰 [6/8] Migrando tabela de despesas...")
        
        if not table_exists(cursor, 'despesas'):
            cursor.execute('''
                CREATE TABLE despesas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    descricao TEXT NOT NULL,
                    valor REAL NOT NULL,
                    data DATE NOT NULL,
                    pagador TEXT,
                    forma_pagamento TEXT,
                    categoria_id INTEGER,
                    cartao_id INTEGER,
                    grupo_id INTEGER,
                    despesa_fixa_id INTEGER,
                    parcela_atual INTEGER DEFAULT 1,
                    total_parcelas INTEGER DEFAULT 1,
                    grupo_parcela TEXT,
                    tipo TEXT DEFAULT 'individual',
                    observacoes TEXT,
                    user_id INTEGER,
                    created_at TEXT,
                    FOREIGN KEY (categoria_id) REFERENCES categorias (id),
                    FOREIGN KEY (cartao_id) REFERENCES cartoes (id),
                    FOREIGN KEY (grupo_id) REFERENCES grupos (id),
                    FOREIGN KEY (despesa_fixa_id) REFERENCES despesas_fixas (id),
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            print("   ✅ Tabela despesas criada")
        else:
            # Verificar se precisa adicionar novas colunas
            new_columns = [
                ('cartao_id', 'INTEGER', None),
                ('grupo_id', 'INTEGER', None),
                ('despesa_fixa_id', 'INTEGER', None),
                ('observacoes', 'TEXT', None),
                ('created_at', 'TEXT', None)
            ]
            
            columns_added = []
            for column_name, column_type, default_val in new_columns:
                if safe_add_column(cursor, 'despesas', column_name, column_type, default_val):
                    columns_added.append(column_name)
            
            if columns_added:
                print(f"   ✅ Colunas adicionadas: {', '.join(columns_added)}")
            else:
                print("   ✅ Tabela despesas já está atualizada")
        
        # 7. INSERIR DADOS PADRÃO
        print("📝 [7/8] Inserindo dados padrão...")
        
        # Usuários padrão (verificar se já existem)
        usuarios_padrao = [
            ('master', hash_password('Admin@Mhd051121'), 'Master', 'Administrador Master', 'admin@portal.com'),
            ('daniela', hash_password('senha123'), 'usuario', 'Daniela Silva', 'daniela@email.com'),
            ('paulo', hash_password('senha123'), 'usuario', 'Paulo Santos', 'paulo@email.com')
        ]
        
        for username, password_hash, perfil, nome, email in usuarios_padrao:
            # Verificar se usuário já existe
            existe = cursor.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
            if not existe:
                cursor.execute('''
                    INSERT INTO users (username, password_hash, perfil, nome_completo, email, ativo, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, 1, datetime('now'), datetime('now'))
                ''', (username, password_hash, perfil, nome, email))
            else:
                # Atualizar dados se necessário
                cursor.execute('''
                    UPDATE users SET 
                        password_hash = ?, 
                        perfil = ?, 
                        nome_completo = COALESCE(nome_completo, ?), 
                        email = COALESCE(email, ?),
                        updated_at = datetime('now')
                    WHERE username = ?
                ''', (password_hash, perfil, nome, email, username))
        
        # Categorias padrão - inserir de forma segura
        categorias_padrao = [
            ('Alimentação', 'Gastos com comida e bebidas', '#28a745', 'fas fa-utensils'),
            ('Transporte', 'Combustível, transporte público, etc.', '#007bff', 'fas fa-car'),
            ('Moradia', 'Aluguel, condomínio, IPTU, etc.', '#6f42c1', 'fas fa-home'),
            ('Saúde', 'Médicos, medicamentos, planos', '#dc3545', 'fas fa-heartbeat'),
            ('Educação', 'Cursos, livros, material escolar', '#fd7e14', 'fas fa-graduation-cap'),
            ('Lazer', 'Cinema, restaurantes, viagens', '#e83e8c', 'fas fa-gamepad'),
            ('Vestuário', 'Roupas, calçados, acessórios', '#20c997', 'fas fa-tshirt'),
            ('Tecnologia', 'Eletrônicos, internet, telefone', '#6c757d', 'fas fa-laptop'),
            ('Casa em Ordem', 'Despesas familiares compartilhadas', '#667eea', 'fas fa-users'),
            ('Cartão de Crédito', 'Despesas no cartão de crédito', '#ffc107', 'fas fa-credit-card')
        ]
        
        for nome, desc, cor, icone in categorias_padrao:
            insert_categoria_safe(cursor, nome, desc, cor, icone)
        
        # Grupo padrão "Família"
        existe_grupo = cursor.execute('SELECT id FROM grupos WHERE nome = ?', ('Família',)).fetchone()
        if not existe_grupo:
            # Pegar ID do usuário master
            master_id = cursor.execute('SELECT id FROM users WHERE username = ?', ('master',)).fetchone()
            if master_id:
                master_id = master_id[0]
                cursor.execute('''
                    INSERT INTO grupos (nome, descricao, tipo, criado_por, ativo, created_at)
                    VALUES ('Família', 'Grupo familiar para despesas compartilhadas', 'familia', ?, 1, datetime('now'))
                ''', (master_id,))
                
                # Pegar ID do grupo criado
                grupo_id = cursor.lastrowid
                
                # Adicionar todos os usuários ao grupo família
                usuarios = cursor.execute('SELECT id FROM users').fetchall()
                for user_id, in usuarios:
                    cursor.execute('''
                        INSERT INTO grupo_membros (grupo_id, user_id, papel, adicionado_por, created_at)
                        VALUES (?, ?, 'membro', ?, datetime('now'))
                    ''', (grupo_id, user_id, master_id))
        
        print("   ✅ Dados padrão inseridos")
        
        # 8. CRIAR ÍNDICES PARA PERFORMANCE
        print("⚡ [8/8] Criando índices para performance...")
        
        indices = [
            "CREATE INDEX IF NOT EXISTS idx_despesas_data ON despesas(data)",
            "CREATE INDEX IF NOT EXISTS idx_despesas_user ON despesas(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_despesas_grupo ON despesas(grupo_id)",
            "CREATE INDEX IF NOT EXISTS idx_despesas_cartao ON despesas(cartao_id)",
            "CREATE INDEX IF NOT EXISTS idx_grupo_membros_grupo ON grupo_membros(grupo_id)",
            "CREATE INDEX IF NOT EXISTS idx_grupo_membros_user ON grupo_membros(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_cartoes_user ON cartoes(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_despesas_fixas_user ON despesas_fixas(user_id)"
        ]
        
        for indice in indices:
            cursor.execute(indice)
        
        print("   ✅ Índices criados")
        
        # HABILITAR FOREIGN KEYS NOVAMENTE NO FINAL
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Commit da transação
        cursor.execute("COMMIT")
        
        print("\n🎉 Migração concluída com sucesso!")
        print("\n📊 Resumo das melhorias implementadas:")
        print("   ✅ Sistema Casa em Ordem (grupos familiares)")
        print("   ✅ Despesas Fixas (recorrentes mensais)")
        print("   ✅ Cartões de Crédito (com faturas)")
        print("   ✅ Gestão de Usuários (perfis Master/Usuário)")
        print("   ✅ Categorias expandidas")
        print("   ✅ Índices de performance")
        print("   ✅ Migração segura de dados existentes")
        print("   ✅ Correção do erro 'users_new already exists'")
        print("   ✅ Correção do erro 'table categorias has no column named descricao'")
        print("   ✅ Correção do erro 'FOREIGN KEY constraint failed'")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante a migração: {e}")
        import traceback
        traceback.print_exc()
        cursor.execute("ROLLBACK")
        
        # Tentar limpar tabelas temporárias em caso de erro
        try:
            cursor.execute("PRAGMA foreign_keys = OFF")
            cleanup_temp_tables(cursor)
            conn.commit()
        except:
            pass
        
        return False
        
    finally:
        conn.close()

if __name__ == '__main__':
    print("=" * 50)
    print("   MIGRAÇÃO CORRIGIDA v3 - MELHORIAS DO PORTAL")
    print("=" * 50)
    print()
    
    if migrate_database():
        print("\n✅ Migração executada com sucesso!")
        print("🚀 O portal agora possui todas as novas funcionalidades!")
        print("\n🔑 Credenciais de acesso:")
        print("   👑 Master: master / Admin@Mhd051121")
        print("   👤 Daniela: daniela / senha123")
        print("   👤 Paulo: paulo / senha123")
        print("\n📋 Próximos passos:")
        print("   1. Substitua src/main.py pelo main_melhorado.py")
        print("   2. Execute o portal normalmente")
        print("   3. Acesse as novas funcionalidades!")
    else:
        print("\n❌ Falha na migração!")
        print("Verifique os erros acima e tente novamente.")
    
    input("\nPressione Enter para continuar...")