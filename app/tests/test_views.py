import mysql.connector


def test_home(client):
    response = client.get("/")

    assert response.status_code == 200


def test_model(client):
    response = client.get("/model")
    assert response.status_code == 200


def test_database_connection():
    mydb = mysql.connector.connect(
        host="HOST",
        user="USER",
        password="PASSWORD",
        database="DATABSE",
        charset='utf8mb4',
        use_unicode=True
    )
    cursor = mydb.cursor()
    cursor.execute("SELECT * FROM aps_dataset.papers LIMIT 10;")
    results = cursor.fetchall()
    assert len(results) > 0
