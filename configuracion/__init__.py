import pymysql

pymysql.version_info = (2, 2, 8, "final", 0)  # Evita errores de versión
pymysql.install_as_MySQLdb()