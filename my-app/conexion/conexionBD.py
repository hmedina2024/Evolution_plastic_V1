

# Importando Libreria mysql.connector para conectar Python con MySQL
import mysql.connector


def connectionBD():
    try:
        # connection = mysql.connector.connect(
        connection = mysql.connector.connect(
            host="217.15.171.201",
            user="root",
            passwd="Evolution123#",
            database="evolution_DB",
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci',
            raise_on_warnings=True

        )
        if connection.is_connected():
            # print("Conexión exitosa a la BD")
            return connection

    except mysql.connector.Error as error:
        print(f"No se pudo conectar: {error}")
        
        
# AZURE
# connection = mysql.connector.connect(
#             host="data-evolution-plastics.mysql.database.azure.com",
#             user="admin123",
#             passwd="Evolutionplastic123",
#             database="evolution_plastic",
#             charset='utf8mb4',
#             collation='utf8mb4_general_ci',
#             raise_on_warnings=True
