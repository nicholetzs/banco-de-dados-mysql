from flask import render_template, request, redirect, url_for


def init_app(app, db):

  @app.route('/')
  def index():
    # Exibindo a splash screen com informações sobre nossa locadora
    return render_template('splash_screen.html')

  @app.route('/index')
  def list_carros():
    connection = db.get_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute('SELECT * FROM CARROS')
    carros = cursor.fetchall()

    cursor.execute('SELECT * FROM CLIENTES')
    clientes = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template('index.html', carros=carros, clientes=clientes)

  @app.route('/add_carro', methods=['POST'])
  def add_carro():
    modelo = request.form['modelo']
    ano = request.form['ano']
    marca = request.form['marca']
    disponibilidade = request.form.get('disponibilidade', 'off') == 'on'

    connection = db.get_connection()
    cursor = connection.cursor()

    cursor.execute(
        'INSERT INTO CARROS (MODELO, ANO, MARCA, DISPONIBILIDADE) VALUES (%s, %s, %s, %s)',
        (modelo, ano, marca, disponibilidade)
    )
    connection.commit()
    cursor.close()
    connection.close()

    return redirect(url_for('list_carros'))

  @app.route('/delete_carro/<int:carro_id>', methods=['POST'])
  def delete_carro(carro_id):
    connection = db.get_connection()
    cursor = connection.cursor()
    cursor.execute('DELETE FROM LOCACAO WHERE ID_CARRO = %s', (carro_id,))
    cursor.execute('DELETE FROM CARROS WHERE ID = %s', (carro_id,))
    connection.commit()
    cursor.close()
    connection.close()
    return redirect(url_for('list_carros'))

  @app.route('/edit_carro/<int:carro_id>', methods=['GET', 'POST'])
  def edit_carro(carro_id):
    if request.method == 'POST':
      modelo = request.form['modelo']
      ano = request.form['ano']
      marca = request.form['marca']
      disponibilidade = request.form.get('disponibilidade', 'off') == 'on'

      connection = db.get_connection()
      cursor = connection.cursor()
      cursor.execute(
          'UPDATE CARROS SET MODELO = %s, ANO = %s, MARCA = %s, DISPONIBILIDADE = %s WHERE ID = %s',
          (modelo, ano, marca, disponibilidade, carro_id)
      )
      connection.commit()
      cursor.close()
      connection.close()

      return redirect(url_for('list_carros'))

    connection = db.get_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute('SELECT * FROM CARROS WHERE ID = %s', (carro_id,))
    carro = cursor.fetchone()
    cursor.close()
    connection.close()

    return render_template('edit.html', carro=carro)

  @app.route('/alugar_carro/<int:carro_id>', methods=['POST'])
  def alugar_carro(carro_id):
    connection = db.get_connection()
    cursor = connection.cursor(dictionary=True)

    cliente_id = request.form.get('id_cliente')
    data_locacao = request.form.get('data_locacao')
    data_retorno = request.form.get('data_retorno')
    valor_diaria = request.form.get('valor_diaria')

    try:
      cursor.execute(
          "SELECT DISPONIBILIDADE FROM CARROS WHERE ID = %s", (carro_id,))
      disponibilidade = cursor.fetchone()

      if not disponibilidade:
        return "O carro não foi encontrado."

      if not disponibilidade['DISPONIBILIDADE']:
        return "O carro já está alugado ou indisponível."

      cursor.execute(
          """INSERT INTO LOCACAO (ID_CARRO, ID_CLIENTE, DATA_LOCACAO, DATA_RETORNO, VALOR_DIARIA) 
                VALUES (%s, %s, %s, %s, %s)""",
          (carro_id, cliente_id, data_locacao, data_retorno, valor_diaria)
      )
      connection.commit()

      cursor.execute(
          "UPDATE CARROS SET DISPONIBILIDADE = FALSE WHERE ID = %s", (carro_id,))
      connection.commit()

      return redirect(url_for('list_carros'))

    except Exception as e:
      connection.rollback()
      return f"Ocorreu um erro: {str(e)}"

    finally:
      cursor.close()
      connection.close()

  @app.route('/devolver_carro/<int:carro_id>', methods=['POST'])
  def devolver_carro(carro_id):
    disponibilidade = request.form.get('disponibilidade') == 'on'

    connection = db.get_connection()
    cursor = connection.cursor()

    try:
      if disponibilidade:
        cursor.execute(
            "UPDATE CARROS SET DISPONIBILIDADE = TRUE WHERE ID = %s", (carro_id,))
      else:
        cursor.execute(
            "UPDATE CARROS SET DISPONIBILIDADE = FALSE WHERE ID = %s", (carro_id,))
      connection.commit()

      return redirect(url_for('list_carros'))

    except Exception as e:
      connection.rollback()
      return f"Ocorreu um erro ao devolver o carro: {str(e)}"

    finally:
      cursor.close()
      connection.close()

  @app.route('/relatorios')
  def list_reservas():
    connection = db.get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
            SELECT CARROS.ID AS carro_id, CARROS.MODELO, CARROS.ANO, CARROS.MARCA,
                   CLIENTES.NOME AS cliente_nome, CLIENTES.ID AS cliente_id
            FROM LOCACAO
            JOIN CARROS ON LOCACAO.ID_CARRO = CARROS.ID
            JOIN CLIENTES ON LOCACAO.ID_CLIENTE = CLIENTES.ID
            WHERE CARROS.DISPONIBILIDADE = FALSE
        """)
    reservas = cursor.fetchall()

    cursor.execute('SELECT COUNT(*) AS total FROM LOCACAO')

    total_locacoes = cursor.fetchone()['total']

    cursor.close()
    connection.close()

    return render_template('relatorios.html', reservas=reservas, total_locacoes=total_locacoes)
