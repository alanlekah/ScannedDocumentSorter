import json, os
 
__version__ = '1.0'
__author__  = 'DirectorX'
 
db_name = 'udb.xdb'
def check_db(name = db_name):
    if not os.path.isfile(name):
        print ('[Database] %s database not found\n[Database] Creating..' % name)
        udb = open(name,'wb')
        udb.close()
       
def read_db(name = db_name):
    try:
        udb = open(name, 'rb')
    except:
        check_db(name)
        read_db(name)
    try:
        dicT = json.load(udb)
        udb.close()
        return dicT
    except:
        return {}
   
def update_db(newdata, name = db_name):
    data = read_db(name)
    wdb = dict(data.items() + newdata.items())    
    udb = open(name, 'wb')
    json.dump(wdb, udb)
    udb.close()
    check_db(name)
 
def clear_db(name = db_name):
    try:
        os.remove(name)
        check_db(name)
    except:
        print 'Error: ' + name + ' file not found'
 
def del_db(name = db_name):
    try:
        os.remove(name)
    except:
        print 'Error: ' + name + ' file not found'
 
 
if __name__ == '__main__':
    def files():
        print 'Files list:'
        dirs = os.listdir(str(os.getcwd()))
        for file in dirs:
           if '.xdb' in str(file):
               print str(file) + ' (xDB format)'
           else:
               print file
        print
    def cd(dIr):
        os.chdir(dIr)
   
    print __author__ + '  -  Simple database ' + __version__ + ' : for help type: print help_me\n'
    help_me = '''
Commands:
1) check_db  - using: check_db('DatabaseName.xdb')
2) read_db   - using: print read_db('DatabaseName.xdb')
3) update_db - using: update_db({'Key':'Value'} ,'DatabaseName.xdb')
4) clear_db  - using: clear_db('DatabaseName.xdb')
5) del_db    - using: del_db('DatabaseName.xdb')
 
6) files     - using: files()
7) cd        - using: cd('directory path')
 
8) exit()    - using: exit() or quit()
'''

#    while True:
#        try:
#            exec(raw_input(str(os.getcwd()) + '> '))
#        except Exception as e:
#            print 'Error: ' + str(e)
