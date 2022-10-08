import sqlite3
import uuid
# create table
# sql = '''
# create table token_info
#     (token text not null,
#     person text not null
#     )
#
# '''
def do_create(sql):
    connect = sqlite3.connect('data.db')
    cursor = connect.cursor()
    cursor.execute(sql)
    cursor.close()
    connect.close()



def query_sql(sql):
    connect = sqlite3.connect('./data.db')
    cursor = connect.cursor()
    cursor.execute(sql)
    result=cursor.fetchall()
    cursor.close()
    connect.close()
    return result

def query_token():
    sql='select * from token_info;'
    result=query_sql(sql)
    return [i[0] for i in result]











