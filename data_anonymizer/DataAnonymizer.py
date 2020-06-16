import mysql.connector
import sys
import subprocess
from .ConfigReader import config
from .informationgenerator import get_anonymized_data


class Anonymize:

    def __init__(self):
        self.host = "127.0.0.1"
        self.user = "root"
        self.password = "toor"
        self.database = "anonymizer"
        self.mysql_connection = self.initialise_database_connection()
        self.config = config(open('data_anonymizer/config.yml', 'r'))
        self.cursor = self.mysql_connection.cursor(buffered=True)

    def initialise_database_connection(self):
        return mysql.connector.connect(
            host=self.host,
            user=self.user,
            password=self.password
        )

    def populate_database(self):
        if not len(sys.argv) > 1 or not sys.argv[1].endswith('.sql'):
            print('missing sql dump')
            exit(1)

        self.cursor.execute("drop database if exists {}".format(self.database))
        self.cursor.execute("create database {}".format(self.database))
        self.mysql_connection.commit()
        self.cursor.execute("use {}".format(self.database))

        with open(sys.argv[1], 'r') as f:
            sql_dump = f.read()

        command = subprocess.run(
            ['mysql', '-h', self.host, '-u', self.user, '-p' + self.password, self.database],
            stdout=subprocess.PIPE, input=sql_dump, encoding='utf-8')

        print(command.stdout)

    def export_database(self):
        output_filename = "out.sql"
        command_output = subprocess.check_output(
            ['mysqldump', '-h', self.host, '-u', self.user, '-p' + self.password, self.database])

        with open(output_filename, 'wb') as f:
            f.write(command_output)

    def anonymize_database(self):
        tables = self.config.tables()

        for table in tables:
            self.cursor.execute("select * from anonymizer.{}".format(table))
            rows = self.cursor.fetchall()
            columns = self.config.columns(table)
            iterator = self.config.iterator(table)
            self.update_database(rows, iterator, columns, table)

    def update_database(self, rows, iterator, columns, table):
        for column in columns:
            for row in rows:
                column_data = columns[column]
                value = get_anonymized_data(column_data)
                sql = '''UPDATE anonymizer.{} SET {} = '{}' where {} = '{}' '''.format(
                    table, column, value, iterator, row[0])
                try:
                    self.cursor.execute(sql)
                    self.mysql_connection.commit()
                except Exception as e:
                    print(e)
